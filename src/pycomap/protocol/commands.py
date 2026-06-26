"""Controller command definitions.

``ControllerCommand`` bundles a command's wire-level code, argument, and expected
success return value. ``Command`` is a namespace of pre-built named instances for all
known IL3 commands. Pass them to ``ComApClient.execute_command``.

Source: InteliLite Global Guide §6.1 "List of commands and arguments" and decompiled
``ComAp.Controller.dll`` ``CommandNumber`` class.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerCommand:
    """A controller command bundling its code, argument, and the return value that
    indicates success.

    To execute: ``await client.execute_command(command)``.
    To check the result: compare the returned ``uint32`` against ``expected_return``
    or use ``command.succeeded(result)``.
    """

    code: int
    argument: int
    expected_return: int

    # Application-level failure codes returned inside COMMAND_ARGUMENT on error.
    RESULT_INVALID_ARGUMENT: int = 0x00000001
    RESULT_REFUSED: int = 0x00000002

    def succeeded(self, result: int) -> bool:
        """True if ``result`` (the uint32 read back from ``COMMAND_ARGUMENT``) matches
        the expected success return value for this command.

        Note: a successful return value means the *protocol* acknowledged the command —
        not that the mechanical action was carried out. The controller's own mode logic
        gates execution (e.g. ENGINE_START returns the success code even outside MAN mode,
        but the engine does not start). Always verify the physical outcome separately.
        """
        return result == self.expected_return


class Command:
    """Named controller commands. Pass to ``ComApClient.execute_command``.

    Some commands require the controller to be in a specific mode (e.g. MAN for engine
    start/stop); the controller returns ``RESULT_REFUSED`` (0x02) otherwise.
    """

    ENGINE_START = ControllerCommand(0x01, 0x01FE0000, 0x000001FF)
    ENGINE_STOP = ControllerCommand(0x01, 0x02FD0000, 0x000002FE)
    FAULT_RESET = ControllerCommand(0x01, 0x08F70000, 0x000008F8)
    HORN_RESET = ControllerCommand(0x01, 0x04FB0000, 0x000004FC)
    GCB_TOGGLE = ControllerCommand(0x02, 0x11EE0000, 0x000011EF)
    GCB_ON = ControllerCommand(0x02, 0x11EF0000, 0x000011F0)
    GCB_OFF = ControllerCommand(0x02, 0x11F00000, 0x000011F1)
    MCB_TOGGLE = ControllerCommand(0x02, 0x12ED0000, 0x000012EE)
    MCB_ON = ControllerCommand(0x02, 0x12EE0000, 0x000012EF)
    MCB_OFF = ControllerCommand(0x02, 0x12EF0000, 0x000012F0)
