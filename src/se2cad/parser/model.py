"""CAD-neutral parsed representation of a single-grid Large Grid blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GridSize(str, Enum):
    LARGE = "Large"


class Direction(str, Enum):
    """Space Engineers Base6Directions.Direction tokens, stored exactly."""

    FORWARD = "Forward"
    BACKWARD = "Backward"
    LEFT = "Left"
    RIGHT = "Right"
    UP = "Up"
    DOWN = "Down"


class AppearanceSupport(str, Enum):
    """Independently reportable from catalog geometry ``SupportStatus``.

    ``DEFAULT`` is the evidenced omitted ``ColorMaskHSV`` mapping.
    ``EXPLICIT`` is a serialized ``ColorMaskHSV`` payload. Unknown
    appearance is not a current parser state.
    """

    DEFAULT = "default"
    EXPLICIT = "explicit"


@dataclass(frozen=True)
class GridCoordinate:
    x: int
    y: int
    z: int


@dataclass(frozen=True)
class ColorMaskHSV:
    """Keen ``ColorMaskHSV`` HSV-offset vector from blueprint XML ``x``/``y``/``z``.

    This is per-instance Space Engineers color, not RGB and not a
    geometry identity. ``h`` is XML ``x`` (hue). ``s`` is XML ``y``
    (saturation-offset). ``v`` is XML ``z`` (value-offset).
    """

    h: float
    s: float
    v: float

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.h, self.s, self.v)


# XmlSerializer omits ColorMaskHSV when it equals SerializableVector3(0, -1, 0).
DEFAULT_COLOR_MASK_HSV = ColorMaskHSV(0.0, -1.0, 0.0)


@dataclass(frozen=True)
class ParsedBlock:
    subtype_id: str
    min: GridCoordinate
    min_serialized: bool
    forward: Direction
    up: Direction
    orientation_serialized: bool
    color_mask_hsv: ColorMaskHSV
    color_serialized: bool
    appearance_support: AppearanceSupport
    source_index: int
    source: str


@dataclass(frozen=True)
class ParsedGrid:
    display_name: Optional[str]
    grid_size: GridSize
    blocks: tuple[ParsedBlock, ...]

    @property
    def block_count(self) -> int:
        return len(self.blocks)


@dataclass(frozen=True)
class ParsedBlueprint:
    identity_subtype: Optional[str]
    display_name: Optional[str]
    grid: ParsedGrid
