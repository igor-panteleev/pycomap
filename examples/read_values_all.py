"""Manual integration check against a real controller.

Not run in CI (needs live hardware on the LAN). Usage::

    uv run python examples/read_values_all.py 192.168.1.9 0
"""

from __future__ import annotations

import asyncio
import sys

from pycomap.protocol import ComApClient, CommunicationObject
from pycomap.protocol.transport import EthernetTransport


async def main(host: str, access_code: str) -> None:
    async with ComApClient(EthernetTransport(host)) as client:
        await client.authenticate(access_code)
        print("ACCESS VERIFIED")

        max_lengths = await client.read_object(CommunicationObject.MAX_MESSAGE_DATA_LENGTHS)
        print(f"MaxMessageDataLengths: {max_lengths.hex()}")

        values_all = await client.read_object(CommunicationObject.VALUES_ALL)
        print(f"ValuesAll: {len(values_all)} bytes")
        print(values_all.hex())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <host> <access_code>", file=sys.stderr)
        raise SystemExit(2)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
