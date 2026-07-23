"""Shared binary-record builders for unit tests.

These construct minimal synthetic configuration-table blobs that mirror the real
IL3 wire layout, letting tests verify parsing logic without embedding the full ~100 KB
live table as a fixture.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence

from pycomap.datatypes import DataType

_IL3_CONTROLLER_TYPE = 14
_NAMES_HEAP_END = 700  # past every fixed names-heap offset used by the parser (max 594)

_COMMON_NAMES = ["VOne", "VTwo"]
_DIMENSIONS = ["V"]


def value_record(
    *,
    data_type: DataType,
    data_index: int,
    state_index: int = 1023,
    decimal_places: int = 0,
    name_index: int = 0,
    dim_index: int = 0,
    low_limit: int = 0,
    high_limit: int = 65535,
    var_low_limit: bool = False,
    var_high_limit: bool = False,
    bit_name_index: int | None = None,
) -> bytes:
    dword1 = (
        name_index
        | (dim_index << 12)
        | (decimal_places << 18)
        | (int(var_low_limit) << 23)
        | (int(var_high_limit) << 24)
    )
    raw_bit_name = 1023 if bit_name_index is None else bit_name_index
    dword2 = (raw_bit_name << 1) | (state_index << 11) | (data_index << 21)
    return struct.pack("<IIBHH", dword1, dword2, int(data_type), low_limit, high_limit)


def _bcd(v: int) -> int:
    return ((v // 10) << 4) | (v % 10)


def history_record(
    *,
    reason_index: int = 0,
    reason_category: int = 0,
    prefix_index: int = 0,
    level: int = 0,
    index: int = 0,
    day: int = 1,
    month: int = 1,
    year: int = 26,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    payload: bytes = b"",
) -> bytes:
    """Build one 69-byte ``HistoryRecord`` wire blob (see ``pycomap.history`` module docstring).

    Defaults to a valid, resolvable wall-clock (RTC) record with a zeroed payload.
    """
    word = (reason_index & 0xFFF) | ((reason_category & 0x3) << 13)
    flags_byte = (prefix_index & 0x1F) | ((level & 0x7) << 5)
    date_time_bytes = bytes(
        [_bcd(day), _bcd(month), _bcd(year), _bcd(hour), _bcd(minute), _bcd(second)]
    )
    ts = date_time_bytes + bytes([0]) + struct.pack("<H", index)
    return struct.pack("<HB", word, flags_byte) + ts + payload.ljust(57, b"\x00")


def setpoint_record(
    *,
    data_type: DataType,
    data_index: int,
    decimal_places: int = 0,
    name_index: int = 0,
    dim_index: int = 0,
    access_level: int = 0,
    low_limit: int = 0,
    high_limit: int = 65535,
    var_low_limit: bool = False,
    var_high_limit: bool = False,
) -> bytes:
    dword1 = name_index | (dim_index << 12) | (access_level << 24)
    byte1 = decimal_places << 4
    dword2 = (data_index << 13) | (int(var_low_limit) << 1) | (int(var_high_limit) << 2)
    return struct.pack("<IBBIHH", dword1, byte1, int(data_type), dword2, low_limit, high_limit)


def build_table(
    *,
    category_counts: tuple[int, int, int, int],
    numbers: list[int],
    records: list[bytes],
    controller_type: int = _IL3_CONTROLLER_TYPE,
    setpoint_category_counts: tuple[int, int] = (0, 0),
    setpoint_numbers: Sequence[int] = (),
    setpoint_records: Sequence[bytes] = (),
    history_items: Sequence[tuple[int, int, int]] = (),
) -> bytes:
    """``history_items`` is a sequence of ``(val_index, data_index, name_index)`` tuples --
    see ``pycomap.configuration._parse_history_description``. ``val_index`` is a 0-based
    index into ``numbers``/``records`` (declaration order, not a comm-object number).
    """
    header = bytearray(_NAMES_HEAP_END)
    header[5] = 4  # ConfigFormatTerminal > 3 → names-heap access vector items are uint32
    header[6] = controller_type
    struct.pack_into("<4H", header, 50, *category_counts)
    struct.pack_into("<2H", header, 98, *setpoint_category_counts)

    value_ids_addr = _NAMES_HEAP_END
    ids_blob = struct.pack(f"<{len(numbers)}H", *numbers)
    value_descriptions_addr = value_ids_addr + len(ids_blob)
    struct.pack_into("<II", header, 84, value_ids_addr, value_descriptions_addr)

    setpoint_ids_blob = struct.pack(f"<{len(setpoint_numbers)}H", *setpoint_numbers)
    setpoint_ids_addr = value_descriptions_addr + len(ids_blob) + len(b"".join(records))
    setpoint_descriptions_addr = setpoint_ids_addr + len(setpoint_ids_blob)
    struct.pack_into("<II", header, 110, setpoint_ids_addr, setpoint_descriptions_addr)

    blob = (
        bytes(header)
        + ids_blob
        + b"".join(records)
        + setpoint_ids_blob
        + b"".join(setpoint_records)
    )

    heap_contents_addr = len(blob) + 4 * (len(_COMMON_NAMES) + len(_DIMENSIONS))
    access_vector = b""
    heap_contents = b""
    for name in [*_COMMON_NAMES, *_DIMENSIONS]:
        access_vector += struct.pack("<I", len(heap_contents))
        encoded = name.encode("utf-8")
        heap_contents += bytes([len(encoded)]) + encoded
    access_vector_addr = len(blob)
    blob += access_vector + heap_contents
    assert heap_contents_addr == access_vector_addr + len(access_vector)

    language_record_addr = len(blob)
    blob += b"\x00" * 6 + struct.pack("<II", access_vector_addr, heap_contents_addr)

    blob = bytearray(blob)
    struct.pack_into("<I", blob, 169, language_record_addr)
    struct.pack_into("<H", blob, 592, 0)
    struct.pack_into("<H", blob, 594, len(_COMMON_NAMES))
    struct.pack_into("<H", blob, 503, len(_COMMON_NAMES))
    blob[505] = len(_DIMENSIONS)

    if history_items:
        hist_table_addr = len(blob)
        for val_index, data_index, name_index in history_items:
            word = (val_index & 0x7FF) | ((data_index & 0x1FF) << 11) | ((name_index & 0xFFF) << 20)
            blob += struct.pack("<I", word)
        struct.pack_into("<H", blob, 152, len(history_items))
        struct.pack_into("<I", blob, 156, hist_table_addr)

    return bytes(blob)
