"""ComAp ``EthernetMessage`` wire framing.

See ``docs/protocol.md`` section 2.1 for the full format. Two nested layers:

Outer "block alignment" wrapper (present on every message except the very first one on a
connection, see [pycomap.protocol.client][])::

    [1 byte: block_count][block_count * 16 bytes: payload, zero-padded to the boundary]

Inner ``EthernetMessage``::

    offset  size  field
    0       2     data_length (uint16 LE)
    2       1     bits[0:3]=Operation, bits[3:8]=ControllerAddress-1
    3       1     Identifier
    4       2     CommunicationObject id (uint16 LE)
    6       dlen  data (or, for SendToBlock: 1 block-info byte + (dlen-1) bytes of data)
    6+dlen  2     CRC16 LE over bytes [0 .. 6+dlen)

This module only deals with bytes — it knows nothing about sockets or encryption. The outer
wrapper's payload may be plaintext (before AES is established) or AES-CBC ciphertext (after);
either way this module just packs/unpacks the block-count-prefixed, 16-byte-aligned blob.
"""

from __future__ import annotations

import enum
import struct
from dataclasses import dataclass

from pycomap.exceptions import ComApProtocolError
from pycomap.protocol.crc import crc16

BLOCK_SIZE = 16


class Operation(enum.IntEnum):
    """ComAp ``Message.Operation`` enum (3 bits on the wire)."""

    SEND_ME = 0
    SEND_TO = 1
    SEND_TO_BLOCK = 2
    NEXT = 3  # aka "Acknowledgment"
    ERROR = 4
    REPEAT = 5


@dataclass(slots=True)
class Message:
    """A parsed (or about-to-be-built) inner ``EthernetMessage``."""

    op: Operation
    addr: int
    ident: int
    comm_obj: int
    data: bytes
    block_index: int | None = None
    is_last_block: bool | None = None

    @property
    def is_error(self) -> bool:
        return self.op is Operation.ERROR

    @property
    def error_code(self) -> int:
        """Decode the ``uint32`` LE error code carried in an ``ERROR`` message's data."""
        if not self.is_error:
            raise ValueError("not an ERROR message")
        return struct.unpack_from("<I", self.data, 0)[0]


def parse_inner(buf: bytes) -> Message:
    """Parse one inner ``EthernetMessage`` from ``buf`` (CRC-validated)."""
    if len(buf) < 8:
        raise ComApProtocolError(f"message too short: {len(buf)} bytes")
    data_len = struct.unpack_from("<H", buf, 0)[0]
    total = data_len + 8
    if total > len(buf):
        raise ComApProtocolError(f"truncated message: need {total} bytes, have {len(buf)}")
    buf = buf[:total]

    b2 = buf[2]
    op = Operation(b2 & 0x07)
    addr = (b2 >> 3) + 1
    ident = buf[3]
    comm_obj = struct.unpack_from("<H", buf, 4)[0]

    block_index: int | None = None
    is_last_block: bool | None = None
    if op is Operation.SEND_TO_BLOCK:
        block_byte = buf[6]
        block_index = block_byte & 0x7F
        is_last_block = bool(block_byte & 0x80)
        data = buf[7 : 6 + data_len]
    else:
        data = buf[6 : 6 + data_len]

    crc_expected = struct.unpack_from("<H", buf, len(buf) - 2)[0]
    crc_actual = crc16(buf[:-2])
    if crc_expected != crc_actual:
        raise ComApProtocolError(
            f"CRC mismatch: expected {crc_expected:#06x}, got {crc_actual:#06x} ({buf.hex()})"
        )

    return Message(
        op=op,
        addr=addr,
        ident=ident,
        comm_obj=comm_obj,
        data=bytes(data),
        block_index=block_index,
        is_last_block=is_last_block,
    )


def build_inner(
    op: Operation,
    addr: int,
    comm_obj: int,
    data: bytes,
    ident: int,
) -> bytes:
    """Build one inner ``EthernetMessage`` (header + data + CRC), CRC-validated by construction."""
    b2 = (op & 0x07) | ((addr - 1) << 3)
    header = struct.pack("<H", len(data)) + bytes([b2, ident]) + struct.pack("<H", comm_obj)
    msg = header + data
    return msg + struct.pack("<H", crc16(msg))


def pad_to_block(payload: bytes) -> bytes:
    """Zero-pad ``payload`` up to the next 16-byte boundary."""
    remainder = len(payload) % BLOCK_SIZE
    if remainder == 0:
        return payload
    return payload + b"\x00" * (BLOCK_SIZE - remainder)


def wrap_outer(block_payload: bytes) -> bytes:
    """Prefix an already block-aligned payload with its 1-byte block count."""
    if len(block_payload) % BLOCK_SIZE != 0:
        raise ComApProtocolError("outer payload is not block-aligned")
    count = len(block_payload) // BLOCK_SIZE
    if count > 255:
        raise ComApProtocolError("message too long for a single block-count byte")
    return bytes([count]) + block_payload
