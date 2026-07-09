"""Transport layer abstraction for the ComAp native protocol.

``Transport`` is an ``abc.ABC`` — implementations must subclass it and provide the four
async methods. ``EthernetTransport`` is the only implementation for now; AirGate (cloud
relay) and serial transports can be added later without changing ``ComApClient``.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from abc import ABC, abstractmethod
from ipaddress import IPv4Address

from pycomap.exceptions import ComApConnectionError

DEFAULT_PORT = 23

_log = logging.getLogger(__name__)


class Transport(ABC):
    """Byte-stream transport used by ``ComApClient``."""

    @abstractmethod
    async def connect(self) -> None:
        """Open the underlying connection."""

    @abstractmethod
    async def close(self) -> None:
        """Close the underlying connection, suppressing already-closed errors."""

    @abstractmethod
    async def read_exactly(self, n: int) -> bytes:
        """Read exactly ``n`` bytes, raising ``ComApConnectionError`` if the stream ends."""

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """Write ``data`` and flush."""


class EthernetTransport(Transport):
    """TCP transport for the ComAp native protocol (port 23).

    Connects to ``host:port`` via plain TCP; the ``ComApClient`` layer adds the
    ECDH/AES framing on top.
    """

    def __init__(self, host: IPv4Address, port: int = DEFAULT_PORT) -> None:
        """
        Args:
            host: Controller IP address. Exposed back via
                [host][pycomap.protocol.EthernetTransport.host] for e.g. probing reachability
                via [discover_host][pycomap.discovery.discover_host].
            port: TCP port; defaults to ``23`` (ComAp native protocol port).
        """
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    @property
    def host(self) -> IPv4Address:
        """The controller's configured IP address."""
        return self._host

    @property
    def port(self) -> int:
        """The controller's configured TCP port."""
        return self._port

    async def connect(self) -> None:
        _log.debug("connecting to %s:%d", self._host, self._port)
        try:
            self._reader, self._writer = await asyncio.open_connection(str(self._host), self._port)
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
        if self._reader is None:
            raise ComApConnectionError("not connected — call connect() first")
        try:
            return await self._reader.readexactly(n)
        except asyncio.IncompleteReadError as exc:
            raise ComApConnectionError("connection closed while reading a message") from exc

    async def write(self, data: bytes) -> None:
        if self._writer is None:
            raise ComApConnectionError("not connected — call connect() first")
        self._writer.write(data)
        await self._writer.drain()
