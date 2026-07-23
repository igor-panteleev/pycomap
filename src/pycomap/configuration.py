"""Parsing of the controller's ``ConfigurationTable`` and decoding of the blobs it describes.

See ``docs/protocol.md`` section 4 for the full reverse-engineering notes (decompiled from
``ComAp.Controller.dll``, cross-validated against a live controller's raw bytes and against
``cfgmodbus.txt``'s independently-exported Modbus table).

The short version: ``ValuesAll``/``ValueStatesAndDataAll`` are not a fixed schema. Each value
is placed at a byte offset (``data_index``) and length (``data_length``) computed from the
controller's own ``ConfigurationTable`` (communication object 24575) -- decoding one requires
decoding the other first.

Only the InteliLite3 (``IL3``) binary format is implemented (``ControllerType`` byte 14 at
offset 6 of the table, format versions 0-4), since that's the only hardware this has been
validated against. ``SetpointsAll`` decoding doesn't resolve substituted-setpoint info,
default values, or "periphery setpoint" info (all read via their own absolute offsets, not
the main per-record stream, and not needed to decode a setpoint's current value).
String/domain/timer/date-typed values are returned as raw bytes rather than decoded.

Each value's human-readable name and unit are resolved from the "unified names heap": the
``name_index``/``dim_index`` fields in a value's record are indices into a per-category,
per-language array of length-prefixed strings, reached through one level of indirection (an
"access vector" mapping index -> byte offset into a separate heap of string contents). Only
the first/default language is decoded -- this hasn't been tested against a multi-language
configuration.

Wire type codec (`DataType`, `decode_raw_value`, `encode_raw_value`) lives in
[pycomap.datatypes][]. Alarm and history record parsing live in [pycomap.alarms][]
and [pycomap.history][] respectively.
"""

from __future__ import annotations

import dataclasses
import enum
import functools
import logging
import struct
from collections.abc import Sequence
from dataclasses import dataclass

from pycomap.datatypes import (
    _DATA_TYPE_LENGTH,
    DataType,
    ProtectionState,
    RawValue,
    decode_raw_value,
    encode_raw_value,
    get_bits,
)
from pycomap.exceptions import ComApProtocolError

_log = logging.getLogger(__name__)

__all__ = [
    "ConfigurationTable",
    "HistoryFieldDescription",
    "NamesCategory",
    "ProtectionState",
    "SetpointCategory",
    "SetpointDescription",
    "ValueCategory",
    "ValueDescription",
    "ValueState",
    "decode_history_snapshot",
    "decode_raw_value",
    "decode_setpoints_all",
    "decode_states_all",
    "decode_values_all",
    "encode_raw_value",
    "parse_configuration_table",
    "parse_names_heap",
]

_IL3_CONTROLLER_TYPE = 14
_CONTROLLER_TYPE_OFFSET = 6
_CONFIG_FORMAT_TERMINAL_OFFSET = 5
_NUM_VALUES_CAT_I_OFFSET = 50
_VALUE_RECORD_SIZE = 13
_STATE_INDEX_FOR_NO_STATE = 1023
_NUM_SETPOINTS_CAT_P_OFFSET = 98
_SETPOINT_RECORD_SIZE = 14

# History snapshot field layout (IL3, ConfigurationTableLoaderIL3.CreateConfigurationTableLoadInfo
# NumHistFieldsOffset=152, IsNumHistFieldsByte=false). Distinct from ValuesAll's data_index --
# see HistoryFieldDescription and _parse_history_description.
_NUM_HIST_FIELDS_OFFSET = 152

# Unified names heap (IL3-specific fixed offsets, see module docstring and
# docs/protocol.md section 4).
_DESCR_LANG_OFFSET = 169
_NAMES_HEAP_ACCESS_VECTOR_OFFSET = 6
_NAMES_HEAP_CONTENTS_OFFSET = 10


class NamesCategory(enum.Enum):
    """Subset of ComAp's ``NamesCategory`` enum -- only the categories needed to resolve a
    value's name/dimension/group, alarm reason/prefix, and history reason/prefix are implemented.
    Values are arbitrary (used only as a dict key into ``_NAMES_CATEGORY_LAYOUT``), not
    wire values.
    """

    COMMON_NAMES = enum.auto()
    DIMENSIONS = enum.auto()
    ALARM_REASON_NAMES = enum.auto()
    HISTORY_PREFIX_NAMES = enum.auto()
    HISTORY_REASON_NAMES = enum.auto()
    GROUP_NAMES = enum.auto()


