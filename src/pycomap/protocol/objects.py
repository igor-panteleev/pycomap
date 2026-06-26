"""Known ``CommunicationObject`` IDs and ``ControllerError`` codes.

Source: decompiled ``ComAp.Controller.dll`` (class ``CommunicationObject`` — a plain class
with one ``static readonly`` field per object, not a C# ``enum``) and decompiled
``ComAp.GlobalShared.dll`` (``enum ControllerError : uint``). See ``docs/protocol.md``
sections 2.5/2.6 for the full table and how to extend it.

This is a partial list — only what's been confirmed useful so far. Re-decompile the DLLs
with ``ilspycmd`` to extend it.

Controller commands (``ControllerCommand``, ``Command``) live in
[pycomap.protocol.commands][].
"""

from __future__ import annotations

import enum


class CommunicationObject(enum.IntEnum):
    """Known communication object IDs."""

    VERSION_IB = 24533
    DISCOVERY = 24237
    ECDH_PUBLIC_KEY = 24119
    VERIFY_ACCESS_HASH = 24324
    VERIFY_ACCESS = 24534
    MAX_MESSAGE_DATA_LENGTHS = 24269
    COMAP_PROTOCOL_FEATURES = 24023

    VALUES_ALL = 24560
    VALUE_STATES_ALL = 24555
    VALUE_STATES_AND_DATA_ALL = 24529
    VALUES_CATEGORY_I = 24563
    VALUES_CATEGORY_II = 24562
    VALUES_CATEGORY_III = 24561
    VALUE_STATES_CATEGORY_I = 24558
    VALUE_STATES_CATEGORY_II = 24557
    VALUE_STATES_CATEGORY_III = 24556

    SETPOINTS_ALL = 24559
    SETPOINTS_R = 24543
    SETPOINTS_P = 24544

    ALARM_LIST = 24545
    ALARM_LIST_WITH_VERSION = 24024

    CONFIGURATION_TABLE = 24575
    TERMINAL_CONFIGURATION_TABLE = 24574
    CONFIGURATION_TABLE_CRC16 = 24573
    TERMINAL_CONFIGURATION_TABLE_CRC16 = 24572

    SERIAL_NUMBER = 24548
    FIRMWARE_VERSION_TEXT = 24339
    BOOTLOADER_FIRMWARE_VERSION = 24277
    CONTROLLER_FIRMWARE_IDENTIFICATION = 24115

    COMMAND = 24551
    COMMAND_WITH_ARGUMENT = 23859
    COMMAND_ARGUMENT = 24550

    CONTROLLER_STATE = 24496

    HISTORY_LENGTH = 24538
    MAX_HISTORY_RECORDS = 24564
    READ_INDEX_IN_HISTORY = 24565
    WRITE_INDEX_IN_HISTORY = 24566
    OLDER_HISTORY_RECORD = 24567
    YOUNGER_HISTORY_RECORD = 24568
    YOUNGEST_HISTORY_RECORD = 24569
    NEW_HISTORY_RECORDS = 24570

    COMMUNICATION_STATE = 24571
    CONTROLLER_ADDRESS = 24537
    DISPLAY_CONTRAST = 24547
    GSM_PIN = 24536
    PASSWORD_FOR_WRITE = 24524
    PASSWORD_FOR_WRITE_HASH = 24286
    PASSWORD_DECODE = 24202
    TIME_UNTIL_PASSWORD_ENTERING_UNBLOCKS = 24109
    CHANGE_ACCESS = 24535
    SYSTEM_TIME = 24552
    DATE = 24553  # setpoint FDATE, access_level=1 (requires elevate_access to write)
    TIME = 24554  # setpoint FTIME, access_level=1 (requires elevate_access to write)
    TIME_ZONE = 24366  # setpoint STRING_LIST, access_level=0
    INTELI_MAINS = 24528


class ControllerError(enum.IntEnum):
    """Known ``ControllerError`` values (``uint32`` on the wire)."""

    OK = 0
    NO_ANSWER = 1
    ANSWER_POSTPONED = 2
    NON_EXISTING_COMMUNICATION_OBJECT = 100_794_368
    TERMINAL_ACCESS_DISABLED = 134_217_960
    BAD_WRITE_VALUE = 134_217_955
    INVALID_PASSWORD = 134_217_978
