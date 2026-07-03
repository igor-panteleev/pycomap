"""Async client for ComAp's native ``EthernetMessage`` protocol (TCP port 23).

See ``docs/protocol.md`` section 2 for the full reverse-engineering notes this implements,
and the docstrings on [pycomap.protocol.crypto][] / [pycomap.protocol.framing][] for
the trickiest details (read/write key-format asymmetry, the single shared IV chain).

Typical usage::

    from ipaddress import IPv4Address

    from pycomap.protocol.transport import EthernetTransport

    async with ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))) as client:
        await client.authenticate("0")
        values = await client.read_object(CommunicationObject.VALUES_ALL)
"""

from __future__ import annotations

import datetime
import enum
import hashlib
import logging
import struct
from types import TracebackType

from pycomap.datatypes import decode_fdate, decode_ftime, encode_fdate, encode_ftime
from pycomap.exceptions import (
    ComApControllerError,
    ComApInvalidAccessCodeError,
    ComApInvalidPasswordError,
    ComApProtocolError,
)
from pycomap.protocol import crypto
from pycomap.protocol.commands import ControllerCommand
from pycomap.protocol.crypto import ChainedAesCbc
from pycomap.protocol.framing import (
    BLOCK_SIZE,
    Message,
    Operation,
    build_inner,
    pad_to_block,
    parse_inner,
    wrap_outer,
)
from pycomap.protocol.objects import CommunicationObject, ControllerError
from pycomap.protocol.transport import Transport


class _Mode(enum.Enum):
    """Wire mode the connection has progressed through: NONE -> ALIGNED -> AES."""

    NONE = enum.auto()
    ALIGNED = enum.auto()
    AES = enum.auto()


_AUTH_FALLBACK_CODES = {
    ControllerError.TERMINAL_ACCESS_DISABLED,
    ControllerError.NON_EXISTING_COMMUNICATION_OBJECT,
}

_log = logging.getLogger(__name__)


