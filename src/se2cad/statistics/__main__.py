"""Operator entry for CAD-neutral blueprint statistics.

Not a general SE2CAD CLI. Usage: python -m se2cad.statistics <blueprint.sbc>
"""

from __future__ import annotations

import sys

from se2cad.parser import BlueprintParseError
from se2cad.statistics.compute import compute_blueprint_statistics_from_path
from se2cad.statistics.model import (
    BlueprintStatistics,
    NamedCount,
    OrientationCount,
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m se2cad.statistics <blueprint.sbc>")
        return 2
    try:
        stats = compute_blueprint_statistics_from_path(args[0])
    except BlueprintParseError as exc:
        _print_operator_text(str(exc))
        return 2
    _print_operator_text(_format_statistics(stats))
    return 0


def _format_statistics(stats: BlueprintStatistics) -> str:
    lines = [
        f"identity_subtype={_one_line(stats.identity_subtype)}",
        f"display_name={_one_line(stats.display_name)}",
        f"grid_display_name={_one_line(stats.grid_display_name)}",
        f"grid_size={stats.grid_size.value}",
        f"block_count={stats.block_count}",
        f"cell_pitch_mm={stats.cell_pitch_mm}",
        f"subtype_counts={_format_named(stats.subtype_counts)}",
        f"geometry_id_counts={_format_named(stats.geometry_id_counts)}",
        f"orientation_counts={_format_orientations(stats.orientation_counts)}",
        (
            "catalog_coverage="
            f"{stats.catalog_coverage.resolved_blocks}/"
            f"{stats.block_count} resolved"
        ),
        (
            "unresolved_subtype_counts="
            f"{_format_named(stats.catalog_coverage.unresolved_subtype_counts)}"
        ),
        f"unique_min_cells={stats.occupancy.unique_min_cells}",
        f"bounding_box_cells={stats.occupancy.bounding_box_cells}",
        f"occupancy_coverage={_format_coverage(stats)}",
    ]
    if stats.cell_extents is None or stats.millimetre_size is None:
        lines.append("cell_extents=")
        lines.append("millimetre_size=")
    else:
        extents = stats.cell_extents
        size = stats.millimetre_size
        lines.append(
            "cell_extents="
            f"x[{extents.x.minimum}..{extents.x.maximum}] "
            f"y[{extents.y.minimum}..{extents.y.maximum}] "
            f"z[{extents.z.minimum}..{extents.z.maximum}]"
        )
        lines.append(f"millimetre_size={size.x} x {size.y} x {size.z}")
    return "\n".join(lines)


def _format_named(counts: tuple[NamedCount, ...]) -> str:
    if not counts:
        return ""
    return ",".join(f"{item.name}={item.count}" for item in counts)


def _format_orientations(counts: tuple[OrientationCount, ...]) -> str:
    if not counts:
        return ""
    return ",".join(
        f"{item.forward.value}/{item.up.value}={item.count}" for item in counts
    )


def _format_coverage(stats: BlueprintStatistics) -> str:
    coverage = stats.occupancy.coverage
    if coverage is None:
        return ""
    return f"{coverage.numerator}/{coverage.denominator}"


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
