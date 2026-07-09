"""End-to-end test decoding a real controller's ConfigurationTable + ValuesAll/SetpointsAll.
See tests/integration/conftest.py for the comap_host/comap_access_code fixtures this depends
on.
"""

from __future__ import annotations

from ipaddress import IPv4Address

import pytest

from pycomap.configuration import (
    ValueCategory,
    decode_setpoints_all,
    decode_states_all,
    decode_values_all,
    parse_configuration_table,
)
from pycomap.protocol import ComApClient, CommunicationObject, EthernetTransport

pytestmark = pytest.mark.integration


async def test_decode_live_values_all(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        config_data = await client.read_object(CommunicationObject.CONFIGURATION_TABLE)
        values_data = await client.read_object(CommunicationObject.VALUES_ALL)

    table = parse_configuration_table(config_data)
    assert table.values

    # Gaps between values are possible (e.g. reserved/unused space), so the data region's
    # size is the highest data_index + data_length, not the sum of all data_lengths.
    expected_length = max(
        v.data_index + v.data_length
        for v in table.values
        if v.category is not ValueCategory.ONE_TIME
    )
    assert expected_length == len(values_data)

    decoded = decode_values_all(table, values_data)
    assert len(decoded) == sum(1 for v in table.values if v.category is not ValueCategory.ONE_TIME)

    rpm = next(v for v in table.values if v.number == 10123)
    assert rpm.name == "RPM"
    assert rpm.dimension == "RPM"


async def test_decode_live_setpoints_all(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        config_data = await client.read_object(CommunicationObject.CONFIGURATION_TABLE)
        setpoints_data = await client.read_object(CommunicationObject.SETPOINTS_ALL)

    table = parse_configuration_table(config_data)
    assert table.setpoints

    expected_length = max(s.data_index + s.data_length for s in table.setpoints)
    assert expected_length == len(setpoints_data)

    decoded = decode_setpoints_all(table, setpoints_data)
    assert len(decoded) == len(table.setpoints)

    nominal_rpm = next(s for s in table.setpoints if s.number == 8253)
    assert nominal_rpm.name == "Nominal RPM"
    assert nominal_rpm.dimension == "RPM"


async def test_decode_live_states_all(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        config_data = await client.read_object(CommunicationObject.CONFIGURATION_TABLE)
        states_data = await client.read_object(CommunicationObject.VALUE_STATES_ALL)

    table = parse_configuration_table(config_data)
    states = decode_states_all(table, states_data)

    # Every returned entry must map to a value that has a state_index
    numbered = {v.number: v for v in table.values}
    for num, _state in states.items():
        assert numbered[num].state_index is not None
    # Values without state_index must not appear in the result
    no_state = {v.number for v in table.values if v.state_index is None}
    assert not (no_state & states.keys())
