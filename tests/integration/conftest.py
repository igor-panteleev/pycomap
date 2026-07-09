"""Fixtures for tests that talk to a real ComAp controller on the network.

Requires PYCOMAP_TEST_HOST to be set (e.g. via a `.env` file at the project root, loaded
automatically by pytest-env — see `.env.example`). Tests are skipped otherwise.
"""

from __future__ import annotations

import os
from ipaddress import IPv4Address, IPv4Interface

import ifaddr
import pytest

DEFAULT_ACCESS_CODE = "0"


@pytest.fixture(scope="session")
def comap_host() -> IPv4Address:
    host = os.environ.get("PYCOMAP_TEST_HOST")
    if not host:
        pytest.skip("PYCOMAP_TEST_HOST not set; see .env.example to run integration tests")
    return IPv4Address(host)


@pytest.fixture(scope="session")
def comap_interface(comap_host: IPv4Address) -> IPv4Interface:
    """The local IPv4 interface actually on ``comap_host``'s subnet.

    Broadcasting from the wrong interface (or from a wildcard bind on a multi-homed host)
    silently reaches nothing — see [discover][pycomap.discovery.discover]'s docstring.
    """
    for adapter in ifaddr.get_adapters():
        for ip in adapter.ips:
            if not ip.is_IPv4:
                continue
            interface = IPv4Interface(f"{ip.ip}/{ip.network_prefix}")
            if comap_host in interface.network:
                return interface
    pytest.skip(f"no local interface found on {comap_host}'s subnet")


@pytest.fixture(scope="session")
def comap_access_code() -> str:
    return os.environ.get("PYCOMAP_TEST_ACCESS_CODE", DEFAULT_ACCESS_CODE)


@pytest.fixture(scope="session")
def comap_password() -> int:
    raw = os.environ.get("PYCOMAP_TEST_PASSWORD")
    if not raw:
        pytest.skip("PYCOMAP_TEST_PASSWORD not set; see .env.example")
    return int(raw)
