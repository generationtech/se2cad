"""CAD-neutral placement transforms (S2C-3.1.1).

Consumes parsed Forward/Up tokens and integer Min coordinates plus the
catalog cell-pitch constant. Independent of CAD backends and game-install
scanning.
"""

from se2cad.transform.directions import (
    SE_DIRECTION_VECTORS,
    direction_vector,
    is_valid_orientation,
    legal_orientations,
    same_axis,
)
from se2cad.transform.errors import InvalidOrientationError, TransformError
from se2cad.transform.rotation import (
    IDENTITY_ROTATION,
    RotationMatrix,
    rotation_from_forward_up,
)
from se2cad.transform.translation import MillimetrePosition, cell_center_mm

__all__ = [
    "IDENTITY_ROTATION",
    "SE_DIRECTION_VECTORS",
    "InvalidOrientationError",
    "MillimetrePosition",
    "RotationMatrix",
    "TransformError",
    "cell_center_mm",
    "direction_vector",
    "is_valid_orientation",
    "legal_orientations",
    "rotation_from_forward_up",
    "same_axis",
]
