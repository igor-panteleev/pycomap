"""Unit tests for pycomap.datatypes (DataType codec, ProtectionState, BCD)."""

from __future__ import annotations

import datetime
import struct

import pytest

from pycomap.datatypes import (
    _DATA_TYPE_LENGTH,
    DataType,
    ProtectionState,
    decode_fdate,
    decode_ftime,
    decode_raw_value,
    encode_fdate,
    encode_ftime,
    encode_raw_value,
)
from pycomap.exceptions import ComApProtocolError

# -- FDate --------------------------------------------------------------------


def test_decode_fdate_valid() -> None:
    # 25 Jun 2026 → [BCD(25), BCD(6), BCD(26)] = [0x25, 0x06, 0x26]
    raw = bytes([0x25, 0x06, 0x26])
    assert decode_fdate(raw) == datetime.date(2026, 6, 25)


def test_decode_fdate_invalid_all_ff() -> None:
    assert decode_fdate(bytes([0xFF, 0xFF, 0xFF])) is None


def test_decode_fdate_invalid_day_zero() -> None:
    assert decode_fdate(bytes([0x00, 0x06, 0x26])) is None


def test_decode_fdate_wrong_length() -> None:
    with pytest.raises(ComApProtocolError):
        decode_fdate(bytes([0x01, 0x01]))


def test_decode_fdate_invalid_month_returns_none() -> None:
    # month=13 passes the early-return guards (day≠0, not all-FF) but raises ValueError
    # inside datetime.date() → caught and returns None (lines 174-175 in datatypes.py)
    assert decode_fdate(bytes([0x25, 0x13, 0x26])) is None


def test_encode_fdate_roundtrip() -> None:
    date = datetime.date(2026, 6, 25)
    assert decode_fdate(encode_fdate(date)) == date


def test_encode_fdate_year_before_2000() -> None:
    with pytest.raises(ComApProtocolError):
        encode_fdate(datetime.date(1999, 12, 31))


# -- FTime --------------------------------------------------------------------


def test_decode_ftime_valid() -> None:
    # 21:07:47 → [BCD(21), BCD(7), BCD(47)] = [0x21, 0x07, 0x47]
    raw = bytes([0x21, 0x07, 0x47])
    assert decode_ftime(raw) == datetime.time(21, 7, 47)


def test_decode_ftime_midnight() -> None:
    raw = bytes([0x00, 0x00, 0x00])
    assert decode_ftime(raw) == datetime.time(0, 0, 0)


def test_decode_ftime_invalid_hour_ge_0x36() -> None:
    # 0x36 = 54 decimal > 23, so invalid
    assert decode_ftime(bytes([0x36, 0x00, 0x00])) is None


def test_decode_ftime_wrong_length() -> None:
    with pytest.raises(ComApProtocolError):
        decode_ftime(bytes([0x12, 0x00]))


def test_decode_ftime_invalid_minute_returns_none() -> None:
    # minute=60: 0x60 is valid BCD but datetime.time rejects it → ValueError → None
    # (lines 196-197); hour=0x10 < 0x36 so it passes the early guard
    assert decode_ftime(bytes([0x10, 0x60, 0x00])) is None


def test_encode_ftime_roundtrip() -> None:
    time = datetime.time(21, 7, 47)
    assert decode_ftime(encode_ftime(time)) == time


def test_encode_ftime_midnight_roundtrip() -> None:
    time = datetime.time(0, 0, 0)
    assert decode_ftime(encode_ftime(time)) == time


# -- DataType codec -----------------------------------------------------------


@pytest.mark.parametrize(
    ("data_type", "raw", "decimal_places", "expected"),
    [
        (DataType.UNSIGNED16, struct.pack("<H", 2300), 2, 23.0),
        (DataType.INTEGER16, struct.pack("<h", -5), 0, -5),
        (DataType.FLOAT, struct.pack("<f", 1.5), 0, 1.5),
        (DataType.BINARY16, struct.pack("<H", 0b101), 2, 0b101),  # decimal_places ignored
        (DataType.SHORT_STRING, b"x" * 16, 0, b"x" * 16),  # not decoded, returned raw
    ],
)
def test_decode_raw_value(
    data_type: DataType, raw: bytes, decimal_places: int, expected: object
) -> None:
    assert decode_raw_value(data_type, raw, decimal_places) == expected


@pytest.mark.parametrize(
    ("data_type", "value", "decimal_places"),
    [
        (DataType.UNSIGNED16, 23.0, 2),
        (DataType.INTEGER16, -5, 0),
        (DataType.FLOAT, 1.5, 0),
        (DataType.BINARY16, 0b101, 2),
        (DataType.UNSIGNED8, 200, 0),
    ],
)
def test_encode_raw_value_round_trips_through_decode(
    data_type: DataType, value: int | float, decimal_places: int
) -> None:
    raw = encode_raw_value(data_type, value, decimal_places)
    assert len(raw) == _DATA_TYPE_LENGTH[data_type]
    assert decode_raw_value(data_type, raw, decimal_places) == value


def test_encode_raw_value_rejects_non_numeric_type() -> None:
    with pytest.raises(ComApProtocolError):
        encode_raw_value(DataType.SHORT_STRING, 1)


# -- ProtectionState ----------------------------------------------------------


def test_protection_state_combinable_flags() -> None:
    active_unconfirmed = ProtectionState.ACTIVE | ProtectionState.NOT_CONFIRMED
    assert active_unconfirmed & ProtectionState.ACTIVE
    assert active_unconfirmed & ProtectionState.NOT_CONFIRMED
    assert int(active_unconfirmed) == 6
