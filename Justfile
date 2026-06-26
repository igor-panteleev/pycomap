set shell := ["bash", "-c"]

# --- Main Entry Point ---

# List all available commands (default)
default:
    @just --list

# --- Internal Helpers ---

[private]
prepare:
    @uv sync --group dev --frozen --quiet

# --- Aliases ---
alias c := check
alias l := lint
alias tc := typecheck
alias fmt := format
alias f := format
alias t := test
alias u := unit
alias i := integration
alias cov := coverage

# --- Verification (Read-only) ---

# Run all checks (lint, format, types, tests)
check: lint typecheck

# Check for lint violations and code formatting
lint: prepare
    uv run ruff check
    uv run ruff format --check

# Run static type analysis with ty
typecheck: prepare
    uv run ty check

# --- Auto-Fixing (Modifies files) ---

# Fix linting and reformat code
format: prepare
    uv run ruff check --fix
    uv run ruff format

# --- Development Workflow ---

# Run pytest suite (pass args with 'just t --arg')
test *args: prepare
    uv run pytest {{args}}

# Run unit tests only (no hardware needed)
unit *args: prepare
    uv run pytest tests/unit {{args}}

# Run integration tests only (requires .env / PYCOMAP_TEST_HOST, see .env.example)
integration *args: prepare
    uv run pytest tests/integration {{args}}

# Run tests with coverage report
coverage: prepare
    uv run pytest tests/unit --cov=pycomap --cov-report=term -q

# --- Documentation ---

# Build MkDocs static site (output: site/)
docs: prepare
    uv run mkdocs build

# Serve MkDocs site locally with live reload
docs-serve: prepare
    uv run mkdocs serve

# Regenerate llms.txt and CLAUDE.md from README.md
ai-docs: prepare
    uv run python scripts/gen_ai_docs.py
