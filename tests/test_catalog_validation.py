"""Negative validation tests for catalog JSON loading."""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from se2cad.catalog import (
    CatalogValidationError,
    load_catalog_file,
    load_catalog_text,
    load_default_catalog,
)


def _valid_catalog() -> dict:
    return {
        "schema_version": 1,
        "entries": [
            _entry("LargeBlockArmorBlock", "large_armor_block", "Box"),
            _entry("LargeBlockArmorSlope", "large_armor_slope", "Slope"),
        ],
    }


def _entry(subtype_id: str, geometry_id: str, cube_topology: str) -> dict:
    return {
        "subtype_id": subtype_id,
        "observed": {
            "type_id": "CubeBlock",
            "cube_size": "Large",
            "size": {"x": 1, "y": 1, "z": 1},
            "block_topology": "Cube",
            "cube_topology": cube_topology,
        },
        "se2cad": {
            "geometry_id": geometry_id,
            "recipe_kind": "native_procedural",
            "support_status": "supported",
        },
    }


class CatalogValidationTests(unittest.TestCase):
    def test_duplicate_subtype_ids_fail(self) -> None:
        data = _valid_catalog()
        data["entries"].append(
            _entry("LargeBlockArmorBlock", "large_armor_block_dup", "Box")
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="dup-subtype")
        self.assertIn("duplicate subtype_id", str(ctx.exception))
        self.assertIn("LargeBlockArmorBlock", str(ctx.exception))

    def test_duplicate_geometry_ids_fail(self) -> None:
        data = _valid_catalog()
        data["entries"].append(
            _entry("LargeBlockArmorCorner", "large_armor_block", "Corner")
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="dup-geometry")
        self.assertIn("duplicate geometry_id", str(ctx.exception))
        self.assertIn("large_armor_block", str(ctx.exception))

    def test_unknown_recipe_kind_fails(self) -> None:
        data = _valid_catalog()
        data["entries"][0]["se2cad"]["recipe_kind"] = "procedural"
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="bad-recipe")
        self.assertIn("unknown recipe_kind", str(ctx.exception))
        self.assertIn("procedural", str(ctx.exception))

    def test_malformed_json_fails(self) -> None:
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text("{not json", source="broken")
        self.assertIn("malformed", str(ctx.exception))

    def test_missing_required_fields_fail(self) -> None:
        data = _valid_catalog()
        del data["entries"][0]["observed"]["cube_topology"]
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="missing-field")
        self.assertIn("cube_topology", str(ctx.exception))

    def test_empty_subtype_id_fails(self) -> None:
        data = _valid_catalog()
        data["entries"][0]["subtype_id"] = ""
        with self.assertRaises(CatalogValidationError):
            load_catalog_text(json.dumps(data), source="empty-subtype")

    def test_non_integer_size_fails(self) -> None:
        data = _valid_catalog()
        data["entries"][0]["observed"]["size"]["x"] = "1"
        with self.assertRaises(CatalogValidationError):
            load_catalog_text(json.dumps(data), source="string-size")

    def test_boolean_size_is_not_an_integer(self) -> None:
        data = _valid_catalog()
        data["entries"][0]["observed"]["size"]["y"] = True
        with self.assertRaises(CatalogValidationError):
            load_catalog_text(json.dumps(data), source="bool-size")

    def test_unsupported_schema_version_fails(self) -> None:
        data = _valid_catalog()
        data["schema_version"] = 2
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="schema-2")
        self.assertIn("schema_version", str(ctx.exception))

    def test_unexpected_fields_fail(self) -> None:
        data = _valid_catalog()
        data["entries"][0]["observed"]["model"] = (
            r"Models\Cubes\Large\Armor\SquarePlate.mwm"
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="extra-model")
        self.assertIn("unexpected field", str(ctx.exception))
        self.assertIn("model", str(ctx.exception))

    def test_unknown_support_status_fails(self) -> None:
        data = _valid_catalog()
        data["entries"][0]["se2cad"]["support_status"] = "maybe"
        with self.assertRaises(CatalogValidationError) as ctx:
            load_catalog_text(json.dumps(data), source="bad-support")
        self.assertIn("support_status", str(ctx.exception))

    def test_file_loader_rejects_missing_path(self) -> None:
        with self.assertRaises(CatalogValidationError):
            load_catalog_file(Path("/tmp/se2cad-missing-catalog.json"))

    def test_file_loader_reads_explicit_temp_file(self) -> None:
        data = _valid_catalog()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            catalog = load_catalog_file(path)
        self.assertEqual(len(catalog.entries), 2)
        self.assertEqual(
            catalog.lookup("LargeBlockArmorSlope").geometry_id,
            "large_armor_slope",
        )

    def test_default_catalog_is_valid_and_independent_of_file_loader_samples(self) -> None:
        sample = deepcopy(_valid_catalog())
        sample["entries"][0]["subtype_id"] = "NotARealSubtype"
        loaded = load_catalog_text(json.dumps(sample), source="sample")
        default = load_default_catalog()
        self.assertEqual(loaded.entries[0].subtype_id, "NotARealSubtype")
        self.assertEqual(default.entries[0].subtype_id, "LargeBlockArmorBlock")


if __name__ == "__main__":
    unittest.main()
