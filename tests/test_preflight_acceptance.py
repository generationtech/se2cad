"""Preflight against the qualified all-supported acceptance fixture."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from se2cad.catalog import SupportStatus, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import AppearanceSupport, GridSize, parse_blueprint
from se2cad.preflight import (
    CatalogOutcome,
    compute_conversion_preflight,
    compute_conversion_preflight_from_path,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"


class AcceptancePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.catalog = load_default_catalog()
        cls.ir = build_canonical_blueprint(cls.parsed, cls.catalog)
        cls.report = compute_conversion_preflight(cls.parsed, cls.catalog)

    def test_fixture_sha256_is_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)

    def test_fixture_preflight_is_clean_and_complete(self) -> None:
        self.assertEqual(self.report.identity_subtype, "se2cad-test1")
        self.assertEqual(self.report.grid_size, GridSize.LARGE)
        self.assertEqual(self.report.block_count, 24)
        self.assertEqual(self.report.block_count, self.parsed.grid.block_count)
        self.assertEqual(self.report.block_count, self.ir.grid.block_count)
        self.assertEqual(len(self.report.blocks), 24)
        self.assertEqual(self.report.supported_count, 24)
        self.assertEqual(self.report.unsupported_count, 0)
        self.assertEqual(self.report.unknown_count, 0)
        self.assertEqual(self.report.unknown_subtype_counts, ())
        self.assertEqual(self.report.unsupported_subtype_counts, ())
        self.assertTrue(self.report.all_supported)

    def test_every_fixture_block_matches_parser_and_catalog(self) -> None:
        self.assertEqual(len(self.report.blocks), len(self.parsed.grid.blocks))
        for parsed_block, preflight_block, ir_block in zip(
            self.parsed.grid.blocks,
            self.report.blocks,
            self.ir.grid.blocks,
            strict=True,
        ):
            self.assertEqual(preflight_block.source_index, parsed_block.source_index)
            self.assertEqual(preflight_block.subtype_id, parsed_block.subtype_id)
            self.assertEqual(preflight_block.grid_min, parsed_block.min)
            self.assertEqual(preflight_block.catalog_outcome, CatalogOutcome.SUPPORTED)
            self.assertEqual(preflight_block.geometry_id, ir_block.geometry_id)
            self.assertEqual(preflight_block.geometry_support, SupportStatus.SUPPORTED)
            self.assertEqual(preflight_block.appearance_support, parsed_block.appearance_support)
            self.assertEqual(preflight_block.appearance_support, AppearanceSupport.DEFAULT)

    def test_path_entry_matches_in_memory_compute(self) -> None:
        from_path = compute_conversion_preflight_from_path(FIXTURE_PATH, self.catalog)
        self.assertEqual(from_path, self.report)


if __name__ == "__main__":
    unittest.main()
