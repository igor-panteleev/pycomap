"""Fixtures for tests that talk to a real ComAp controller on the network.

Requires PYCOMAP_TEST_HOST to be set (e.g. via a `.env` file at the project root, loaded
automatically by pytest-env — see `.env.example`). Tests are skipped otherwise.
"""

from __future__ import annotations

import os

import pytest

DEFAULT_ACCESS_CODE = "0"


@pytest.fixture(scope="session")
def comap_host() -> str:
    host = os.environ.get("PYCOMAP_TEST_HOST")
    if not host:
        pytest.skip("PYCOMAP_TEST_HOST not set; see .env.example to run integration tests")
    return host


@pytest.fixture(scope="session")
def comap_access_code() -> str:
    return os.environ.get("PYCOMAP_TEST_ACCESS_CODE", DEFAULT_ACCESS_CODE)


@pytest.fixture(scope="session")
def comap_password() -> int:
    raw = os.environ.get("PYCOMAP_TEST_PASSWORD")
    if not raw:
        pytest.skip("PYCOMAP_TEST_PASSWORD not set; see .env.example")
    return int(raw)
