"""pycomap — async Python client for ComAp controllers (InteliLite/AMF25 and others).

Quick start::

    from ipaddress import IPv4Address

    from pycomap import Command, Controller, EthernetTransport, discover

    async with ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))) as client:
        await client.authenticate("0")
        await client.elevate_access(password)
        result = await client.execute_command(Command.FAULT_RESET)

Public API surface:

- [ComApClient][pycomap.protocol.ComApClient] — low-level protocol client
- [Command][pycomap.protocol.Command] — named controller commands
- [EthernetTransport][pycomap.protocol.EthernetTransport] /
  [Transport][pycomap.protocol.transport.Transport]
- [discover][pycomap.discovery.discover] — UDP controller discovery
- [pycomap.configuration][] — `ConfigurationTable` parsing and value/setpoint decode
- [pycomap.alarms][] — alarm list parsing
- [pycomap.history][] — history record parsing
- [pycomap.datatypes][] — wire types and BCD codec

See ``docs/protocol.md`` in the project repository for the full reverse-engineering notes.
"""

from __future__ import annotations

import logging

from pycomap.controller import Controller
from pycomap.datatypes import Value
from pycomap.discovery import discover
from pycomap.exceptions import (
    ComApAuthError,
    ComApConnectionError,
    ComApControllerError,
    ComApError,
    ComApInvalidAccessCodeError,
    ComApInvalidPasswordError,
    ComApProtocolError,
)
from pycomap.protocol import ComApClient, Command, ControllerCommand, EthernetTransport

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "ComApAuthError",
    "ComApClient",
    "ComApConnectionError",
    "ComApControllerError",
    "ComApError",
    "ComApInvalidAccessCodeError",
    "ComApInvalidPasswordError",
    "ComApProtocolError",
    "Command",
    "Controller",
    "ControllerCommand",
    "EthernetTransport",
    "Value",
    "discover",
]
