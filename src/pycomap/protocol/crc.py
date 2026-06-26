"""CRC16 used to checksum every ComAp ``EthernetMessage``.

Standard MODBUS/ANSI CRC16: init ``0xFFFF``, polynomial ``0xA001`` (reflected ``0x8005``),
no final XOR. Verified byte-for-byte against live ComAp traffic — see
``docs/protocol.md`` section 2.2.
"""

from __future__ import annotations

_POLY = 0xA001


def crc16(data: bytes) -> int:
    """Compute the CRC16 used by the ComAp wire protocol over ``data``."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ _POLY if crc & 1 else crc >> 1
    return crc
