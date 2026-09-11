"""CAD-neutral multi-cell occupancy and placement translation.

Definition facts required for placement are supplied by the caller.
This module does not read CubeBlocks XML, search a game install, or
grant runtime support.

Min is the axis-aligned minimum occupied grid cell. Size is local
Right/Up/Back cell occupancy before orientation. Occupied Max is:

    Max = Min + abs(R · (Size − 1))

componentwise. CAD translation is the occupancy-center in millimetres
plus the orientation-rotated Keen ModelOffset (metres → millimetres):

    t = ((Min + Max) / 2) * pitch_mm + R · ModelOffset_mm

Definition Center is not an input and is not CAD translation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from se2cad.catalog.constants import LARGE_GRID_CELL_PITCH_MM
from se2cad.catalog.model import CellSize
from se2cad.parser.model import GridCoordinate
from se2cad.transform.errors import (
    InvalidBlockSizeError,
    InvalidModelOffsetError,
    TransformError,
)
from se2cad.transform.rotation import RotationMatrix
from se2cad.transform.translation import MillimetrePosition

# Keen ModelOffset is a Vector3 in metres (same space as GridIntegerToWorld).
# SE2CAD IR translation is millimetres.
MILLIMETRES_PER_METRE = 1000

_ZERO = Fraction(0)


def _require_positive_cell(value: object, axis: str) -> int:
    if type(value) is not int:
        raise InvalidBlockSizeError(f"Size.{axis} must be an integer >= 1")
    if value < 1:
        raise InvalidBlockSizeError(f"Size.{axis} must be >= 1, got {value}")
    return value


def require_cell_size(size: CellSize) -> CellSize:
    """Reject zero/negative/non-integer Size at the transform boundary."""
    if not isinstance(size, CellSize):
        raise InvalidBlockSizeError("Size must be a CellSize")
    _require_positive_cell(size.x, "x")
    _require_positive_cell(size.y, "y")
    _require_positive_cell(size.z, "z")
    return size


def _metres_component(value: object, axis: str) -> Fraction:
    if isinstance(value, bool) or value is None:
        raise InvalidModelOffsetError(
            f"ModelOffset.{axis} must be an exact metre value"
        )
    if isinstance(value, float):
        raise InvalidModelOffsetError(
            f"ModelOffset.{axis} must be an exact metre value "
            "(int, numeric string, or Fraction), not float"
        )
    if isinstance(value, Fraction):
        return value
    if type(value) is int:
        return Fraction(value)
    if isinstance(value, str):
        text = value.strip()
        if text == "" or text != value:
            raise InvalidModelOffsetError(
                f"ModelOffset.{axis} is not an exact metre value: {value!r}"
            )
        try:
            return Fraction(text)
        except (ValueError, ZeroDivisionError) as exc:
            raise InvalidModelOffsetError(
                f"ModelOffset.{axis} is not an exact metre value: {value!r}"
            ) from exc
    raise InvalidModelOffsetError(
        f"ModelOffset.{axis} must be an exact metre value"
    )


@dataclass(frozen=True)
class ModelOffset:
    """Keen ``ModelOffset`` in metres, local Right/Up/Back before orientation.

    Equivalent to Keen ``TransformNormal(ModelOffset, orientation)``.
    Conversion to millimetres is exact; values that are not integer
    millimetres after rotation fail closed.
    """

    x: Fraction
    y: Fraction
    z: Fraction

    @classmethod
    def zero(cls) -> ModelOffset:
        return cls(_ZERO, _ZERO, _ZERO)

    @classmethod
    def from_metres(
        cls,
        x: int | str | Fraction,
        y: int | str | Fraction,
        z: int | str | Fraction,
    ) -> ModelOffset:
        return cls(
            _metres_component(x, "x"),
            _metres_component(y, "y"),
            _metres_component(z, "z"),
        )

    def as_tuple(self) -> tuple[Fraction, Fraction, Fraction]:
        return (self.x, self.y, self.z)

    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0


@dataclass(frozen=True)
class BlockPlacementDefinition:
    """Definition facts required to compute a CAD-neutral placement.

    This is not a catalog grant and not a support status. Size is local
    Right/Up/Back cell occupancy. ModelOffset is metres. Definition
    Center is intentionally absent: it is pivot/reference metadata, not
    CAD translation.
    """

    size: CellSize
    model_offset: ModelOffset

    def __post_init__(self) -> None:
        require_cell_size(self.size)
        if not isinstance(self.model_offset, ModelOffset):
            raise InvalidModelOffsetError(
                "model_offset must be a ModelOffset value"
            )


# Established 1×1×1 contract: packaged/library-supported identities with
# no ModelOffset metadata, and the designated 1×1×1 filler solid.
# Not a global default for arbitrary unresolved definitions.
QUALIFIED_ONE_BY_ONE_PLACEMENT = BlockPlacementDefinition(
    size=CellSize(1, 1, 1),
    model_offset=ModelOffset.zero(),
)


def placement_from_cell_size(size: CellSize) -> BlockPlacementDefinition:
    """Placement metadata from an already-known Size and explicit zero offset."""
    return BlockPlacementDefinition(size=size, model_offset=ModelOffset.zero())


def occupied_max(
    min_cell: GridCoordinate,
    size: CellSize,
    rotation: RotationMatrix,
) -> GridCoordinate:
    """Axis-aligned maximum occupied cell: Min + abs(R · (Size − 1)).

    Integer input and output. Size axes are rotated first; the
    componentwise absolute value is applied after that mapping.
    """
    require_cell_size(size)
    local_extent = (size.x - 1, size.y - 1, size.z - 1)
    mapped = rotation.apply(local_extent)
    return GridCoordinate(
        x=min_cell.x + abs(mapped[0]),
        y=min_cell.y + abs(mapped[1]),
        z=min_cell.z + abs(mapped[2]),
    )


def occupancy_center_mm(
    min_cell: GridCoordinate,
    max_cell: GridCoordinate,
    pitch_mm: int = LARGE_GRID_CELL_PITCH_MM,
) -> MillimetrePosition:
    """Inclusive AABB center in millimetres. Half-cell centers are kept exact."""
    if type(pitch_mm) is not int or pitch_mm <= 0:
        raise TransformError("pitch_mm must be an integer > 0")
    return MillimetrePosition(
        x=_exact_half_sum_times_pitch(min_cell.x, max_cell.x, pitch_mm, "x"),
        y=_exact_half_sum_times_pitch(min_cell.y, max_cell.y, pitch_mm, "y"),
        z=_exact_half_sum_times_pitch(min_cell.z, max_cell.z, pitch_mm, "z"),
    )


def _exact_half_sum_times_pitch(
    first: int, second: int, pitch_mm: int, axis: str
) -> int:
    numerator = (first + second) * pitch_mm
    if numerator % 2 != 0:
        raise TransformError(
            f"occupancy-center {axis} is not an integer millimetre: "
            f"({first} + {second}) * {pitch_mm} / 2"
        )
    return numerator // 2


def model_offset_translation_mm(
    model_offset: ModelOffset,
    rotation: RotationMatrix,
) -> MillimetrePosition:
    """Rotate ModelOffset (metres) into grid axes and convert to millimetres."""
    if not isinstance(model_offset, ModelOffset):
        raise InvalidModelOffsetError("model_offset must be a ModelOffset value")
    local_mm = (
        model_offset.x * MILLIMETRES_PER_METRE,
        model_offset.y * MILLIMETRES_PER_METRE,
        model_offset.z * MILLIMETRES_PER_METRE,
    )
    rotated = (
        local_mm[0] * rotation.c0[0]
        + local_mm[1] * rotation.c1[0]
        + local_mm[2] * rotation.c2[0],
        local_mm[0] * rotation.c0[1]
        + local_mm[1] * rotation.c1[1]
        + local_mm[2] * rotation.c2[1],
        local_mm[0] * rotation.c0[2]
        + local_mm[1] * rotation.c1[2]
        + local_mm[2] * rotation.c2[2],
    )
    return MillimetrePosition(
        x=_require_integer_mm(rotated[0], "x"),
        y=_require_integer_mm(rotated[1], "y"),
        z=_require_integer_mm(rotated[2], "z"),
    )


def _require_integer_mm(value: Fraction, axis: str) -> int:
    if value.denominator != 1:
        raise InvalidModelOffsetError(
            f"ModelOffset.{axis} is not an integer millimetre after "
            f"conversion and rotation: {value}"
        )
    return int(value)


def placement_translation_mm(
    min_cell: GridCoordinate,
    placement: BlockPlacementDefinition,
    rotation: RotationMatrix,
    pitch_mm: int = LARGE_GRID_CELL_PITCH_MM,
) -> MillimetrePosition:
    """Occupancy-center translation plus one rotated ModelOffset.

    Definition Center is not consulted. ModelOffset is applied once and
    is not scaled by Size.
    """
    if not isinstance(placement, BlockPlacementDefinition):
        raise TransformError("placement must be a BlockPlacementDefinition")
    max_cell = occupied_max(min_cell, placement.size, rotation)
    center = occupancy_center_mm(min_cell, max_cell, pitch_mm)
    offset = model_offset_translation_mm(placement.model_offset, rotation)
    return MillimetrePosition(
        x=center.x + offset.x,
        y=center.y + offset.y,
        z=center.z + offset.z,
    )
