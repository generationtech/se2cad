"""Operator entry for CAD-neutral conversion policy.

Not a general SE2CAD CLI.
Usage: python -m se2cad.policy <blueprint.sbc> [--policy strict|permissive]

Default policy is strict. Exit 0 means conversion produced an IR.
Exit 2 means usage, parse, or strict refusal.
"""

from __future__ import annotations

import sys

from se2cad.parser import BlueprintParseError
from se2cad.policy.convert import convert_blueprint_from_path
from se2cad.policy.errors import ConversionRefusedError
from se2cad.policy.model import ConversionPolicy, ConversionResult
from se2cad.preflight.model import BlockPreflight, ConversionPreflight
from se2cad.statistics.model import NamedCount


def main(argv: list[str] | None = None) -> int:
    parsed_args = _parse_argv(sys.argv[1:] if argv is None else argv)
    if parsed_args is None:
        return 2
    path, policy = parsed_args
    try:
        result = convert_blueprint_from_path(path, policy=policy)
    except BlueprintParseError as exc:
        _print_operator_text(str(exc))
        return 2
    except ConversionRefusedError as exc:
        _print_operator_text(_format_refusal(exc.preflight, policy))
        return 2
    _print_operator_text(_format_success(result))
    return 0


def _parse_argv(argv: list[str]) -> tuple[str, ConversionPolicy] | None:
    usage = "usage: python -m se2cad.policy <blueprint.sbc> [--policy strict|permissive]"
    if not argv or argv[0].startswith("-"):
        _print_operator_text(usage)
        return None
    path = argv[0]
    policy = ConversionPolicy.STRICT
    rest = argv[1:]
    if not rest:
        return path, policy
    if rest == ["--policy", ConversionPolicy.STRICT.value]:
        return path, ConversionPolicy.STRICT
    if rest == ["--policy", ConversionPolicy.PERMISSIVE.value]:
        return path, ConversionPolicy.PERMISSIVE
    _print_operator_text(usage)
    return None


def _format_success(result: ConversionResult) -> str:
    report = result.preflight
    lines = _preflight_lines(report)
    lines.extend(
        [
            f"policy={result.policy.value}",
            f"filler_count={result.filler_count}",
            f"ir_block_count={result.ir.grid.block_count}",
            "conversion_performed=true",
        ]
    )
    for block in result.ir.grid.blocks:
        lines.append(
            f"ir {block.source_index} {block.subtype_id} "
            f"geometry_id={block.geometry_id} "
            f"support_status={block.support_status.value}"
        )
    return "\n".join(lines)


def _format_refusal(report: ConversionPreflight, policy: ConversionPolicy) -> str:
    lines = _preflight_lines(report)
    lines.extend(
        [
            f"policy={policy.value}",
            "filler_count=0",
            "conversion_performed=false",
        ]
    )
    return "\n".join(lines)


def _preflight_lines(report: ConversionPreflight) -> list[str]:
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
    ]
    for block in report.blocks:
        lines.append(_format_block(block))
    return lines


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
