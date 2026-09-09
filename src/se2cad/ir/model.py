"""CAD-neutral canonical intermediate representation.

Placement types come from the transform engine. This module holds only
immutable domain values: identities, grid coordinates, millimetre
positions, and integer rotations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from se2cad.catalog.model import RecipeKind, SupportStatus
from se2cad.parser.model import (
    AppearanceSupport,
    ColorMaskHSV,
    Direction,
    GridCoordinate,
    GridSize,
)
from se2cad.transform.rotation import RotationMatrix
from se2cad.transform.translation import MillimetrePosition


@dataclass(frozen=True)
class CanonicalBlock:
    """One catalog-resolved block with an exact canonical placement."""

    subtype_id: str
    geometry_id: str
    recipe_kind: RecipeKind
    support_status: SupportStatus
    grid_min: GridCoordinate
    min_serialized: bool
    forward: Direction
    up: Direction
    orientation_serialized: bool
    color_mask_hsv: ColorMaskHSV
    color_serialized: bool
    appearance_support: AppearanceSupport
    position_mm: MillimetrePosition
    rotation: RotationMatrix
    source_index: int
    source: str


@dataclass(frozen=True)
class CanonicalGrid:
    display_name: Optional[str]
    grid_size: GridSize
    blocks: tuple[CanonicalBlock, ...]

    @property
    def block_count(self) -> int:
        return len(self.blocks)


@dataclass(frozen=True)
class CanonicalBlueprint:
    identity_subtype: Optional[str]
    display_name: Optional[str]
    grid: CanonicalGrid
