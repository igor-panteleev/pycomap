import pytest

from pycomap.exceptions import ComApProtocolError
from pycomap.protocol.client import ComApClient, _Mode
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
