# Contributing

## Setup

```sh
uv sync
uv run pre-commit install
```

## Branches

- `dev` — default branch; push directly here
- `main` — stable releases only; updated via PR from `dev`

## Workflow

```sh
just format      # ruff check --fix + ruff format
just typecheck   # ty check
just unit        # unit tests (no hardware)
just lint        # read-only lint check
just coverage    # unit tests with coverage report
just docs-serve  # browse API docs locally
```

Integration tests require real hardware:

```sh
cp .env.example .env   # fill in PYCOMAP_TEST_HOST
just integration
```

## Releasing

1. Bump `version` in `pyproject.toml` on `dev`
2. Open a PR from `dev` → `main`
3. Merge — the `Auto-tag` workflow creates `vX.Y.Z` automatically
4. The `Release` workflow builds, publishes to PyPI, and deploys docs

Pre-releases: use PEP 440 suffixes (`1.1.0a1`, `1.1.0rc1`); PyPI marks them as pre-release and docs are not deployed.
