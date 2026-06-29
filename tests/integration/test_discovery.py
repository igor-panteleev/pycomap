"""End-to-end UDP discovery test against a real controller on the LAN. See
tests/integration/conftest.py for the PYCOMAP_TEST_HOST fixture this depends on.
"""

from __future__ import annotations

import pytest

from pycomap.discovery import discover

pytestmark = pytest.mark.integration


async def test_discover_finds_controller(comap_host: str) -> None:
    devices = await discover(timeout=3.0)
    assert any(str(device.ip) == comap_host for device in devices)
