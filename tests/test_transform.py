"""Deterministic tests for Space Engineers placement transforms."""

from __future__ import annotations

import unittest
from pathlib import Path

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM
from se2cad.parser.model import Direction, GridCoordinate
from se2cad.transform import (
    IDENTITY_ROTATION,
    SE_DIRECTION_VECTORS,
    InvalidOrientationError,
    cell_center_mm,
    direction_vector,
    is_valid_orientation,
    legal_orientations,
    rotation_from_forward_up,
    same_axis,
)

# Keen Base6Directions.LeftDirections[forward * 6 + up] for the 24 valid pairs.
# Local VRage.Math.dll still stores this exact 36-entry table.
_KEEN_LEFT_TABLE = (
    Direction.FORWARD,
    Direction.FORWARD,
    Direction.DOWN,
    Direction.UP,
    Direction.LEFT,
    Direction.RIGHT,
    Direction.FORWARD,
    Direction.FORWARD,
    Direction.UP,
    Direction.DOWN,
    Direction.RIGHT,
    Direction.LEFT,
    Direction.UP,
    Direction.DOWN,
    Direction.LEFT,
    Direction.LEFT,
    Direction.BACKWARD,
    Direction.FORWARD,
    Direction.DOWN,
    Direction.UP,
    Direction.LEFT,
    Direction.LEFT,
    Direction.FORWARD,
    Direction.BACKWARD,
    Direction.RIGHT,
    Direction.LEFT,
    Direction.FORWARD,
    Direction.BACKWARD,
    Direction.LEFT,
    Direction.RIGHT,
    Direction.LEFT,
    Direction.RIGHT,
    Direction.BACKWARD,
    Direction.FORWARD,
    Direction.LEFT,
    Direction.RIGHT,
)

_DIRECTION_INDEX = {
    Direction.FORWARD: 0,
    Direction.BACKWARD: 1,
    Direction.LEFT: 2,
    Direction.RIGHT: 3,
    Direction.UP: 4,
    Direction.DOWN: 5,
}

_VECTOR_TO_DIRECTION = {vector: token for token, vector in SE_DIRECTION_VECTORS.items()}

_FIXTURE_ORIENTATIONS = (
    (Direction.FORWARD, Direction.UP),
    (Direction.DOWN, Direction.FORWARD),
    (Direction.DOWN, Direction.RIGHT),
    (Direction.FORWARD, Direction.RIGHT),
    (Direction.DOWN, Direction.LEFT),
    (Direction.BACKWARD, Direction.DOWN),
)

# Hand-computed columns (Right, Up, Backward) from proven SE vectors.
_FIXTURE_EXPECTED_COLUMNS = {
    (Direction.FORWARD, Direction.UP): ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    (Direction.DOWN, Direction.FORWARD): ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    (Direction.DOWN, Direction.RIGHT): ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    (Direction.FORWARD, Direction.RIGHT): ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    (Direction.DOWN, Direction.LEFT): ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
    (Direction.BACKWARD, Direction.DOWN): ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
}


class DirectionVectorTests(unittest.TestCase):
    def test_proven_se_direction_vectors(self) -> None:
        self.assertEqual(direction_vector(Direction.FORWARD), (0, 0, -1))
        self.assertEqual(direction_vector(Direction.BACKWARD), (0, 0, 1))
        self.assertEqual(direction_vector(Direction.LEFT), (-1, 0, 0))
        self.assertEqual(direction_vector(Direction.RIGHT), (1, 0, 0))
        self.assertEqual(direction_vector(Direction.UP), (0, 1, 0))
        self.assertEqual(direction_vector(Direction.DOWN), (0, -1, 0))

    def test_vectors_are_unit_and_axis_aligned(self) -> None:
        seen = set()
        for token, vector in SE_DIRECTION_VECTORS.items():
            self.assertEqual(sum(c * c for c in vector), 1)
            self.assertTrue(all(c in (-1, 0, 1) for c in vector))
            self.assertNotIn(vector, seen)
            seen.add(vector)
            self.assertIsInstance(token, Direction)

    def test_right_cross_up_is_backward(self) -> None:
        right = direction_vector(Direction.RIGHT)
        up = direction_vector(Direction.UP)
        backward = (
            right[1] * up[2] - right[2] * up[1],
            right[2] * up[0] - right[0] * up[2],
            right[0] * up[1] - right[1] * up[0],
        )
        self.assertEqual(backward, direction_vector(Direction.BACKWARD))


class LegalOrientationTests(unittest.TestCase):
    def test_exactly_twenty_four_legal_pairs(self) -> None:
        pairs = legal_orientations()
        self.assertEqual(len(pairs), 24)
        self.assertEqual(len(set(pairs)), 24)
        for forward, up in pairs:
            self.assertTrue(is_valid_orientation(forward, up))
            self.assertFalse(same_axis(forward, up))

    def test_invalid_same_and_opposite_axis_pairs_fail(self) -> None:
        invalid = (
            (Direction.FORWARD, Direction.FORWARD),
            (Direction.FORWARD, Direction.BACKWARD),
            (Direction.BACKWARD, Direction.FORWARD),
            (Direction.UP, Direction.DOWN),
            (Direction.DOWN, Direction.UP),
            (Direction.LEFT, Direction.RIGHT),
            (Direction.RIGHT, Direction.LEFT),
            (Direction.LEFT, Direction.LEFT),
        )
        for forward, up in invalid:
            with self.subTest(forward=forward, up=up):
                self.assertFalse(is_valid_orientation(forward, up))
                with self.assertRaises(InvalidOrientationError) as ctx:
                    rotation_from_forward_up(forward, up)
                self.assertIn(forward.value, str(ctx.exception))
                self.assertIn(up.value, str(ctx.exception))


