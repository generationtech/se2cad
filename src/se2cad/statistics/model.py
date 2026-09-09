"""CAD-neutral blueprint and conversion statistics values.

These types hold derived counts and extents. They do not invent a second
identity system: subtype, geometry, grid size, and pitch come from the
parser and catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

from se2cad.parser.model import Direction, GridSize


@dataclass(frozen=True)
class NamedCount:
    name: str
    count: int


@dataclass(frozen=True)
class OrientationCount:
    forward: Direction
    up: Direction
    count: int


@dataclass(frozen=True)
class AxisRange:
    """Inclusive integer cell range on one axis."""

    minimum: int
    maximum: int

    @property
    def span_cells(self) -> int:
        return self.maximum - self.minimum + 1


@dataclass(frozen=True)
class CellExtents:
    x: AxisRange
    y: AxisRange
    z: AxisRange

    @property
    def bounding_box_cells(self) -> int:
        return self.x.span_cells * self.y.span_cells * self.z.span_cells


@dataclass(frozen=True)
class MillimetreSize:
    """Axis-aligned occupied-cell envelope size, millimetres."""

    x: int
    y: int
    z: int


@dataclass(frozen=True)
class Occupancy:
    """Coverage of unique ``Min`` cells inside the inclusive cell AABB."""

    unique_min_cells: int
    bounding_box_cells: int

    @property
    def coverage(self) -> Optional[Fraction]:
        if self.bounding_box_cells == 0:
            return None
        return Fraction(self.unique_min_cells, self.bounding_box_cells)


@dataclass(frozen=True)
class CatalogCoverage:
    """How many parsed blocks resolve to a catalog geometry identity."""

    resolved_blocks: int
    unresolved_blocks: int
    unresolved_subtype_counts: tuple[NamedCount, ...]


@dataclass(frozen=True)
class BlueprintStatistics:
    """Deterministic summary of one parsed single-grid blueprint."""

    identity_subtype: Optional[str]
    display_name: Optional[str]
    grid_display_name: Optional[str]
    grid_size: GridSize
    block_count: int
    subtype_counts: tuple[NamedCount, ...]
    geometry_id_counts: tuple[NamedCount, ...]
    cell_extents: Optional[CellExtents]
    millimetre_size: Optional[MillimetreSize]
    occupancy: Occupancy
    orientation_counts: tuple[OrientationCount, ...]
    catalog_coverage: CatalogCoverage
    cell_pitch_mm: int
