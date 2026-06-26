"""History record parsing for IL3 controllers.

Source: ``ClientDrivenHistorySerializer.LoadHeaderIL3`` + ``LoadHeaderIL3CommonPart``
+ ``HistoryTimeStamp.LoadDefinedByHistRecord`` in ``ComAp.Controller.dll``.
See ``docs/protocol.md`` for the full binary format notes.

IL3 record wire layout (ConfigFormatTerminal < 7, confirmed on live controller):

  Bytes 0-1  uint16 LE  bits 0-11 = reason_index, bits 13-14 = reason_category
  Byte  2               bits 0-4  = prefix_index, bits 5-7  = level
  Bytes 3-11  9-byte timestamp (DefinedByHistRecord format):
      [0]=BCD(day)  [1]=BCD(month)  [2]=BCD(year-2000)
      [3]=BCD(hour) [4]=BCD(minute) [5]=BCD(second)
      [6] bit7=type(0=RTC,1=EngHours)  bits0-3=tenths-of-second
      [7-8] uint16 LE = sequential record index
  Bytes 12+  payload: null-terminated ASCII for text records, raw value
             snapshots for alarm/event records

prefix_index sentinel values: 30 = text record, 31 = invalid record.
reason_category: 0=HistoryReasonNames, 1=CommonNames, 2=DiagNames, 3=AlarmReasonNames
"""

from __future__ import annotations

import datetime
import struct
from dataclasses import dataclass

from pycomap.configuration import NamesCategory, parse_names_heap
from pycomap.datatypes import _bcd_decode, get_bits

_HIST_PREFIX_TEXT = 30
_HIST_PREFIX_INVALID = 31

_HIST_CAT_REASON_NAMES: dict[int, NamesCategory] = {
    0: NamesCategory.HISTORY_REASON_NAMES,
    1: NamesCategory.COMMON_NAMES,
    3: NamesCategory.ALARM_REASON_NAMES,
    # 2 = EcuDiagnosticCodes (DiagNames) — not implemented; returned as empty string
}


@dataclass(slots=True, frozen=True)
class HistoryRecord:
    """One entry from the controller's history ring buffer (``YOUNGEST_HISTORY_RECORD``
    / ``OLDER_HISTORY_RECORD``, C.O. 24569/24567).

    For alarm events: ``reason`` is the value name that triggered the event (e.g.
    ``"Generator Voltage L1-N"``), ``prefix`` is the protection type (``"Wrn"``,
    ``"Sd"``, etc.), ``level`` encodes severity (1-3) or transition type (4=Start,
    5=Stop).

    For configuration-change events (``is_text=True``): ``text`` holds the human-readable
    description (e.g. ``"T=ETH CA1 A CON(24554)=21:25:08"``); ``reason`` and ``prefix``
    are usually empty.

    ``timestamp`` is the controller's local time at the event (see ``read_datetime`` note
    about Summer Time Mode). ``engine_hours`` is set instead when the controller uses
    run-hours as the time reference (rare; RTC is the norm for IL3).
    """

    index: int
    timestamp: datetime.datetime | None
    engine_hours: datetime.timedelta | None
    tenth_seconds: int
    reason: str
    prefix: str
    level: int
    is_text: bool
    text: str
    data: bytes


def _parse_history_timestamp(
    ts: bytes,
) -> tuple[datetime.datetime | None, datetime.timedelta | None, int]:
    """Decode the 9-byte DefinedByHistRecord timestamp.

    Returns ``(datetime, engine_hours, tenth_seconds)``. Exactly one of the first two
    will be non-None.
    """
    is_engine_hours = bool(ts[6] & 0x80)
    tenth_seconds = _bcd_decode(ts[6] & 0x0F)

    if is_engine_hours:
        dw = struct.unpack_from("<I", ts, 0)[0]
        hours = (dw >> 0) & 0xFFFFFF
        minutes = (dw >> 24) & 0xFF
        return None, datetime.timedelta(hours=hours, minutes=minutes), tenth_seconds

    try:
        dt = datetime.datetime(
            year=_bcd_decode(ts[2]) + 2000,
            month=_bcd_decode(ts[1]),
            day=_bcd_decode(ts[0]),
            hour=_bcd_decode(ts[3]),
            minute=_bcd_decode(ts[4]),
            second=_bcd_decode(ts[5]),
        )
    except ValueError:
        dt = None
    return dt, None, tenth_seconds


def parse_history_record(config_data: bytes, record_data: bytes) -> HistoryRecord | None:
    """Parse one history record blob returned by ``YOUNGEST_HISTORY_RECORD`` /
    ``OLDER_HISTORY_RECORD`` (C.O. 24569/24567).

    Returns ``None`` for invalid records (prefix_index=31 or unparseable timestamp).
    Pass the full raw ``ConfigurationTable`` blob as ``config_data`` — it is used to
    resolve reason and prefix names from the unified names heap.
    """
    if len(record_data) < 12:
        return None

    word, flags_byte = struct.unpack_from("<HB", record_data, 0)
    reason_index = get_bits(word, 0, 12)
    reason_category = get_bits(word, 13, 2)
    prefix_index = get_bits(flags_byte, 0, 5)
    level = get_bits(flags_byte, 5, 3)

    if prefix_index == _HIST_PREFIX_INVALID:
        return None

    is_text = prefix_index == _HIST_PREFIX_TEXT
    ts_bytes = record_data[3:12]
    payload = record_data[12:]

    dt, engine_hours, tenth_seconds = _parse_history_timestamp(ts_bytes)
    index = struct.unpack_from("<H", ts_bytes, 7)[0]

    if dt is None and engine_hours is None:
        return None

    # Resolve reason name
    names_cat = _HIST_CAT_REASON_NAMES.get(reason_category)
    reason = ""
    if names_cat is not None:
        names = parse_names_heap(config_data, names_cat)
        reason = names[reason_index] if reason_index < len(names) else ""

    # Resolve prefix name. Index 0 = '-' (info/status, no protection class).
    prefix = ""
    if not is_text:
        prefix_names = parse_names_heap(config_data, NamesCategory.HISTORY_PREFIX_NAMES)
        prefix = prefix_names[prefix_index] if prefix_index < len(prefix_names) else ""

    # Decode text payload (null-terminated ASCII)
    text = ""
    if is_text:
        null = payload.find(0)
        raw_text = payload[:null] if null >= 0 else payload
        text = raw_text.decode("ascii", errors="replace")

    return HistoryRecord(
        index=index,
        timestamp=dt,
        engine_hours=engine_hours,
        tenth_seconds=tenth_seconds,
        reason=reason,
        prefix=prefix,
        level=level,
        is_text=is_text,
        text=text,
        data=payload if not is_text else b"",
    )
