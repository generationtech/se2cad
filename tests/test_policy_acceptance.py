"""Policy conversion against the qualified all-supported acceptance fixture."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from se2cad.catalog import FILLER_GEOMETRY_ID, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import parse_blueprint
from se2cad.policy import ConversionPolicy, convert_blueprint, convert_blueprint_from_path
from se2cad.preflight import compute_conversion_preflight

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"


class AcceptancePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.catalog = load_default_catalog()
        cls.resolved = build_canonical_blueprint(cls.parsed, cls.catalog)
        cls.preflight = compute_conversion_preflight(cls.parsed, cls.catalog)
        cls.strict = convert_blueprint(
            cls.parsed, cls.catalog, ConversionPolicy.STRICT
        )
        cls.permissive = convert_blueprint(
            cls.parsed, cls.catalog, ConversionPolicy.PERMISSIVE
        )

    def test_fixture_sha256_is_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)

    def test_both_policies_emit_the_qualified_supported_ir(self) -> None:
        self.assertTrue(self.preflight.all_supported)
        self.assertEqual(self.strict.ir.grid.block_count, 24)
        self.assertEqual(self.permissive.ir.grid.block_count, 24)
        self.assertEqual(self.strict.ir, self.resolved)
        self.assertEqual(self.permissive.ir, self.resolved)
        self.assertEqual(self.strict.filler_count, 0)
        self.assertEqual(self.permissive.filler_count, 0)
        self.assertEqual(self.strict.preflight, self.preflight)
        self.assertEqual(self.permissive.preflight, self.preflight)
        self.assertTrue(
            all(block.geometry_id != FILLER_GEOMETRY_ID for block in self.strict.ir.grid.blocks)
        )

    def test_path_entry_matches_in_memory_strict(self) -> None:
        from_path = convert_blueprint_from_path(FIXTURE_PATH, self.catalog)
        self.assertEqual(from_path.ir, self.strict.ir)
        self.assertEqual(from_path.filler_count, 0)
        self.assertEqual(from_path.policy, ConversionPolicy.STRICT)


if __name__ == "__main__":
    unittest.main()
