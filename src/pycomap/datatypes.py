"""ComAp wire data types, protection states, and raw value encode/decode.

``DataType`` mirrors ``DataTypeIdentifier`` from ``ComAp.GlobalShared.dll``; the byte-length
table and struct formats are from ``DataTypeDescription.DataTypeLength`` in
``ComAp.Controller.dll``.  ``decode_raw_value``/``encode_raw_value`` are the round-trip
codec for individual values/setpoints — their callers (``decode_values_all``,
``decode_setpoints_all``, ``encode_raw_value``) live in [pycomap.configuration][].

``ProtectionState`` mirrors ``enum ProtectionState`` from ``ComAp.Controller.dll``
(``ComAp.Controller.DataTypes`` namespace).

``decode_fdate`` / ``decode_ftime`` / ``encode_fdate`` / ``encode_ftime`` implement the
3-byte BCD ``FDate``/``FTime`` types used by ``CommunicationObject.DATE`` (24553) and
``CommunicationObject.TIME`` (24554). Source: ``ComAp.Controller.DataTypes.FDate`` /
``FTime`` in ``ComAp.Controller.dll``.
"""

from __future__ import annotations

import datetime
import enum
import struct

from pycomap.exceptions import ComApProtocolError


class DataType(enum.IntEnum):
    """ComAp ``DataTypeIdentifier`` enum."""

    INTEGER8 = 2
    INTEGER16 = 3
    INTEGER32 = 4
    UNSIGNED8 = 5
    UNSIGNED16 = 6
    UNSIGNED32 = 7
    FLOAT = 8
    DATE = 11
    DOMAIN = 15
    TIMER = 16
    BINARY8 = 64
    BINARY16 = 65
    BINARY32 = 66
    FTIME = 67
    FDATE = 68
    CHAR = 69
    STRING_LIST = 70
    SHORT_STRING = 71
    LONG_STRING = 72
    HUGE_STRING = 73
    IP_ADDRESS = 74
    TELEPHONE_NUMBER = 75
    EMAIL = 76


_DATA_TYPE_LENGTH: dict[DataType, int] = {
    DataType.INTEGER8: 1,
    DataType.UNSIGNED8: 1,
    DataType.BINARY8: 1,
    DataType.CHAR: 1,
    DataType.STRING_LIST: 1,
    DataType.INTEGER16: 2,
    DataType.UNSIGNED16: 2,
    DataType.BINARY16: 2,
    DataType.FTIME: 3,
    DataType.FDATE: 3,
    DataType.INTEGER32: 4,
    DataType.UNSIGNED32: 4,
    DataType.FLOAT: 4,
    DataType.BINARY32: 4,
    DataType.TIMER: 8,
    DataType.SHORT_STRING: 16,
    DataType.IP_ADDRESS: 16,
    DataType.LONG_STRING: 32,
    DataType.TELEPHONE_NUMBER: 32,
    DataType.HUGE_STRING: 64,
    DataType.EMAIL: 64,
}

_NUMERIC_STRUCT_FORMAT: dict[DataType, str] = {
    DataType.INTEGER8: "<b",
    DataType.INTEGER16: "<h",
    DataType.INTEGER32: "<i",
    DataType.UNSIGNED8: "<B",
    DataType.UNSIGNED16: "<H",
    DataType.UNSIGNED32: "<I",
    DataType.FLOAT: "<f",
    DataType.BINARY8: "<B",
    DataType.BINARY16: "<H",
    DataType.BINARY32: "<I",
}

_BINARY_TYPES = (DataType.BINARY8, DataType.BINARY16, DataType.BINARY32)


class ProtectionState(enum.IntFlag):
    """ComAp ``ProtectionState`` enum (``ValueState.Level1``/``Level2``/``SensorFail``).

    ``Delay``, ``Active``, and ``NotConfirmed`` are combinable: ``Active | NotConfirmed``
    (value 6) means the alarm is active but not yet acknowledged by the operator.
    Source: ``ComAp.Controller.DataTypes.ProtectionState`` in ``ComAp.Controller.dll``.
    """

    NOT_ACTIVE = 0
    DELAY = 1
    ACTIVE = 2
    NOT_CONFIRMED = 4


