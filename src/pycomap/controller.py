"""High-level ``Controller`` — a caching, name-aware client for ComAp controllers.

``Controller`` wraps a ``ComApClient`` and fetches the ``ConfigurationTable`` once on
connect, enabling value/setpoint lookup by human-readable name, transparent password
elevation for protected setpoints, and timezone-aware time synchronisation.

Typical usage::

    from ipaddress import IPv4Address

    import pytz
    from pycomap import Controller
    from pycomap.protocol import ComApClient
    from pycomap.protocol.transport import EthernetTransport

    tz = pytz.timezone("Europe/Kiev")
    async with Controller(
        ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))),
        access_code="0",
        password=1234,
    ) as ctrl:
        values = await ctrl.read_values()
        await ctrl.set_setpoint("Nominal RPM", 1500)
        await ctrl.sync_time(tz=tz)
"""

from __future__ import annotations

import datetime
import logging
import re
from collections.abc import Mapping
from types import MappingProxyType, TracebackType
from typing import Self

from pycomap.alarms import AlarmRecord, parse_alarm_list
from pycomap.configuration import (
    ConfigurationTable,
    NamesCategory,
    SetpointDescription,
    ValueCategory,
    ValueDescription,
    ValueState,
    decode_history_snapshot,
    decode_setpoints_all,
    decode_states_all,
    decode_values_all,
    parse_configuration_table,
    parse_names_heap,
)
from pycomap.datatypes import (
    _BINARY_TYPES,
    _DATA_TYPE_LENGTH,
    DataType,
    RawValue,
    Value,
    decode_raw_value,
    encode_raw_value,
)
from pycomap.exceptions import ComApAuthError, ComApProtocolError
from pycomap.history import HistoryRecord, parse_history_record
from pycomap.protocol.client import ComApClient
from pycomap.protocol.commands import ControllerCommand
from pycomap.protocol.objects import CommunicationObject
from pycomap.protocol.transport import Transport

_log = logging.getLogger(__name__)

_STRING_TYPES = frozenset(
    {
        DataType.SHORT_STRING,
        DataType.LONG_STRING,
        DataType.HUGE_STRING,
        DataType.IP_ADDRESS,
        DataType.TELEPHONE_NUMBER,
        DataType.EMAIL,
    }
)

_INDEX_TYPES = frozenset({DataType.STRING_LIST, DataType.CHAR})

# Types for which low_limit/high_limit represent a valid numeric range to enforce.
_RANGE_VALIDATABLE = frozenset(
    {
        DataType.INTEGER8,
        DataType.INTEGER16,
        DataType.INTEGER32,
        DataType.UNSIGNED8,
        DataType.UNSIGNED16,
        DataType.UNSIGNED32,
    }
)

# Human-readable setpoint names used to look up timezone configuration.
# Looked up by name at connect time so no hardcoded comm object numbers are needed.
_SETPOINT_TIME_ZONE = "Time Zone"
_SETPOINT_SUMMER_TIME_MODE = "Summer Time Mode"

# Summer Time Mode option labels that indicate DST is active (+1 h on top of base offset).
_SUMMER_MODE_DST_LABELS = frozenset({"Summer", "Summer-S"})


def _parse_gmt_label(label: str) -> datetime.timedelta | None:
    """Parse a ComAp timezone label like ``'GMT+2:00'`` or ``'GMT-3:30'`` into a
    ``timedelta``.  Returns ``None`` if the label cannot be parsed.
    """
    m = re.fullmatch(r"GMT([+-])(\d{1,2}):(\d{2})", label.strip())
    if not m:
        return None
    sign = 1 if m.group(1) == "+" else -1
    hours, minutes = int(m.group(2)), int(m.group(3))
    if hours > 23 or minutes > 59:
        return None
    return sign * datetime.timedelta(hours=hours, minutes=minutes)


def _encode_setpoint_value(
    data_type: DataType,
    decimal_places: int,
    value: Value,
) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        if data_type not in _STRING_TYPES:
            raise ComApProtocolError(
                f"str value given for DataType.{data_type.name}; "
                "expected int/float or pass bytes directly"
            )
        encoded = value.encode("ascii")
        length = _DATA_TYPE_LENGTH[data_type]
        return encoded[:length].ljust(length, b"\x00")
    if data_type in _INDEX_TYPES:
        return bytes([int(value)])
    return encode_raw_value(data_type, value, decimal_places)


