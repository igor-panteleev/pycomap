"""Integration tests for controller clock read/write.

Requires PYCOMAP_TEST_PASSWORD in .env — skipped otherwise.
Summer Time Mode and Time Zone setpoints are read-only verified (not changed by these
tests); only the clock is written.
"""

from __future__ import annotations

import datetime

import pytest

from pycomap.protocol import ComApClient, EthernetTransport

pytestmark = pytest.mark.integration


async def test_read_datetime(comap_host: str, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        dt = await client.read_datetime()

    assert dt is not None
    assert dt.year >= 2020


async def test_sync_datetime(comap_host: str, comap_access_code: str, comap_password: int) -> None:
    now = datetime.datetime.now().replace(microsecond=0)

    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        await client.elevate_access(comap_password)
        await client.write_datetime(now)
        result = await client.read_datetime()

    assert result is not None
    drift = abs((result - now).total_seconds())
    assert drift <= 2, f"clock drift after sync: {drift}s (expected ≤ 2s)"