def decode_raw_value(
    data_type: DataType, raw: bytes, decimal_places: int = 0
) -> int | float | bytes:
    """Decode ``raw`` bytes (``len(raw) == _DATA_TYPE_LENGTH[data_type]``) per ``data_type``.

    Only numeric and binary(bitfield) types are decoded to Python numbers; string/domain/
    timer/date types are returned as raw bytes.
    """
    fmt = _NUMERIC_STRUCT_FORMAT.get(data_type)
    if fmt is None:
        return raw
    value = struct.unpack(fmt, raw)[0]
    if decimal_places and data_type not in _BINARY_TYPES:
        return value / (10**decimal_places)
    return value


def encode_raw_value(data_type: DataType, value: int | float, decimal_places: int = 0) -> bytes:
    """Encode ``value`` into the raw bytes ``decode_raw_value`` would decode it back from.

    Only numeric and binary(bitfield) types can be encoded -- there's no encoder for
    string/domain/timer/date types (write raw bytes directly via ``client.write_object``
    instead). The controller itself enforces the setpoint's min/max (returning
    ``ControllerError.BAD_WRITE_VALUE`` on rejection), so this doesn't validate limits.
    """
    fmt = _NUMERIC_STRUCT_FORMAT.get(data_type)
    if fmt is None:
        raise ComApProtocolError(f"cannot encode DataType.{data_type.name} -- not numeric")
    if data_type is not DataType.FLOAT and decimal_places and data_type not in _BINARY_TYPES:
        value = round(value * (10**decimal_places))
    return struct.pack(fmt, value if data_type is DataType.FLOAT else int(value))


# -- FDate / FTime BCD codec --------------------------------------------------
# Source: ComAp.Controller.DataTypes.FDate / FTime in ComAp.Controller.dll.
# Both types are 3-byte, each byte standard nibble-BCD (high nibble = tens, low = units).


def get_bits(value: int, start: int, width: int) -> int:
    """Extract ``width`` bits from ``value`` starting at bit ``start`` (LSB=0)."""
    return (value >> start) & ((1 << width) - 1)


def _bcd_decode(b: int) -> int:
    return 10 * ((b >> 4) & 0xF) + (b & 0xF)


def _bcd_encode(v: int) -> int:
    return ((v // 10) << 4) | (v % 10)


def decode_fdate(raw: bytes) -> datetime.date | None:
    """Decode a 3-byte FDate payload ``[BCD(day), BCD(month), BCD(year-2000)]``.

    Returns ``None`` for invalid/unset values (all 0xFF, or day byte == 0).
    """
    if len(raw) != 3:
        raise ComApProtocolError(f"FDate requires 3 bytes, got {len(raw)}")
    if raw[0] == 0 or (raw[0] == 0xFF and raw[1] == 0xFF and raw[2] == 0xFF):
        return None
    day = _bcd_decode(raw[0])
    month = _bcd_decode(raw[1])
    year = _bcd_decode(raw[2]) + 2000
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def encode_fdate(date: datetime.date) -> bytes:
    """Encode a ``datetime.date`` as a 3-byte FDate payload."""
    if date.year < 2000:
        raise ComApProtocolError("FDate cannot represent years before 2000")
    return bytes([_bcd_encode(date.day), _bcd_encode(date.month), _bcd_encode(date.year - 2000)])


def decode_ftime(raw: bytes) -> datetime.time | None:
    """Decode a 3-byte FTime payload ``[BCD(hour), BCD(minute), BCD(second)]``.

    Returns ``None`` for invalid/unset values (hour byte ≥ 0x36 per source check).
    """
    if len(raw) != 3:
        raise ComApProtocolError(f"FTime requires 3 bytes, got {len(raw)}")
    if raw[0] >= 0x36:
        return None
    try:
        return datetime.time(_bcd_decode(raw[0]), _bcd_decode(raw[1]), _bcd_decode(raw[2]))
    except ValueError:
        return None


def encode_ftime(time: datetime.time) -> bytes:
    """Encode a ``datetime.time`` as a 3-byte FTime payload."""
    return bytes([_bcd_encode(time.hour), _bcd_encode(time.minute), _bcd_encode(time.second)])
