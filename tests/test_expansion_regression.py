"""S2C-11.5.1 expansion regression: fixture, install-free runtime, asset paths."""

from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

from se2cad.catalog import (
    RecipeKind,
    SupportStatus,
    UnknownSubtypeError,
    assert_packaged_leftover_matches_catalog,
    conversion_may_report_supported,
    default_catalog_path,
    default_leftover_path,
    load_default_catalog,
)
from se2cad.ir import build_canonical_blueprint
from se2cad.library import lookup_recipe
from se2cad.parser import parse_blueprint

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src" / "se2cad"
_FIXTURE = _REPO / "fixtures" / "acceptance" / "four-block-armor-asymmetric" / "bp.sbc"
_FIXTURE_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"
_ORIGINAL = {
    "LargeBlockArmorBlock": "large_armor_block",
    "LargeBlockArmorSlope": "large_armor_slope",
    "LargeBlockArmorCorner": "large_armor_corner",
    "LargeBlockArmorCornerInv": "large_armor_corner_inv",
}
_FORBIDDEN_RUNTIME = (
    "se2cad.discovery",
    "SE2CAD_GAME_ROOT",
    "SE2CAD_SDK_ROOT",
)
_RUNTIME_DIRS = (
    "parser",
    "catalog",
    "ir",
    "library",
    "transform",
    "statistics",
    "solidworks",
)
_ASSET_MARKERS = (".mwm", ".fbx", ".dds", ".hkt")


class FixtureConversionRegressionTests(unittest.TestCase):
    def test_original_four_block_fixture_still_converts(self) -> None:
        digest = hashlib.sha256(_FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(digest, _FIXTURE_SHA256)
        catalog = load_default_catalog()
        ir = build_canonical_blueprint(parse_blueprint(_FIXTURE), catalog)
        self.assertEqual(ir.identity_subtype, "se2cad-test1")
        self.assertEqual(len(ir.grid.blocks), 24)
        leftover_set = assert_packaged_leftover_matches_catalog()
        for block in ir.grid.blocks:
            self.assertIn(block.subtype_id, _ORIGINAL)
            self.assertEqual(block.geometry_id, _ORIGINAL[block.subtype_id])
            self.assertEqual(block.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertEqual(block.support_status, SupportStatus.SUPPORTED)
            self.assertEqual(
                lookup_recipe(block.geometry_id).geometry_id, block.geometry_id
            )
            entry = catalog.lookup(block.subtype_id)
            self.assertEqual(leftover_set.coverage_claim, "not_universal_vanilla")
            self.assertTrue(leftover_set.leftovers)
            self.assertTrue(conversion_may_report_supported(entry, leftover_set))

    def test_unknown_subtype_still_fails_closed(self) -> None:
        with self.assertRaises(UnknownSubtypeError):
            load_default_catalog().lookup("NotACataloguedSubtype")


class InstallFreeRuntimeTests(unittest.TestCase):
    def test_runtime_modules_do_not_open_a_game_or_sdk_install(self) -> None:
        public = (_SRC / "__init__.py").read_text(encoding="utf-8")
        for token in _FORBIDDEN_RUNTIME:
            self.assertNotIn(token, public)
        for directory in _RUNTIME_DIRS:
            for path in (_SRC / directory).glob("*.py"):
                text = path.read_text(encoding="utf-8")
                for token in _FORBIDDEN_RUNTIME:
                    self.assertNotIn(
                        token, text, msg=f"{path.name} mentions {token}"
                    )

    def test_leftover_module_does_not_import_discovery_or_cad(self) -> None:
        path = _SRC / "catalog" / "leftover.py"
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                self.assertFalse(module.startswith("se2cad.discovery"), msg=module)
                self.assertFalse(module.startswith("se2cad.parser"), msg=module)
                self.assertFalse(module.startswith("se2cad.solidworks"), msg=module)
                self.assertNotIn(module, {"win32com", "blender", "subprocess"})


class PackagedMetadataNeutralityTests(unittest.TestCase):
    def test_packaged_catalog_and_leftover_forbid_asset_paths(self) -> None:
        catalog_path = default_catalog_path()
        leftover_path = default_leftover_path()
        self.assertEqual(catalog_path.name, "large_grid_armor.json")
        self.assertEqual(leftover_path.name, "leftover_set.json")
        for path in (catalog_path, leftover_path):
            serialized = json.dumps(json.loads(path.read_text(encoding="utf-8")))
            lowered = serialized.lower()
            self.assertNotIn("/home/", serialized)
            self.assertNotIn("C:\\\\", serialized)
            self.assertNotIn("Steam", serialized)
            self.assertNotIn("SpaceEngineers", serialized)
            for marker in _ASSET_MARKERS:
                self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
