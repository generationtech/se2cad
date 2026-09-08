"""Pack a qualified IR transform into a SolidWorks MathTransform ArrayData.

Official IMathUtility.CreateTransform / IMathTransform.ArrayData layout
(help.solidworks.com, still current for 2026 method pages):

    [0:3]   X-axis of the component in parent space
    [3:6]   Y-axis
    [6:9]   Z-axis
    [9:12]  translation in metres
    [12]    scale
    [13:16] unused

SE2CAD rotation columns are those same axes: local +X/+Y/+Z in world,
which are the axes of the qualified canonical SLDPRT. No transpose, no
corrective rotation, no half-cell offset.

Live SolidWorks 2026 CDispatch (revision 34.3.2) confirmed this packing
by writing ArrayData and reading it back after save/reopen.
"""

from __future__ import annotations

from se2cad.solidworks.units import point_mm_to_metres
from se2cad.transform.rotation import RotationMatrix

SOLIDWORKS_TRANSFORM_SCALE = 1.0


def solidworks_arraydata(
    rotation: RotationMatrix,
    position_mm: tuple[int, int, int],
) -> tuple[float, ...]:
    """Return the 16-double ArrayData for ``(R, t)``.

    ``R`` is the qualified column-vector matrix. ``t`` is millimetres.
    """
    tx, ty, tz = point_mm_to_metres(position_mm)
    c0, c1, c2 = rotation.columns
    return (
        float(c0[0]),
        float(c0[1]),
        float(c0[2]),
        float(c1[0]),
        float(c1[1]),
        float(c1[2]),
        float(c2[0]),
        float(c2[1]),
        float(c2[2]),
        float(tx),
        float(ty),
        float(tz),
        SOLIDWORKS_TRANSFORM_SCALE,
        0.0,
        0.0,
        0.0,
    )


def arraydata_translation_m(data: tuple[float, ...]) -> tuple[float, float, float]:
    return (data[9], data[10], data[11])


def arraydata_axes(
    data: tuple[float, ...],
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    return (
        (data[0], data[1], data[2]),
        (data[3], data[4], data[5]),
        (data[6], data[7], data[8]),
    )
