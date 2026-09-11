"""CAD-neutral placement transforms (S2C-3.1.1 / S2C-11.10.1).

Consumes parsed Forward/Up tokens, integer Min coordinates, optional
Size/ModelOffset placement metadata, and the catalog cell-pitch
constant. Independent of CAD backends and game-install scanning.
"""

from se2cad.transform.directions import (
    SE_DIRECTION_VECTORS,
    direction_vector,
    is_valid_orientation,
    legal_orientations,
    same_axis,
)
from se2cad.transform.errors import (
    InvalidBlockSizeError,
    InvalidModelOffsetError,
    InvalidOrientationError,
    TransformError,
)
from se2cad.transform.placement import (
    MILLIMETRES_PER_METRE,
    QUALIFIED_ONE_BY_ONE_PLACEMENT,
    BlockPlacementDefinition,
    ModelOffset,
    model_offset_translation_mm,
    occupied_max,
    occupancy_center_mm,
    placement_from_cell_size,
    placement_translation_mm,
)
from se2cad.transform.rotation import (
    IDENTITY_ROTATION,
    RotationMatrix,
    rotation_from_forward_up,
)
from se2cad.transform.translation import MillimetrePosition, cell_center_mm

__all__ = [
    "IDENTITY_ROTATION",
    "MILLIMETRES_PER_METRE",
    "QUALIFIED_ONE_BY_ONE_PLACEMENT",
    "SE_DIRECTION_VECTORS",
    "BlockPlacementDefinition",
    "InvalidBlockSizeError",
    "InvalidModelOffsetError",
    "InvalidOrientationError",
    "MillimetrePosition",
    "ModelOffset",
    "RotationMatrix",
    "TransformError",
    "cell_center_mm",
    "direction_vector",
    "is_valid_orientation",
    "legal_orientations",
    "model_offset_translation_mm",
    "occupied_max",
    "occupancy_center_mm",
    "placement_from_cell_size",
    "placement_translation_mm",
    "rotation_from_forward_up",
    "same_axis",
]
