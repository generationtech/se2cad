"""Compute CAD-neutral statistics from a parsed blueprint and catalog."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional

from se2cad.catalog import DefinitionCatalog, UnknownSubtypeError, load_default_catalog
from se2cad.parser import parse_blueprint, parse_blueprint_xml
from se2cad.parser.model import Direction, GridCoordinate, ParsedBlueprint
from se2cad.statistics.model import (
    AxisRange,
    BlueprintStatistics,
    CatalogCoverage,
    CellExtents,
    MillimetreSize,
    NamedCount,
    Occupancy,
    OrientationCount,
)


def compute_blueprint_statistics(
    parsed: ParsedBlueprint,
    catalog: DefinitionCatalog,
) -> BlueprintStatistics:
    """Derive deterministic counts and extents. Do not drop blocks."""
    pitch_mm = catalog.large_grid_cell_pitch_mm
    subtype_counter: Counter[str] = Counter()
    geometry_counter: Counter[str] = Counter()
    orientation_counter: Counter[tuple[Direction, Direction]] = Counter()
    unresolved_counter: Counter[str] = Counter()
    unique_mins: set[tuple[int, int, int]] = set()
    resolved_blocks = 0

    for block in parsed.grid.blocks:
        subtype_counter[block.subtype_id] += 1
        orientation_counter[(block.forward, block.up)] += 1
        unique_mins.add(_min_tuple(block.min))
        try:
            entry = catalog.lookup(block.subtype_id)
        except UnknownSubtypeError:
            unresolved_counter[block.subtype_id] += 1
            continue
        geometry_counter[entry.geometry_id] += 1
        resolved_blocks += 1

    block_count = len(parsed.grid.blocks)
    extents = _extents_from_mins(unique_mins)
    millimetre_size = None
    bounding_box_cells = 0
    if extents is not None:
        bounding_box_cells = extents.bounding_box_cells
        millimetre_size = MillimetreSize(
            x=extents.x.span_cells * pitch_mm,
            y=extents.y.span_cells * pitch_mm,
            z=extents.z.span_cells * pitch_mm,
        )

    return BlueprintStatistics(
        identity_subtype=parsed.identity_subtype,
        display_name=parsed.display_name,
        grid_display_name=parsed.grid.display_name,
        grid_size=parsed.grid.grid_size,
        block_count=block_count,
        subtype_counts=_named_counts(subtype_counter),
        geometry_id_counts=_named_counts(geometry_counter),
        cell_extents=extents,
        millimetre_size=millimetre_size,
        occupancy=Occupancy(
            unique_min_cells=len(unique_mins),
            bounding_box_cells=bounding_box_cells,
        ),
        orientation_counts=_orientation_counts(orientation_counter),
        catalog_coverage=CatalogCoverage(
            resolved_blocks=resolved_blocks,
            unresolved_blocks=block_count - resolved_blocks,
            unresolved_subtype_counts=_named_counts(unresolved_counter),
        ),
        cell_pitch_mm=pitch_mm,
    )


def compute_blueprint_statistics_from_path(
    path: str | Path,
    catalog: Optional[DefinitionCatalog] = None,
) -> BlueprintStatistics:
    """Parse an operator-selected blueprint and compute statistics."""
    parsed = parse_blueprint(path)
    return compute_blueprint_statistics(parsed, catalog or load_default_catalog())


def compute_blueprint_statistics_from_xml(
    xml_text: str,
    catalog: Optional[DefinitionCatalog] = None,
    *,
    source: str = "<xml>",
) -> BlueprintStatistics:
    """Parse already-loaded XML and compute statistics."""
    parsed = parse_blueprint_xml(xml_text, source=source)
    return compute_blueprint_statistics(parsed, catalog or load_default_catalog())


def _min_tuple(coordinate: GridCoordinate) -> tuple[int, int, int]:
    return (coordinate.x, coordinate.y, coordinate.z)


def _extents_from_mins(
    unique_mins: set[tuple[int, int, int]],
) -> Optional[CellExtents]:
    if not unique_mins:
        return None
    xs = [cell[0] for cell in unique_mins]
    ys = [cell[1] for cell in unique_mins]
    zs = [cell[2] for cell in unique_mins]
    return CellExtents(
        x=AxisRange(minimum=min(xs), maximum=max(xs)),
        y=AxisRange(minimum=min(ys), maximum=max(ys)),
        z=AxisRange(minimum=min(zs), maximum=max(zs)),
    )


def _named_counts(counter: Counter[str]) -> tuple[NamedCount, ...]:
    return tuple(
        NamedCount(name=name, count=counter[name]) for name in sorted(counter)
    )


def _orientation_counts(
    counter: Counter[tuple[Direction, Direction]],
) -> tuple[OrientationCount, ...]:
    return tuple(
        OrientationCount(forward=forward, up=up, count=counter[(forward, up)])
        for forward, up in sorted(
            counter, key=lambda pair: (pair[0].value, pair[1].value)
        )
    )
