import pytest

from pycomap.exceptions import ComApProtocolError
from pycomap.protocol.client import ComApClient, _Mode
from pycomap.protocol.framing import Message, Operation
from pycomap.protocol.transport import Transport


class _StubTransport(Transport):
    """Minimal ``Transport`` that never touches the network."""

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def read_exactly(self, n: int) -> bytes:
        return b"\x00" * n

    async def write(self, data: bytes) -> None:
        pass


@pytest.fixture
def client_in_aes_mode_without_cipher() -> ComApClient[_StubTransport]:
    """A client that has (incorrectly) reached AES mode with no cipher set.

    Never happens through the public API — ``authenticate()`` sets ``_mode`` and
    ``_cipher`` together — but the internal invariant is guarded explicitly rather
    than assumed, so we drive it here directly to exercise that guard.
    """
    client = ComApClient(_StubTransport())
    client._mode = _Mode.AES
    return client


async def test_read_inner_without_cipher_in_aes_mode_raises_protocol_error(
    client_in_aes_mode_without_cipher: ComApClient[_StubTransport],
) -> None:
    with pytest.raises(ComApProtocolError, match="cipher not initialized"):
        await client_in_aes_mode_without_cipher._read_inner()


async def test_write_inner_without_cipher_in_aes_mode_raises_protocol_error(
    client_in_aes_mode_without_cipher: ComApClient[_StubTransport],
) -> None:
    with pytest.raises(ComApProtocolError, match="cipher not initialized"):
        await client_in_aes_mode_without_cipher._write_inner(b"\x00" * 16)


# ---------------------------------------------------------------------------
# addr default (ControllerAddress, C.O. 24537 -- see docs/protocol.md 2.1)
# ---------------------------------------------------------------------------


async def test_read_object_uses_constructor_addr_by_default(mocker) -> None:
    client = ComApClient(_StubTransport(), addr=5)
    write_message = mocker.patch.object(client, "_write_message")
    mocker.patch.object(
        client,
        "_read_message",
        return_value=Message(op=Operation.SEND_TO, addr=5, ident=0, comm_obj=100, data=b"\x01\x02"),
    )

    result = await client.read_object(100)

    assert result == b"\x01\x02"
    assert write_message.call_args.args[1] == 5  # addr


async def test_read_object_per_call_addr_overrides_constructor_default(mocker) -> None:
    client = ComApClient(_StubTransport(), addr=5)
    write_message = mocker.patch.object(client, "_write_message")
    mocker.patch.object(
        client,
        "_read_message",
        return_value=Message(op=Operation.SEND_TO, addr=9, ident=0, comm_obj=100, data=b""),
    )

    await client.read_object(100, addr=9)

    assert write_message.call_args.args[1] == 9  # addr


async def test_write_object_uses_constructor_addr_by_default(mocker) -> None:
    client = ComApClient(_StubTransport(), addr=7)
    write_message = mocker.patch.object(client, "_write_message")
    mocker.patch.object(
        client,
        "_read_message",
        return_value=Message(op=Operation.NEXT, addr=7, ident=0, comm_obj=100, data=b""),
    )

    await client.write_object(100, b"\x00")

    assert write_message.call_args.args[1] == 7  # addr


async def test_client_defaults_to_addr_1(mocker) -> None:
    client = ComApClient(_StubTransport())
    write_message = mocker.patch.object(client, "_write_message")
    mocker.patch.object(
        client,
        "_read_message",
        return_value=Message(op=Operation.SEND_TO, addr=1, ident=0, comm_obj=100, data=b""),
    )

    await client.read_object(100)

    assert write_message.call_args.args[1] == 1  # addr
