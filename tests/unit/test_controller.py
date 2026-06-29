"""Unit tests for controller-level logic: _parse_gmt_label, _coerce_setpoint_value,
and var_limit flag parsing.
"""

from __future__ import annotations

import datetime
import struct

import pytest

from pycomap.configuration import (
    DataType,
    SetpointCategory,
    SetpointDescription,
    parse_configuration_table,
)
from pycomap.controller import Controller, _encode_setpoint_value, _parse_gmt_label
from pycomap.exceptions import ComApAuthError, ComApProtocolError
from tests.unit.builders import build_table, setpoint_record, value_record

# ---------------------------------------------------------------------------
# _parse_gmt_label
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("GMT+0:00", datetime.timedelta(0)),
        ("GMT+2:00", datetime.timedelta(hours=2)),
        ("GMT-3:30", datetime.timedelta(hours=-3, minutes=-30)),
        ("GMT+5:30", datetime.timedelta(hours=5, minutes=30)),
        ("GMT-12:00", datetime.timedelta(hours=-12)),
        ("GMT+13:00", datetime.timedelta(hours=13)),
        (" GMT+1:00 ", datetime.timedelta(hours=1)),  # leading/trailing whitespace
    ],
)
def test_parse_gmt_label_valid(label: str, expected: datetime.timedelta) -> None:
    assert _parse_gmt_label(label) == expected


@pytest.mark.parametrize(
    "label",
    ["UTC+2", "GMT2:00", "GMT+2", "+2:00", "", "GMT+25:00"],
)
def test_parse_gmt_label_invalid_returns_none(label: str) -> None:
    assert _parse_gmt_label(label) is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_setpoint(
    *,
    data_type: DataType,
    low_limit: int = 0,
    high_limit: int = 100,
    var_low_limit: bool = False,
    var_high_limit: bool = False,
    decimal_places: int = 0,
    name: str = "Test",
) -> SetpointDescription:
    return SetpointDescription(
        number=1000,
        category=SetpointCategory.P,
        data_type=data_type,
        data_length=2,
        decimal_places=decimal_places,
        data_index=0,
        name=name,
        dimension="",
        group=None,
        access_level=0,
        low_limit=low_limit,
        high_limit=high_limit,
        var_low_limit=var_low_limit,
        var_high_limit=var_high_limit,
    )


# ---------------------------------------------------------------------------
# var_low_limit / var_high_limit parsing (via _setpoint_record in configuration)
# ---------------------------------------------------------------------------


def test_setpoint_record_var_flags_parsed() -> None:
    """Bits 1 and 2 of dword2 map to var_low_limit and var_high_limit."""
    data = build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(2, 0),
        setpoint_numbers=[100, 200],
        setpoint_records=[
            setpoint_record(
                data_type=DataType.UNSIGNED16, data_index=0, low_limit=10, high_limit=90
            ),
            setpoint_record(
                data_type=DataType.UNSIGNED16,
                data_index=2,
                low_limit=5,
                high_limit=35,
                var_high_limit=True,
            ),
        ],
    )
    table = parse_configuration_table(data)
    fixed, variable_hi = table.setpoints

    assert not fixed.var_low_limit
    assert not fixed.var_high_limit
    assert fixed.low_limit == 10
    assert fixed.high_limit == 90

    assert not variable_hi.var_low_limit
    assert variable_hi.var_high_limit
    assert variable_hi.low_limit == 5
    assert variable_hi.high_limit == 35  # raw setpoint index, not a real limit


# ---------------------------------------------------------------------------
# _coerce_setpoint_value — numeric range
# ---------------------------------------------------------------------------


def test_coerce_unsigned_in_range(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.UNSIGNED16, low_limit=100, high_limit=4000)
    assert Controller._coerce_setpoint_value(ctrl, desc, 1500) == 1500


def test_coerce_unsigned_below_low_raises(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.UNSIGNED16, low_limit=100, high_limit=4000)
    with pytest.raises(ValueError, match="out of range"):
        Controller._coerce_setpoint_value(ctrl, desc, 50)


