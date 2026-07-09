"""UDP discovery of ComAp controllers on the local network.

See ``docs/protocol.md`` section 1. InteliConfig broadcasts a probe to
``<subnet-broadcast>:2413`` (e.g. ``192.168.1.255``, never the global ``255.255.255.255``);
controllers reply unicast from port 2413. Despite living on its own
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
import struct
from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Interface

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
    ip: IPv4Address
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

    ip = IPv4Address(bytes(data[offset : offset + 4]))
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

    if offset != header_size:
        raise ComApProtocolError(
            f"discovery device header parse offset mismatch: got {offset}, expected {header_size}"
        )
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


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    """Collects decoded ``Discovery`` replies, keyed by replying IP address."""

    def __init__(self, found: dict[IPv4Address, DiscoveryDevice]) -> None:
        self._found = found

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = parse_inner(data)
        except ComApProtocolError:
            return
        if message.comm_obj != CommunicationObject.DISCOVERY:
            return
        if message.is_error or not message.data:
            return
        device = _parse_device(message.data)
        self._found[device.ip] = device


async def _send_probe(
    loop: asyncio.AbstractEventLoop,
    local_ip: IPv4Address,
    destination: IPv4Address,
    found: dict[IPv4Address, DiscoveryDevice],
    *,
    allow_broadcast: bool = False,
) -> asyncio.DatagramTransport:
    """Bind a socket to ``local_ip`` and send a discovery probe to ``destination``.

    Replies land in ``found`` (keyed by replying IP) as they arrive; the caller is responsible
    for waiting out the collection window and closing the returned transport.
    """
    transport, _protocol = await loop.create_datagram_endpoint(
        lambda: _DiscoveryProtocol(found),
        local_addr=(str(local_ip), 0),
        allow_broadcast=allow_broadcast,
    )
    _log.debug("sending discovery probe from %s to %s:%d", local_ip, destination, DISCOVERY_PORT)
    transport.sendto(_build_probe(), (str(destination), DISCOVERY_PORT))
    return transport


async def discover(
    *interfaces: IPv4Interface,
    timeout: float = 2.0,
) -> list[DiscoveryDevice]:
    """Broadcast a discovery probe from each of ``interfaces`` and collect replies for
    ``timeout`` seconds.

    On a host with multiple NICs on different subnets, a probe sent to the global broadcast
    address `255.255.255.255` only egresses via whichever interface the OS routes it through,
    so it may never reach the controller's actual subnet — pass one `IPv4Interface` per local
    interface you want to probe from (e.g. `IPv4Interface("192.168.1.5/24")`, your own address
    on that subnet) to bind and broadcast on each of them; this module doesn't enumerate
    network interfaces itself. Pass `IPv4Interface("0.0.0.0/0")` to fall back to the wildcard
    bind + global broadcast address on a single-NIC host.

    Returns one [DiscoveryDevice][pycomap.discovery.DiscoveryDevice] per distinct
    replying IP address. Malformed or unrelated UDP traffic on the same port
    (CRC mismatch, wrong communication object) is
    silently skipped.
    """
    loop = asyncio.get_running_loop()
    found: dict[IPv4Address, DiscoveryDevice] = {}
    transports = await asyncio.gather(
        *(
            _send_probe(
                loop, interface.ip, interface.network.broadcast_address, found, allow_broadcast=True
            )
            for interface in interfaces
        )
    )
    try:
        await asyncio.sleep(timeout)
    finally:
        for transport in transports:
            transport.close()

    _log.info("discovery found %d device(s)", len(found))
    return list(found.values())


async def discover_host(ip: IPv4Address, timeout: float = 2.0) -> DiscoveryDevice | None:
    """Send a discovery probe directly (unicast) to a known ``ip`` and wait up to ``timeout``
    seconds for its reply.

    Useful when the controller's address is already known, so there's no need to broadcast
    and no ambiguity about which local interface/subnet to use.

    Returns `None` if ``ip`` doesn't reply within ``timeout``.
    """
    loop = asyncio.get_running_loop()
    found: dict[IPv4Address, DiscoveryDevice] = {}
    transport = await _send_probe(loop, IPv4Address("0.0.0.0"), ip, found)
    try:
        await asyncio.sleep(timeout)
    finally:
        transport.close()

    return found.get(ip)
