"""UDP discovery of ComAp controllers on the local network.

See ``docs/protocol.md`` section 1. InteliConfig broadcasts a probe to
``<broadcast>:2413``; controllers reply unicast from port 2413. Despite living on its own
UDP port, the probe and reply are not a bespoke discovery-only format — they're a regular
[pycomap.protocol.framing.Message][] (the exact same CRC16-validated `EthernetMessage`
framing used by the TCP protocol on port 23): a ``SendMe`` for the ``Discovery``
communication object, replied to with a ``SendTo`` carrying a binary ``DiscoveryDevice``
payload (IP, MAC, TCP port, firmware version, and the list of units behind the gateway).

The controller validates the CRC on this probe just like any other message, so a
malformed/random payload of the right length is silently ignored — it must be built via
[pycomap.protocol.framing.build_inner][], not improvised.
"""

from __future__ import annotations

import asyncio
import enum
import logging
import socket
import struct
from dataclasses import dataclass, field

from pycomap.exceptions import ComApProtocolError
from pycomap.protocol.framing import Operation, build_inner, parse_inner
from pycomap.protocol.objects import CommunicationObject

DISCOVERY_PORT = 2413

_log = logging.getLogger(__name__)

_HEADER_SIZE_V0 = 42
_HEADER_SIZE_V1 = 44
_UNIT_RECORD_SIZE = 21


class DeviceType(enum.IntEnum):
    """ComAp ``DiscoveryDevice.DeviceType`` enum."""

    IB_NT = 0
    IB_COM = 1
    IB_LITE = 2
    CM_ETHERNET = 4
    IG500_BUILT_IN_ETHERNET = 5


class AccessType(enum.IntFlag):
    """ComAp ``DiscoveryDevice.AccessType`` flags."""

    IP_ADDRESS = 1
    AIR_GATE = 2


@dataclass(slots=True, frozen=True)
class DiscoveryUnit:
    """A controller unit reachable through the replying gateway device."""

    type: int
    name: str
    serial: str


@dataclass(slots=True, frozen=True)
class DiscoveryDevice:
    """A controller's decoded reply to a discovery probe."""

    format_version: int
    device_type: DeviceType
    serial_number: int
    firmware_major_minor: int
    firmware_patch_build: int
    ip: str
    mac: str
    comm_port: int
    access_type: AccessType
    airgate_identifier: str
    connected_units: int
    is_units_list_complete: bool
    units: list[DiscoveryUnit] = field(default_factory=list)


def _build_probe() -> bytes:
    """Build the discovery probe: a ``SendMe`` ``EthernetMessage`` for ``Discovery``."""
    return build_inner(
        Operation.SEND_ME, addr=1, comm_obj=CommunicationObject.DISCOVERY, data=b"", ident=0
    )


def _parse_device(data: bytes) -> DiscoveryDevice:
    """Parse a ``DiscoveryDevice`` payload (the ``Message.data`` of a ``Discovery`` reply)."""
    format_version = data[0]
    device_type = DeviceType(data[1])
    serial_number = struct.unpack_from("<I", data, 2)[0]

    header_size = _HEADER_SIZE_V0 if format_version == 0 else _HEADER_SIZE_V1
    offset = 6
    firmware_major_minor = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    if format_version >= 1:
        firmware_patch_build = struct.unpack_from("<H", data, offset)[0]
        offset += 2
    else:
        firmware_patch_build = 0

    ip = ".".join(str(b) for b in data[offset : offset + 4])
    offset += 4
    mac = ":".join(f"{b:02x}" for b in data[offset : offset + 6])
    offset += 6
    comm_port = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    access_type = AccessType(data[offset])
    offset += 1
    airgate_identifier = data[offset : offset + 16].split(b"\x00", 1)[0].decode("ascii", "replace")
    offset += 16
    connected_units = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    is_units_list_complete = bool(data[offset])
    offset += 1

    assert offset == header_size
    units = [
        DiscoveryUnit(
            type=data[i],
            name=data[i + 1 : i + 17].split(b"\x00", 1)[0].decode("ascii", "replace"),
            serial=data[i + 17 : i + 21].hex(),
        )
        for i in range(header_size, len(data), _UNIT_RECORD_SIZE)
    ]

    return DiscoveryDevice(
        format_version=format_version,
        device_type=device_type,
        serial_number=serial_number,
        firmware_major_minor=firmware_major_minor,
        firmware_patch_build=firmware_patch_build,
        ip=ip,
        mac=mac,
        comm_port=comm_port,
        access_type=access_type,
        airgate_identifier=airgate_identifier,
        connected_units=connected_units,
        is_units_list_complete=is_units_list_complete,
        units=units,
    )


async def discover(
    timeout: float = 2.0,
    broadcast_address: str = "255.255.255.255",
) -> list[DiscoveryDevice]:
    """Broadcast a discovery probe and collect replies for ``timeout`` seconds.

    Returns one [DiscoveryDevice][pycomap.discovery.DiscoveryDevice] per distinct
    replying IP address. Malformed or unrelated UDP traffic on the same port
    (CRC mismatch, wrong communication object) is
    silently skipped.
    """
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(False)

    found: dict[str, DiscoveryDevice] = {}
    try:
        sock.bind(("", 0))
        _log.debug("sending discovery probe to %s:%d", broadcast_address, DISCOVERY_PORT)
        sock.sendto(_build_probe(), (broadcast_address, DISCOVERY_PORT))

        end_time = loop.time() + timeout
        while True:
            remaining = end_time - loop.time()
            if remaining <= 0:
                break
            try:
                payload, _peer_addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 4096), timeout=remaining
                )
            except TimeoutError:
                break
            try:
                message = parse_inner(payload)
            except ComApProtocolError:
                continue
            if message.comm_obj != CommunicationObject.DISCOVERY:
                continue
            if message.is_error or not message.data:
                continue
            device = _parse_device(message.data)
            found[device.ip] = device
    finally:
        sock.close()

    _log.info("discovery found %d device(s)", len(found))
    return list(found.values())
