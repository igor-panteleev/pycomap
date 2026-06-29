"""Unit tests for the pycomap exception hierarchy."""

from __future__ import annotations

import pytest

from pycomap.exceptions import (
    ComApAuthError,
    ComApControllerError,
    ComApInvalidAccessCodeError,
    ComApInvalidPasswordError,
)


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


def test_invalid_access_code_error_is_auth_error() -> None:
    err = ComApInvalidAccessCodeError("bad code")
    assert isinstance(err, ComApAuthError)


def test_invalid_password_error_is_auth_error() -> None:
    err = ComApInvalidPasswordError("bad password")
    assert isinstance(err, ComApAuthError)


def test_auth_subclasses_caught_as_auth_error() -> None:
    for cls in (ComApInvalidAccessCodeError, ComApInvalidPasswordError):
        with pytest.raises(ComApAuthError):
            raise cls("test")
