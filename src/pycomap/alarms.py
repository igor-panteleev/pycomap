"""Alarm list parsing for IL3 controllers.

Source: ``AlarmListRecord.LoadIL3`` + ``LoadCommonPart`` in ``ComAp.Controller.dll``.
See ``docs/protocol.md`` for the full binary format notes.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from pycomap.configuration import NamesCategory, parse_names_heap
from pycomap.datatypes import get_bits

# IL3 alarm list: 112 bytes = up to 16 x 7-byte records.
# Record: uint32 dw + uint16 flags + uint8 source.
# IsUsed: bit 31 of dw must be 1 AND not all fields 0xFF.
# DiagnosticCodeType.ComAp = 7 (bits 0-2 of flags).

_IL3_ALARM_RECORD_SIZE = 7
_DIAGNOSTIC_CODE_TYPE_COMAP = 7
_ALARM_RECORD_STRUCT = struct.Struct("<IHB")  # uint32 dw, uint16 flags, uint8 source


@dataclass(slots=True, frozen=True)
class AlarmRecord:
    """One entry from the controller's alarm list (``CommunicationObject.ALARM_LIST``,
    C.O. 24545).

    Source: ``AlarmListRecord.LoadIL3`` + ``LoadCommonPart`` in ``ComAp.Controller.dll``.
    The IL3 format is 112 bytes = up to 16 x 7-byte records; records stop at the first
    unused slot (all fields at max value) or end of buffer.

    ``reason`` is resolved from ``AlarmReasonNames`` and matches the value's display name
    (e.g. ``"Generator Voltage L1-N"``). ``prefix`` comes from ``HistoryPrefixNames`` and
    encodes the protection type (e.g. ``"Wrn"``, ``"Sd"``).

    For non-ComAp diagnostic codes (ECU alarms from CAN bus), ``reason`` and ``prefix``
    will be empty strings and ``fault_code`` carries the raw ECU fault code.
    """

    is_active: bool
    is_confirmed: bool
    reason: str
    prefix: str
    occurred: int
    source: int
    fault_code: int


def parse_alarm_list(config_data: bytes, alarm_data: bytes) -> list[AlarmRecord]:
    """Parse the controller's ``ALARM_LIST`` blob (C.O. 24545) into a list of
    ``AlarmRecord`` objects, in list order (most recent first per controller behaviour).

    Only active (``IsUsed``) slots are returned; the list will be empty if there are no
    current alarms.  Pass the full raw ``ConfigurationTable`` blob as ``config_data`` —
    it is used to resolve the ``AlarmReasonNames`` and ``HistoryPrefixNames`` heaps.
    """
    reason_names = parse_names_heap(config_data, NamesCategory.ALARM_REASON_NAMES)
    prefix_names = parse_names_heap(config_data, NamesCategory.HISTORY_PREFIX_NAMES)

    records: list[AlarmRecord] = []
    for offset in range(0, len(alarm_data) - _IL3_ALARM_RECORD_SIZE + 1, _IL3_ALARM_RECORD_SIZE):
        dw, flags, source = _ALARM_RECORD_STRUCT.unpack_from(alarm_data, offset)

        is_used = bool(get_bits(dw, 31, 1)) and not (
            dw == 0xFFFFFFFF and flags == 0xFFFF and source == 0xFF
        )
        if not is_used:
            break

        kind = get_bits(flags, 0, 3)
        reason_index = get_bits(flags, 3, 11)
        is_active = bool(get_bits(flags, 14, 1))
        is_confirmed = bool(get_bits(flags, 15, 1))

        fault_code = get_bits(dw, 0, 19)
        prefix_index = get_bits(dw, 19, 5)
        occurred = get_bits(dw, 24, 7)

        if kind == _DIAGNOSTIC_CODE_TYPE_COMAP:
            reason = reason_names[reason_index] if reason_index < len(reason_names) else ""
            prefix = prefix_names[prefix_index] if prefix_index < len(prefix_names) else ""
        else:
            reason = ""
            prefix = ""

        records.append(
            AlarmRecord(
                is_active=is_active,
                is_confirmed=is_confirmed,
                reason=reason,
                prefix=prefix,
                occurred=occurred,
                source=source,
                fault_code=fault_code,
            )
        )

    return records
