"""Unit tests for ConfigurationTable parsing and ValuesAll decoding.

The byte layout is reverse-engineered from ``ComAp.Controller.dll`` (decompiled) and verified
against a live controller's raw ``ConfigurationTable``/``ValuesAll`` -- see
docs/protocol.md section 4. ``_build_table`` below constructs a minimal synthetic table with
the same layout, rather than embedding the real ~100KB table as a fixture.
"""

from __future__ import annotations

import struct

import pytest

from pycomap.configuration import (
    NamesCategory,
    SetpointCategory,
    ValueCategory,
    decode_history_snapshot,
    decode_setpoints_all,
    decode_states_all,
    decode_values_all,
    parse_configuration_table,
    parse_names_heap,
)
from pycomap.datatypes import (
    DataType,
    ProtectionState,
)
from pycomap.exceptions import ComApProtocolError
from tests.unit.builders import _COMMON_NAMES, _DIMENSIONS
from tests.unit.builders import build_table as _build_table
from tests.unit.builders import setpoint_record as _setpoint_record
from tests.unit.builders import value_record as _value_record


def test_parse_rejects_non_il3_controller_type() -> None:
    data = _build_table(category_counts=(0, 0, 0, 0), numbers=[], records=[], controller_type=5)
    with pytest.raises(ComApProtocolError):
        parse_configuration_table(data)


def test_parse_names_heap() -> None:
    data = _build_table(category_counts=(0, 0, 0, 0), numbers=[], records=[])
    assert parse_names_heap(data, NamesCategory.COMMON_NAMES) == _COMMON_NAMES
    assert parse_names_heap(data, NamesCategory.DIMENSIONS) == _DIMENSIONS


def test_parse_and_decode_values_all() -> None:
    # First: one Unsigned16 value with a state. Second: one Binary8 value, no state.
    # OneTime: one Unsigned8 value, excluded from ValuesAll entirely.
    data = _build_table(
        category_counts=(1, 1, 0, 1),
        numbers=[100, 200, 300],
        records=[
            _value_record(data_type=DataType.UNSIGNED16, data_index=0, state_index=0),
            _value_record(data_type=DataType.BINARY8, data_index=2, name_index=1),
            _value_record(data_type=DataType.UNSIGNED8, data_index=0),
        ],
    )

    table = parse_configuration_table(data)
    assert [v.number for v in table.values] == [100, 200, 300]
    assert [v.category for v in table.values] == [
        ValueCategory.FIRST,
        ValueCategory.SECOND,
        ValueCategory.ONE_TIME,
    ]

    first = table.values[0]
    assert first.data_type is DataType.UNSIGNED16
    assert first.data_length == 2
    assert first.data_index == 0
    assert first.state_index == 0
    assert first.name == "VOne"
    assert first.dimension == "V"

    second = table.values[1]
    assert second.state_index is None  # 1023 sentinel -> no state
    assert second.name == "VTwo"
    assert second.dimension == "V"  # dim_index defaults to 0 -> DIMENSIONS[0]

    values_all = struct.pack("<H", 0x1234) + bytes([0x05])
    decoded = decode_values_all(table, values_all)

    assert decoded == {100: 0x1234, 200: 0x05}
    assert 300 not in decoded  # ONE_TIME values are not in ValuesAll


def test_decode_values_all_skips_and_warns_non_one_time_value_beyond_blob(caplog) -> None:
    import logging

    # A non-ONE_TIME (FIRST category) value whose data_index exceeds the blob.
    data = _build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[42],
        records=[_value_record(data_type=DataType.UNSIGNED16, data_index=10)],
    )
    table = parse_configuration_table(data)
    blob = b"\x01\x02"  # only 2 bytes; value at data_index=10 does not fit

    with caplog.at_level(logging.WARNING, logger="pycomap.configuration"):
        result = decode_values_all(table, blob)

    assert 42 not in result
    assert "exceeds blob size" in caplog.text


def test_parse_and_decode_setpoints_all() -> None:
    data = _build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(1, 1),
        setpoint_numbers=[400, 500],
        setpoint_records=[
            _setpoint_record(data_type=DataType.UNSIGNED16, data_index=0, decimal_places=1),
            _setpoint_record(data_type=DataType.UNSIGNED8, data_index=2, name_index=1),
        ],
    )

    table = parse_configuration_table(data)
    assert [s.number for s in table.setpoints] == [400, 500]
    assert [s.category for s in table.setpoints] == [SetpointCategory.P, SetpointCategory.R]

    first = table.setpoints[0]
    assert first.data_type is DataType.UNSIGNED16
    assert first.name == "VOne"

    setpoints_all = struct.pack("<H", 150) + bytes([7])
    decoded = decode_setpoints_all(table, setpoints_all)
    assert decoded == {400: 15.0, 500: 7}


def test_decode_states_all_maps_state_index_to_value_number() -> None:
    # Value at data_index=0, state_index=0 → first byte of states blob
    data = _build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[42],
        records=[
            _value_record(
                data_type=DataType.UNSIGNED16,
                data_index=0,
                state_index=0,
            )
        ],
    )
    table = parse_configuration_table(data)

    # state byte: Level1=ACTIVE(2), Level2=DELAY(1), SensorFail raw=1→<<1=2=ACTIVE
    state_byte = bytes([0b01_001_010])  # bits 0-2=2(ACTIVE), 3-5=1(DELAY), 6-7=1(raw→ACTIVE)
    states = decode_states_all(table, state_byte)

    assert 42 in states
    s = states[42]
    assert s.level1 == ProtectionState.ACTIVE
    assert s.level2 == ProtectionState.DELAY
    assert s.sensor_fail == ProtectionState.ACTIVE
    assert s.any_alarm


