"""One-shot status snapshot: values, active alarms, and recent history.

Usage::

    uv run python examples/status.py 192.168.1.9 0
    uv run python examples/status.py 192.168.1.9 0 --history 20
    uv run python examples/status.py 192.168.1.9 0 --invisible
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import logging
import sys

from pycomap import Controller, EthernetTransport
from pycomap.configuration import ValueDescription
from pycomap.protocol import ComApClient

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)])


def _display(desc: ValueDescription, val: int | float | bytes | str) -> str:
    if isinstance(val, float):
        return f"{val:.{desc.decimal_places}f}"
    if isinstance(val, bytes):
        return val.hex()
    return str(val)


async def main(host: str, access_code: str, history_count: int, show_invisible: bool) -> None:
    async with Controller(ComApClient(EthernetTransport(host)), access_code=access_code) as ctrl:
        values = await ctrl.read_values()
        alarms = await ctrl.read_alarms()
        history = await ctrl.read_history(count=history_count)

    # -- Values (grouped by Group, fall back to ValueCategory) ----------------
    header = f"{'NAME':<40} {'VALUE':>12}  UNIT"
    rule = "-" * 60
    visible = sorted(
        (d for d in ctrl.values if show_invisible or d.group != "Invisible"),
        key=lambda d: d.group,
    )
    for group_label, group_iter in itertools.groupby(visible, key=lambda d: d.group):
        print(f"\n{group_label}")
        print(header)
        print(rule)
        for desc in group_iter:
            val = values.get(desc.number)
            if val is None:
                continue
            print(f"{desc.name:<40} {_display(desc, val):>12}  {desc.dimension}")

    # -- Alarms ---------------------------------------------------------------
    print(f"\nAlarms ({len(alarms)} active):")
    if alarms:
        for alarm in alarms:
            status = "ACTIVE" if alarm.is_active else "inactive"
            ack = "" if alarm.is_confirmed else "  [unconfirmed]"
            print(f"  [{alarm.prefix}] {alarm.reason}  — {status}{ack}")
    else:
        print("  (none)")

    # -- History --------------------------------------------------------------
    print(f"\nLast {len(history)} history records:")
    for rec in history:
        when = (
            rec.timestamp.strftime("%Y-%m-%d %H:%M:%S") if rec.timestamp else str(rec.engine_hours)
        )
        if rec.is_text:
            print(f"  #{rec.index:5d}  {when}  {rec.text}")
        else:
            print(f"  #{rec.index:5d}  {when}  [{rec.prefix}] {rec.reason}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One-shot controller status snapshot.")
    parser.add_argument("host")
    parser.add_argument("access_code")
    parser.add_argument("--history", type=int, default=10, metavar="N")
    parser.add_argument(
        "--invisible",
        action="store_true",
        help="include values in the 'Invisible' group (hidden internal signals)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.host, args.access_code, args.history, args.invisible))