@dataclass(frozen=True, slots=True)
class _NamesCategoryLayout:
    num_names_offset: int
    tab_names_offset: int
    num_names_is_byte: bool


# Absolute offsets within the ConfigurationTable, hardcoded for IL3 in
# ConfigurationTableLoaderIL3.CreateNamesOffsetDescription/GetNamesCategoryOffset.
# namesOffset base = 503 (Dimensions tab); each category's tab = namesOffset+N,
# count = namesOffset+N+2 (per GetNamesCategoryOffset in ComAp.Controller.dll).
# GroupNames is at namesOffset+10 (4th in the ordered CreateNamesOffsetDescription list:
# Dimensions(byte)+3, FixedNames(u16)+4, SetpointLimitNames(byte)+3, GroupNames(byte)).
_NAMES_CATEGORY_LAYOUT = {
    NamesCategory.COMMON_NAMES: _NamesCategoryLayout(594, 592, num_names_is_byte=False),
    NamesCategory.DIMENSIONS: _NamesCategoryLayout(505, 503, num_names_is_byte=True),
    NamesCategory.HISTORY_PREFIX_NAMES: _NamesCategoryLayout(525, 523, num_names_is_byte=True),
    NamesCategory.HISTORY_REASON_NAMES: _NamesCategoryLayout(528, 526, num_names_is_byte=False),
    NamesCategory.ALARM_REASON_NAMES: _NamesCategoryLayout(532, 530, num_names_is_byte=False),
    NamesCategory.GROUP_NAMES: _NamesCategoryLayout(515, 513, num_names_is_byte=True),
}

# Group table header offsets (IL3, ConfigurationTableLoaderIL3.CreateConfigurationTableLoadInfo).
# NumGroupsOffset=134 (uint16), DescrGroupsItemOffset=136 (uint32 absolute address).
# GroupTableBaseOffset=0 means items/subgroups offsets in each group record are absolute.
_NUM_GROUPS_OFFSET = 134
_GROUPS_ADDR_OFFSET = 136


@functools.cache
def parse_names_heap(data: bytes, category: NamesCategory) -> list[str]:
    """Decode one category of the controller's "unified names heap" (first/default
    language only). Returned list is indexed directly by a value record's ``name_index``/
    ``dim_index`` field.
    """
    layout = _NAMES_CATEGORY_LAYOUT[category]
    item_size = 2 if data[_CONFIG_FORMAT_TERMINAL_OFFSET] <= 3 else 4

    language_base = struct.unpack_from("<I", data, _DESCR_LANG_OFFSET)[0]
    access_vector_addr = struct.unpack_from(
        "<I", data, language_base + _NAMES_HEAP_ACCESS_VECTOR_OFFSET
    )[0]
    heap_contents_addr = struct.unpack_from(
        "<I", data, language_base + _NAMES_HEAP_CONTENTS_OFFSET
    )[0]

    count = (
        data[layout.num_names_offset]
        if layout.num_names_is_byte
        else struct.unpack_from("<H", data, layout.num_names_offset)[0]
    )
    base_index = struct.unpack_from("<H", data, layout.tab_names_offset)[0]

    access_vector_fmt = "<H" if item_size == 2 else "<I"
    names = []
    for j in range(count):
        position = access_vector_addr + item_size * (base_index + j)
        heap_offset = struct.unpack_from(access_vector_fmt, data, position)[0]
        string_position = heap_contents_addr + heap_offset
        length = data[string_position]
        names.append(data[string_position + 1 : string_position + 1 + length].decode("utf-8"))
    return names


class ValueCategory(enum.IntEnum):
    """ComAp ``ValueCategory`` enum.

    ``FIRST``/``SECOND``/``THIRD`` are refresh-rate tiers (each with its own poll period, read
    from the table); ``ONE_TIME`` values aren't included in ``ValuesAll``/
    ``ValueStatesAndDataAll`` at all.
    """

    FIRST = 0
    SECOND = 1
    THIRD = 2
    ONE_TIME = 3


@dataclass(slots=True, frozen=True)
class ValueDescription:
    """One entry from the controller's ``ConfigurationTable`` describing a single value."""

    number: int
    category: ValueCategory
    data_type: DataType
    data_length: int
    decimal_places: int
    data_index: int
    state_index: int | None
    name: str
    dimension: str
    group: str | None
    low_limit: int
    high_limit: int
    var_low_limit: bool
    var_high_limit: bool
    bit_name_index: int | None


