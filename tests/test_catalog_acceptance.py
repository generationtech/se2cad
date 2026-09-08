"""Parser-to-catalog integration against the qualified acceptance fixture."""

from __future__ import annotations

import hashlib
import unittest
from collections import Counter
from pathlib import Path

from se2cad.catalog import load_default_catalog
from se2cad.parser import parse_blueprint

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"

EXPECTED_GEOMETRY = {
    "LargeBlockArmorBlock": "large_armor_block",
    "LargeBlockArmorSlope": "large_armor_slope",
    "LargeBlockArmorCorner": "large_armor_corner",
    "LargeBlockArmorCornerInv": "large_armor_corner_inv",
}


class AcceptanceCatalogResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.catalog = load_default_catalog()

    def test_fixture_sha256_is_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)

    def test_every_parsed_block_resolves_to_one_of_four_entries(self) -> None:
        resolved = []
        for block in self.parsed.grid.blocks:
            entry = self.catalog.lookup(block.subtype_id)
            self.assertEqual(entry.subtype_id, block.subtype_id)
            self.assertEqual(entry.geometry_id, EXPECTED_GEOMETRY[block.subtype_id])
            resolved.append(entry.geometry_id)

        self.assertEqual(len(resolved), len(self.parsed.grid.blocks))
        self.assertEqual(set(resolved), set(EXPECTED_GEOMETRY.values()))
        counts = Counter(block.subtype_id for block in self.parsed.grid.blocks)
        geometry_counts = Counter(resolved)
        self.assertEqual(
            geometry_counts,
            Counter(
                {
                    EXPECTED_GEOMETRY[subtype]: count
                    for subtype, count in counts.items()
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
