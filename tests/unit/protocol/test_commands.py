"""Unit tests for ControllerCommand / Command constants (no live hardware)."""

from __future__ import annotations

import struct

from pycomap.protocol.commands import Command, ControllerCommand


def test_controller_command_succeeded():
    cmd = Command.ENGINE_START
    assert cmd.succeeded(cmd.expected_return)
    assert not cmd.succeeded(ControllerCommand.RESULT_REFUSED)
    assert not cmd.succeeded(ControllerCommand.RESULT_INVALID_ARGUMENT)
    assert not cmd.succeeded(0)


def test_all_commands_have_nonzero_expected_return():
    commands = [
        Command.ENGINE_START,
        Command.ENGINE_STOP,
        Command.FAULT_RESET,
        Command.HORN_RESET,
        Command.GCB_TOGGLE,
        Command.GCB_ON,
        Command.GCB_OFF,
        Command.MCB_TOGGLE,
        Command.MCB_ON,
        Command.MCB_OFF,
    ]
    for cmd in commands:
        assert cmd.expected_return != 0
        assert cmd.argument != 0


def test_command_argument_fits_uint32():
    for cmd in [
        Command.ENGINE_START,
        Command.ENGINE_STOP,
        Command.FAULT_RESET,
        Command.HORN_RESET,
        Command.GCB_TOGGLE,
        Command.GCB_ON,
        Command.GCB_OFF,
        Command.MCB_TOGGLE,
        Command.MCB_ON,
        Command.MCB_OFF,
    ]:
        # verify the argument round-trips through the wire encoding used by execute_command
        encoded = struct.pack("<I", cmd.argument)
        assert len(encoded) == 4
        assert struct.unpack("<I", encoded)[0] == cmd.argument
        encoded_code = struct.pack("<H", cmd.code)
        assert len(encoded_code) == 2
        assert struct.unpack("<H", encoded_code)[0] == cmd.code


def test_fault_reset_different_from_engine_start():
    # sanity: commands that look similar are distinct
    assert Command.FAULT_RESET.argument != Command.ENGINE_START.argument
    assert Command.FAULT_RESET.expected_return != Command.ENGINE_START.expected_return


def test_gcb_on_off_are_distinct():
    assert Command.GCB_ON.argument != Command.GCB_OFF.argument
    assert Command.GCB_ON.expected_return != Command.GCB_OFF.expected_return
