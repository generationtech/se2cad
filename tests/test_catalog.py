"""Deterministic tests for the S2C-2.1.1 definition catalog."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from se2cad.catalog import (
    CATALOG_SCHEMA_VERSION,
    LARGE_GRID_CELL_PITCH_MM,
    CellSize,
    RecipeKind,
    SupportStatus,
    UnknownSubtypeError,
    default_catalog_path,
    load_default_catalog,
)

EXPECTED_SUPPORTED = {
    "LargeBlockArmorBlock": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Box",
        "geometry_id": "large_armor_block",
    },
    "LargeBlockArmorSlope": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Slope",
        "geometry_id": "large_armor_slope",
    },
    "LargeBlockArmorCorner": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Corner",
        "geometry_id": "large_armor_corner",
    },
    "LargeBlockArmorCornerInv": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "InvCorner",
        "geometry_id": "large_armor_corner_inv",
    },
}

EXPECTED_EXPANDED = {
    "LargeHeavyBlockArmorBlock": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Box",
        "geometry_id": "large_heavy_block_armor_block",
    },
    "LargeHeavyBlockArmorSlope": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Slope",
        "geometry_id": "large_heavy_block_armor_slope",
    },
    "LargeHeavyBlockArmorCorner": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Corner",
        "geometry_id": "large_heavy_block_armor_corner",
    },
    "LargeHeavyBlockArmorCornerInv": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "InvCorner",
        "geometry_id": "large_heavy_block_armor_corner_inv",
    },
}


class DefaultCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()

    def test_original_four_supported_subtypes_remain(self) -> None:
        ids = [entry.subtype_id for entry in self.catalog.entries]
        self.assertEqual(ids[:4], list(EXPECTED_SUPPORTED))
        self.assertGreater(len(ids), 4)
        self.assertEqual(ids[4:8], list(EXPECTED_EXPANDED))
        self.assertEqual(ids[8], "LargeBlockSmallHydrogenThrust")
        self.assertEqual(
            ids[9:],
            [
                "LargeBlockArmorSlope2Base",
                "LargeBlockArmorSlope2Tip",
                "LargeHalfArmorBlock",
                "LargeHeavyHalfArmorBlock",
            ],
        )

    def test_observed_definition_facts(self) -> None:
        for subtype_id, expected in {**EXPECTED_SUPPORTED, **EXPECTED_EXPANDED}.items():
            entry = self.catalog.lookup(subtype_id)
            self.assertEqual(entry.observed.type_id, expected["type_id"])
            self.assertEqual(entry.observed.cube_size, expected["cube_size"])
            self.assertEqual(
                entry.observed.size,
                CellSize(*expected["size"]),
            )
            self.assertEqual(
                entry.observed.block_topology, expected["block_topology"]
            )
            self.assertEqual(
                entry.observed.cube_topology, expected["cube_topology"]
            )

    def test_geometry_identities_are_distinct_se2cad_ids(self) -> None:
        geometry_ids = []
        for subtype_id, expected in {**EXPECTED_SUPPORTED, **EXPECTED_EXPANDED}.items():
            entry = self.catalog.lookup(subtype_id)
            self.assertEqual(entry.geometry_id, expected["geometry_id"])
            self.assertNotEqual(entry.geometry_id, subtype_id)
            geometry_ids.append(entry.geometry_id)
        self.assertEqual(len(set(geometry_ids)), len(geometry_ids))
        self.assertNotEqual(
            EXPECTED_SUPPORTED["LargeBlockArmorCorner"]["geometry_id"],
            EXPECTED_SUPPORTED["LargeBlockArmorCornerInv"]["geometry_id"],
        )
        self.assertNotEqual(
            EXPECTED_SUPPORTED["LargeBlockArmorBlock"]["geometry_id"],
            EXPECTED_EXPANDED["LargeHeavyBlockArmorBlock"]["geometry_id"],
        )

    def test_recipe_kind_and_support_status(self) -> None:
        for subtype_id in EXPECTED_SUPPORTED:
            entry = self.catalog.lookup(subtype_id)
            self.assertEqual(entry.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)
        for subtype_id in EXPECTED_EXPANDED:
            entry = self.catalog.lookup(subtype_id)
            self.assertEqual(entry.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)

    def test_lookup_is_exact_and_case_sensitive(self) -> None:
        exact = self.catalog.lookup("LargeBlockArmorBlock")
        self.assertEqual(exact.subtype_id, "LargeBlockArmorBlock")
        for wrong in (
            "largeblockarmorblock",
            "LARGEBLOCKARMORBLOCK",
            "LargeBlockArmorblock",
            "LargeBlockArmorBlock ",
            " LargeBlockArmorBlock",
        ):
            with self.subTest(wrong=wrong):
                with self.assertRaises(UnknownSubtypeError) as ctx:
                    self.catalog.lookup(wrong)
                self.assertIn(wrong, str(ctx.exception))
                self.assertNotIn("LargeBlockArmorSlope", str(ctx.exception))

    def test_unknown_subtype_fails_clearly(self) -> None:
        with self.assertRaises(UnknownSubtypeError) as ctx:
            self.catalog.lookup("SmallBlockArmorBlock")
        self.assertIn("SmallBlockArmorBlock", str(ctx.exception))

    def test_cell_pitch_comes_from_the_named_constant(self) -> None:
        self.assertEqual(LARGE_GRID_CELL_PITCH_MM, 2500)
        self.assertEqual(
            self.catalog.large_grid_cell_pitch_mm, LARGE_GRID_CELL_PITCH_MM
        )

    def test_packaged_catalog_has_no_machine_or_asset_paths(self) -> None:
        path = default_catalog_path()
        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "large_grid_armor.json")
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        self.assertEqual(data["schema_version"], CATALOG_SCHEMA_VERSION)
        serialized = json.dumps(data)
        self.assertNotIn("/home/", serialized)
        self.assertNotIn("C:\\\\", serialized)
        self.assertNotIn(".mwm", serialized.lower())
        self.assertNotIn(".fbx", serialized.lower())
        self.assertNotIn(".dds", serialized.lower())
        self.assertNotIn("Steam", serialized)
        self.assertNotIn("SpaceEngineers", serialized)


class CatalogIndependenceTests(unittest.TestCase):
    def test_catalog_modules_do_not_import_parser_or_cad(self) -> None:
        catalog_root = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "catalog"
        forbidden = (
            "se2cad.parser",
            "solidworks",
            "win32com",
            "blender",
            "subprocess",
        )
        for path in catalog_root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, msg=f"{path.name} mentions {token}")

    def test_catalog_implementation_does_not_encode_fixture_counts(self) -> None:
        catalog_root = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "catalog"
        for path in list(catalog_root.glob("*.py")) + list(catalog_root.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\b24\b", msg=f"{path.name} encodes 24")


if __name__ == "__main__":
    unittest.main()
