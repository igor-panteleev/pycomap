# pycomap — Claude Code instructions

## After any code change

Run these in order using `just` (see `Justfile` for all targets):

```
just format      # ruff check --fix + ruff format  (auto-fixes, modifies files)
just typecheck   # ty check
just unit        # pytest tests/unit  (no hardware needed)
```

Never leave a change with lint errors, type errors, or failing unit tests.

## All just targets

```
just format      # fix lint + reformat  (aliases: f, fmt)
just lint        # check lint + format, read-only  (alias: l)
just typecheck   # ty check  (alias: tc)
just check       # lint + typecheck, read-only  (alias: c)
just unit        # pytest tests/unit, no hardware  (alias: u)
just test        # full pytest suite  (alias: t)
just integration # pytest tests/integration, requires .env  (alias: i)
just coverage    # unit tests with coverage report  (alias: cov)
just docs        # build Zensical static site → site/
just docs-serve  # live-reload preview at localhost:8000
just ai-docs     # regenerate llms.txt and CLAUDE.md from README.md
```

Integration tests require `PYCOMAP_TEST_HOST` in `.env` (copy `.env.example`).
Skip them unless explicitly testing against hardware.

## Security constraints

- `access_code` (default `"0"`) and `password` (integer) are separate credentials — never conflate.
- Never write the real password to any committed file.
- Never commit `.env`.

---

# pycomap

Async Python client for ComAp controllers (InteliLite AMF25 and likely compatible
siblings): LAN discovery and the native ECDH/AES-encrypted control protocol on port 23.

## Quick start

```python
from ipaddress import IPv4Address

from pycomap import Controller, EthernetTransport
from pycomap.protocol import ComApClient

async with Controller(
    ComApClient(EthernetTransport(IPv4Address("192.168.1.9"))),
    access_code="0",   # factory default (drives ECDH key derivation)
    password=1234,     # write-protection password (0-9999); omit for read-only
) as ctrl:
    values = await ctrl.read_values()
    print(values)

    await ctrl.set_setpoint("Nominal RPM", 1500)
    await ctrl.set_setpoint("Summer Time Mode", "Winter")  # STRING_LIST by label
```

See the [API docs](https://igor-panteleev.github.io/pycomap/) for full reference, built with [Zensical](https://zensical.org/). `just docs-serve` to browse locally.

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