class SetpointCategory(enum.IntEnum):
    """ComAp ``SetpointCategory`` enum. Unlike values, every setpoint is included in
    ``SetpointsAll`` regardless of category, and setpoints have no associated state.
    """

    P = 0
    R = 1


@dataclass(slots=True, frozen=True)
class SetpointDescription:
    """One entry from the controller's ``ConfigurationTable`` describing a single setpoint."""

    number: int
    category: SetpointCategory
    data_type: DataType
    data_length: int
    decimal_places: int
    data_index: int
    name: str
    dimension: str
    group: str | None
    access_level: int
    low_limit: int
    high_limit: int
    var_low_limit: bool
    var_high_limit: bool

    @property
    def needs_password(self) -> bool:
        """True if writing this setpoint requires a password (``access_level > 0``)."""
        return self.access_level > 0


@dataclass(slots=True, frozen=True)
class ValueState:
    """Protection state for one value, decoded from a ``ValueStatesAll`` byte.

    Each field is a ``ProtectionState`` flag combination — check for activity with
    ``state.level1 & ProtectionState.ACTIVE``.  ``NOT_CONFIRMED`` is a combinable flag:
    ``ACTIVE | NOT_CONFIRMED`` (value 6) means the alarm is active but not yet
    acknowledged by the operator pressing Fault Reset.

    Source: ``ComAp.Controller.DataTypes.ValueState`` in ``ComAp.Controller.dll``::

        Level1     = bits 0-2, direct ProtectionState cast
        Level2     = bits 3-5, direct ProtectionState cast
        SensorFail = bits 6-7, left-shifted by 1 (raw 1 → ACTIVE, raw 2 → NOT_CONFIRMED)
    """

    level1: ProtectionState
    level2: ProtectionState
    sensor_fail: ProtectionState

    @property
    def any_alarm(self) -> bool:
        """True if any protection level or sensor failure is active."""
        active = ProtectionState.ACTIVE
        return bool((self.level1 & active) or (self.level2 & active) or (self.sensor_fail & active))


@dataclass(slots=True, frozen=True)
class HistoryFieldDescription:
    """One entry in the controller's history-snapshot field layout.

    Describes where a single value's raw bytes sit within a ``HistoryRecord.data`` snapshot.
    This is a **separate** layout from ``ValuesAll`` -- ``data_index`` here is the byte offset
    within the 57-byte history snapshot, unrelated to ``value.data_index`` (which is the
    offset within ``ValuesAll``/``ValueStatesAndDataAll``). See
    [decode_history_snapshot][pycomap.configuration.decode_history_snapshot].
    """

    data_index: int
    value: ValueDescription


@dataclass(slots=True, frozen=True)
class ConfigurationTable:
    """Parsed ``ConfigurationTable`` (value and setpoint descriptions -- see module
    docstring).
    """

    values: list[ValueDescription]
    setpoints: list[SetpointDescription]
    history_fields: list[HistoryFieldDescription]


def _as_int16(v: int) -> int:
    """Reinterpret a uint16 as a signed int16 (same bit pattern, different sign)."""
    return struct.unpack("<h", struct.pack("<H", v))[0]


def _expand_categories[T](counts: list[int], categories: list[T]) -> list[T]:
    """Expand per-category counts into a per-item category list.

    E.g. ``counts=[2, 1]``, ``categories=[A, B]`` → ``[A, A, B]``.
    """
    result: list[T] = []
    for cat, count in zip(categories, counts, strict=True):
        result.extend([cat] * count)
    return result


