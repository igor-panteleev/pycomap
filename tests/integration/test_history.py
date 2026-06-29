"""Integration tests for history record reading against a real controller."""

from __future__ import annotations

import pytest

from pycomap import Controller
from pycomap.history import parse_history_record
from pycomap.protocol import ComApClient, CommunicationObject, EthernetTransport

pytestmark = pytest.mark.integration


async def test_read_history_records(comap_host: str, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        config_data = await client.read_object(CommunicationObject.CONFIGURATION_TABLE)

        raw = await client.read_object(CommunicationObject.YOUNGEST_HISTORY_RECORD)
        records = []
        rec = parse_history_record(config_data, raw)
        if rec:
            records.append(rec)

        for _ in range(9):
            raw = await client.read_object(CommunicationObject.OLDER_HISTORY_RECORD)
            rec = parse_history_record(config_data, raw)
            if rec:
                records.append(rec)

    assert records, "expected at least one history record"

    for rec in records:
        assert (rec.timestamp is None) != (rec.engine_hours is None)
        if rec.timestamp is not None:
            assert rec.timestamp.year >= 2020
        if rec.is_text:
            assert rec.text
        else:
            assert rec.reason or rec.data


async def test_controller_read_history(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        records = await ctrl.read_history(count=10)

    assert records, "expected at least one history record"

    for rec in records:
        assert (rec.timestamp is None) != (rec.engine_hours is None)
        if rec.timestamp is not None:
            assert rec.timestamp.year >= 2020
        # prefix is always resolved — '-' for info events, named prefix for alarms
        if not rec.is_text:
            assert isinstance(rec.prefix, str)


async def test_controller_history_indices_descending(
    comap_host: str, comap_access_code: str
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        records = await ctrl.read_history(count=5)

    # read_history returns newest-first; indices should be strictly decreasing
    indices = [r.index for r in records]
    assert indices == sorted(indices, reverse=True)


async def test_controller_decode_history_snapshot(comap_host: str, comap_access_code: str) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        records = await ctrl.read_history(count=200)
        alarm_records = [r for r in records if not r.is_text and r.data]
        assert alarm_records, "expected at least one alarm record with snapshot data"

        rec = alarm_records[0]
        snapshot = ctrl.decode_history_snapshot(rec)

    assert snapshot, "snapshot should contain decoded values"
    # All decoded values must be of a supported type
    for number, val in snapshot.items():
        assert isinstance(val, (int, float, bytes, str)), f"unexpected type for value {number}"
    # Binary Inputs (#8235) should always be present — it has data_index=0
    assert any(v is not None for v in snapshot.values())


async def test_decode_history_snapshot_empty_for_text_record(
    comap_host: str, comap_access_code: str
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(comap_host)), access_code=comap_access_code
    ) as ctrl:
        records = await ctrl.read_history(count=50)
        text_records = [r for r in records if r.is_text]
        assert text_records, "expected at least one text record"

        snapshot = ctrl.decode_history_snapshot(text_records[0])

    assert snapshot == {}