class Controller[TransportT: Transport]:
    """High-level async client for a ComAp controller.

    Fetches and caches the ``ConfigurationTable`` on [connect][pycomap.Controller.connect],
    enabling name-based lookup for all subsequent calls.  Password elevation for
    write-protected setpoints is handled automatically (lazy, on first protected write)
    when ``password`` is provided.

    Args:
        client: A ``ComApClient`` wrapping any transport.  The ``Controller`` takes
            ownership of the connection lifecycle — do not call ``client.connect()`` yourself.
        access_code: The controller's AccessCode (base/anonymous read-only code, often
            ``"0"``).  Drives ECDH/AES key derivation — **not** the write password.
        password: The write-protection password (integer 0-9999).  Required for setpoints
            with ``access_level > 0``; omit to operate in read-only mode.
        include_invisible: When ``False`` (default), ONE_TIME values in the ``'Invisible'``
            group are skipped during connect, saving one ``read_object`` round-trip per
            invisible item.  Set to ``True`` to cache them anyway.

    Examples:
        Read-only access::

            async with Controller(
                ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))), access_code="0"
            ) as ctrl:
                values = await ctrl.read_values()

        With write access::

            async with Controller(
                ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))),
                access_code="0",
                password=1234,
            ) as ctrl:
                await ctrl.set_setpoint("Nominal RPM", 1500)
    """

    def __init__(
        self,
        client: ComApClient[TransportT],
        access_code: str,
        password: int | None = None,
        include_invisible: bool = False,
    ) -> None:
        self._client = client
        self._access_code = access_code
        self._password = password
        self._include_invisible = include_invisible
        self._elevated = False
        self._config_data: bytes | None = None
        self._table: ConfigurationTable | None = None
        self._values_by_name: dict[str, ValueDescription] = {}
        self._values_by_number: dict[int, ValueDescription] = {}
        self._ambiguous_value_names: set[str] = set()
        self._setpoints_by_name: dict[str, SetpointDescription] = {}
        self._setpoints_by_number: dict[int, SetpointDescription] = {}
        self._ambiguous_setpoint_names: set[str] = set()
        self._common_names: list[str] = []
        self._timezone: datetime.timezone = datetime.UTC
        self._summer_time_mode_raw: int = 0
        self._one_time_values: dict[int, Value] = {}

    # -- connection lifecycle -------------------------------------------------

    async def connect(self) -> None:
        """Open the transport, authenticate, and fetch the ``ConfigurationTable``."""
        await self._client.connect()
        await self._client.authenticate(self._access_code)
        await self._load_config()

    async def close(self) -> None:
        """Close the underlying transport."""
        await self._client.close()

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- properties ----------------------------------------------------------

    @property
    def client(self) -> ComApClient[TransportT]:
        """The underlying low-level client (escape hatch for direct comm object access)."""
        return self._client

    @property
    def table(self) -> ConfigurationTable:
        """The cached ``ConfigurationTable``.

        Available after [connect][pycomap.Controller.connect].
        """
        if self._table is None:
            raise ComApProtocolError("not connected — call connect() first")
        return self._table

    # -- listing -------------------------------------------------------------

    @property
    def values(self) -> list[ValueDescription]:
        """All value descriptions from the cached ``ConfigurationTable``."""
        return self.table.values

    @property
    def setpoints(self) -> list[SetpointDescription]:
        """All setpoint descriptions from the cached ``ConfigurationTable``."""
        return self.table.setpoints

    @property
    def one_time_values(self) -> Mapping[int, Value]:
        """Static ``ONE_TIME`` values read once at connect time.

        Returns a read-only ``{comm_object_number: value}`` mapping for every ``ONE_TIME``
        value successfully read during [connect][pycomap.Controller.connect]. Entries use
        the same type and resolution rules as [read_values][pycomap.Controller.read_values].
        Empty before connect; stable for the lifetime of the connection.
        """
        return MappingProxyType(self._one_time_values)

    # -- name / number resolution --------------------------------------------

    def value_info(self, name_or_number: str | int) -> ValueDescription:
        """Look up a value description by name or comm object number.

        Args:
            name_or_number: Exact value name (e.g. ``"RPM"``) or comm object number.

        Returns:
            The matching ``ValueDescription``.

        Raises:
            KeyError: If no value with that name or number exists.
            ComApProtocolError: If the name is shared by multiple values — use a number instead.
        """
        if isinstance(name_or_number, int):
            try:
                return self._values_by_number[name_or_number]
            except KeyError:
                raise KeyError(f"no value with number {name_or_number}") from None
        if name_or_number in self._ambiguous_value_names:
            raise ComApProtocolError(
                f"value name {name_or_number!r} is ambiguous — "
                "multiple values share this name; use a comm object number instead"
            )
        try:
            return self._values_by_name[name_or_number]
        except KeyError:
            raise KeyError(f"no value named {name_or_number!r}") from None

    def setpoint_info(self, name_or_number: str | int) -> SetpointDescription:
        """Look up a setpoint description by name or comm object number.

        Args:
            name_or_number: Exact setpoint name (e.g. ``"Nominal RPM"``) or comm object number.

        Returns:
            The matching ``SetpointDescription``.

        Raises:
            KeyError: If no setpoint with that name or number exists.
            ComApProtocolError: If the name is shared by multiple setpoints — use a number instead.
        """
        if isinstance(name_or_number, int):
            try:
                return self._setpoints_by_number[name_or_number]
            except KeyError:
                raise KeyError(f"no setpoint with number {name_or_number}") from None
        if name_or_number in self._ambiguous_setpoint_names:
            raise ComApProtocolError(
                f"setpoint name {name_or_number!r} is ambiguous — "
                "multiple setpoints share this name; use a comm object number instead"
            )
        try:
            return self._setpoints_by_name[name_or_number]
        except KeyError:
            raise KeyError(f"no setpoint named {name_or_number!r}") from None

    def _string_list_options(
        self, desc: ValueDescription | SetpointDescription
    ) -> list[tuple[int, str]]:
        """Shared ``STRING_LIST`` option lookup for
        [value_options][pycomap.Controller.value_options] and
        [setpoint_options][pycomap.Controller.setpoint_options].

        Options are stored in ``CommonNames`` at indices ``[low_limit .. high_limit]``.
        """
        if desc.data_type is not DataType.STRING_LIST:
            raise ComApProtocolError(
                f"{desc.name!r} is DataType.{desc.data_type.name}, not STRING_LIST"
            )
        return [
            (wire_value, self._common_names[desc.low_limit + wire_value])
            for wire_value in range(desc.high_limit - desc.low_limit + 1)
            if desc.low_limit + wire_value < len(self._common_names)
        ]

    def value_options(self, name_or_number: str | int) -> list[tuple[int, str]]:
        """Return the available options for a ``STRING_LIST`` value.

        Options are stored in ``CommonNames`` at indices ``[low_limit .. high_limit]``.
        The wire value (0-based) is what the controller sends on the wire and what
        [value_label][pycomap.Controller.value_label] expects; the label is the string
        shown on the front panel and in InteliConfig. Note that
        [read_values][pycomap.Controller.read_values] resolves ``STRING_LIST`` values to
        their label automatically — this method is for enumerating all possible options
        up front (e.g. to build a legend or validate against known states).

        Args:
            name_or_number: Value name or comm object number.

        Returns:
            ``[(wire_value, label), ...]`` ordered by wire value.

        Raises:
            ComApProtocolError: If the value is not ``STRING_LIST`` type.

        Examples:
            >>> ctrl.value_options("Engine State")
            [(0, 'Ready'), (1, 'Prestart'), (2, 'Cranking'), ...]
        """
        return self._string_list_options(self.value_info(name_or_number))

    def setpoint_options(self, name_or_number: str | int) -> list[tuple[int, str]]:
        """Return the available options for a ``STRING_LIST`` setpoint.

        Options are stored in ``CommonNames`` at indices ``[low_limit .. high_limit]``.
        The wire value (0-based) is what you pass to
        [set_setpoint][pycomap.Controller.set_setpoint]; the label is
        the string shown on the front panel and in InteliConfig.

        Args:
            name_or_number: Setpoint name or comm object number.

        Returns:
            ``[(wire_value, label), ...]`` ordered by wire value.

        Raises:
            ComApProtocolError: If the setpoint is not ``STRING_LIST`` type.

        Examples:
            >>> ctrl.setpoint_options("Summer Time Mode")
            [(0, 'Disabled'), (1, 'Winter'), (2, 'Summer'), (3, 'Winter-S'), (4, 'Summer-S')]
        """
        return self._string_list_options(self.setpoint_info(name_or_number))

    def value_label(self, name_or_number: str | int, wire_value: int) -> str:
        """Return the display label for a ``STRING_LIST`` value's wire integer.

        Label = ``CommonNames[low_limit + wire_value]``.  Note that
        [read_values][pycomap.Controller.read_values] resolves ``STRING_LIST`` values
        automatically — this
        method is for cases where you have a raw wire integer and need the label.

        Args:
            name_or_number: Value name or comm object number.
            wire_value: Raw 0-based wire integer (as returned by the controller).

        Returns:
            Human-readable label string, or ``str(wire_value)`` if out of range.

        Raises:
            ComApProtocolError: If the value is not ``STRING_LIST`` type.
        """
        desc = self.value_info(name_or_number)
        if desc.data_type is not DataType.STRING_LIST:
            raise ComApProtocolError(
                f"value {desc.name!r} is DataType.{desc.data_type.name}, not STRING_LIST"
            )
        idx = desc.low_limit + wire_value
        if idx >= len(self._common_names):
            return str(wire_value)
        return self._common_names[idx]

    def value_bit_names(self, name_or_number: str | int) -> list[tuple[int, str]]:
        """Return the bit labels for a ``BINARY*`` value.

        Labels come from ``CommonNames`` starting at ``bit_name_index``; bits without a
        name are omitted from the result.

        Args:
            name_or_number: Value name or comm object number.

        Returns:
            ``[(bit_index, label), ...]``, bit 0 = LSB, ascending order.

        Raises:
            ComApProtocolError: If the value is not a ``BINARY*`` type or has no bit labels.
        """
        desc = self.value_info(name_or_number)
        if desc.data_type not in _BINARY_TYPES:
            raise ComApProtocolError(
                f"value {desc.name!r} is DataType.{desc.data_type.name}, not a BINARY type"
            )
        if desc.bit_name_index is None:
            raise ComApProtocolError(f"value {desc.name!r} has no bit name labels")
        num_bits = _DATA_TYPE_LENGTH[desc.data_type] * 8
        return [
            (bit, self._common_names[desc.bit_name_index + bit])
            for bit in range(num_bits)
            if desc.bit_name_index + bit < len(self._common_names)
        ]

    # -- bulk reads ----------------------------------------------------------

    def _resolve_raws(
        self,
        raw: dict[int, RawValue],
        by_number: dict[int, ValueDescription] | dict[int, SetpointDescription],
    ) -> dict[int, Value]:
        """Resolve ``STRING_LIST`` wire bytes to labels and text-typed bytes to strings.

        Works for both value and setpoint dicts.  ``STRING_LIST`` entries arrive as 1-byte
        blobs; the byte is a 0-based offset from ``low_limit`` into ``CommonNames``.
        Text-typed entries (``SHORT_STRING``, ``IP_ADDRESS``, etc.) arrive as null-padded
        byte strings and are decoded to ASCII.
        """
        result: dict[int, Value] = {}
        for number, val in raw.items():
            if not isinstance(val, bytes):
                result[number] = val
                continue
            desc = by_number.get(number)
            if desc is None:
                result[number] = val
            elif desc.data_type is DataType.STRING_LIST:
                wire = val[0]
                idx = desc.low_limit + wire
                result[number] = (
                    self._common_names[idx] if idx < len(self._common_names) else str(wire)
                )
            elif desc.data_type in _STRING_TYPES:
                result[number] = val.split(b"\x00")[0].decode("ascii", "replace")
            else:
                result[number] = val
        return result

    async def read_values(self) -> dict[int, Value]:
        """Read all values from ``ValuesAll`` (C.O. 24560).

        ``STRING_LIST`` values are resolved to their display label. Text-typed values
        (``SHORT_STRING``, ``IP_ADDRESS``, etc.) are decoded to ASCII ``str``. All other
        values are ``int``, ``float``, or raw ``bytes`` (binary, domain, timer types).

        Returns:
            ``{comm_object_number: value}`` for every value whose data fits within the
            ``ValuesAll`` blob, including static ``ONE_TIME`` values (firmware version,
            ID string, etc.).

        Examples:
            >>> values = await ctrl.read_values()
            >>> rpm_num = ctrl.value_info("RPM").number
            >>> values[rpm_num]
            1450
        """
        data = await self._client.read_object(CommunicationObject.VALUES_ALL)
        return self._resolve_raws(decode_values_all(self.table, data), self._values_by_number)

    async def read_setpoints(self) -> dict[int, Value]:
        """Read all setpoints from ``SetpointsAll`` (C.O. 24559).

        ``STRING_LIST`` setpoints are resolved to their display label, matching what
        [set_setpoint][pycomap.Controller.set_setpoint] accepts for a clean
        read-modify-write round-trip.
        Text-typed setpoints are decoded to ASCII ``str``.

        Returns:
            ``{comm_object_number: value}`` for every setpoint in the controller's table.
        """
        data = await self._client.read_object(CommunicationObject.SETPOINTS_ALL)
        return self._resolve_raws(decode_setpoints_all(self.table, data), self._setpoints_by_number)

    async def read_states(self) -> dict[int, ValueState]:
        """Read all value protection states (``ValueStatesAll``, C.O. 24555)."""
        data = await self._client.read_object(CommunicationObject.VALUE_STATES_ALL)
        return decode_states_all(self.table, data)

    async def read_alarms(self) -> list[AlarmRecord]:
        """Read the current alarm list (``AlarmList``, C.O. 24545)."""
        if self._config_data is None:
            raise ComApProtocolError("not connected — call connect() first")
        data = await self._client.read_object(CommunicationObject.ALARM_LIST)
        return parse_alarm_list(self._config_data, data)

    async def read_history(self, count: int = 10) -> list[HistoryRecord]:
        """Read up to ``count`` of the most recent history records, newest first."""
        if self._config_data is None:
            raise ComApProtocolError("not connected — call connect() first")
        records: list[HistoryRecord] = []
        raw = await self._client.read_object(CommunicationObject.YOUNGEST_HISTORY_RECORD)
        rec = parse_history_record(self._config_data, raw)
        if rec:
            records.append(rec)
        for _ in range(count - 1):
            if len(records) >= count:
                break
            raw = await self._client.read_object(CommunicationObject.OLDER_HISTORY_RECORD)
            rec = parse_history_record(self._config_data, raw)
            if rec:
                records.append(rec)
        return records

    def decode_history_snapshot(self, record: HistoryRecord) -> dict[int, Value]:
        """Decode the value snapshot embedded in an alarm ``HistoryRecord``.

        Alarm/event records carry a snapshot of the ``ValuesAll`` blob captured at the
        moment of the event.  Returns ``{number: decoded_value}`` for every value whose
        data fits within the snapshot; the set of values is typically the first ~31 entries
        from the controller's value table (those with small ``data_index`` values).

        Returns an empty dict for text records (``record.is_text=True``) or records with
        no embedded data.

        Use [value_info][pycomap.Controller.value_info] to look up a number's name and metadata::

            snapshot = ctrl.decode_history_snapshot(rec)
            for number, val in snapshot.items():
                info = ctrl.value_info(number)
                print(f"{info.name}: {val}")
        """
        return self._resolve_raws(
            decode_history_snapshot(self.table, record.data), self._values_by_number
        )

    # -- individual read/write -----------------------------------------------

    async def read_value(self, name_or_number: str | int) -> Value:
        """Read a single value by name or number.

        Reads ``ValuesAll`` internally — use
        [read_values][pycomap.Controller.read_values] when you need multiple
        values to avoid redundant round-trips. For ``ONE_TIME`` static values use
        [one_time_value][pycomap.Controller.one_time_value] or
        [one_time_values][pycomap.Controller.one_time_values].

        Args:
            name_or_number: Value name or comm object number.

        Returns:
            Decoded value; same type rules as [read_values][pycomap.Controller.read_values].

        Raises:
            KeyError: If no value with that name or number exists.
            ComApProtocolError: If the name is shared by multiple values, or if the value
                is ``ONE_TIME`` category — use ``one_time_value()`` instead.
        """
        desc = self.value_info(name_or_number)
        if desc.category is ValueCategory.ONE_TIME:
            raise ComApProtocolError(
                f"value {desc.name!r} (number {desc.number}) is ONE_TIME — "
                "use Controller.one_time_values instead"
            )
        values = await self.read_values()
        if desc.number not in values:
            raise ComApProtocolError(
                f"value {desc.name!r} (number {desc.number}) is not present in ValuesAll"
            )
        return values[desc.number]

    def one_time_value(self, name_or_number: str | int) -> Value:
        """Return a cached ONE_TIME value by name or number (no network call).

        ONE_TIME values are read once at connect time and stored in
        [one_time_values][pycomap.Controller.one_time_values].

        Args:
            name_or_number: Value name or comm object number.

        Returns:
            Resolved value; strings are already null-stripped.

        Raises:
            KeyError: If no value with that name or number exists in the table.
            ComApProtocolError: If the name is shared by multiple values, if the value
                is not ``ONE_TIME`` category, or if it was not cached (e.g. skipped as
                invisible or failed to read at connect).
        """
        desc = self.value_info(name_or_number)
        if desc.category is not ValueCategory.ONE_TIME:
            raise ComApProtocolError(
                f"value {desc.name!r} (number {desc.number}) is not ONE_TIME — "
                "use read_value() instead"
            )
        if desc.number not in self._one_time_values:
            raise ComApProtocolError(
                f"ONE_TIME value {desc.name!r} (number {desc.number}) is not in cache "
                "(skipped as invisible or failed to read at connect)"
            )
        return self._one_time_values[desc.number]

    async def read_setpoint(self, name_or_number: str | int) -> Value:
        """Read a single setpoint by name or number (one round-trip).

        Args:
            name_or_number: Setpoint name or comm object number.

        Returns:
            Decoded value; same type rules as [read_setpoints][pycomap.Controller.read_setpoints].

        Raises:
            KeyError: If no setpoint with that name or number exists.
        """
        desc = self.setpoint_info(name_or_number)
        raw = await self._client.read_object(desc.number)
        val = decode_raw_value(desc.data_type, raw, desc.decimal_places)
        return self._resolve_raws({desc.number: val}, self._setpoints_by_number)[desc.number]

    def _coerce_setpoint_value(
        self,
        desc: SetpointDescription,
        value: Value,
    ) -> Value:
        """Resolve and validate ``value`` for ``desc`` before encoding.

        - ``STRING_LIST`` + ``str``: looks up the label in
          [setpoint_options][pycomap.Controller.setpoint_options] and
          returns the matching wire index.  Raises ``ValueError`` for unknown labels.
        - ``STRING_LIST`` + ``int``: validates the index is in range (0..high-low).
        - Integer / unsigned types: validates the scaled wire value against
          ``low_limit`` / ``high_limit``, skipping whichever bound has ``var_*=True``.
        - All other types: returned unchanged.

        ``bytes`` values are always passed through without validation.
        """
        if isinstance(value, bytes):
            return value

        if desc.data_type is DataType.STRING_LIST:
            if isinstance(value, str):
                by_label = {label: wire for wire, label in self.setpoint_options(desc.number)}
                if value not in by_label:
                    raise ValueError(
                        f"{value!r} is not a valid option for {desc.name!r}; "
                        f"valid: {list(by_label)}"
                    )
                return by_label[value]
            # int index
            if not desc.var_high_limit:
                max_index = desc.high_limit - desc.low_limit
                if int(value) not in range(max_index + 1):
                    raise ValueError(
                        f"wire index {int(value)!r} is out of range for {desc.name!r}: "
                        f"valid indices are 0..{max_index}"
                    )
            return value

        if isinstance(value, (int, float)) and desc.data_type in _RANGE_VALIDATABLE:
            dp = desc.decimal_places
            raw = round(value * (10**dp)) if dp else int(value)
            low_ok = desc.var_low_limit or desc.low_limit <= raw
            high_ok = desc.var_high_limit or raw <= desc.high_limit
            if not (low_ok and high_ok):
                scale = 10**dp if dp else 1
                lo: int | float | str = "?" if desc.var_low_limit else desc.low_limit / scale
                hi: int | float | str = "?" if desc.var_high_limit else desc.high_limit / scale
                raise ValueError(
                    f"{value!r} is out of range for {desc.name!r}: valid range is [{lo}..{hi}]"
                )

        return value

    async def set_setpoint(self, name_or_number: str | int, value: Value) -> None:
        """Write a setpoint by name or number.

        Args:
            name_or_number: Setpoint name or comm object number.
            value: New value. Type depends on the setpoint's ``DataType``:

                - **Numeric** (``UNSIGNED*``, ``INTEGER*``, ``FLOAT``, ``BINARY*``):
                  pass ``int`` or ``float``; ``decimal_places`` scaling is applied
                  automatically. Range-checked against ``low_limit``/``high_limit``.
                - **``STRING_LIST``**: pass a ``str`` label (e.g. ``"Winter"``) or
                  an ``int`` wire index. Labels are resolved via
                  [setpoint_options][pycomap.Controller.setpoint_options].
                - **``CHAR``**: pass an ``int``.
                - **Text** (``SHORT_STRING``, ``IP_ADDRESS``, etc.): pass a ``str``;
                  ASCII-encoded, zero-padded or truncated to the wire field length.
                - **Any type**: pass ``bytes`` to write the raw wire value directly
                  (skips validation).

        Raises:
            ComApAuthError: If the setpoint requires a password and none was supplied
                at construction, or if the password is rejected / locked out.
            ValueError: If ``value`` is out of the setpoint's valid range.

        Examples:
            >>> await ctrl.set_setpoint("Nominal RPM", 1500)
            >>> await ctrl.set_setpoint("Summer Time Mode", "Winter")
            >>> await ctrl.set_setpoint("IP Address", "192.168.1.10")
        """
        desc = self.setpoint_info(name_or_number)
        if desc.needs_password:
            await self.elevate_access()
        value = self._coerce_setpoint_value(desc, value)
        raw = _encode_setpoint_value(desc.data_type, desc.decimal_places, value)
        await self._client.write_object(desc.number, raw)
        _log.debug("set_setpoint %r = %r", desc.name, value)

    async def execute_command(self, command: ControllerCommand) -> int:
        """Execute a controller command.

        Args:
            command: A ``ControllerCommand`` instance; use the ``Command`` enum for
                named commands (e.g. ``Command.FAULT_RESET``).

        Returns:
            Raw integer result code returned by the controller.
        """
        return await self._client.execute_command(command)

    # -- datetime / timezone -------------------------------------------------

    @property
    def timezone(self) -> datetime.timezone:
        """Controller's configured UTC offset, derived from the ``Time Zone`` setpoint
        (C.O. 24366) read at connect time.

        Derived by parsing the ``Time Zone`` setpoint's GMT label (e.g. ``'GMT+2:00'``
        for EET) and adding one hour when ``Summer Time Mode`` is ``'Summer'`` or
        ``'Summer-S'``.  Supports half-hour offsets.
        Call [refresh_timezone][pycomap.Controller.refresh_timezone] to
        re-read after a setpoint change.
        """
        return self._timezone

    @property
    def summer_time_mode(self) -> int:
        """Raw value of the ``Summer Time Mode`` setpoint (8727) read at connect time.

        Known values: ``0`` = Winter, ``2`` = Summer, ``4`` = Summer-S.
        Call [refresh_timezone][pycomap.Controller.refresh_timezone] to re-read after a change.
        """
        return self._summer_time_mode_raw

    async def refresh_timezone(self) -> None:
        """Re-read the ``Time Zone`` and ``Summer Time Mode`` setpoints and update the
        cached [timezone][pycomap.Controller.timezone] and
        [summer_time_mode][pycomap.Controller.summer_time_mode] values.

        Both setpoints are looked up by name from the cached ``ConfigurationTable``, so
        no comm object numbers are hardcoded.  Call this if the setpoints were changed
        while the ``Controller`` is connected.
        """
        base_offset: datetime.timedelta | None = None

        tz_desc = self._setpoints_by_name.get(_SETPOINT_TIME_ZONE)
        if tz_desc is not None:
            tz_raw = await self._client.read_object(tz_desc.number)
            wire_value = tz_raw[0]
            # Resolve wire value → GMT label via the options list, then parse the label.
            # This handles half-hour offsets (e.g. 'GMT+5:30') correctly without any
            # hardcoded index arithmetic.
            options = dict(self.setpoint_options(tz_desc.number))
            label = options.get(wire_value, "")
            base_offset = _parse_gmt_label(label)

        dst_desc = self._setpoints_by_name.get(_SETPOINT_SUMMER_TIME_MODE)
        if dst_desc is not None:
            dst_raw = await self._client.read_object(dst_desc.number)
            self._summer_time_mode_raw = dst_raw[0]
            dst_options = dict(self.setpoint_options(dst_desc.number))
            dst_label = dst_options.get(self._summer_time_mode_raw, "")
            if base_offset is not None and dst_label in _SUMMER_MODE_DST_LABELS:
                base_offset += datetime.timedelta(hours=1)

        if base_offset is not None:
            self._timezone = datetime.timezone(base_offset)

    async def read_datetime(self) -> datetime.datetime | None:
        """Read the controller's current clock as a **naive** datetime (local wall-clock
        time).  Use [read_aware_datetime][pycomap.Controller.read_aware_datetime]
        to get a timezone-aware result.
        """
        return await self._client.read_datetime()

    async def read_aware_datetime(self) -> datetime.datetime | None:
        """Read the controller's current clock as a **timezone-aware** datetime.

        Combines the naive clock reading with the
        [timezone][pycomap.Controller.timezone] cached at connect time
        (derived from the ``Time Zone`` setpoint 24366).  Returns ``None`` if the
        controller's clock is invalid/unset.
        """
        dt = await self._client.read_datetime()
        if dt is None:
            return None
        return dt.replace(tzinfo=self._timezone)

    async def sync_time(self, tz: datetime.tzinfo | None = None) -> None:
        """Sync the controller clock to the current UTC time.

        Requires write access — elevates automatically if a ``password`` was supplied.

        Args:
            tz: Timezone for the local time written to the controller.

                - ``None`` (default): uses [timezone][pycomap.Controller.timezone] —
                  the UTC offset read from
                  the controller's own ``Time Zone`` setpoint at connect time.
                - Any ``datetime.tzinfo`` (``pytz``, ``zoneinfo``, or
                  ``datetime.timezone``): overrides the controller's setting. Use when
                  the setpoint is not yet configured::

                      import pytz
                      await ctrl.sync_time(tz=pytz.timezone("Europe/Kiev"))

        Raises:
            ComApAuthError: If write access is needed but no password was provided.
        """
        await self.elevate_access()
        effective_tz: datetime.tzinfo = tz if tz is not None else self._timezone
        now = datetime.datetime.now(datetime.UTC).astimezone(effective_tz).replace(tzinfo=None)
        await self._client.write_datetime(now)

    # -- private helpers -----------------------------------------------------

    async def _load_config(self) -> None:
        self._config_data = await self._client.read_object(CommunicationObject.CONFIGURATION_TABLE)
        self._table = parse_configuration_table(self._config_data)
        self._values_by_number = {v.number: v for v in self._table.values}
        self._values_by_name = {}
        self._ambiguous_value_names = set()
        for v in self._table.values:
            if v.name in self._values_by_name:
                self._ambiguous_value_names.add(v.name)
            else:
                self._values_by_name[v.name] = v
        self._setpoints_by_number = {s.number: s for s in self._table.setpoints}
        self._setpoints_by_name = {}
        self._ambiguous_setpoint_names = set()
        for s in self._table.setpoints:
            if s.name in self._setpoints_by_name:
                self._ambiguous_setpoint_names.add(s.name)
            else:
                self._setpoints_by_name[s.name] = s
        self._common_names = parse_names_heap(self._config_data, NamesCategory.COMMON_NAMES)
        await self.refresh_timezone()
        await self._cache_one_time_values()
        _log.info(
            "configuration loaded: %d values, %d setpoints, %d one-time",
            len(self._table.values),
            len(self._table.setpoints),
            len(self._one_time_values),
        )

    async def _cache_one_time_values(self) -> None:
        descs = [
            v
            for v in self.table.values
            if v.category is ValueCategory.ONE_TIME
            and (self._include_invisible or v.group != "Invisible")
        ]
        if not descs:
            return
        raw_map: dict[int, RawValue] = {}
        for desc in descs:
            try:
                raw = await self._client.read_object(desc.number)
            except Exception as exc:
                _log.warning(
                    "failed to read ONE_TIME value %r (number %d): %s",
                    desc.name,
                    desc.number,
                    exc,
                )
                continue
            raw_map[desc.number] = decode_raw_value(desc.data_type, raw, desc.decimal_places)
        self._one_time_values = self._resolve_raws(raw_map, self._values_by_number)

    async def elevate_access(self) -> None:
        """Send the write-protection password to the controller, enabling protected writes.

        Idempotent — safe to call multiple times; the password is only sent once.
        Call this early to validate the password without waiting for the first write.

        Raises:
            ComApAuthError: If no password was supplied to the ``Controller``.
            ComApInvalidPasswordError: If the controller rejects the password.
        """
        if self._elevated:
            return
        if self._password is None:
            raise ComApAuthError(
                "this operation requires a password but none was supplied to Controller"
            )
        _log.debug("elevating write access")
        await self._client.elevate_access(self._password)
        self._elevated = True

    async def _refresh_config(self) -> None:
        """Re-fetch the ``ConfigurationTable`` and timezone (call after firmware update
        or reconnect).
        """
        await self._load_config()
        self._elevated = False
