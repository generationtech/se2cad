"""Independence and asset-boundary tests for the block library."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

LIBRARY_ROOT = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "library"


def _library_sources() -> list[Path]:
    return sorted(LIBRARY_ROOT.glob("*.py"))


class LibraryNeutralityTests(unittest.TestCase):
    def test_library_has_no_backend_or_game_asset_dependency(self) -> None:
        forbidden_import = (
            r"(?m)^\s*(?:import|from)\s+(?:solidworks|win32com|pythoncom|blender|bpy)\b",
            r"(?m)^\s*(?:import|from)\s+subprocess\b",
            r"(?m)^\s*(?:import|from)\s+se2cad\.ir\b",
            r"(?m)^\s*(?:import|from)\s+se2cad\.parser\.blueprint\b",
        )
        forbidden_text = (
            ".sldprt",
            ".sldasm",
            ".mwm",
            ".fbx",
            ".dds",
            ".hkt",
            "sqlite",
            "Steam",
            "SpaceEngineers",
            "/home/",
            "C:\\",
        )
        for path in _library_sources():
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for pattern in forbidden_import:
                self.assertNotRegex(text, pattern, msg=f"{path.name} matches {pattern}")
            for token in forbidden_text:
                self.assertNotIn(token.lower(), lowered, msg=f"{path.name} mentions {token}")
            self.assertNotRegex(text, r"\b2500\b", msg=f"{path.name} copies 2500")
            self.assertNotRegex(text, r"\b1250\b", msg=f"{path.name} copies 1250")

    def test_library_imports_are_stdlib_plus_qualified_se2cad(self) -> None:
        allowed_se2cad = {
            "se2cad.catalog.authorized",
            "se2cad.catalog.constants",
            "se2cad.catalog.model",
            "se2cad.library.errors",
            "se2cad.library.frame",
            "se2cad.library.lookup",
            "se2cad.library.model",
            "se2cad.library.recipes",
            "se2cad.library.sdk_bind",
            "se2cad.library.solid",
            "se2cad.library.treatment",
            "se2cad.parser.model",
            "se2cad.transform.directions",
        }
        for path in _library_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertFalse(
                            alias.name.startswith("se2cad."),
                            msg=f"{path.name} imports {alias.name}",
                        )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("se2cad."):
                        self.assertIn(node.module, allowed_se2cad, msg=path.name)

    def test_package_surface_does_not_require_a_game_install(self) -> None:
        from se2cad.library import all_library_records, lookup_recipe

        records = all_library_records()
        self.assertEqual(len(records), 12)
        self.assertEqual(
            lookup_recipe("large_armor_corner").geometry_id, "large_armor_corner"
        )
        self.assertEqual(
            lookup_recipe("large_heavy_block_armor_block").geometry_id,
            "large_heavy_block_armor_block",
        )


if __name__ == "__main__":
    unittest.main()
