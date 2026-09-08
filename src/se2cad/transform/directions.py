"""Proven Space Engineers Base6Directions vectors.

These integer vectors are Space Engineers facts established from current
local assemblies plus Keen published source. They are not SE2CAD inventions.
The architecture contract records the evidence trail.
"""

from __future__ import annotations

from se2cad.parser.model import Direction

# Space Engineers world/grid axes, millimetre-independent unit vectors.
# Forward is -Z, Right is +X, Up is +Y. Right-handed: Right × Up = Backward.
SE_DIRECTION_VECTORS: dict[Direction, tuple[int, int, int]] = {
    Direction.FORWARD: (0, 0, -1),
    Direction.BACKWARD: (0, 0, 1),
    Direction.LEFT: (-1, 0, 0),
    Direction.RIGHT: (1, 0, 0),
    Direction.UP: (0, 1, 0),
    Direction.DOWN: (0, -1, 0),
}

_AXIS = {
    Direction.FORWARD: "forward_backward",
    Direction.BACKWARD: "forward_backward",
    Direction.LEFT: "left_right",
    Direction.RIGHT: "left_right",
    Direction.UP: "up_down",
    Direction.DOWN: "up_down",
}


def direction_vector(direction: Direction) -> tuple[int, int, int]:
    """Return the proven SE unit vector for a Base6Directions token."""
    return SE_DIRECTION_VECTORS[direction]


def same_axis(first: Direction, second: Direction) -> bool:
    return _AXIS[first] == _AXIS[second]


def is_valid_orientation(forward: Direction, up: Direction) -> bool:
    """True iff Forward and Up are orthogonal Base6Directions (24 legal pairs)."""
    return not same_axis(forward, up)


def legal_orientations() -> tuple[tuple[Direction, Direction], ...]:
    """All 24 valid Space Engineers Forward/Up pairs, deterministic order."""
    directions = tuple(Direction)
    return tuple(
        (forward, up)
        for forward in directions
        for up in directions
        if is_valid_orientation(forward, up)
    )
