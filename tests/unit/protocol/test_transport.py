from ipaddress import IPv4Address

import pytest

from pycomap.exceptions import ComApConnectionError
from pycomap.protocol.transport import EthernetTransport, Transport


@pytest.fixture
def transport() -> EthernetTransport:
    return EthernetTransport(IPv4Address("192.168.1.9"))


def test_transport_subclass_missing_methods_cannot_be_instantiated() -> None:
    class Incomplete(Transport):
        async def connect(self) -> None:
            pass

    with pytest.raises(TypeError, match="abstract"):
        Incomplete()  # type: ignore[abstract]


async def test_read_exactly_before_connect_raises_connection_error(
    transport: EthernetTransport,
) -> None:
    with pytest.raises(ComApConnectionError, match="not connected"):
        await transport.read_exactly(1)


async def test_write_before_connect_raises_connection_error(
    transport: EthernetTransport,
) -> None:
    with pytest.raises(ComApConnectionError, match="not connected"):
        await transport.write(b"\x00")


async def test_read_exactly_after_close_raises_connection_error(
    transport: EthernetTransport,
) -> None:
    await transport.close()  # closing without ever connecting is a no-op
    with pytest.raises(ComApConnectionError, match="not connected"):
        await transport.read_exactly(1)


async def test_write_after_close_raises_connection_error(transport: EthernetTransport) -> None:
    await transport.close()
    with pytest.raises(ComApConnectionError, match="not connected"):
        await transport.write(b"\x00")
