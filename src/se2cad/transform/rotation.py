"""Exact integer rotation from Space Engineers Forward/Up.

Column-vector convention: v_world = R @ v_local.
Columns of R are the world images of the canonical local block axes:

    local +X → block Right
    local +Y → block Up
    local +Z → block Backward  (local -Z → block Forward)

Right is constructed as Forward × Up, matching Keen CreateWorld /
CreateFromForwardUp (Right = Up × Backward = Forward × Up).
"""

from __future__ import annotations

from dataclasses import dataclass

from se2cad.parser.model import Direction
from se2cad.transform.directions import (
    direction_vector,
    is_valid_orientation,
)
from se2cad.transform.errors import InvalidOrientationError


def _cross(
    a: tuple[int, int, int], b: tuple[int, int, int]
) -> tuple[int, int, int]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _neg(a: tuple[int, int, int]) -> tuple[int, int, int]:
    return (-a[0], -a[1], -a[2])


@dataclass(frozen=True)
class RotationMatrix:
    """Orthonormal integer 3×3. Entries are -1, 0, or 1.

    Stored as columns ``c0, c1, c2`` so ``apply((x, y, z))`` is
    ``x*c0 + y*c1 + z*c2``.
    """

    c0: tuple[int, int, int]
    c1: tuple[int, int, int]
    c2: tuple[int, int, int]

    @property
    def columns(self) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        return (self.c0, self.c1, self.c2)

    @property
    def rows(self) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        return (
            (self.c0[0], self.c1[0], self.c2[0]),
            (self.c0[1], self.c1[1], self.c2[1]),
            (self.c0[2], self.c1[2], self.c2[2]),
        )

    @property
    def right(self) -> tuple[int, int, int]:
        return self.c0

    @property
    def up(self) -> tuple[int, int, int]:
        return self.c1

    @property
    def backward(self) -> tuple[int, int, int]:
        return self.c2

    @property
    def forward(self) -> tuple[int, int, int]:
        return _neg(self.c2)

    def apply(self, vector: tuple[int, int, int]) -> tuple[int, int, int]:
        """Rotate a column vector by this matrix. Exact integer arithmetic."""
        x, y, z = vector
        return (
            x * self.c0[0] + y * self.c1[0] + z * self.c2[0],
            x * self.c0[1] + y * self.c1[1] + z * self.c2[1],
            x * self.c0[2] + y * self.c1[2] + z * self.c2[2],
        )

    def determinant(self) -> int:
        return _dot(self.c0, _cross(self.c1, self.c2))

    def is_identity(self) -> bool:
        return self.columns == ((1, 0, 0), (0, 1, 0), (0, 0, 1))

    def is_orthonormal(self) -> bool:
        cols = (self.c0, self.c1, self.c2)
        if any(_dot(col, col) != 1 for col in cols):
            return False
        if _dot(self.c0, self.c1) != 0:
            return False
        if _dot(self.c0, self.c2) != 0:
            return False
        if _dot(self.c1, self.c2) != 0:
            return False
        return True


IDENTITY_ROTATION = RotationMatrix((1, 0, 0), (0, 1, 0), (0, 0, 1))


def rotation_from_forward_up(forward: Direction, up: Direction) -> RotationMatrix:
    """Build the unique SE2CAD rotation for a valid Forward/Up pair.

    Invalid same-axis or opposite-axis pairs fail closed.
    """
    if not is_valid_orientation(forward, up):
        raise InvalidOrientationError(
            f"Forward={forward.value!r} Up={up.value!r} are not orthogonal"
        )
    forward_vec = direction_vector(forward)
    up_vec = direction_vector(up)
    right_vec = _cross(forward_vec, up_vec)
    backward_vec = _neg(forward_vec)
    rotation = RotationMatrix(right_vec, up_vec, backward_vec)
    if not rotation.is_orthonormal() or rotation.determinant() != 1:
        raise InvalidOrientationError(
            f"Forward={forward.value!r} Up={up.value!r} did not produce a "
            "right-handed orthonormal rotation"
        )
    return rotation