class ComApClient:
    """Speaks the ECDH/AES-encrypted ``EthernetMessage`` protocol over any ``Transport``.

    Pass any ``Transport`` implementation — typically ``EthernetTransport``::

        from ipaddress import IPv4Address

        from pycomap.protocol.transport import EthernetTransport

        async with ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))) as client:
            await client.authenticate("0")
    """

    def __init__(self, transport: Transport) -> None:
        """
        Args:
            transport: Byte-stream transport to use (typically ``EthernetTransport``).
        """
        self._transport = transport
        self._identifier = 0
        self._mode = _Mode.NONE
        self._cipher: ChainedAesCbc | None = None

    @property
    def transport(self) -> Transport:
        """The underlying byte-stream transport."""
        return self._transport

    # -- connection lifecycle -------------------------------------------------

    async def connect(self) -> None:
        """Open the transport and consume the controller's unsolicited ``VersionIB``."""
        await self._transport.connect()

        message = await self._read_message()
        if message.comm_obj != CommunicationObject.VERSION_IB:
            raise ComApProtocolError(
                f"expected VersionIB as the first message, got comm_obj={message.comm_obj}"
            )
        version_word = struct.unpack_from("<H", message.data, 0)[0]
        if not version_word & 0x8000:
            raise ComApProtocolError(
                "controller requires the legacy Blowfish cipher, which is not supported"
            )
        _log.debug("VersionIB received (version_word=0x%04X)", version_word)
        self._mode = _Mode.ALIGNED

    async def authenticate(self, access_code: str) -> None:
        """Perform the ECDH handshake and verify ``access_code`` with the controller.

        The AES session key is derived once from ``access_code`` and cannot be changed
        without reconnecting. Pass the base/anonymous code (often ``"0"``), not a
        privileged write code. To unlock write-protected setpoints afterward, call
        [elevate_access][pycomap.protocol.ComApClient.elevate_access] —
        re-calling this method with a different code would
        corrupt the cipher state.

        Args:
            access_code: The controller's base AccessCode (drives ECDH/AES key derivation).

        Raises:
            ComApInvalidAccessCodeError: If the controller rejects the access code.
            ComApProtocolError: If the ECDH exchange produces an unexpected response.
        """
        server_pub_data = await self.read_object(CommunicationObject.ECDH_PUBLIC_KEY)
        server_pub_point = server_pub_data[4:]

        private_key = crypto.generate_keypair()
        our_pub_point = crypto.public_point_bytes(private_key)
        await self.write_object(
            CommunicationObject.ECDH_PUBLIC_KEY,
            bytes([len(our_pub_point)]) + our_pub_point,
        )

        secret = crypto.shared_secret(private_key, server_pub_point)
        aes_key, iv = crypto.derive_key_and_iv(secret, access_code)
        self._cipher = ChainedAesCbc(aes_key, iv)
        self._mode = _Mode.AES

        try:
            nonce = await self.read_object(CommunicationObject.VERIFY_ACCESS_HASH)
        except ComApControllerError as exc:
            if exc.code not in _AUTH_FALLBACK_CODES:
                raise ComApInvalidAccessCodeError("access verification failed") from exc
            _log.warning("hash auth not supported by controller, falling back to plain access code")
            source = access_code.encode("ascii").ljust(16, b"\x00")
            try:
                await self.write_object(CommunicationObject.VERIFY_ACCESS, source)
            except ComApControllerError as exc2:
                raise ComApInvalidAccessCodeError("access code rejected by controller") from exc2
            _log.info("authenticated via plain access code")
        else:
            digest = hashlib.md5(nonce + access_code.encode("ascii")).digest()
            credentials = "".join(f"{b:02X}" for b in digest).encode("ascii")
            try:
                await self.write_object(CommunicationObject.VERIFY_ACCESS_HASH, credentials)
            except ComApControllerError as exc3:
                raise ComApInvalidAccessCodeError("access code rejected by controller") from exc3
            _log.info("authenticated via hash")

    async def elevate_access(self, password: int) -> None:
        """Submit the controller's write-protection password to unlock password-protected
        setpoints for this session.

        This is a completely separate credential from the ``access_code`` passed to
        [authenticate][pycomap.protocol.ComApClient.authenticate] —
        the *AccessCode* gates the TCP connection itself, while the
        *Password* (0-9999) gates individual setpoint writes based on each setpoint's
        configured ``accessLevel``. Verified live against a real controller: write
        ``CommunicationObject.PASSWORD_FOR_WRITE`` (24524) with the 2-byte little-endian
        password value, then setpoint writes that would otherwise return
        ``ControllerError.INVALID_PASSWORD`` succeed.

        The controller enforces brute-force protection (5 wrong attempts → 1 min block,
        doubling each time, 100 wrong → permanent lockout). Do not call this in a retry
        loop. See ``docs/protocol.md`` section 2.4.1 for the full picture.
        """
        try:
            await self.write_object(
                CommunicationObject.PASSWORD_FOR_WRITE, struct.pack("<H", password)
            )
        except ComApControllerError as exc:
            raise ComApInvalidPasswordError(
                "password rejected by controller (wrong password or brute-force lockout active)"
            ) from exc
        _log.info("write-protection password accepted")

    async def close(self) -> None:
        await self._transport.close()
        self._mode = _Mode.NONE
        self._cipher = None

    async def __aenter__(self) -> ComApClient:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- communication objects -------------------------------------------------

    async def read_object(self, comm_obj: int, addr: int = 1) -> bytes:
        """Read a communication object, handling ``SendToBlock`` continuation transparently.

        Args:
            comm_obj: Communication object number (C.O.).
            addr: Controller unit address; ``1`` for the primary unit.

        Returns:
            Raw payload bytes.

        Raises:
            ComApControllerError: If the controller responds with an error code.
            ComApProtocolError: If an unexpected message operation is received.
        """
        ident = self._next_identifier()
        await self._write_message(Operation.SEND_ME, addr, comm_obj, b"", ident)

        data = bytearray()
        while True:
            message = await self._read_message()
            if message.is_error:
                raise ComApControllerError(message.error_code)
            if message.op is Operation.SEND_TO:
                data.extend(message.data)
                return bytes(data)
            if message.op is Operation.SEND_TO_BLOCK:
                data.extend(message.data)
                if message.is_last_block:
                    return bytes(data)
                next_ident = self._next_identifier()
                await self._write_message(Operation.NEXT, addr, comm_obj, b"", next_ident)
                continue
            raise ComApProtocolError(
                f"unexpected operation {message.op!r} while reading {comm_obj}"
            )

    async def write_object(self, comm_obj: int, data: bytes, addr: int = 1) -> bytes:
        """Write a communication object.

        Args:
            comm_obj: Communication object number (C.O.).
            data: Raw payload bytes to write.
            addr: Controller unit address; ``1`` for the primary unit.

        Returns:
            Any data carried back on the ``NEXT`` acknowledgment (usually empty).

        Raises:
            ComApControllerError: If the controller responds with an error code.
        """
        ident = self._next_identifier()
        await self._write_message(Operation.SEND_TO, addr, comm_obj, data, ident)
        message = await self._read_message()
        if message.is_error:
            raise ComApControllerError(message.error_code)
        if message.op is not Operation.NEXT:
            raise ComApProtocolError(
                f"unexpected operation {message.op!r} while writing {comm_obj}"
            )
        return message.data

    async def execute_command(self, command: ControllerCommand) -> int:
        """Execute a controller command and return the ``uint32`` result code.

        Writes the argument to ``COMMAND_ARGUMENT`` (24550), triggers via ``COMMAND``
        (24551), then reads ``COMMAND_ARGUMENT`` back for the return value. Compare the
        result against ``command.expected_return`` (or use ``command.succeeded(result)``)
        to determine success. A result of ``ControllerCommand.RESULT_REFUSED`` (``0x02``)
        means the controller state doesn't allow the action right now (e.g. engine start
        attempted outside MAN mode); ``RESULT_INVALID_ARGUMENT`` (``0x01``) means the
        command/argument combination is unrecognised.

        Note: some commands require the session to be password-elevated first via
        [elevate_access][pycomap.protocol.ComApClient.elevate_access] — the controller will raise
        ``ControllerError.INVALID_PASSWORD`` on the write if so.
        """
        await self.write_object(
            CommunicationObject.COMMAND_ARGUMENT, struct.pack("<I", command.argument)
        )
        await self.write_object(CommunicationObject.COMMAND, struct.pack("<H", command.code))
        result_raw = await self.read_object(CommunicationObject.COMMAND_ARGUMENT)
        return struct.unpack("<I", result_raw)[0]

    async def read_datetime(self) -> datetime.datetime | None:
        """Read the controller's current date and time as a **naive** datetime.

        Reads ``DATE`` (C.O. 24553) and ``TIME`` (C.O. 24554) in two round-trips.
        Returns ``None`` if the controller reports an invalid/unset clock (e.g. after a
        factory reset before time sync).

        The value is the controller's local wall-clock time (no timezone info attached).
        DST is governed by the ``Summer Time Mode`` setpoint (8727) and the UTC offset
        by the ``Time Zone`` setpoint (24366).
        """
        date_raw = await self.read_object(CommunicationObject.DATE)
        time_raw = await self.read_object(CommunicationObject.TIME)
        date = decode_fdate(date_raw)
        time = decode_ftime(time_raw)
        if date is None or time is None:
            return None
        return datetime.datetime.combine(date, time)

    async def write_datetime(self, dt: datetime.datetime) -> None:
        """Set the controller's clock to the wall-clock components of ``dt``.

        Writes ``DATE`` (C.O. 24553) then ``TIME`` (C.O. 24554). Seconds are included;
        sub-second precision is dropped. Year must be ≥ 2000.

        Both setpoints have ``access_level=1`` — call
        [elevate_access][pycomap.protocol.ComApClient.elevate_access] first.
        Pass the correct **local time** directly.
        """
        await self.write_object(CommunicationObject.DATE, encode_fdate(dt.date()))
        await self.write_object(CommunicationObject.TIME, encode_ftime(dt.time()))

    # -- low-level framing ---------------------------------------------------

    def _next_identifier(self) -> int:
        ident = self._identifier
        self._identifier = (self._identifier + 1) & 0xFF
        return ident

    async def _read_message(self) -> Message:
        inner = await self._read_inner()
        return parse_inner(inner)

    async def _write_message(
        self, op: Operation, addr: int, comm_obj: int, data: bytes, ident: int
    ) -> None:
        inner = build_inner(op, addr, comm_obj, data, ident)
        await self._write_inner(inner)

    async def _read_inner(self) -> bytes:
        if self._mode is _Mode.NONE:
            header = await self._transport.read_exactly(8)
            data_len = struct.unpack_from("<H", header, 0)[0]
            rest = await self._transport.read_exactly(data_len)
            return header + rest

        count_byte = await self._transport.read_exactly(1)
        block_payload = await self._transport.read_exactly(count_byte[0] * BLOCK_SIZE)

        if self._mode is _Mode.ALIGNED:
            return block_payload
        assert self._cipher is not None
        return self._cipher.decrypt(block_payload)

    async def _write_inner(self, inner: bytes) -> None:
        padded = pad_to_block(inner)
        if self._mode is _Mode.NONE:
            await self._transport.write(inner)
        elif self._mode is _Mode.ALIGNED:
            await self._transport.write(wrap_outer(padded))
        else:
            assert self._cipher is not None
            await self._transport.write(wrap_outer(self._cipher.encrypt(padded)))
