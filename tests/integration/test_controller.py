"""Integration tests for the high-level Controller class."""

from __future__ import annotations

import datetime

import pytest
import pytz

from pycomap import Controller
from pycomap.protocol import ComApClient
from pycomap.protocol.transport import EthernetTransport

pytestmark = pytest.mark.integration


async def test_controller_connects_and_reads_values(
    comap_host: str, comap_access_code: str
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        assert len(ctrl.table.values) > 0
        assert len(ctrl.table.setpoints) > 0

        values = await ctrl.read_values()
        assert values

        rpm_info = ctrl.value_info("RPM")
        assert rpm_info.number in values


async def test_controller_value_bit_names(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        binary_values = [v for v in ctrl.values if v.bit_name_index is not None]
        assert binary_values, "expected at least one BINARY* value with bit labels"

        desc = binary_values[0]
        bit_names = ctrl.value_bit_names(desc.number)

    assert isinstance(bit_names, list)
    assert all(isinstance(bit, int) and isinstance(label, str) for bit, label in bit_names)
    # bit indices must be unique and in ascending order
    indices = [bit for bit, _ in bit_names]
    assert indices == sorted(set(indices))


async def test_controller_named_setpoint_read(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        nom_rpm = await ctrl.read_setpoint("Nominal RPM")
        assert isinstance(nom_rpm, (int, float))
        assert nom_rpm > 0


async def test_controller_read_setpoints_bulk(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        bulk = await ctrl.read_setpoints()
        assert len(bulk) == len(ctrl.setpoints)

        # cross-check one value against individual read
        desc = ctrl.setpoint_info("Nominal RPM")
        individual = await ctrl.read_setpoint("Nominal RPM")
        assert bulk[desc.number] == individual


async def test_controller_set_setpoint(
    comap_host: str, comap_access_code: str, comap_password: int
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)),
        access_code=comap_access_code,
        password=comap_password,
    ) as ctrl:
        original = await ctrl.read_setpoint("Emergency Start Delay")
        new_val = int(original) + 1
        await ctrl.set_setpoint("Emergency Start Delay", new_val)
        assert await ctrl.read_setpoint("Emergency Start Delay") == new_val
        await ctrl.set_setpoint("Emergency Start Delay", int(original))


async def test_controller_timezone_from_setpoint(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        tz = ctrl.timezone
        mode = ctrl.summer_time_mode

    # timezone must be a valid fixed-offset timezone
    assert isinstance(tz, datetime.timezone)
    # summer_time_mode must be one of the known values
    assert mode in (0, 2, 4)


async def test_controller_read_aware_datetime(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        aware = await ctrl.read_aware_datetime()
        naive = await ctrl.read_datetime()
        tz = ctrl.timezone

    assert aware is not None
    assert naive is not None
    assert aware.tzinfo == tz
    assert aware.replace(tzinfo=None) == naive


async def test_controller_sync_time_uses_controller_tz(
    comap_host: str, comap_access_code: str, comap_password: int
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)),
        access_code=comap_access_code,
        password=comap_password,
    ) as ctrl:
        await ctrl.sync_time()  # uses controller's own Time Zone setpoint
        result = await ctrl.read_aware_datetime()
        tz = ctrl.timezone

    assert result is not None
    expected = datetime.datetime.now(datetime.UTC).astimezone(tz)
    assert abs((result - expected).total_seconds()) <= 5


async def test_controller_one_time_values_populated_on_connect(
    comap_host: str, comap_access_code: str
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        ot = ctrl.one_time_values

    from types import MappingProxyType

    assert ot, "expected at least one ONE_TIME value to be cached"
    assert all(isinstance(v, (int, float, bytes, str)) for v in ot.values())
    assert isinstance(ot, MappingProxyType)


async def test_controller_one_time_values_contains_strings(
    comap_host: str, comap_access_code: str
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        ot = ctrl.one_time_values

    string_values = {k: v for k, v in ot.items() if isinstance(v, str)}
    assert string_values, "expected at least one string-typed ONE_TIME value (e.g. FW Version)"
    assert all(v for v in string_values.values())  # all non-empty


async def test_controller_sync_time_with_pytz_override(
    comap_host: str, comap_access_code: str, comap_password: int
) -> None:
    tz = pytz.timezone("Europe/Kiev")
    async with Controller(
        ComApClient(EthernetTransport(comap_host)),
        access_code=comap_access_code,
        password=comap_password,
    ) as ctrl:
        await ctrl.sync_time(tz=tz)
        result = await ctrl.read_datetime()

    assert result is not None
    expected = datetime.datetime.now(datetime.UTC).astimezone(tz).replace(tzinfo=None)
    assert abs((result - expected).total_seconds()) <= 5
