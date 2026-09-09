"""Independence tests: CAD-neutral packages stay free of pywin32."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "se2cad"
CAD_NEUTRAL = (
    SRC / "parser",
    SRC / "catalog",
    SRC / "ir",
    SRC / "transform",
    SRC / "library",
    SRC / "statistics",
)
BACKEND_NEUTRAL_MODULES = (
    SRC / "solidworks" / "__init__.py",
    SRC / "solidworks" / "errors.py",
    SRC / "solidworks" / "units.py",
    SRC / "solidworks" / "artifacts.py",
    SRC / "solidworks" / "locator.py",
    SRC / "solidworks" / "config.py",
    SRC / "solidworks" / "availability.py",
    SRC / "solidworks" / "recipe_plan.py",
    SRC / "solidworks" / "pipeline.py",
    SRC / "solidworks" / "placement.py",
    SRC / "solidworks" / "appearance.py",
    SRC / "solidworks" / "transform_pack.py",
)
FORBIDDEN_IMPORTS = {"win32com", "pythoncom", "win32api", "win32com.client"}


def _py_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.glob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
            names.add(node.module)
    return names


class NeutralityTests(unittest.TestCase):
    def test_cad_neutral_packages_do_not_import_pywin32(self) -> None:
        for root in CAD_NEUTRAL:
            for path in _py_files(root):
                imported = _imported_modules(path)
                overlap = imported & FORBIDDEN_IMPORTS
                self.assertFalse(
                    overlap, msg=f"{path} imports {sorted(overlap)}"
                )
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("win32com", text)
                self.assertNotIn("pythoncom", text)

    def test_backend_neutral_modules_do_not_import_pywin32(self) -> None:
        for path in BACKEND_NEUTRAL_MODULES:
            imported = _imported_modules(path)
            self.assertFalse(imported & FORBIDDEN_IMPORTS, msg=path.name)

    def test_top_level_package_imports_without_pywin32(self) -> None:
        import se2cad

        self.assertTrue(hasattr(se2cad, "parse_blueprint"))
        self.assertTrue(hasattr(se2cad, "lookup_recipe"))
        self.assertTrue(hasattr(se2cad, "compute_blueprint_statistics"))
        self.assertTrue(hasattr(se2cad, "component_name"))
        self.assertTrue(hasattr(se2cad, "ColorMaskHSV"))
        self.assertTrue(hasattr(se2cad, "AppearanceSupport"))
        self.assertTrue(hasattr(se2cad, "DEFAULT_COLOR_MASK_HSV"))
        self.assertFalse(hasattr(se2cad, "generate_canonical_parts"))

    def test_solidworks_package_imports_without_pywin32(self) -> None:
        import se2cad.solidworks as sw

        self.assertEqual(
            sw.logical_part_filename("large_armor_block"),
            "large_armor_block.SLDPRT",
        )
        with patch("se2cad.solidworks.availability._windows", return_value=True):
            with patch("se2cad.solidworks.availability._pywin32_present", return_value=False):
                self.assertFalse(sw.solidworks_backend_available())
                status = sw.solidworks_backend_status()
                self.assertFalse(status.available)
                self.assertIn("pywin32", status.reason)

    def test_authoritative_catalog_has_no_machine_paths(self) -> None:
        catalog = (SRC / "catalog" / "large_grid_armor.json").read_text(encoding="utf-8")
        for token in ("/home/", "C:\\", "C:/", ".SLDPRT", ".sldprt"):
            self.assertNotIn(token, catalog)

    def test_library_records_remain_unbound(self) -> None:
        from se2cad.library import all_library_records

        for record in all_library_records():
            self.assertIsNone(record.placement.part_locator)
