"""Integer grid-cell to millimetre translation.

``cell_center_mm`` remains the qualified 1×1×1 Min-cell mapping.
Multi-cell occupancy-center translation lives in
``se2cad.transform.placement`` and is exactly this function when
Size is 1×1×1 and ModelOffset is zero.
"""

from __future__ import annotations

from dataclasses import dataclass

from se2cad.catalog.constants import LARGE_GRID_CELL_PITCH_MM
from se2cad.parser.model import GridCoordinate


@dataclass(frozen=True)
class MillimetrePosition:
    """Physical position in millimetres, SE2CAD grid/world frame."""

    x: int
    y: int
    z: int

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)


def cell_center_mm(
    coordinate: GridCoordinate,
    pitch_mm: int = LARGE_GRID_CELL_PITCH_MM,
) -> MillimetrePosition:
    """Map a 1×1×1 block Min cell to its canonical cell-center position.

    Space Engineers ``GridIntegerToWorld`` multiplies the integer cell by
    grid pitch with no half-cell offset. The cell at Min=(0,0,0) is
    centered at the grid origin. Orientation does not change this anchor
    for these 1×1×1 blocks.
    """
    return MillimetrePosition(
        x=coordinate.x * pitch_mm,
        y=coordinate.y * pitch_mm,
        z=coordinate.z * pitch_mm,
    )
