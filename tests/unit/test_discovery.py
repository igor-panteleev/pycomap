from ipaddress import IPv4Address

from pycomap.discovery import AccessType, DeviceType, _build_probe, _parse_device
from pycomap.protocol.framing import parse_inner

# Real, CRC-validated reply captured live from a controller (see docs/protocol.md section 1).
REAL_REPLY = bytes.fromhex(
    "41000100ad5e010400000000c900a10fc0a801096869f2022e8617000100"
    "000000000000000075900000000f0001000000010e465620313530303000"
    "00000000000000222912761818"
)


def test_build_probe_is_a_valid_send_me_discovery_message() -> None:
    probe = _build_probe()
    assert probe == bytes.fromhex("00000000ad5efd73")
    message = parse_inner(probe)
    assert message.comm_obj == 24237
    assert message.data == b""


def test_parse_device_matches_real_captured_reply() -> None:
    message = parse_inner(REAL_REPLY)
    device = _parse_device(message.data)

    assert device.format_version == 1
    assert device.device_type is DeviceType.CM_ETHERNET
    assert device.ip == IPv4Address("192.168.1.9")
    assert device.mac == "68:69:f2:02:2e:86"
    assert device.comm_port == 23
    assert device.access_type is AccessType.IP_ADDRESS
    assert device.airgate_identifier == ""
    assert device.connected_units == 0b1
    assert device.is_units_list_complete is True

    assert len(device.units) == 1
    unit = device.units[0]
    assert unit.name == "FV 15000"
    assert unit.serial == "22291276"
