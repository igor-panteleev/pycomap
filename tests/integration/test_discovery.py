"""End-to-end UDP discovery test against a real controller on the LAN. See
tests/integration/conftest.py for the PYCOMAP_TEST_HOST fixture this depends on.
"""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Interface

import pytest

from pycomap.discovery import discover, discover_host

pytestmark = pytest.mark.integration


async def test_discover_finds_controller(
    comap_host: IPv4Address, comap_interface: IPv4Interface
) -> None:
    devices = await discover(comap_interface, timeout=3.0)
    assert any(device.ip == comap_host for device in devices)


async def test_discover_host_finds_controller(comap_host: IPv4Address) -> None:
    device = await discover_host(comap_host, timeout=3.0)
    assert device is not None
    assert device.ip == comap_host
