"""Unit tests for pycomap.alarms (parse_alarm_list / AlarmRecord)."""

from __future__ import annotations

import struct

import pytest

from pycomap.alarms import parse_alarm_list
from pycomap.configuration import NamesCategory


def _make_il3_alarm_record(
    *,
    fault_code: int = 0,
    prefix_index: int = 0,
    occurred: int = 1,
    kind: int = 7,  # ComAp
    reason_index: int = 0,
    is_active: bool = True,
    is_confirmed: bool = False,
    source: int = 0,
) -> bytes:
    """Build a 7-byte IL3 alarm record for testing."""
    dw = (
        (fault_code & 0x7FFFF)
        | ((prefix_index & 0x1F) << 19)
        | ((occurred & 0x7F) << 24)
        | (1 << 31)  # is_used sentinel
    )
    flags = (
        (kind & 0x7)
        | ((reason_index & 0x7FF) << 3)
        | ((1 if is_active else 0) << 14)
        | ((1 if is_confirmed else 0) << 15)
    )
    return struct.pack("<IHB", dw, flags, source)


def test_parse_alarm_list_empty_returns_no_records(monkeypatch: pytest.MonkeyPatch) -> None:
    import pycomap.alarms as alarms_mod

    monkeypatch.setattr(alarms_mod, "parse_names_heap", lambda _data, _cat: ["Reason0", "Prefix0"])
    # All-zero blob → bit 31 of first uint32 is 0 → no used records
    result = parse_alarm_list(b"", bytes(112))
    assert result == []


def test_parse_alarm_list_single_active_record(monkeypatch: pytest.MonkeyPatch) -> None:
    import pycomap.alarms as alarms_mod

    reason_names = ["Gen Voltage", "Gen Frequency"]
    prefix_names = ["-", "Wrn", "Sd"]

    def fake_parse_names_heap(data: bytes, category: NamesCategory) -> list[str]:
        if category is NamesCategory.ALARM_REASON_NAMES:
            return reason_names
        return prefix_names

    monkeypatch.setattr(alarms_mod, "parse_names_heap", fake_parse_names_heap)

    record = _make_il3_alarm_record(
        prefix_index=1,  # "Wrn"
        reason_index=0,  # "Gen Voltage"
        occurred=3,
        is_active=True,
        is_confirmed=False,
        source=0,
    )
    alarm_data = record + bytes(112 - 7)
    records = parse_alarm_list(b"", alarm_data)

    assert len(records) == 1
    r = records[0]
    assert r.is_active
    assert not r.is_confirmed
    assert r.reason == "Gen Voltage"
    assert r.prefix == "Wrn"
    assert r.occurred == 3
    assert r.source == 0


def test_parse_alarm_list_stops_at_first_unused(monkeypatch: pytest.MonkeyPatch) -> None:
    import pycomap.alarms as alarms_mod

    monkeypatch.setattr(alarms_mod, "parse_names_heap", lambda _d, _c: ["R"])

    rec = _make_il3_alarm_record(reason_index=0)
    alarm_data = rec + rec + bytes(112 - 14)
    records = parse_alarm_list(b"", alarm_data)
    assert len(records) == 2


def test_parse_alarm_list_confirmed_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    import pycomap.alarms as alarms_mod

    monkeypatch.setattr(alarms_mod, "parse_names_heap", lambda _d, _c: ["R", "P"])

    rec = _make_il3_alarm_record(is_active=False, is_confirmed=True, reason_index=0, prefix_index=0)
    records = parse_alarm_list(b"", rec + bytes(112 - 7))
    assert len(records) == 1
    assert not records[0].is_active
    assert records[0].is_confirmed


def test_parse_alarm_list_non_comap_kind_has_empty_reason_and_prefix(mocker) -> None:
    # kind != 7 (e.g. ECU/CAN alarm) → reason and prefix are always ""
    mocker.patch("pycomap.alarms.parse_names_heap", return_value=["Reason0", "Prefix0"])

    rec = _make_il3_alarm_record(kind=5, fault_code=0x1234, prefix_index=1, reason_index=0)
    records = parse_alarm_list(b"", rec + bytes(112 - 7))

    assert len(records) == 1
    r = records[0]
    assert r.reason == ""
    assert r.prefix == ""
    assert r.fault_code == 0x1234