def _parse_group_map(
    data: bytes,
    value_numbers: Sequence[int],
    setpoint_numbers: Sequence[int],
) -> dict[int, str]:
    """Parse the GroupDescription section and return {CO_number: group_name}.

    Source: ConfigurationTableLoaderIL3.LoadGroupDescriptionFromStream and
    ConfigurationTableLoader.CommonLoadGroupsFromStream in ComAp.Controller.dll.
    Each group record is 11 bytes (3x uint16 fields + uint16 items_offset +
    uint16 subgroups_offset + 1 byte flags).  Each item is 4 bytes (2x uint16):
    bits 0-1 of iw1 = CommunicationObjectType (0=value, 1=setpoint), bits 2-12 = object index.
    """
    group_names = parse_names_heap(data, NamesCategory.GROUP_NAMES)
    num_groups = struct.unpack_from("<H", data, _NUM_GROUPS_OFFSET)[0]
    groups_addr = struct.unpack_from("<I", data, _GROUPS_ADDR_OFFSET)[0]

    co_to_group: dict[int, str] = {}
    pos = groups_addr
    for _ in range(num_groups):
        w2 = struct.unpack_from("<H", data, pos + 2)[0]
        w3 = struct.unpack_from("<H", data, pos + 4)[0]
        items_offset = struct.unpack_from("<H", data, pos + 6)[0]
        pos += 11

        name_idx = get_bits(w3, 9, 6)
        num_items = get_bits(w2, 9, 7)
        group_name = group_names[name_idx] if name_idx < len(group_names) else ""

        item_pos = items_offset
        for _ in range(num_items):
            iw1 = struct.unpack_from("<H", data, item_pos)[0]
            item_pos += 4
            obj_type = get_bits(iw1, 0, 2)
            obj_idx = get_bits(iw1, 2, 11)
            if obj_type == 0 and obj_idx < len(value_numbers):
                co_to_group[value_numbers[obj_idx]] = group_name
            elif obj_type == 1 and obj_idx < len(setpoint_numbers):
                co_to_group[setpoint_numbers[obj_idx]] = group_name

    return co_to_group


def _parse_history_description(
    data: bytes, values: list[ValueDescription]
) -> list[HistoryFieldDescription]:
    """Parse the history-snapshot field layout section of the ``ConfigurationTable``.

    Source: ``ConfigurationTableLoaderCommonExtensions.CommonLoadHistoryFromStream`` +
    ``ConfigurationTableLoaderIL3.LoadHistoryItemDescriptionFromStream`` in
    ``ComAp.Controller.dll`` (IL3, non-Format7 -- ``NumHistFieldsOffset=152``,
    ``IsNumHistFieldsByte=false``, ``AreAllAddresses32Bit=true``).

    Layout at offset 152: ``uint16`` item count, ``uint16`` padding (read but discarded by
    the non-byte-count branch), ``uint32`` absolute address of the item table. Each item is
    one ``uint32`` LE: bits 0-10 = ``val_index`` (0-based index into ``values``, in the same
    stream-load order used to build that list -- *not* a comm-object number or a
    ``ValuesAll`` ``data_index``), bits 11-19 = ``data_index`` (byte offset within the
    history snapshot payload, stored directly per item), bits 20-31 = ``name_index`` (into
    ``NamesCategory.COMMON_NAMES`` -- not resolved here; each ``value.name`` already carries
    a name).
    """
    num_items = struct.unpack_from("<H", data, _NUM_HIST_FIELDS_OFFSET)[0]
    table_addr = struct.unpack_from("<I", data, _NUM_HIST_FIELDS_OFFSET + 4)[0]

    fields = []
    offset = table_addr
    for _ in range(num_items):
        word = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        val_index = get_bits(word, 0, 11)
        data_index = get_bits(word, 11, 9)
        if val_index < len(values):
            fields.append(HistoryFieldDescription(data_index=data_index, value=values[val_index]))
    return fields


