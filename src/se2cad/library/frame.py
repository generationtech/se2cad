"""Canonical local block frame used by native armor recipes.

This module consumes the qualified S2C-3.1.1 contract. It does not define
a second coordinate system. Axes, origin, units, and handedness are the
same values the transform engine already uses.
"""

from __future__ import annotations

from dataclasses import dataclass

from se2cad.catalog.constants import LARGE_GRID_CELL_PITCH_MM
from se2cad.parser.model import Direction
from se2cad.transform.directions import SE_DIRECTION_VECTORS


def cell_half_extent_mm() -> int:
    """Half of the Large Grid cell pitch, in millimetres.

    CubeTopology corner signs are ±1 about the cell center. Scaling those
    signs by this half-extent places vertices on the cell envelope.
    """
    if LARGE_GRID_CELL_PITCH_MM % 2 != 0:
        raise ValueError(
            "LARGE_GRID_CELL_PITCH_MM must be even so the cell half-extent "
            "is an integer millimetre value"
        )
    return LARGE_GRID_CELL_PITCH_MM // 2


@dataclass(frozen=True)
class AxisAlignedBoxMm:
    """Inclusive integer millimetre axis-aligned box."""

    min_mm: tuple[int, int, int]
    max_mm: tuple[int, int, int]

    def contains(self, point_mm: tuple[int, int, int]) -> bool:
        return all(
            self.min_mm[i] <= point_mm[i] <= self.max_mm[i] for i in range(3)
        )


@dataclass(frozen=True)
class CanonicalLocalFrame:
    """Library-side view of the qualified SE2CAD local block frame.

    +X is block Right, +Y is block Up, +Z is block Backward. The origin is
    the 1×1×1 cell center. Units are millimetres. Identity Forward/Up is
    the identity rotation.
    """

    plus_x: tuple[int, int, int]
    plus_y: tuple[int, int, int]
    plus_z: tuple[int, int, int]
    plus_x_meaning: str
    plus_y_meaning: str
    plus_z_meaning: str
    origin_meaning: str
    units: str
    half_extent_mm: int
    envelope: AxisAlignedBoxMm


def _build_canonical_local_frame() -> CanonicalLocalFrame:
    half = cell_half_extent_mm()
    return CanonicalLocalFrame(
        plus_x=SE_DIRECTION_VECTORS[Direction.RIGHT],
        plus_y=SE_DIRECTION_VECTORS[Direction.UP],
        plus_z=SE_DIRECTION_VECTORS[Direction.BACKWARD],
        plus_x_meaning="Right",
        plus_y_meaning="Up",
        plus_z_meaning="Backward",
        origin_meaning="cell_center",
        units="millimetre",
        half_extent_mm=half,
        envelope=AxisAlignedBoxMm(
            min_mm=(-half, -half, -half),
            max_mm=(half, half, half),
        ),
    )


CANONICAL_LOCAL_FRAME = _build_canonical_local_frame()
CANONICAL_CELL_ENVELOPE = CANONICAL_LOCAL_FRAME.envelope
