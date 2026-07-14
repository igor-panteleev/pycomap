"""Regenerate docs/controller_reference.md from a live ComAp controller.

Connects read-only (no password) to a real controller and writes the full Values,
Setpoints, and String Lists tables from its ``ConfigurationTable`` plus a single
``read_values()``/``read_setpoints()`` snapshot. Re-run whenever the controller's
configuration changes.

Usage::

    uv run python scripts/gen_controller_reference.py --host 192.168.1.9 --access-code 0

``--host``/``--access-code`` fall back to ``PYCOMAP_TEST_HOST``/``PYCOMAP_TEST_ACCESS_CODE``
from ``.env`` (see ``.env.example``) when omitted.
"""

from __future__ import annotations

import asyncio
import re
from ipaddress import IPv4Address
from pathlib import Path

import configargparse
from dotenv import load_dotenv

from pycomap import Controller, EthernetTransport
from pycomap.configuration import SetpointDescription, ValueDescription
from pycomap.datatypes import DataType, Value
from pycomap.protocol import ComApClient

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "docs" / "controller_reference.md"

# Values that identify this specific controller/network rather than describing its generic
# configuration -- redacted so the generated reference is safe to commit/publish.
_REDACTED_VALUE_NAMES = frozenset({"Password Decode", "MAC Address"})
_REDACTED = "***"

Description = ValueDescription | SetpointDescription
StringListEntry = tuple[Description, list[tuple[int, str]]]


def _slugify(text: str) -> str:
    """Reproduce python-markdown's default TOC heading-id algorithm.

    mkdocs/Zensical use this to generate heading anchors -- links computed here must match
    the anchors actually rendered, or the cross-links from the Values/Setpoints tables into
    the String Lists section will silently 404.
    """
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s+", "-", text.strip())


def _anchor(desc: Description) -> str:
    return _slugify(f"{desc.name} ({desc.number})")


def _display(desc: Description, val: Value | None) -> str:
    if val is None:
        return "—"
    if desc.name in _REDACTED_VALUE_NAMES:
        return _REDACTED
    if isinstance(val, float) and desc.decimal_places:
        return f"{val:.{desc.decimal_places}f}"
    if isinstance(val, bytes):
        return val.hex()
    return str(val)


def _type_cell(desc: Description, string_list_numbers: set[int]) -> str:
    if desc.number in string_list_numbers:
        return f"[STRING_LIST](#{_anchor(desc)})"
    return desc.data_type.name


async def _gather(
    host: IPv4Address, access_code: str
) -> tuple[
    dict[int, Value],
    dict[int, Value],
    list[ValueDescription],
    list[SetpointDescription],
    list[StringListEntry],
]:
    async with Controller(ComApClient(EthernetTransport(host)), access_code=access_code) as ctrl:
        values = await ctrl.read_values()
        setpoints = await ctrl.read_setpoints()
        value_descs = sorted(ctrl.values, key=lambda d: d.number)
        setpoint_descs = sorted(ctrl.setpoints, key=lambda d: d.number)

        string_lists: list[StringListEntry] = []
        for value_desc in value_descs:
            if value_desc.data_type is DataType.STRING_LIST:
                string_lists.append((value_desc, ctrl.value_options(value_desc.number)))
        for setpoint_desc in setpoint_descs:
            if setpoint_desc.data_type is DataType.STRING_LIST:
                string_lists.append((setpoint_desc, ctrl.setpoint_options(setpoint_desc.number)))

    return values, setpoints, value_descs, setpoint_descs, string_lists


def _render(
    values: dict[int, Value],
    setpoints: dict[int, Value],
    value_descs: list[ValueDescription],
    setpoint_descs: list[SetpointDescription],
    string_lists: list[StringListEntry],
) -> str:
    string_list_numbers = {desc.number for desc, _ in string_lists}

    lines: list[str] = [
        "---",
        "hide:",
        "  - navigation",
        "---",
        "",
        "# ComAp Controller Reference",
        "",
        "## Values",
        "",
        "| # | Category | Group | Name | Type | Unit | Value |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for value_desc in value_descs:
        val = _display(value_desc, values.get(value_desc.number))
        lines.append(
            f"| {value_desc.number} | {value_desc.category.name} | {value_desc.group or ''} | "
            f"{value_desc.name} | {_type_cell(value_desc, string_list_numbers)} | "
            f"{value_desc.dimension} | {val} |"
        )

    lines += [
        "",
        "## Setpoints",
        "",
        "| # | Group | Name | Type | Unit | Min | Max | Password | Value |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for setpoint_desc in setpoint_descs:
        val = _display(setpoint_desc, setpoints.get(setpoint_desc.number))
        lo = "var" if setpoint_desc.var_low_limit else setpoint_desc.low_limit
        hi = "var" if setpoint_desc.var_high_limit else setpoint_desc.high_limit
        password = "yes" if setpoint_desc.needs_password else "no"
        lines.append(
            f"| {setpoint_desc.number} | {setpoint_desc.group or ''} | {setpoint_desc.name} | "
            f"{_type_cell(setpoint_desc, string_list_numbers)} | {setpoint_desc.dimension} | "
            f"{lo} | {hi} | {password} | {val} |"
        )

    lines += [
        "",
        "## String Lists",
        "",
        "Option tables for every `STRING_LIST` value and setpoint above, linked from their "
        "**Type** column. The wire value is the raw 0-based integer used on the wire (e.g. "
        "by [set_setpoint][pycomap.Controller.set_setpoint]); the label is what's shown on "
        "the front panel and in InteliConfig.",
    ]
    for desc, options in string_lists:
        lines += [
            "",
            f"### {desc.name} ({desc.number})",
            "",
            "| Wire Value | Label |",
            "| --- | --- |",
        ]
        lines += [f"| {wire_value} | {label} |" for wire_value, label in options]
    lines.append("")

    return "\n".join(lines)


async def main(host: IPv4Address, access_code: str) -> None:
    values, setpoints, value_descs, setpoint_descs, string_lists = await _gather(host, access_code)
    OUTPUT.write_text(_render(values, setpoints, value_descs, setpoint_descs, string_lists))
    print(
        f"wrote {OUTPUT.relative_to(ROOT)}: {len(value_descs)} values, "
        f"{len(setpoint_descs)} setpoints, {len(string_lists)} string lists"
    )


if __name__ == "__main__":
    load_dotenv()
    parser = configargparse.ArgParser(description=__doc__)
    parser.add_argument("--host", type=IPv4Address, required=True, env_var="PYCOMAP_TEST_HOST")
    parser.add_argument("--access-code", default="0", env_var="PYCOMAP_TEST_ACCESS_CODE")
    args = parser.parse_args()
    asyncio.run(main(args.host, args.access_code))
