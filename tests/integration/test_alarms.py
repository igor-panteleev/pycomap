"""Integration tests for alarm list parsing against a real controller."""

from __future__ import annotations

import pytest

from pycomap.alarms import parse_alarm_list
from pycomap.configuration import NamesCategory, parse_names_heap
from pycomap.protocol import ComApClient, CommunicationObject, EthernetTransport

pytestmark = pytest.mark.integration


async def test_parse_live_alarm_list(comap_host: str, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        config_data = await client.read_object(CommunicationObject.CONFIGURATION_TABLE)
        alarm_data = await client.read_object(CommunicationObject.ALARM_LIST)

    assert len(alarm_data) == 112  # IL3 StandardUnifiedWithSource alarm list size

    reasons = parse_names_heap(config_data, NamesCategory.ALARM_REASON_NAMES)
    prefixes = parse_names_heap(config_data, NamesCategory.HISTORY_PREFIX_NAMES)
    assert len(reasons) > 0
    assert "Wrn" in prefixes
    assert "Sd" in prefixes

    records = parse_alarm_list(config_data, alarm_data)
    assert isinstance(records, list)

    for rec in records:
        assert rec.reason in reasons or rec.reason == ""
