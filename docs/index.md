# pycomap

Async Python client for ComAp controllers (InteliLite AMF25 and likely compatible
siblings): LAN discovery and the native ECDH/AES-encrypted control protocol on port 23.

## Quick start

```python
from pycomap import Controller, EthernetTransport
from pycomap.protocol import ComApClient

async with Controller(
    ComApClient(EthernetTransport("192.168.1.9")),
    access_code="0",
    password=1234,
) as ctrl:
    values = await ctrl.read_values()
    await ctrl.set_setpoint("Nominal RPM", 1500)
```

## API Reference

| Page | Contents |
|---|---|
| [Controller](api/controller.md) | High-level `Controller` — the main entry point |
| [Low-level Client](api/client.md) | `ComApClient`, `EthernetTransport` |
| [Configuration](api/configuration.md) | `ValueDescription`, `SetpointDescription`, table parsing |
| [Data Types](api/datatypes.md) | `DataType` enum, wire encode/decode |
| [Discovery](api/discovery.md) | UDP `discover()`, `DiscoveryDevice` |
| [Alarms](api/alarms.md) | `AlarmRecord`, alarm list parsing |
| [History](api/history.md) | `HistoryRecord`, history record parsing |
| [Exceptions](api/exceptions.md) | Exception hierarchy |
