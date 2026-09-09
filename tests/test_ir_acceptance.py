"""Parser + catalog + IR against the qualified acceptance fixture."""

from __future__ import annotations

import hashlib
import unittest
from collections import Counter
from pathlib import Path

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    Direction,
    parse_blueprint,
)
from se2cad.transform import IDENTITY_ROTATION, rotation_from_forward_up

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"

EXPECTED_GEOMETRY = {
    "LargeBlockArmorBlock": "large_armor_block",
    "LargeBlockArmorSlope": "large_armor_slope",
    "LargeBlockArmorCorner": "large_armor_corner",
    "LargeBlockArmorCornerInv": "large_armor_corner_inv",
}


class AcceptanceIrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.catalog = load_default_catalog()
        cls.ir = build_canonical_blueprint(cls.parsed, cls.catalog)

    def test_fixture_sha256_is_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)

    def test_all_twenty_four_blocks_become_ir_instances(self) -> None:
        self.assertEqual(self.ir.grid.block_count, 24)
        self.assertEqual(len(self.ir.grid.blocks), 24)
        self.assertEqual(self.ir.identity_subtype, "se2cad-test1")
        self.assertEqual(self.ir.grid.display_name, "se2cad-test1")

    def test_identities_survive_into_ir(self) -> None:
        parsed_blocks = self.parsed.grid.blocks
        ir_blocks = self.ir.grid.blocks
        self.assertEqual(len(ir_blocks), len(parsed_blocks))
        geometry_ids = []
        for parsed, canonical in zip(parsed_blocks, ir_blocks, strict=True):
            self.assertEqual(canonical.subtype_id, parsed.subtype_id)
            self.assertEqual(canonical.geometry_id, EXPECTED_GEOMETRY[parsed.subtype_id])
            self.assertEqual(canonical.grid_min, parsed.min)
            self.assertEqual(canonical.forward, parsed.forward)
            self.assertEqual(canonical.up, parsed.up)
            self.assertEqual(canonical.source_index, parsed.source_index)
            self.assertEqual(canonical.min_serialized, parsed.min_serialized)
            self.assertEqual(
                canonical.orientation_serialized, parsed.orientation_serialized
            )
            self.assertEqual(canonical.color_mask_hsv, parsed.color_mask_hsv)
            self.assertEqual(canonical.color_serialized, parsed.color_serialized)
            self.assertEqual(
                canonical.appearance_support, parsed.appearance_support
            )
            self.assertEqual(canonical.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)
            self.assertEqual(canonical.appearance_support, AppearanceSupport.DEFAULT)
            self.assertFalse(canonical.color_serialized)
            geometry_ids.append(canonical.geometry_id)
        self.assertEqual(
            Counter(geometry_ids),
            Counter(
                {
                    "large_armor_block": 9,
                    "large_armor_slope": 12,
                    "large_armor_corner": 2,
                    "large_armor_corner_inv": 1,
                }
            ),
        )

    def test_known_fixture_translations(self) -> None:
        pitch = LARGE_GRID_CELL_PITCH_MM
        by_min = {
            (block.grid_min.x, block.grid_min.y, block.grid_min.z): block
            for block in self.ir.grid.blocks
        }
        self.assertEqual(len(by_min), 24)
        self.assertEqual(by_min[(0, 0, 0)].position_mm.as_tuple(), (0, 0, 0))
        self.assertEqual(by_min[(1, 0, 0)].position_mm.as_tuple(), (pitch, 0, 0))
        self.assertEqual(by_min[(0, 0, 1)].position_mm.as_tuple(), (0, 0, pitch))
        self.assertEqual(by_min[(0, 0, -1)].position_mm.as_tuple(), (0, 0, -pitch))
        self.assertEqual(by_min[(5, 0, -2)].position_mm.as_tuple(), (5 * pitch, 0, -2 * pitch))
        self.assertEqual(by_min[(1, 1, 0)].position_mm.as_tuple(), (pitch, pitch, 0))
        self.assertEqual(
            by_min[(5, 2, -2)].position_mm.as_tuple(),
            (5 * pitch, 2 * pitch, -2 * pitch),
        )
        for (x, y, z), block in by_min.items():
            self.assertEqual(
                block.position_mm.as_tuple(),
                (x * pitch, y * pitch, z * pitch),
            )
            self.assertTrue(all(isinstance(c, int) for c in block.position_mm.as_tuple()))

    def test_fixture_orientations(self) -> None:
        omitted = [
            block
            for block in self.ir.grid.blocks
            if not block.orientation_serialized
        ]
        self.assertEqual(len(omitted), 15)
        for block in omitted:
            self.assertEqual(block.forward, Direction.FORWARD)
            self.assertEqual(block.up, Direction.UP)
            self.assertEqual(block.rotation, IDENTITY_ROTATION)

        expected_explicit = {
            ((0, 0, -1), Direction.DOWN, Direction.FORWARD),
            ((1, 0, -1), Direction.DOWN, Direction.FORWARD),
            ((2, 0, -1), Direction.DOWN, Direction.FORWARD),
            ((3, 0, -1), Direction.DOWN, Direction.FORWARD),
            ((4, 0, -1), Direction.DOWN, Direction.FORWARD),
            ((1, 1, 0), Direction.DOWN, Direction.RIGHT),
            ((3, 1, 0), Direction.FORWARD, Direction.RIGHT),
            ((0, 1, 0), Direction.DOWN, Direction.LEFT),
            ((5, 0, 0), Direction.BACKWARD, Direction.DOWN),
        }
        explicit = {
            (
                (block.grid_min.x, block.grid_min.y, block.grid_min.z),
                block.forward,
                block.up,
            )
            for block in self.ir.grid.blocks
            if block.orientation_serialized
        }
        self.assertEqual(explicit, expected_explicit)
        for _min, forward, up in expected_explicit:
            block = next(
                item
                for item in self.ir.grid.blocks
                if (item.grid_min.x, item.grid_min.y, item.grid_min.z) == _min
            )
            self.assertEqual(block.rotation, rotation_from_forward_up(forward, up))
            self.assertEqual(block.rotation.determinant(), 1)

    def test_first_block_is_omitted_origin_cube(self) -> None:
        first = self.ir.grid.blocks[0]
        self.assertEqual(first.subtype_id, "LargeBlockArmorBlock")
        self.assertEqual(first.geometry_id, "large_armor_block")
        self.assertFalse(first.min_serialized)
        self.assertFalse(first.orientation_serialized)
        self.assertEqual(first.position_mm.as_tuple(), (0, 0, 0))
        self.assertTrue(first.rotation.is_identity())


if __name__ == "__main__":
    unittest.main()