class RotationMatrixTests(unittest.TestCase):
    def test_default_forward_up_is_identity(self) -> None:
        rotation = rotation_from_forward_up(Direction.FORWARD, Direction.UP)
        self.assertEqual(rotation, IDENTITY_ROTATION)
        self.assertTrue(rotation.is_identity())
        self.assertEqual(rotation.columns, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))

    def test_every_legal_orientation_is_orthonormal_unique_and_right_handed(self) -> None:
        seen: dict[tuple[tuple[int, int, int], ...], tuple[Direction, Direction]] = {}
        for forward, up in legal_orientations():
            with self.subTest(forward=forward, up=up):
                rotation = rotation_from_forward_up(forward, up)
                self.assertTrue(rotation.is_orthonormal())
                self.assertEqual(rotation.determinant(), 1)
                self.assertEqual(rotation.forward, direction_vector(forward))
                self.assertEqual(rotation.up, direction_vector(up))
                self.assertTrue(all(c in (-1, 0, 1) for col in rotation.columns for c in col))
                self.assertTrue(all(isinstance(c, int) for col in rotation.columns for c in col))
                self.assertNotIsInstance(rotation.determinant(), float)
                key = rotation.columns
                self.assertNotIn(key, seen)
                seen[key] = (forward, up)
                local_x = rotation.apply((1, 0, 0))
                local_y = rotation.apply((0, 1, 0))
                local_z = rotation.apply((0, 0, 1))
                self.assertEqual(local_x, rotation.right)
                self.assertEqual(local_y, rotation.up)
                self.assertEqual(local_z, rotation.backward)
        self.assertEqual(len(seen), 24)

    def test_derived_left_matches_keen_left_table(self) -> None:
        for forward, up in legal_orientations():
            rotation = rotation_from_forward_up(forward, up)
            left = (-rotation.right[0], -rotation.right[1], -rotation.right[2])
            expected = _KEEN_LEFT_TABLE[
                _DIRECTION_INDEX[forward] * 6 + _DIRECTION_INDEX[up]
            ]
            self.assertEqual(_VECTOR_TO_DIRECTION[left], expected)

    def test_fixture_orientations(self) -> None:
        for forward, up in _FIXTURE_ORIENTATIONS:
            with self.subTest(forward=forward, up=up):
                rotation = rotation_from_forward_up(forward, up)
                self.assertEqual(rotation.columns, _FIXTURE_EXPECTED_COLUMNS[(forward, up)])
                self.assertEqual(rotation.determinant(), 1)
                self.assertTrue(rotation.is_orthonormal())


class TranslationTests(unittest.TestCase):
    def test_origin_cell_is_grid_origin(self) -> None:
        position = cell_center_mm(GridCoordinate(0, 0, 0))
        self.assertEqual(position.as_tuple(), (0, 0, 0))

    def test_integer_multiples_of_pitch(self) -> None:
        pitch = LARGE_GRID_CELL_PITCH_MM
        cases = (
            ((1, 0, 0), (pitch, 0, 0)),
            ((0, 0, 1), (0, 0, pitch)),
            ((0, 1, 0), (0, pitch, 0)),
            ((0, 2, 0), (0, 2 * pitch, 0)),
            ((0, 0, -1), (0, 0, -pitch)),
            ((0, 0, -2), (0, 0, -2 * pitch)),
            ((5, 2, -2), (5 * pitch, 2 * pitch, -2 * pitch)),
        )
        for cell, expected in cases:
            with self.subTest(cell=cell):
                position = cell_center_mm(GridCoordinate(*cell))
                self.assertEqual(position.as_tuple(), expected)
                self.assertTrue(all(isinstance(c, int) for c in position.as_tuple()))

    def test_uses_catalog_pitch_constant(self) -> None:
        position = cell_center_mm(GridCoordinate(1, 0, 0), LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(position.x, LARGE_GRID_CELL_PITCH_MM)

    def test_orientation_does_not_move_one_by_one_anchor(self) -> None:
        coordinate = GridCoordinate(3, 1, -1)
        positions = {
            cell_center_mm(coordinate).as_tuple()
            for forward, up in legal_orientations()
        }
        self.assertEqual(positions, {cell_center_mm(coordinate).as_tuple()})


class TransformIndependenceTests(unittest.TestCase):
    def test_transform_modules_do_not_import_cad_or_duplicate_pitch(self) -> None:
        transform_root = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "transform"
        forbidden_import = (
            r"(?m)^\s*(?:import|from)\s+(?:solidworks|win32com|pythoncom|blender|bpy)\b",
            r"(?m)^\s*(?:import|from)\s+subprocess\b",
        )
        for path in transform_root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden_import:
                self.assertNotRegex(
                    text, pattern, msg=f"{path.name} matches {pattern}"
                )
            if path.name != "__init__.py":
                self.assertNotRegex(text, r"\b2500\b", msg=f"{path.name} copies 2500")


if __name__ == "__main__":
    unittest.main()
