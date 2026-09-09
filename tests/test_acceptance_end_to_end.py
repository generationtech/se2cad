"""S2C-6.1.1 ordinary end-to-end comparison against the qualified fixture.

Walks the composed conversion path without SolidWorks or a Space Engineers
install. Live SolidWorks evidence lives in test_solidworks_integration.py.
"""

from __future__ import annotations

import hashlib
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from se2cad.catalog import (
    LARGE_GRID_CELL_PITCH_MM,
    UnknownSubtypeError,
    load_default_catalog,
)
from se2cad.ir import build_canonical_blueprint, component_name_from_block
from se2cad.library import lookup_recipe
from se2cad.parser import Direction, GridSize, parse_blueprint
from se2cad.solidworks.artifacts import canonical_geometry_ids
from se2cad.solidworks.pipeline import resolve_recipes_from_blueprint
from se2cad.solidworks.placement import placements_from_ir
from se2cad.solidworks.transform_pack import (
    arraydata_axes,
    arraydata_translation_m,
    solidworks_arraydata,
)
from se2cad.transform import IDENTITY_ROTATION, cell_center_mm, rotation_from_forward_up

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"

ALLOWED_SUBTYPES = {
    "LargeBlockArmorBlock",
    "LargeBlockArmorSlope",
    "LargeBlockArmorCorner",
    "LargeBlockArmorCornerInv",
}
EXPECTED_SUBTYPE_COUNTS = {
    "LargeBlockArmorBlock": 9,
    "LargeBlockArmorSlope": 12,
    "LargeBlockArmorCorner": 2,
    "LargeBlockArmorCornerInv": 1,
}
EXPECTED_GEOMETRY = {
    "LargeBlockArmorBlock": "large_armor_block",
    "LargeBlockArmorSlope": "large_armor_slope",
    "LargeBlockArmorCorner": "large_armor_corner",
    "LargeBlockArmorCornerInv": "large_armor_corner_inv",
}
EXPLICIT_ORIENTATIONS = {
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


class AcceptanceEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.catalog = load_default_catalog()
        cls.ir = build_canonical_blueprint(cls.parsed, cls.catalog)
        cls.resolved = resolve_recipes_from_blueprint(FIXTURE_PATH)
        cls.placements = placements_from_ir(cls.ir)

    def test_fixture_sha256_is_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)
        self.assertEqual(self.resolved.ir.identity_subtype, "se2cad-test1")

    def test_single_supported_large_grid(self) -> None:
        self.assertEqual(self.parsed.grid.grid_size, GridSize.LARGE)
        self.assertEqual(self.ir.grid.grid_size, GridSize.LARGE)
        self.assertEqual(self.parsed.grid.block_count, 24)
        self.assertEqual(len(self.parsed.grid.blocks), 24)
        self.assertEqual(len(self.ir.grid.blocks), 24)
        self.assertEqual(len(self.placements), 24)

    def test_subtype_and_geometry_counts(self) -> None:
        subtype_counts = Counter(block.subtype_id for block in self.parsed.grid.blocks)
        self.assertEqual(dict(subtype_counts), EXPECTED_SUBTYPE_COUNTS)
        self.assertEqual(set(subtype_counts), ALLOWED_SUBTYPES)
        geometry_counts = Counter(block.geometry_id for block in self.ir.grid.blocks)
        self.assertEqual(
            dict(geometry_counts),
            {
                EXPECTED_GEOMETRY[subtype]: count
                for subtype, count in EXPECTED_SUBTYPE_COUNTS.items()
            },
        )

    def test_all_blocks_resolve_through_catalog_into_ir(self) -> None:
        for parsed, canonical, placement in zip(
            self.parsed.grid.blocks,
            self.ir.grid.blocks,
            self.placements,
            strict=True,
        ):
            entry = self.catalog.lookup(parsed.subtype_id)
            self.assertEqual(canonical.subtype_id, parsed.subtype_id)
            self.assertEqual(canonical.geometry_id, entry.geometry_id)
            self.assertEqual(canonical.geometry_id, EXPECTED_GEOMETRY[parsed.subtype_id])
            self.assertEqual(canonical.source_index, parsed.source_index)
            self.assertEqual(placement.source_index, parsed.source_index)
            self.assertEqual(placement.geometry_id, canonical.geometry_id)
            self.assertEqual(placement.part_filename, f"{canonical.geometry_id}.SLDPRT")
            self.assertEqual(
                placement.component_name, component_name_from_block(canonical)
            )
            self.assertEqual(
                placement.grid_min, (parsed.min.x, parsed.min.y, parsed.min.z)
            )
            self.assertEqual(placement.orientation_serialized, parsed.orientation_serialized)

    def test_qualified_recipes_exist_for_all_four_geometry_ids(self) -> None:
        self.assertEqual(set(self.resolved.geometry_ids), set(canonical_geometry_ids()))
        self.assertEqual(len(self.resolved.recipes), 4)
        for geometry_id in canonical_geometry_ids():
            recipe = lookup_recipe(geometry_id)
            self.assertEqual(recipe.geometry_id, geometry_id)

    def test_all_twenty_four_translations_match_source_min(self) -> None:
        pitch = LARGE_GRID_CELL_PITCH_MM
        mins = []
        for parsed, canonical, placement in zip(
            self.parsed.grid.blocks,
            self.ir.grid.blocks,
            self.placements,
            strict=True,
        ):
            expected = cell_center_mm(parsed.min, pitch)
            self.assertEqual(canonical.position_mm, expected)
            self.assertEqual(placement.position_mm, expected.as_tuple())
            self.assertEqual(
                expected.as_tuple(),
                (parsed.min.x * pitch, parsed.min.y * pitch, parsed.min.z * pitch),
            )
            mins.append((parsed.min.x, parsed.min.y, parsed.min.z))
        self.assertEqual(len(set(mins)), 24)

    def test_all_twenty_four_orientations_match_qualified_rotation(self) -> None:
        omitted = 0
        explicit = set()
        distinct_pairs = set()
        for parsed, canonical, placement in zip(
            self.parsed.grid.blocks,
            self.ir.grid.blocks,
            self.placements,
            strict=True,
        ):
            expected = rotation_from_forward_up(parsed.forward, parsed.up)
            self.assertEqual(canonical.forward, parsed.forward)
            self.assertEqual(canonical.up, parsed.up)
            self.assertEqual(canonical.rotation, expected)
            self.assertEqual(placement.rotation, expected)
            self.assertEqual(expected.determinant(), 1)
            distinct_pairs.add((parsed.forward, parsed.up))
            if parsed.orientation_serialized:
                explicit.add(
                    ((parsed.min.x, parsed.min.y, parsed.min.z), parsed.forward, parsed.up)
                )
            else:
                omitted += 1
                self.assertEqual(parsed.forward, Direction.FORWARD)
                self.assertEqual(parsed.up, Direction.UP)
                self.assertEqual(canonical.rotation, IDENTITY_ROTATION)
                self.assertTrue(placement.rotation.is_identity())
        self.assertEqual(omitted, 15)
        self.assertEqual(explicit, EXPLICIT_ORIENTATIONS)
        self.assertEqual(
            distinct_pairs,
            {
                (Direction.FORWARD, Direction.UP),
                (Direction.DOWN, Direction.FORWARD),
                (Direction.DOWN, Direction.RIGHT),
                (Direction.FORWARD, Direction.RIGHT),
                (Direction.DOWN, Direction.LEFT),
                (Direction.BACKWARD, Direction.DOWN),
            },
        )

    def test_packed_arraydata_matches_every_ir_transform(self) -> None:
        for canonical, placement in zip(self.ir.grid.blocks, self.placements, strict=True):
            data = solidworks_arraydata(placement.rotation, placement.position_mm)
            self.assertEqual(data, solidworks_arraydata(canonical.rotation, canonical.position_mm.as_tuple()))
            self.assertEqual(arraydata_axes(data), canonical.rotation.columns)
            self.assertEqual(
                arraydata_translation_m(data),
                (
                    canonical.position_mm.x / 1000,
                    canonical.position_mm.y / 1000,
                    canonical.position_mm.z / 1000,
                ),
            )
            self.assertEqual(data[12], 1.0)

    def test_unknown_subtype_fails_closed(self) -> None:
        bad_block = replace(self.parsed.grid.blocks[0], subtype_id="LargeBlockArmor")
        bad_grid = replace(self.parsed.grid, blocks=(bad_block,) + self.parsed.grid.blocks[1:])
        bad = replace(self.parsed, grid=bad_grid)
        with self.assertRaises(UnknownSubtypeError):
            build_canonical_blueprint(bad, self.catalog)


if __name__ == "__main__":
    unittest.main()
