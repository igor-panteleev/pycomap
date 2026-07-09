"""End-to-end tests for command execution against a real controller. See
tests/integration/conftest.py for the comap_host/comap_access_code fixtures this depends on.

SAFETY: only FAULT_RESET and HORN_RESET are tested here — both are idempotent (safe to
send when there is nothing to reset) and don't affect engine or breaker state. ENGINE_START/
STOP and GCB/MCB commands are intentionally excluded: they depend on controller mode and
can have real mechanical consequences.

Observed on a live InteliLite/AMF25 in AUTO mode: ENGINE_START returns the expected success
code (0x000001FF) but the engine does NOT start because the controller's own mode logic
(not in MAN) gates the mechanical action — command.succeeded(result) means the *protocol*
acknowledged it, not that the action was executed. GCB_ON/OFF return RESULT_REFUSED (0x02)
because the generator is offline.
"""

from __future__ import annotations

from ipaddress import IPv4Address

import pytest

from pycomap.protocol import ComApClient, EthernetTransport
from pycomap.protocol.commands import Command

pytestmark = pytest.mark.integration


async def test_fault_reset(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        result = await client.execute_command(Command.FAULT_RESET)
    assert Command.FAULT_RESET.succeeded(result)


async def test_horn_reset(comap_host: IPv4Address, comap_access_code: str) -> None:
    async with ComApClient(EthernetTransport(comap_host)) as client:
        await client.authenticate(comap_access_code)
        result = await client.execute_command(Command.HORN_RESET)
    assert Command.HORN_RESET.succeeded(result)