def parse_configuration_table(data: bytes) -> ConfigurationTable:
    """Parse the value-description section of a raw ``ConfigurationTable`` blob."""
    controller_type = data[_CONTROLLER_TYPE_OFFSET]
    if controller_type != _IL3_CONTROLLER_TYPE:
        raise ComApProtocolError(
            f"unsupported ControllerType {controller_type}; "
            f"only InteliLite3 ({_IL3_CONTROLLER_TYPE}) is implemented"
        )

    offset = _NUM_VALUES_CAT_I_OFFSET
    category_counts = list(struct.unpack_from("<4H", data, offset))
    offset += 4 * 2 + 2  # category counts + redundant total count
    offset += 4 * 2 + 2  # per-category data lengths + redundant total data length
    offset += 3 * 2 + 2  # per-category state lengths + redundant total state length
    offset += 3 * 2  # refresh periods (First/Second/Third), unused here
    value_ids_addr, value_descriptions_addr = struct.unpack_from("<II", data, offset)

    total = sum(category_counts)
    numbers = struct.unpack_from(f"<{total}H", data, value_ids_addr)
    category_of = _expand_categories(
        category_counts,
        [ValueCategory.FIRST, ValueCategory.SECOND, ValueCategory.THIRD, ValueCategory.ONE_TIME],
    )

    common_names = parse_names_heap(data, NamesCategory.COMMON_NAMES)
    dimensions = parse_names_heap(data, NamesCategory.DIMENSIONS)

    offset = value_descriptions_addr
    values = []
    for i in range(total):
        dword1, dword2 = struct.unpack_from("<II", data, offset)
        name_index = get_bits(dword1, 0, 12)
        dim_index = get_bits(dword1, 12, 6)
        decimal_places = get_bits(dword1, 18, 3)
        var_low_limit = bool(get_bits(dword1, 23, 1))
        var_high_limit = bool(get_bits(dword1, 24, 1))
        raw_bit_name_index = get_bits(dword2, 1, 10)
        raw_state_index = get_bits(dword2, 11, 10)
        data_index = get_bits(dword2, 21, 10)
        data_type = DataType(data[offset + 8])
        raw_low, raw_high = struct.unpack_from("<HH", data, offset + 9)
        if data_type in (DataType.INTEGER8, DataType.INTEGER16, DataType.INTEGER32):
            low_limit, high_limit = _as_int16(raw_low), _as_int16(raw_high)
        else:
            low_limit, high_limit = raw_low, raw_high
        offset += _VALUE_RECORD_SIZE

        values.append(
            ValueDescription(
                number=numbers[i],
                category=category_of[i],
                data_type=data_type,
                data_length=_DATA_TYPE_LENGTH[data_type],
                decimal_places=decimal_places,
                data_index=data_index,
                state_index=(
                    None if raw_state_index == _STATE_INDEX_FOR_NO_STATE else raw_state_index
                ),
                name=common_names[name_index],
                dimension=dimensions[dim_index],
                group=None,
                low_limit=low_limit,
                high_limit=high_limit,
                var_low_limit=var_low_limit,
                var_high_limit=var_high_limit,
                bit_name_index=(
                    None if raw_bit_name_index == _STATE_INDEX_FOR_NO_STATE else raw_bit_name_index
                ),
            )
        )

    setpoints = _parse_setpoints(data, common_names, dimensions)

    group_map = _parse_group_map(data, list(numbers), [s.number for s in setpoints])
    values = [dataclasses.replace(v, group=group_map.get(v.number)) for v in values]
    setpoints = [dataclasses.replace(s, group=group_map.get(s.number)) for s in setpoints]

    history_fields = _parse_history_description(data, values)

    return ConfigurationTable(values=values, setpoints=setpoints, history_fields=history_fields)


def _parse_setpoints(
    data: bytes, common_names: list[str], dimensions: list[str]
) -> list[SetpointDescription]:
    offset = _NUM_SETPOINTS_CAT_P_OFFSET
    category_counts = list(struct.unpack_from("<2H", data, offset))
    offset += 2 * 2 + 2  # category counts (P, R) + redundant total count
    offset += 2 * 2 + 2  # per-category data lengths + redundant total data length
    setpoint_ids_addr, setpoint_descriptions_addr = struct.unpack_from("<II", data, offset)

    total = sum(category_counts)
    numbers = struct.unpack_from(f"<{total}H", data, setpoint_ids_addr)
    category_of = _expand_categories(category_counts, [SetpointCategory.P, SetpointCategory.R])

    offset = setpoint_descriptions_addr
    setpoints = []
    for i in range(total):
        dword1, byte1 = struct.unpack_from("<IB", data, offset)
        name_index = get_bits(dword1, 0, 12)
        dim_index = get_bits(dword1, 12, 6)
        access_level = get_bits(dword1, 24, 8)
        decimal_places = get_bits(byte1, 4, 3)
        data_type = DataType(data[offset + 5])
        dword2 = struct.unpack_from("<I", data, offset + 6)[0]
        # bit 1 = varLowLimit, bit 2 = varHighLimit (IL3, ComObjectsHas32BitLimits=False,
        # so num=1; GetBit(dword2, num) and GetBit(dword2, 1+num) per ReadLimit source).
        var_low_limit = bool(get_bits(dword2, 1, 1))
        var_high_limit = bool(get_bits(dword2, 2, 1))
        data_index = get_bits(dword2, 13, 11)
        raw_low, raw_high = struct.unpack_from("<HH", data, offset + 10)
        # For signed integer types, reinterpret uint16 as int16 (IL3 always has 16-bit
        # limits even for INTEGER32).  Source: IsSignedDataType cast in ConfigTableLoader.
        if data_type in (DataType.INTEGER8, DataType.INTEGER16, DataType.INTEGER32):
            low_limit, high_limit = _as_int16(raw_low), _as_int16(raw_high)
        else:
            low_limit, high_limit = raw_low, raw_high
        offset += _SETPOINT_RECORD_SIZE

        setpoints.append(
            SetpointDescription(
                number=numbers[i],
                category=category_of[i],
                data_type=data_type,
                data_length=_DATA_TYPE_LENGTH[data_type],
                decimal_places=decimal_places,
                data_index=data_index,
                name=common_names[name_index],
                dimension=dimensions[dim_index],
                group=None,
                access_level=access_level,
                low_limit=low_limit,
                high_limit=high_limit,
                var_low_limit=var_low_limit,
                var_high_limit=var_high_limit,
            )
        )

    return setpoints


