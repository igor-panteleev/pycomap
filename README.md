# pycomap

Async Python client for ComAp controllers (InteliLite AMF25 and likely compatible
siblings): LAN discovery and the native ECDH/AES-encrypted control protocol on port 23.

Reverse-engineered from `ComAp.Controller.dll` and cross-validated against live hardware.

Requires Python 3.13+. Dependencies: `cryptography`, `pytz`.

## Quick start

```python
from pycomap import Controller, EthernetTransport
from pycomap.protocol import ComApClient

async with Controller(
    ComApClient(EthernetTransport("192.168.1.9")),
    access_code="0",   # factory default (drives ECDH key derivation)
    password=1234,     # write-protection password (0-9999); omit for read-only
) as ctrl:
    values = await ctrl.read_values()
    print(values)

    await ctrl.set_setpoint("Nominal RPM", 1500)
    await ctrl.set_setpoint("Summer Time Mode", "Winter")  # STRING_LIST by label
```

See the [API docs](https://igor-panteleev.github.io/pycomap/) for full reference. `just docs-serve` to browse locally.

## Development

```sh
just format       # ruff check --fix + ruff format
just typecheck    # ty check
just unit         # tests/unit (no hardware needed)
just integration  # tests/integration (requires .env with PYCOMAP_TEST_HOST)
just docs-serve   # browse API docs locally
just ai-docs      # regenerate llms.txt and CLAUDE.md
```

`pre-commit` runs format + typecheck on every commit:

```sh
uv run pre-commit install
```
