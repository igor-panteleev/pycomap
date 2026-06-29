"""Transport layer abstraction for the ComAp native protocol.

``Transport`` is a structural ``typing.Protocol`` — any object with the four async
methods qualifies, no subclassing required. ``EthernetTransport`` is the only
implementation for now; AirGate (cloud relay) and serial transports can be added later
without changing ``ComApClient``.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from ipaddress import IPv4Address
from typing import Protocol, runtime_checkable

from pycomap.exceptions import ComApConnectionError

DEFAULT_PORT = 23

_log = logging.getLogger(__name__)


@runtime_checkable
class Transport(Protocol):
    """Byte-stream transport used by ``ComApClient``."""

    async def connect(self) -> None:
        """Open the underlying connection."""
        ...

    async def close(self) -> None:
        """Close the underlying connection, suppressing already-closed errors."""
        ...

    async def read_exactly(self, n: int) -> bytes:
        """Read exactly ``n`` bytes, raising ``ComApConnectionError`` if the stream ends."""
        ...

    async def write(self, data: bytes) -> None:
        """Write ``data`` and flush."""
        ...


class EthernetTransport:
    """TCP transport for the ComAp native protocol (port 23).

    Connects to ``host:port`` via plain TCP; the ``ComApClient`` layer adds the
    ECDH/AES framing on top.
    """

    def __init__(self, host: IPv4Address | str, port: int = DEFAULT_PORT) -> None:
        """
        Args:
            host: Controller IP address (``IPv4Address`` or dotted string) or hostname.
            port: TCP port; defaults to ``23`` (ComAp native protocol port).
        """
        self._host = str(host)
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        _log.debug("connecting to %s:%d", self._host, self._port)
        try:
            self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        except OSError as exc:
            raise ComApConnectionError(f"failed to connect to {self._host}:{self._port}") from exc
        _log.info("connected to %s:%d", self._host, self._port)

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            with contextlib.suppress(OSError):
                await self._writer.wait_closed()
            _log.info("disconnected from %s:%d", self._host, self._port)
        self._reader = None
        self._writer = None

    async def read_exactly(self, n: int) -> bytes:
        assert self._reader is not None
        try:
            return await self._reader.readexactly(n)
        except asyncio.IncompleteReadError as exc:
            raise ComApConnectionError("connection closed while reading a message") from exc

    async def write(self, data: bytes) -> None:
        assert self._writer is not None
        self._writer.write(data)
        await self._writer.drain()