def decode_values_all(table: ConfigurationTable, data: bytes) -> dict[int, RawValue]:
    """Decode a ``ValuesAll`` (or the data portion of ``ValueStatesAndDataAll``) blob.

    Returns a mapping of value ``number`` -> decoded value for every
    ``ValueCategory.FIRST``/``SECOND``/``THIRD`` value. ``ONE_TIME`` values are excluded
    — they are not present in ``ValuesAll`` and must be read individually.
    """
    result: dict[int, RawValue] = {}
    for value in table.values:
        if value.category is ValueCategory.ONE_TIME:
            continue
        end = value.data_index + value.data_length
        if end > len(data):
            _log.warning(
                "value %r (number %d) data_index %d+%d exceeds blob size %d — skipping",
                value.name,
                value.number,
                value.data_index,
                value.data_length,
                len(data),
            )
            continue
        raw = data[value.data_index : end]
        result[value.number] = decode_raw_value(value.data_type, raw, value.decimal_places)
    return result


def decode_history_snapshot(table: ConfigurationTable, snapshot: bytes) -> dict[int, RawValue]:
    """Decode the value snapshot from a ``HistoryRecord.data`` field.

    Alarm/event history records carry a fixed-format snapshot of a specific set of values
    (RPM, voltages, frequencies, battery voltage, binary I/O, mode, ...), captured at the
    moment the event occurred. This layout is defined by the controller's own
    ``HistoryDescriptionCollection`` (``table.history_fields`` -- a separate section of the
    ``ConfigurationTable``, unrelated to ``ValuesAll``'s per-value ``data_index``) rather than
    being a truncated copy of ``ValuesAll``. Verified field-for-field against a live
    controller's WebSupervisor history view.

    Returns ``{number: decoded_value}`` for every history field that fits within
    ``len(snapshot)``, using the same type/decimal-places decoding as
    [decode_values_all][pycomap.configuration.decode_values_all]. Returns an empty dict if
    ``snapshot`` is empty (text records).
    """
    result: dict[int, RawValue] = {}
    for field in table.history_fields:
        value = field.value
        if value.category is ValueCategory.ONE_TIME:
            continue
        end = field.data_index + value.data_length
        if end > len(snapshot):
            continue
        raw = snapshot[field.data_index : end]
        result[value.number] = decode_raw_value(value.data_type, raw, value.decimal_places)
    return result


def decode_setpoints_all(table: ConfigurationTable, data: bytes) -> dict[int, RawValue]:
    """Decode a ``SetpointsAll`` blob into a mapping of setpoint ``number`` -> decoded value.

    Unlike values, every setpoint (both ``P`` and ``R`` categories) is included.
    """
    result: dict[int, RawValue] = {}
    for setpoint in table.setpoints:
        raw = data[setpoint.data_index : setpoint.data_index + setpoint.data_length]
        result[setpoint.number] = decode_raw_value(setpoint.data_type, raw, setpoint.decimal_places)
    return result


def decode_states_all(table: ConfigurationTable, data: bytes) -> dict[int, ValueState]:
    """Decode a ``ValueStatesAll`` blob (or the state portion of ``ValueStatesAndDataAll``).

    Returns a mapping of value ``number`` -> ``ValueState`` for every value that has a
    ``state_index`` (i.e. ``ValueDescription.state_index is not None``). Values with no
    state (``state_index is None``) are omitted.

    For ``ValueStatesAndDataAll`` (C.O. 24529): the blob is the data region (size =
    max ``data_index + data_length`` across non-OneTime values) followed immediately by
    the state region — pass only the state suffix to this function, or slice it yourself:
    ``data[data_region_size:]``.
    """
    result: dict[int, ValueState] = {}
    for value in table.values:
        if value.category is ValueCategory.ONE_TIME or value.state_index is None:
            continue
        raw = data[value.state_index]
        result[value.number] = ValueState(
            level1=ProtectionState(get_bits(raw, 0, 3)),
            level2=ProtectionState(get_bits(raw, 3, 3)),
            sensor_fail=ProtectionState(get_bits(raw, 6, 2) << 1),
        )
    return result