def test_decode_states_all_skips_values_without_state() -> None:
    data = _build_table(
        category_counts=(2, 0, 0, 0),
        numbers=[10, 20],
        records=[
            _value_record(data_type=DataType.UNSIGNED16, data_index=0, state_index=0),
            _value_record(data_type=DataType.UNSIGNED8, data_index=2),  # state_index=1023→None
        ],
    )
    table = parse_configuration_table(data)
    states = decode_states_all(table, bytes([0x02, 0x00]))

    assert 10 in states
    assert 20 not in states  # no state_index


def test_value_state_any_alarm_false_when_all_not_active() -> None:
    from pycomap.configuration import ValueState

    na = ProtectionState.NOT_ACTIVE
    s = ValueState(na, na, na)
    assert not s.any_alarm


# ---------------------------------------------------------------------------
# SetpointDescription.needs_password
# ---------------------------------------------------------------------------


def test_setpoint_needs_password_when_access_level_nonzero() -> None:
    data = _build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(1, 0),
        setpoint_numbers=[10],
        setpoint_records=[
            _setpoint_record(data_type=DataType.UNSIGNED16, data_index=0, access_level=1),
        ],
    )
    table = parse_configuration_table(data)
    desc = table.setpoints[0]
    assert desc.needs_password is True


def test_setpoint_needs_password_false_when_access_level_zero() -> None:
    data = _build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(1, 0),
        setpoint_numbers=[10],
        setpoint_records=[
            _setpoint_record(data_type=DataType.UNSIGNED16, data_index=0, access_level=0),
        ],
    )
    table = parse_configuration_table(data)
    desc = table.setpoints[0]
    assert desc.needs_password is False


# ---------------------------------------------------------------------------
# Signed limit reinterpretation (INTEGER* types)
# ---------------------------------------------------------------------------


def test_setpoint_signed_limits_reinterpreted_for_integer_type() -> None:
    # 0xFC18 = 64536 as uint16 = -1000 as int16; 0x03E8 = 1000
    data = _build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(1, 0),
        setpoint_numbers=[20],
        setpoint_records=[
            _setpoint_record(
                data_type=DataType.INTEGER16,
                data_index=0,
                low_limit=0xFC18,
                high_limit=0x03E8,
            ),
        ],
    )
    table = parse_configuration_table(data)
    desc = table.setpoints[0]
    assert desc.low_limit == -1000
    assert desc.high_limit == 1000


def test_value_signed_limits_reinterpreted_for_integer_type() -> None:
    data = _build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[30],
        records=[
            _value_record(
                data_type=DataType.INTEGER16,
                data_index=0,
                low_limit=0xFC18,
                high_limit=0x03E8,
            ),
        ],
    )
    table = parse_configuration_table(data)
    desc = table.values[0]
    assert desc.low_limit == -1000
    assert desc.high_limit == 1000


# ---------------------------------------------------------------------------
# decode_history_snapshot
# ---------------------------------------------------------------------------


def test_decode_history_snapshot_decodes_fitting_values() -> None:
    # Two UNSIGNED16 values at data_index 0 and 2; snapshot is exactly 4 bytes.
    data = _build_table(
        category_counts=(2, 0, 0, 0),
        numbers=[10, 20],
        records=[
            _value_record(data_type=DataType.UNSIGNED16, data_index=0),
            _value_record(data_type=DataType.UNSIGNED16, data_index=2),
        ],
    )
    table = parse_configuration_table(data)
    snapshot = struct.pack("<HH", 230, 50)  # 4 bytes exactly covering both values
    result = decode_history_snapshot(table, snapshot)

    assert result == {10: 230, 20: 50}


def test_decode_history_snapshot_omits_values_beyond_snapshot() -> None:
    # First value fits in 2-byte snapshot; second (data_index=2) does not.
    data = _build_table(
        category_counts=(2, 0, 0, 0),
        numbers=[10, 20],
        records=[
            _value_record(data_type=DataType.UNSIGNED16, data_index=0),
            _value_record(data_type=DataType.UNSIGNED16, data_index=2),
        ],
    )
    table = parse_configuration_table(data)
    snapshot = struct.pack("<H", 100)  # only 2 bytes — value 20 is out of range
    result = decode_history_snapshot(table, snapshot)

    assert 10 in result
    assert result[10] == 100
    assert 20 not in result


def test_decode_history_snapshot_empty_returns_empty_dict() -> None:
    data = _build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[10],
        records=[_value_record(data_type=DataType.UNSIGNED16, data_index=0)],
    )
    table = parse_configuration_table(data)
    assert decode_history_snapshot(table, b"") == {}


def test_decode_history_snapshot_skips_one_time_values() -> None:
    # ONE_TIME values (category index 3) are never in the snapshot.
    data = _build_table(
        category_counts=(0, 0, 0, 1),  # one ONE_TIME value
        numbers=[99],
        records=[_value_record(data_type=DataType.UNSIGNED16, data_index=0)],
    )
    table = parse_configuration_table(data)
    snapshot = struct.pack("<H", 42)
    result = decode_history_snapshot(table, snapshot)

    assert 99 not in result
    assert result == {}
