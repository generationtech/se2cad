"""Operator entry for CAD-neutral conversion preflight.

Not a general SE2CAD CLI. Usage: python -m se2cad.preflight <blueprint.sbc>

Exit 0 means a report was produced. That is not conversion success.
"""

from __future__ import annotations

import sys

from se2cad.parser import BlueprintParseError
from se2cad.preflight.compute import compute_conversion_preflight_from_path
from se2cad.preflight.model import BlockPreflight, ConversionPreflight
from se2cad.statistics.model import NamedCount


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m se2cad.preflight <blueprint.sbc>")
        return 2
    try:
        report = compute_conversion_preflight_from_path(args[0])
    except BlueprintParseError as exc:
        _print_operator_text(str(exc))
        return 2
    _print_operator_text(_format_preflight(report))
    return 0


def _format_preflight(report: ConversionPreflight) -> str:
    lines = [
        f"identity_subtype={_one_line(report.identity_subtype)}",
        f"display_name={_one_line(report.display_name)}",
        f"grid_display_name={_one_line(report.grid_display_name)}",
        f"grid_size={report.grid_size.value}",
        f"block_count={report.block_count}",
        f"supported_count={report.supported_count}",
        f"unsupported_count={report.unsupported_count}",
        f"unknown_count={report.unknown_count}",
        (
            "unknown_subtype_counts="
            f"{_format_named(report.unknown_subtype_counts)}"
        ),
        (
            "unsupported_subtype_counts="
            f"{_format_named(report.unsupported_subtype_counts)}"
        ),
        f"all_supported={_format_bool(report.all_supported)}",
        "conversion_performed=false",
    ]
    for block in report.blocks:
        lines.append(_format_block(block))
    return "\n".join(lines)


def _format_block(block: BlockPreflight) -> str:
    geometry_id = block.geometry_id if block.geometry_id is not None else ""
    geometry_support = (
        block.geometry_support.value if block.geometry_support is not None else ""
    )
    minimum = block.grid_min
    return (
        f"block {block.source_index} {block.subtype_id} "
        f"min={minimum.x},{minimum.y},{minimum.z} "
        f"catalog_outcome={block.catalog_outcome.value} "
        f"geometry_id={geometry_id} "
        f"geometry_support={geometry_support} "
        f"appearance_support={block.appearance_support.value}"
    )


def _format_named(counts: tuple[NamedCount, ...]) -> str:
    if not counts:
        return ""
    return ",".join(f"{item.name}={item.count}" for item in counts)


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def _one_line(value: str | None) -> str:
    if value is None:
        return ""
    return value.replace("\r", " ").replace("\n", " ")


def _print_operator_text(text: str) -> None:
    """Write text the operator console can encode. Keep the structured result Unicode."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe = text.encode(encoding, errors="backslashreplace").decode(encoding)
    print(safe)


if __name__ == "__main__":
    raise SystemExit(main())
