import pytest

from pycomap.exceptions import ComApProtocolError
from pycomap.protocol.framing import (
    Operation,
    build_inner,
    pad_to_block,
    parse_inner,
    wrap_outer,
)
from pycomap.protocol.objects import CommunicationObject


def test_parse_inner_known_version_ib_message() -> None:
    """Real, CRC-validated ``VersionIB`` message captured live (plain framing, no outer
    block wrapper, since it's the very first message of a connection).
    """
    raw = bytes.fromhex("02000100d55f0080c9bd")
    message = parse_inner(raw)
    assert message.op is Operation.SEND_TO
    assert message.addr == 1
    assert message.ident == 0
    assert message.comm_obj == CommunicationObject.VERSION_IB
    assert message.data == bytes.fromhex("0080")


def test_parse_inner_rejects_bad_crc() -> None:
    raw = bytes.fromhex("02000100d55f0080ffff")
    with pytest.raises(ComApProtocolError):
        parse_inner(raw)


def test_build_then_parse_roundtrip() -> None:
    built = build_inner(Operation.SEND_TO, addr=3, comm_obj=24560, data=b"hello", ident=42)
    parsed = parse_inner(built)
    assert parsed.op is Operation.SEND_TO
    assert parsed.addr == 3
    assert parsed.ident == 42
    assert parsed.comm_obj == 24560
    assert parsed.data == b"hello"


def test_build_then_parse_roundtrip_send_to_block() -> None:
    built = build_inner(
        Operation.SEND_TO_BLOCK,
        addr=1,
        comm_obj=24575,
        data=bytes([0x05]) + b"payload!",  # block_info byte + real data
        ident=1,
    )
    parsed = parse_inner(built)
    assert parsed.op is Operation.SEND_TO_BLOCK
    assert parsed.block_index == 5
    assert parsed.is_last_block is False
    assert parsed.data == b"payload!"


def test_error_message_decodes_code() -> None:
    error_data = (134_217_955).to_bytes(4, "little")
    built = build_inner(Operation.ERROR, addr=1, comm_obj=1, data=error_data, ident=0)
    parsed = parse_inner(built)
    assert parsed.is_error
    assert parsed.error_code == 134_217_955


def test_pad_to_block() -> None:
    assert pad_to_block(b"") == b""
    assert pad_to_block(b"1234567890123456") == b"1234567890123456"
    assert pad_to_block(b"123") == b"123" + b"\x00" * 13


def test_wrap_outer_and_block_count() -> None:
    payload = pad_to_block(b"hello world")
    wrapped = wrap_outer(payload)
    assert wrapped[0] == 1
    assert wrapped[1:] == payload


def test_wrap_outer_rejects_unaligned_payload() -> None:
    with pytest.raises(ComApProtocolError):
        wrap_outer(b"not aligned")


def test_parse_inner_too_short_raises() -> None:
    with pytest.raises(ComApProtocolError):
        parse_inner(b"\x00" * 7)


def test_parse_inner_truncated_raises() -> None:
    # data_len=16 → total=24, but we only provide 8 bytes
    with pytest.raises(ComApProtocolError):
        parse_inner(b"\x10\x00" + b"\x00" * 6)


def test_error_code_on_non_error_message_raises() -> None:
    raw = bytes.fromhex("02000100d55f0080c9bd")  # known VersionIB (SEND_TO, not ERROR)
    msg = parse_inner(raw)
    assert not msg.is_error
    with pytest.raises(ValueError, match="not an ERROR message"):
        _ = msg.error_code


def test_wrap_outer_too_many_blocks_raises() -> None:
    from pycomap.protocol.framing import BLOCK_SIZE

    # 256 blocks → count=256 > 255 → raises
    payload = b"\x00" * (256 * BLOCK_SIZE)
    with pytest.raises(ComApProtocolError):
        wrap_outer(payload)
