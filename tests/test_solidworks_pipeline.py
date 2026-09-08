"""Full qualified-upstream pipeline without Space Engineers or SolidWorks."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from se2cad.solidworks.artifacts import canonical_geometry_ids
from se2cad.solidworks.pipeline import resolve_recipes_from_blueprint

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"


class BlueprintToRecipePipelineTests(unittest.TestCase):
    def test_fixture_resolves_four_recipes_without_a_game_install(self) -> None:
        digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SHA256)
        resolved = resolve_recipes_from_blueprint(FIXTURE_PATH)
        self.assertEqual(resolved.ir.grid.block_count, 24)
        self.assertEqual(set(resolved.geometry_ids), set(canonical_geometry_ids()))
        self.assertEqual(len(resolved.recipes), 4)
        self.assertEqual(len(resolved.plans), 4)
        self.assertEqual(
            [recipe.geometry_id for recipe in resolved.recipes],
            list(resolved.geometry_ids),
        )
        for recipe, plan in zip(resolved.recipes, resolved.plans):
            self.assertEqual(plan.geometry_id, recipe.geometry_id)
            self.assertEqual(plan.solid_kind, recipe.solid_kind)

    def test_pipeline_does_not_scan_space_engineers_or_modsdk(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "solidworks"
            / "pipeline.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("win32com", source)
        self.assertNotIn("pythoncom", source)
        self.assertNotIn("Steam", source)
        self.assertNotIn("CubeBlocks", source)
        self.assertNotIn("/home/", source)
        self.assertNotIn("C:\\", source)
