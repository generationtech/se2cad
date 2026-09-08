"""Backend-local millimetre to metre conversion.

SolidWorks COM geometry methods take metres. SE2CAD recipes are millimetres.
This conversion is explicit and local to the SolidWorks backend. It does not
change the qualified canonical frame.

S2C-6.1.1 compares SolidWorks ``ArrayData`` to the packed IR using
``BACKEND_LENGTH_TOLERANCE_M``. IR ``(R, t)`` itself remains exact integers.
"""

from __future__ import annotations

MM_PER_METRE = 1000

# Smallest local API floating-point allowance used when SolidWorks returns
# doubles. 1 micrometre. Not a global numeric-tolerance policy.
BACKEND_LENGTH_TOLERANCE_M = 1e-6


def mm_to_metres(value_mm: int | float) -> float:
    """Convert a millimetre length to metres."""
    return float(value_mm) / MM_PER_METRE


def metres_to_mm(value_m: float) -> float:
    """Convert a metre length to millimetres."""
    return float(value_m) * MM_PER_METRE


def point_mm_to_metres(
    point_mm: tuple[int, int, int],
) -> tuple[float, float, float]:
    """Convert a millimetre point to metres, coordinate-wise."""
    return (
        mm_to_metres(point_mm[0]),
        mm_to_metres(point_mm[1]),
        mm_to_metres(point_mm[2]),
    )


def volume_mm3_to_m3(volume_mm3: float) -> float:
    """Convert cubic millimetres to cubic metres."""
    return float(volume_mm3) / (MM_PER_METRE**3)


def recipe_volume_m3(volume_times_6_mm3: int) -> float:
    """Convert the qualified integer 6×volume (mm³) to cubic metres."""
    return volume_mm3_to_m3(volume_times_6_mm3 / 6.0)


def volume_tolerance_m3(extent_m: float) -> float:
    """Linear-error volume allowance for a cube of the given extent."""
    return 3.0 * extent_m * extent_m * BACKEND_LENGTH_TOLERANCE_M
