"""Manual check of UDP discovery against real controllers on the LAN.

Not run in CI (needs live hardware on the LAN, and a network that actually delivers UDP
broadcast to the controller — see ``docs/protocol.md`` section 1). Usage::

    uv run python examples/discover.py
    uv run python examples/discover.py --interface 192.168.1.5/24 --timeout 5
    uv run python examples/discover.py --interface 192.168.1.5/24 --interface 10.0.0.5/24
    uv run python examples/discover.py --host 192.168.1.9
"""

from __future__ import annotations

import argparse
import asyncio
from ipaddress import IPv4Address, IPv4Interface

from pycomap.discovery import DiscoveryDevice, discover, discover_host

_GLOBAL_BROADCAST_INTERFACE = IPv4Interface("0.0.0.0/0")


def _print_device(device: DiscoveryDevice) -> None:
    print(f"ip={device.ip} mac={device.mac} comm_port={device.comm_port}")
    for unit in device.units:
        print(f"  unit: name={unit.name!r} serial={unit.serial}")


async def main(timeout: float, host: IPv4Address | None, interfaces: list[IPv4Interface]) -> None:
    if host is not None:
        device = await discover_host(host, timeout=timeout)
        if device is None:
            print(f"{host} did not reply")
            return
        _print_device(device)
        return

    devices = await discover(*interfaces, timeout=timeout)
    if not devices:
        print("no controllers replied")
        return
    for device in devices:
        _print_device(device)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--host", type=IPv4Address, help="Probe a known controller IP directly")
    parser.add_argument(
        "--interface",
        dest="interfaces",
        type=IPv4Interface,
        action="append",
        help="Local interface to broadcast from, e.g. 192.168.1.5/24 (repeatable). "
        "Defaults to a wildcard bind + the global broadcast address, which only reliably "
        "reaches the controller on single-NIC hosts.",
    )
    args = parser.parse_args()
    asyncio.run(main(args.timeout, args.host, args.interfaces or [_GLOBAL_BROADCAST_INTERFACE]))
