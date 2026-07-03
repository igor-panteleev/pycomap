"""End-to-end tests against a real controller. See tests/integration/conftest.py for the
PYCOMAP_TEST_HOST / PYCOMAP_TEST_ACCESS_CODE fixtures these depend on.
"""

from __future__ import annotations

from ipaddress import IPv4Address

import pytest

from pycomap.protocol import ComApClient, CommunicationObject, EthernetTransport

pytestmark = pytest.mark.integration


async def test_connect_and_authenticate(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)


async def test_read_max_message_data_lengths(
    comap_host: IPv4Address, comap_access_code: str
) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        data = await client.read_object(CommunicationObject.MAX_MESSAGE_DATA_LENGTHS)
        assert len(data) == 7


async def test_read_values_all(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        data = await client.read_object(CommunicationObject.VALUES_ALL)
        assert len(data) > 0
