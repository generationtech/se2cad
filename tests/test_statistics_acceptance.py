"""Statistics against the qualified S2C-1.1.1 / S2C-1.2.1 / S2C-3.1.1 record."""

from __future__ import annotations

import hashlib
import unittest
from collections import Counter
from fractions import Fraction
from pathlib import Path

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import Direction, GridSize, parse_blueprint
from se2cad.statistics import (
    NamedCount,
    OrientationCount,
    compute_blueprint_statistics,
    compute_blueprint_statistics_from_path,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"


class AcceptanceStatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.catalog = load_default_catalog()
        cls.ir = build_canonical_blueprint(cls.parsed, cls.catalog)
        cls.stats = compute_blueprint_statistics(cls.parsed, cls.catalog)

    def test_fixture_sha256_is_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)

    def test_identity_and_grid_match_qualified_parser(self) -> None:
        self.assertEqual(self.stats.identity_subtype, "se2cad-test1")
        self.assertEqual(self.stats.display_name, "\ue030Kolyma")
        self.assertEqual(self.stats.grid_display_name, "se2cad-test1")
        self.assertEqual(self.stats.grid_size, GridSize.LARGE)
        self.assertEqual(self.stats.block_count, 24)
        self.assertEqual(self.stats.block_count, self.parsed.grid.block_count)
        self.assertEqual(self.stats.block_count, self.ir.grid.block_count)

    def test_subtype_and_geometry_counts_match_parser_catalog_ir(self) -> None:
        self.assertEqual(
            self.stats.subtype_counts,
            (
                NamedCount("LargeBlockArmorBlock", 9),
                NamedCount("LargeBlockArmorCorner", 2),
                NamedCount("LargeBlockArmorCornerInv", 1),
                NamedCount("LargeBlockArmorSlope", 12),
            ),
        )
        self.assertEqual(
            dict(Counter(block.subtype_id for block in self.parsed.grid.blocks)),
            {item.name: item.count for item in self.stats.subtype_counts},
        )
        self.assertEqual(
            self.stats.geometry_id_counts,
            (
                NamedCount("large_armor_block", 9),
                NamedCount("large_armor_corner", 2),
                NamedCount("large_armor_corner_inv", 1),
                NamedCount("large_armor_slope", 12),
            ),
        )
        self.assertEqual(
            dict(Counter(block.geometry_id for block in self.ir.grid.blocks)),
            {item.name: item.count for item in self.stats.geometry_id_counts},
        )

    def test_cell_extents_and_millimetre_size_use_catalog_pitch(self) -> None:
        extents = self.stats.cell_extents
        assert extents is not None
        self.assertEqual((extents.x.minimum, extents.x.maximum), (0, 5))
        self.assertEqual((extents.y.minimum, extents.y.maximum), (0, 2))
        self.assertEqual((extents.z.minimum, extents.z.maximum), (-2, 1))
        self.assertEqual(extents.x.span_cells, 6)
        self.assertEqual(extents.y.span_cells, 3)
        self.assertEqual(extents.z.span_cells, 4)
        assert self.stats.millimetre_size is not None
        self.assertEqual(self.stats.cell_pitch_mm, LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(self.stats.millimetre_size.x, 6 * LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(self.stats.millimetre_size.y, 3 * LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(self.stats.millimetre_size.z, 4 * LARGE_GRID_CELL_PITCH_MM)

    def test_occupancy_is_unique_min_over_cell_aabb(self) -> None:
        mins = {
            (block.min.x, block.min.y, block.min.z) for block in self.parsed.grid.blocks
        }
        self.assertEqual(len(mins), 24)
        self.assertEqual(self.stats.occupancy.unique_min_cells, 24)
        self.assertEqual(self.stats.occupancy.bounding_box_cells, 72)
        self.assertEqual(self.stats.occupancy.coverage, Fraction(24, 72))

    def test_orientation_histogram_matches_qualified_parser(self) -> None:
        self.assertEqual(
            self.stats.orientation_counts,
            (
                OrientationCount(Direction.BACKWARD, Direction.DOWN, 1),
                OrientationCount(Direction.DOWN, Direction.FORWARD, 5),
                OrientationCount(Direction.DOWN, Direction.LEFT, 1),
                OrientationCount(Direction.DOWN, Direction.RIGHT, 1),
                OrientationCount(Direction.FORWARD, Direction.RIGHT, 1),
                OrientationCount(Direction.FORWARD, Direction.UP, 15),
            ),
        )
        parsed_pairs = Counter(
            (block.forward, block.up) for block in self.parsed.grid.blocks
        )
        self.assertEqual(
            parsed_pairs,
            {(item.forward, item.up): item.count for item in self.stats.orientation_counts},
        )

    def test_catalog_resolution_is_complete_for_the_fixture(self) -> None:
        self.assertEqual(self.stats.catalog_coverage.resolved_blocks, 24)
        self.assertEqual(self.stats.catalog_coverage.unresolved_blocks, 0)
        self.assertEqual(self.stats.catalog_coverage.unresolved_subtype_counts, ())

    def test_path_entry_matches_in_memory_compute(self) -> None:
        from_path = compute_blueprint_statistics_from_path(FIXTURE_PATH, self.catalog)
        self.assertEqual(from_path, self.stats)


if __name__ == "__main__":
    unittest.main()