def test_coerce_unsigned_above_high_raises(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.UNSIGNED16, low_limit=100, high_limit=4000)
    with pytest.raises(ValueError, match="out of range"):
        Controller._coerce_setpoint_value(ctrl, desc, 9999)


def test_coerce_signed_negative_in_range(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.INTEGER16, low_limit=-1000, high_limit=1000)
    assert Controller._coerce_setpoint_value(ctrl, desc, -500) == -500


def test_coerce_signed_below_low_raises(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.INTEGER16, low_limit=-1000, high_limit=1000)
    with pytest.raises(ValueError, match="out of range"):
        Controller._coerce_setpoint_value(ctrl, desc, -2000)


def test_coerce_decimal_places_scaling(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    # wire range 500..1500, dp=1 → user range 50.0..150.0
    desc = _make_setpoint(
        data_type=DataType.UNSIGNED16, low_limit=500, high_limit=1500, decimal_places=1
    )
    assert Controller._coerce_setpoint_value(ctrl, desc, 60.0) == 60.0
    with pytest.raises(ValueError, match=r"\[50\.0\.\.150\.0\]"):
        Controller._coerce_setpoint_value(ctrl, desc, 200.0)


def test_coerce_var_low_limit_skips_low_check(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(
        data_type=DataType.UNSIGNED16, low_limit=999, high_limit=4000, var_low_limit=True
    )
    assert Controller._coerce_setpoint_value(ctrl, desc, 0) == 0


def test_coerce_var_high_limit_skips_high_check(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(
        data_type=DataType.UNSIGNED16, low_limit=0, high_limit=35, var_high_limit=True
    )
    assert Controller._coerce_setpoint_value(ctrl, desc, 9999) == 9999


def test_coerce_float_type_skips_validation(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.FLOAT, low_limit=0, high_limit=0)
    assert Controller._coerce_setpoint_value(ctrl, desc, 999.9) == 999.9


def test_coerce_bytes_passthrough(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _make_setpoint(data_type=DataType.UNSIGNED16, low_limit=0, high_limit=10)
    raw = struct.pack("<H", 50000)
    assert Controller._coerce_setpoint_value(ctrl, desc, raw) == raw


# ---------------------------------------------------------------------------
# _coerce_setpoint_value — STRING_LIST
# ---------------------------------------------------------------------------

_OPTIONS = [(0, "Disabled"), (1, "Winter"), (2, "Summer"), (3, "Winter-S"), (4, "Summer-S")]


def _string_list_desc(**kwargs) -> SetpointDescription:
    return _make_setpoint(
        data_type=DataType.STRING_LIST,
        low_limit=72,
        high_limit=76,
        name="Summer Time Mode",
        **kwargs,
    )


def test_coerce_string_list_label_resolves_to_wire_index(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    ctrl.setpoint_options.return_value = _OPTIONS
    assert Controller._coerce_setpoint_value(ctrl, _string_list_desc(), "Summer") == 2


def test_coerce_string_list_unknown_label_raises(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    ctrl.setpoint_options.return_value = _OPTIONS
    with pytest.raises(ValueError, match="not a valid option"):
        Controller._coerce_setpoint_value(ctrl, _string_list_desc(), "Noon")


def test_coerce_string_list_valid_int_index(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    assert Controller._coerce_setpoint_value(ctrl, _string_list_desc(), 3) == 3


def test_coerce_string_list_int_out_of_range_raises(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    with pytest.raises(ValueError, match="out of range"):
        Controller._coerce_setpoint_value(ctrl, _string_list_desc(), 99)


def test_coerce_string_list_var_high_skips_index_check(mocker) -> None:
    ctrl = mocker.MagicMock(spec=Controller)
    desc = _string_list_desc(var_high_limit=True)
    assert Controller._coerce_setpoint_value(ctrl, desc, 99) == 99


# ---------------------------------------------------------------------------
# _encode_setpoint_value (module-level, called from set_setpoint)
# ---------------------------------------------------------------------------


def test_encode_setpoint_value_bytes_passthrough() -> None:
    raw = b"\x01\x02"
    assert _encode_setpoint_value(DataType.UNSIGNED16, 0, raw) is raw


def test_encode_setpoint_value_string_for_string_type() -> None:
    from pycomap.datatypes import _DATA_TYPE_LENGTH

    result = _encode_setpoint_value(DataType.SHORT_STRING, 0, "hello")
    assert result[:5] == b"hello"
    assert len(result) == _DATA_TYPE_LENGTH[DataType.SHORT_STRING]


def test_encode_setpoint_value_string_for_non_string_type_raises() -> None:
    from pycomap.exceptions import ComApProtocolError

    with pytest.raises(ComApProtocolError):
        _encode_setpoint_value(DataType.UNSIGNED8, 0, "not allowed")


def test_encode_setpoint_value_index_type_returns_single_byte() -> None:
    result = _encode_setpoint_value(DataType.STRING_LIST, 0, 3)
    assert result == bytes([3])


def test_encode_setpoint_value_numeric_roundtrips() -> None:
    from pycomap.datatypes import decode_raw_value

    result = _encode_setpoint_value(DataType.UNSIGNED16, 2, 23.0)
    assert decode_raw_value(DataType.UNSIGNED16, result, 2) == 23.0


# ---------------------------------------------------------------------------
# value_bit_names
# ---------------------------------------------------------------------------

# CommonNames layout used in builders.py: ["VOne", "VTwo"] at indices 0 and 1.
# bit_name_index=0 means bit 0 → "VOne", bit 1 → "VTwo".


def _build_binary_table(*, data_type: DataType, bit_name_index: int | None) -> bytes:
    return build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[42],
        records=[value_record(data_type=data_type, data_index=0, bit_name_index=bit_name_index)],
    )


def _make_ctrl_with_table(mocker, table_data: bytes) -> Controller:
    from pycomap.configuration import NamesCategory, parse_configuration_table, parse_names_heap

    ctrl = Controller.__new__(Controller)
    ctrl._table = parse_configuration_table(table_data)
    ctrl._common_names = parse_names_heap(table_data, NamesCategory.COMMON_NAMES)
    ctrl._values_by_number = {v.number: v for v in ctrl._table.values}
    ctrl._values_by_name = {}
    ctrl._ambiguous_value_names = set()
    for v in ctrl._table.values:
        if v.name in ctrl._values_by_name:
            ctrl._ambiguous_value_names.add(v.name)
        else:
            ctrl._values_by_name[v.name] = v
    ctrl._setpoints_by_number = {s.number: s for s in ctrl._table.setpoints}
    ctrl._setpoints_by_name = {}
    ctrl._ambiguous_setpoint_names = set()
    for s in ctrl._table.setpoints:
        if s.name in ctrl._setpoints_by_name:
            ctrl._ambiguous_setpoint_names.add(s.name)
        else:
            ctrl._setpoints_by_name[s.name] = s
    ctrl._one_time_values = {}
    ctrl._include_invisible = False
    return ctrl


def test_value_bit_names_binary8_returns_labels(mocker) -> None:
    table_data = _build_binary_table(data_type=DataType.BINARY8, bit_name_index=0)
    ctrl = _make_ctrl_with_table(mocker, table_data)

    result = ctrl.value_bit_names(42)

    # builders.py _COMMON_NAMES = ["VOne", "VTwo"]; only 2 names available so only 2 tuples
    assert result == [(0, "VOne"), (1, "VTwo")]


def test_value_bit_names_by_name(mocker) -> None:
    table_data = _build_binary_table(data_type=DataType.BINARY16, bit_name_index=0)
    ctrl = _make_ctrl_with_table(mocker, table_data)

    result = ctrl.value_bit_names("VOne")  # name lookup

    assert result[0] == (0, "VOne")
    assert result[1] == (1, "VTwo")


def test_value_bit_names_non_binary_raises(mocker) -> None:
    table_data = build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[10],
        records=[value_record(data_type=DataType.UNSIGNED16, data_index=0)],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)

    with pytest.raises(ComApProtocolError, match="not a BINARY type"):
        ctrl.value_bit_names(10)


def test_value_bit_names_no_bit_name_index_raises(mocker) -> None:
    table_data = _build_binary_table(data_type=DataType.BINARY8, bit_name_index=None)
    ctrl = _make_ctrl_with_table(mocker, table_data)

    with pytest.raises(ComApProtocolError, match="no bit name labels"):
        ctrl.value_bit_names(42)


# ---------------------------------------------------------------------------
# value_info / setpoint_info — ambiguous name detection
# ---------------------------------------------------------------------------


def test_value_info_raises_for_ambiguous_name(mocker) -> None:
    # Both numbers [10, 20] get name_index=0 → "VOne" — duplicate name
    table_data = build_table(
        category_counts=(2, 0, 0, 0),
        numbers=[10, 20],
        records=[
            value_record(data_type=DataType.UNSIGNED8, data_index=0, name_index=0),
            value_record(data_type=DataType.UNSIGNED8, data_index=1, name_index=0),
        ],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)

    with pytest.raises(ComApProtocolError, match="ambiguous"):
        ctrl.value_info("VOne")


def test_value_info_by_number_works_despite_ambiguous_name(mocker) -> None:
    table_data = build_table(
        category_counts=(2, 0, 0, 0),
        numbers=[10, 20],
        records=[
            value_record(data_type=DataType.UNSIGNED8, data_index=0, name_index=0),
            value_record(data_type=DataType.UNSIGNED8, data_index=1, name_index=0),
        ],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)

    assert ctrl.value_info(10).number == 10
    assert ctrl.value_info(20).number == 20


def test_setpoint_info_raises_for_ambiguous_name(mocker) -> None:
    table_data = build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(2, 0),
        setpoint_numbers=[100, 200],
        setpoint_records=[
            setpoint_record(data_type=DataType.UNSIGNED8, data_index=0, name_index=0),
            setpoint_record(data_type=DataType.UNSIGNED8, data_index=1, name_index=0),
        ],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)

    with pytest.raises(ComApProtocolError, match="ambiguous"):
        ctrl.setpoint_info("VOne")


# ---------------------------------------------------------------------------
# _resolve_raws / value_label — STRING_LIST label resolution
# ---------------------------------------------------------------------------

# builders.py: _COMMON_NAMES = ["VOne", "VTwo"] (indices 0 and 1).
# A STRING_LIST value with low_limit=1, wire=0 must resolve to CommonNames[1] = "VTwo",
# not CommonNames[0] = "VOne" (which would be the wrong "bare wire" lookup).


def _build_string_list_table(*, low_limit: int = 0) -> bytes:
    return build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[99],
        records=[
            value_record(
                data_type=DataType.STRING_LIST, data_index=0, low_limit=low_limit, high_limit=1
            )
        ],
    )


def test_value_label_uses_low_limit_offset(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _build_string_list_table(low_limit=1))
    # low_limit=1, wire=0 → CommonNames[1] = "VTwo"
    assert ctrl.value_label(99, 0) == "VTwo"


def test_value_label_wire_plus_low_limit(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _build_string_list_table(low_limit=0))
    # low_limit=0, wire=1 → CommonNames[1] = "VTwo"
    assert ctrl.value_label(99, 1) == "VTwo"


def test_value_label_out_of_range_returns_str_of_wire(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _build_string_list_table(low_limit=1))
    # idx = 1 + 99 = 100 > len(["VOne", "VTwo"]) → falls back to str(99)
    assert ctrl.value_label(99, 99) == "99"


def test_resolve_raws_string_list_uses_low_limit(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _build_string_list_table(low_limit=1))
    # wire byte 0x00, low_limit=1 → idx=1 → "VTwo"
    result = ctrl._resolve_raws({99: b"\x00"}, ctrl._values_by_number)
    assert result[99] == "VTwo"


def test_resolve_raws_text_type_decoded_ascii(mocker) -> None:
    table_data = build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[10],
        records=[value_record(data_type=DataType.SHORT_STRING, data_index=0)],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)
    raw = b"hello" + b"\x00" * 11  # 16 bytes total
    result = ctrl._resolve_raws({10: raw}, ctrl._values_by_number)
    assert result[10] == "hello"


def test_resolve_raws_numeric_passthrough(mocker) -> None:
    table_data = build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[10],
        records=[value_record(data_type=DataType.UNSIGNED16, data_index=0)],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)
    result = ctrl._resolve_raws({10: 1234}, ctrl._values_by_number)
    assert result[10] == 1234


def test_resolve_raws_setpoint_string_list_uses_low_limit(mocker) -> None:
    table_data = build_table(
        category_counts=(0, 0, 0, 0),
        numbers=[],
        records=[],
        setpoint_category_counts=(1, 0),
        setpoint_numbers=[500],
        setpoint_records=[
            setpoint_record(data_type=DataType.STRING_LIST, data_index=0, low_limit=1, high_limit=1)
        ],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)
    # wire byte 0x00, low_limit=1 → idx=1 → "VTwo"
    result = ctrl._resolve_raws({500: b"\x00"}, ctrl._setpoints_by_number)
    assert result[500] == "VTwo"


# ---------------------------------------------------------------------------
# one_time_values / _cache_one_time_values
# ---------------------------------------------------------------------------


def _one_time_table() -> bytes:
    return build_table(
        category_counts=(0, 0, 0, 1),
        numbers=[99],
        records=[value_record(data_type=DataType.UNSIGNED8, data_index=0)],
    )


def test_one_time_values_is_read_only(mocker) -> None:
    from types import MappingProxyType

    ctrl = _make_ctrl_with_table(mocker, _one_time_table())
    ctrl._one_time_values = {99: 42}

    assert isinstance(ctrl.one_time_values, MappingProxyType)


def test_one_time_values_empty_before_cache(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _one_time_table())
    assert dict(ctrl.one_time_values) == {}


async def test_cache_one_time_values_populates_property(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _one_time_table())
    ctrl._client = mocker.AsyncMock()
    ctrl._client.read_object.return_value = bytes([42])

    await ctrl._cache_one_time_values()

    assert ctrl.one_time_values[99] == 42


async def test_cache_one_time_values_skips_failed_reads(mocker) -> None:
    table_data = build_table(
        category_counts=(0, 0, 0, 2),
        numbers=[10, 20],
        records=[
            value_record(data_type=DataType.UNSIGNED8, data_index=0),
            value_record(data_type=DataType.UNSIGNED8, data_index=0),
        ],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)
    ctrl._client = mocker.AsyncMock()
    ctrl._client.read_object.side_effect = [Exception("timeout"), bytes([7])]

    await ctrl._cache_one_time_values()

    assert 10 not in ctrl.one_time_values
    assert ctrl.one_time_values[20] == 7


async def test_read_value_raises_for_one_time(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _one_time_table())

    with pytest.raises(ComApProtocolError, match="ONE_TIME"):
        await ctrl.read_value(99)


def test_one_time_value_returns_cached(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _one_time_table())
    ctrl._one_time_values = {99: 42}

    assert ctrl.one_time_value(99) == 42


def test_one_time_value_raises_if_not_in_cache(mocker) -> None:
    ctrl = _make_ctrl_with_table(mocker, _one_time_table())
    # cache is empty (default)

    with pytest.raises(ComApProtocolError, match="not in cache"):
        ctrl.one_time_value(99)


def test_one_time_value_raises_for_non_one_time(mocker) -> None:
    table_data = build_table(
        category_counts=(1, 0, 0, 0),
        numbers=[10],
        records=[value_record(data_type=DataType.UNSIGNED8, data_index=0)],
    )
    ctrl = _make_ctrl_with_table(mocker, table_data)

    with pytest.raises(ComApProtocolError, match="not ONE_TIME"):
        ctrl.one_time_value(10)


# -- include_invisible filter ------------------------------------------------


def _make_one_time_descs(mocker) -> tuple:
    from pycomap.configuration import ValueCategory, ValueDescription

    visible = ValueDescription(
        number=10,
        category=ValueCategory.ONE_TIME,
        data_type=DataType.UNSIGNED8,
        data_length=1,
        decimal_places=0,
        data_index=0,
        state_index=None,
        name="FW Version",
        dimension="",
        group=None,
        low_limit=0,
        high_limit=255,
        var_low_limit=False,
        var_high_limit=False,
        bit_name_index=None,
    )
    invisible = ValueDescription(
        number=20,
        category=ValueCategory.ONE_TIME,
        data_type=DataType.UNSIGNED8,
        data_length=1,
        decimal_places=0,
        data_index=0,
        state_index=None,
        name="Application",
        dimension="",
        group="Invisible",
        low_limit=0,
        high_limit=255,
        var_low_limit=False,
        var_high_limit=False,
        bit_name_index=None,
    )
    return visible, invisible


def _make_ctrl_with_one_time_descs(mocker, *, include_invisible: bool):  # type: ignore[return]
    from unittest.mock import AsyncMock

    visible, invisible = _make_one_time_descs(mocker)
    ctrl = Controller.__new__(Controller)
    ctrl._include_invisible = include_invisible
    ctrl._one_time_values = {}
    ctrl._common_names = []
    ctrl._values_by_number = {10: visible, 20: invisible}
    mock_client = AsyncMock()
    mock_client.read_object.return_value = bytes([42])
    ctrl._client = mock_client
    table_mock = mocker.Mock()
    table_mock.values = [visible, invisible]
    ctrl._table = table_mock
    return ctrl, mock_client


async def test_cache_one_time_values_skips_invisible_by_default(mocker) -> None:
    ctrl, mock_client = _make_ctrl_with_one_time_descs(mocker, include_invisible=False)

    await ctrl._cache_one_time_values()

    assert 10 in ctrl.one_time_values
    assert 20 not in ctrl.one_time_values
    mock_client.read_object.assert_called_once_with(10)


async def test_cache_one_time_values_includes_invisible_when_requested(mocker) -> None:
    ctrl, mock_client = _make_ctrl_with_one_time_descs(mocker, include_invisible=True)

    await ctrl._cache_one_time_values()

    assert 10 in ctrl.one_time_values
    assert 20 in ctrl.one_time_values
    assert mock_client.read_object.call_count == 2


# ---------------------------------------------------------------------------
# elevate_access
# ---------------------------------------------------------------------------


async def test_elevate_access_raises_without_password(mocker) -> None:
    from unittest.mock import AsyncMock

    ctrl = Controller.__new__(Controller)
    ctrl._elevated = False
    ctrl._password = None
    ctrl._client = AsyncMock()

    with pytest.raises(ComApAuthError):
        await ctrl.elevate_access()

    ctrl._client.elevate_access.assert_not_called()


async def test_elevate_access_sends_password(mocker) -> None:
    from unittest.mock import AsyncMock

    ctrl = Controller.__new__(Controller)
    ctrl._elevated = False
    ctrl._password = 1234
    ctrl._client = AsyncMock()

    await ctrl.elevate_access()

    ctrl._client.elevate_access.assert_called_once_with(1234)
    assert ctrl._elevated is True


async def test_elevate_access_is_idempotent(mocker) -> None:
    from unittest.mock import AsyncMock

    ctrl = Controller.__new__(Controller)
    ctrl._elevated = True
    ctrl._password = 1234
    ctrl._client = AsyncMock()

    await ctrl.elevate_access()
    await ctrl.elevate_access()

    ctrl._client.elevate_access.assert_not_called()
