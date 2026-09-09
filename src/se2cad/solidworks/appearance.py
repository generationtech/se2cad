"""Convert CAD-neutral ColorMaskHSV to a SolidWorks instance RGB.

Parser and IR keep Keen HSV-offset. This module is the SolidWorks-package
conversion: ``MyColorPickerConstants.HSVOffsetToHSV`` deltas, then
standard HSV-to-RGB. It does not import COM.

Published mapping (S2C-9.2.1): official Space Engineers wiki Data Types
cites ``HSVOffsetToHSV`` / ``HSVToHSVOffset`` as saturation minus 0.8
and value minus 0.45 (add those deltas to recover display HSV). Current
ModAPI still lists those methods on ``MyColorPickerConstants``. Display
S/V are clamped to ``[0, 1]`` so the omitted default ``(0, -1, 0)``
becomes S=0, V=0.45 (medium gray), not a invented white.
"""

from __future__ import annotations

from se2cad.parser.model import ColorMaskHSV

# MyColorPickerConstants.SATURATION_DELTA / VALUE_DELTA as published
# by the official wiki citing HSVOffsetToHSV (HSV = offset + delta).
SATURATION_DELTA = 0.8
VALUE_DELTA = 0.45

# Live SolidWorks 2026 CDispatch (revision 34.3.2) stores component
# MaterialPropertyValues RGB as 8-bit channels: written 0.45 is read
# back as 114/255. One LSB is the comparison allowance.
APPEARANCE_RGB_TOLERANCE = 1.0 / 255.0

# IComponent2.MaterialPropertyValues lighting extras. RGB identity is
# [0:3]; these do not encode Space Engineers color.
_AMBIENT = 1.0
_DIFFUSE = 1.0
_SPECULAR = 0.5
_SHININESS = 0.4
_TRANSPARENCY = 0.0
_EMISSION = 0.0


def wrap_unit_interval(value: float) -> float:
    """Wrap hue into [0, 1)."""
    return value - (value // 1.0)


def clamp_unit_interval(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def hsv_offset_to_hsv(color: ColorMaskHSV) -> tuple[float, float, float]:
    """Keen ``HSVOffsetToHSV``: H unchanged, S/V plus the published deltas."""
    return (
        wrap_unit_interval(float(color.h)),
        clamp_unit_interval(float(color.s) + SATURATION_DELTA),
        clamp_unit_interval(float(color.v) + VALUE_DELTA),
    )


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    """Standard HSV-to-RGB with H, S, V in ``[0, 1]``.

    Matches the ``ColorExtensions.HSVtoColor`` 0–1 hue contract used
    after ``HSVOffsetToHSV``.
    """
    if s <= 0.0:
        return (v, v, v)
    sector = h * 6.0
    index = int(sector)
    frac = sector - index
    p = v * (1.0 - s)
    q = v * (1.0 - frac * s)
    t = v * (1.0 - (1.0 - frac) * s)
    remainder = index % 6
    if remainder == 0:
        return (v, t, p)
    if remainder == 1:
        return (q, v, p)
    if remainder == 2:
        return (p, v, t)
    if remainder == 3:
        return (p, q, v)
    if remainder == 4:
        return (t, p, v)
    return (v, p, q)


def color_mask_hsv_to_rgb(color: ColorMaskHSV) -> tuple[float, float, float]:
    """Backend RGB in ``[0, 1]`` from one IR ``ColorMaskHSV``."""
    return hsv_to_rgb(*hsv_offset_to_hsv(color))


def quantize_rgb_8bit(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Match live 34.3.2 MaterialPropertyValues 8-bit truncation."""
    return tuple(int(clamp_unit_interval(channel) * 255.0) / 255.0 for channel in rgb)


def material_property_values(
    rgb: tuple[float, float, float],
) -> tuple[float, ...]:
    """Nine-double ``IComponent2.MaterialPropertyValues`` payload."""
    red, green, blue = quantize_rgb_8bit(rgb)
    return (
        float(red),
        float(green),
        float(blue),
        _AMBIENT,
        _DIFFUSE,
        _SPECULAR,
        _SHININESS,
        _TRANSPARENCY,
        _EMISSION,
    )


def rgb_close(
    observed: tuple[float, float, float],
    expected: tuple[float, float, float],
) -> bool:
    return all(
        abs(a - b) <= APPEARANCE_RGB_TOLERANCE
        for a, b in zip(observed, expected, strict=True)
    )
