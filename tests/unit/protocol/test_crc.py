from pycomap.protocol.crc import crc16


def test_crc16_known_vector_from_live_capture() -> None:
    """The first 8 bytes of a real ``VersionIB`` message (data=0x0080, i.e. version 0,
    AES cipher), CRC-validated live against a real controller. See docs/protocol.md section 2.4.
    """
    header_and_data = bytes.fromhex("02000100d55f0080")
    assert crc16(header_and_data) == 0xBDC9


def test_crc16_empty() -> None:
    assert crc16(b"") == 0xFFFF
