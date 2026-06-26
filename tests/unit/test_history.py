"""Unit tests for history record parsing (parse_history_record)."""

from __future__ import annotations

import datetime
import struct

from pycomap.configuration import NamesCategory
from pycomap.history import parse_history_record


def _bcd(v: int) -> int:
    return ((v // 10) << 4) | (v % 10)


def _make_history_timestamp(
    *,
    day: int = 25,
    month: int = 6,
    year: int = 26,
    hour: int = 21,
    minute: int = 25,
    second: int = 8,
    tenth: int = 2,
    engine_hours: bool = False,
    index: int = 0x24B0,
) -> bytes:
    type_byte = (0x80 if engine_hours else 0x00) | (tenth & 0x0F)
    date_time_bytes = bytes(
        [_bcd(day), _bcd(month), _bcd(year), _bcd(hour), _bcd(minute), _bcd(second)]
    )
    return date_time_bytes + bytes([type_byte]) + struct.pack("<H", index)


def _make_record(
    *,
    reason_index: int = 0,
    reason_category: int = 0,
    prefix_index: int = 0,
    level: int = 0,
    timestamp: bytes | None = None,
    payload: bytes = b"",
) -> bytes:
    word = (reason_index & 0xFFF) | ((reason_category & 0x3) << 13)
    flags_byte = (prefix_index & 0x1F) | ((level & 0x7) << 5)
    ts = timestamp or _make_history_timestamp()
    return struct.pack("<HB", word, flags_byte) + ts + payload.ljust(57, b"\x00")


# ---------------------------------------------------------------------------
# Text records
# ---------------------------------------------------------------------------


def test_parse_text_record(mocker) -> None:
    mocker.patch("pycomap.history.parse_names_heap", return_value=[])

    text = b"T=ETH CA1 A CON(24554)=21:25:08\x00"
    raw = _make_record(prefix_index=30, payload=text)
    rec = parse_history_record(b"", raw)

    assert rec is not None
    assert rec.is_text
    assert rec.text == "T=ETH CA1 A CON(24554)=21:25:08"
    assert rec.timestamp == datetime.datetime(2026, 6, 25, 21, 25, 8)
    assert rec.tenth_seconds == 2
    assert rec.index == 0x24B0


# ---------------------------------------------------------------------------
# Alarm / event records
# ---------------------------------------------------------------------------


def test_parse_alarm_record_with_prefix(mocker) -> None:
    reason_names = ["Gen Voltage"]
    prefix_names = ["-", "Wrn", "Sd"]

    mocker.patch(
        "pycomap.history.parse_names_heap",
        side_effect=lambda _d, cat: (
            reason_names if cat is NamesCategory.HISTORY_REASON_NAMES else prefix_names
        ),
    )

    raw = _make_record(reason_index=0, reason_category=0, prefix_index=1, level=1)
    rec = parse_history_record(b"", raw)

    assert rec is not None
    assert not rec.is_text
    assert rec.reason == "Gen Voltage"
    assert rec.prefix == "Wrn"
    assert rec.level == 1


def test_parse_info_record_prefix_index_zero_returns_dash(mocker) -> None:
    """prefix_index=0 maps to '-' (info/status event, no protection class)."""
    prefix_names = ["-", "Wrn", "Sd"]

    mocker.patch(
        "pycomap.history.parse_names_heap",
        side_effect=lambda _d, cat: (
            [] if cat is NamesCategory.HISTORY_REASON_NAMES else prefix_names
        ),
    )

    raw = _make_record(reason_index=0, prefix_index=0, level=0)
    rec = parse_history_record(b"", raw)

    assert rec is not None
    assert rec.prefix == "-"


# ---------------------------------------------------------------------------
# Invalid / edge cases
# ---------------------------------------------------------------------------


def test_parse_invalid_record_returns_none(mocker) -> None:
    mocker.patch("pycomap.history.parse_names_heap", return_value=[])
    assert parse_history_record(b"", _make_record(prefix_index=31)) is None


def test_parse_too_short_returns_none() -> None:
    assert parse_history_record(b"", b"\x00" * 11) is None


def test_parse_timestamp_engine_hours(mocker) -> None:
    mocker.patch("pycomap.history.parse_names_heap", return_value=[])

    ts = _make_history_timestamp(engine_hours=True, day=0, month=0, year=0, hour=100, minute=30)
    raw = _make_record(timestamp=ts)
    rec = parse_history_record(b"", raw)

    assert rec is not None
    assert rec.timestamp is None
    assert rec.engine_hours is not None


def test_parse_invalid_bcd_wall_clock_timestamp_returns_none(mocker) -> None:
    """An invalid BCD timestamp (e.g. month=13) on a wall-clock record makes both
    dt and engine_hours None, so parse_history_record returns None."""
    mocker.patch("pycomap.history.parse_names_heap", return_value=[])
    ts = _make_history_timestamp(engine_hours=False, month=13)
    raw = _make_record(timestamp=ts)
    assert parse_history_record(b"", raw) is None


def test_parse_level_encoded_correctly(mocker) -> None:
    mocker.patch("pycomap.history.parse_names_heap", return_value=["R", "P"])

    for expected_level in range(6):
        raw = _make_record(prefix_index=0, level=expected_level)
        rec = parse_history_record(b"", raw)
        assert rec is not None
        assert rec.level == expected_level
