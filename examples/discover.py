"""Manual check of UDP discovery against real controllers on the LAN.

Not run in CI (needs live hardware on the LAN, and a network that actually delivers UDP
broadcast to the controller — see ``docs/protocol.md`` section 1). Usage::

    uv run python examples/discover.py
    uv run python examples/discover.py --broadcast-address 192.168.1.255 --timeout 5
"""

from __future__ import annotations

import argparse
import asyncio

from pycomap.discovery import discover


async def main(timeout: float, broadcast_address: str) -> None:
    devices = await discover(timeout=timeout, broadcast_address=broadcast_address)
    if not devices:
        print("no controllers replied")
        return
    for device in devices:
        print(f"ip={device.ip} mac={device.mac} comm_port={device.comm_port}")
        for unit in device.units:
            print(f"  unit: name={unit.name!r} serial={unit.serial}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--broadcast-address", default="255.255.255.255")
    args = parser.parse_args()
    asyncio.run(main(args.timeout, args.broadcast_address))
