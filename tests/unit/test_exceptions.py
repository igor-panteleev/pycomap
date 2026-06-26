"""Unit tests for the pycomap exception hierarchy."""

from __future__ import annotations

from pycomap.exceptions import ComApControllerError


def test_controller_error_stores_code() -> None:
    err = ComApControllerError(0x1234ABCD)
    assert err.code == 0x1234ABCD


def test_controller_error_default_message_contains_hex() -> None:
    err = ComApControllerError(0x1234ABCD)
    assert "0x1234abcd" in str(err)


def test_controller_error_custom_message_overrides_default() -> None:
    err = ComApControllerError(42, "something went wrong")
    assert str(err) == "something went wrong"
    assert err.code == 42


def test_controller_error_is_exception() -> None:
    err = ComApControllerError(0)
    assert isinstance(err, Exception)
