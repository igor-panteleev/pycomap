"""Read a setpoint, write a new value, verify, then restore the original.

Demonstrates password elevation for write-protected setpoints.

Usage::

    uv run python examples/write_setpoint.py 192.168.1.9 0 <password> "Emergency Start Delay" 5
"""

from __future__ import annotations

import argparse
import asyncio
from ipaddress import IPv4Address

from pycomap import Controller, EthernetTransport
from pycomap.protocol import ComApClient


async def main(
    host: IPv4Address, access_code: str, password: int, setpoint_name: str, new_value: float
) -> None:
    async with Controller(
        ComApClient(EthernetTransport(host)), access_code=access_code, password=password
    ) as ctrl:
        desc = ctrl.setpoint_info(setpoint_name)
        print(f"Setpoint : {desc.name!r}  (#{desc.number})")
        print(f"Type     : {desc.data_type.name}  dp={desc.decimal_places}")
        print(
            f"Range    : {desc.low_limit} .. {desc.high_limit}"
            + ("  [password required]" if desc.needs_password else "")
        )

        original = await ctrl.read_setpoint(setpoint_name)
        print(f"Current  : {original}")

        print(f"Writing  : {new_value} ...")
        await ctrl.set_setpoint(setpoint_name, new_value)

        readback = await ctrl.read_setpoint(setpoint_name)
        print(f"Readback : {readback}")

        print(f"Restoring: {original} ...")
        await ctrl.set_setpoint(setpoint_name, original)
        print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read/write/restore a named setpoint.")
    parser.add_argument("host", type=IPv4Address)
    parser.add_argument("access_code")
    parser.add_argument("password", type=int)
    parser.add_argument("setpoint_name")
    parser.add_argument("new_value", type=float)
    args = parser.parse_args()
    asyncio.run(
        main(args.host, args.access_code, args.password, args.setpoint_name, args.new_value)
    )
