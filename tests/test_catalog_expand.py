"""S2C-11.2.1 catalog identity expansion from observed facts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from se2cad.catalog import (
    CATALOG_SCHEMA_VERSION,
    CatalogValidationError,
    CellSize,
    ObservedDefinition,
    ObservedIdentity,
    RecipeKind,
    SupportStatus,
    catalog_to_data,
    expand_catalog_identities,
    geometry_id_for_subtype,
    load_catalog_text,
    load_default_catalog,
)
from se2cad.discovery import parse_cube_block_definitions_xml
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import parse_blueprint

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "acceptance"
    / "four-block-armor-asymmetric"
    / "bp.sbc"
)


def _observed(
    subtype_id: str,
    *,
    cube_size: str = "Large",
    cube_topology: str | None = "Box",
    type_id: str = "CubeBlock",
    block_topology: str = "Cube",
    size: tuple[int, int, int] = (1, 1, 1),
) -> ObservedIdentity:
    return ObservedIdentity(
        subtype_id=subtype_id,
        observed=ObservedDefinition(
            type_id=type_id,
            cube_size=cube_size,
            size=CellSize(*size),
            block_topology=block_topology,
            cube_topology=cube_topology,
        ),
    )


class GeometryIdRuleTests(unittest.TestCase):
    def test_preserved_ids_for_original_four(self) -> None:
        self.assertEqual(
            geometry_id_for_subtype("LargeBlockArmorBlock"), "large_armor_block"
        )
        self.assertEqual(
            geometry_id_for_subtype("LargeBlockArmorSlope"), "large_armor_slope"
        )
        self.assertEqual(
            geometry_id_for_subtype("LargeBlockArmorCorner"), "large_armor_corner"
        )
        self.assertEqual(
            geometry_id_for_subtype("LargeBlockArmorCornerInv"),
            "large_armor_corner_inv",
        )

    def test_derived_ids_are_distinct_from_subtype(self) -> None:
        gid = geometry_id_for_subtype("LargeHeavyBlockArmorBlock")
        self.assertEqual(gid, "large_heavy_block_armor_block")
        self.assertNotEqual(gid, "LargeHeavyBlockArmorBlock")
        already_snake = geometry_id_for_subtype("already_snake")
        self.assertEqual(already_snake, "lg_already_snake")


class ExpandCatalogTests(unittest.TestCase):
    def test_preserves_existing_decisions_and_adds_unsupported(self) -> None:
        existing = load_default_catalog()
        identities = (
            _observed("LargeBlockArmorBlock"),
            _observed("LargeBlockArmorSlope", cube_topology="Slope"),
            _observed("LargeBlockArmorCorner", cube_topology="Corner"),
            _observed("LargeBlockArmorCornerInv", cube_topology="InvCorner"),
            _observed("LargeHeavyBlockArmorBlock"),
            _observed(
                "SyntheticTriangleMesh",
                cube_topology=None,
                block_topology="TriangleMesh",
            ),
        )
        expanded = expand_catalog_identities(identities, existing=existing)
        self.assertEqual(
            [entry.subtype_id for entry in expanded.entries[:4]],
            [entry.subtype_id for entry in existing.entries[:4]],
        )
        for subtype in (
            "LargeBlockArmorBlock",
            "LargeBlockArmorSlope",
            "LargeBlockArmorCorner",
            "LargeBlockArmorCornerInv",
        ):
            entry = expanded.lookup(subtype)
            self.assertEqual(entry.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)
        heavy = expanded.lookup("LargeHeavyBlockArmorBlock")
        self.assertEqual(heavy.geometry_id, "large_heavy_block_armor_block")
        self.assertEqual(heavy.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
        self.assertEqual(heavy.support_status, SupportStatus.UNSUPPORTED)
        mesh = expanded.lookup("SyntheticTriangleMesh")
        self.assertIsNone(mesh.observed.cube_topology)
        self.assertEqual(mesh.recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(mesh.support_status, SupportStatus.UNSUPPORTED)

    def test_does_not_mark_supported_without_existing_decision(self) -> None:
        expanded = expand_catalog_identities((_observed("LargeBlockArmorBlock"),))
        entry = expanded.lookup("LargeBlockArmorBlock")
        self.assertEqual(entry.geometry_id, "large_armor_block")
        self.assertEqual(entry.recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(entry.support_status, SupportStatus.UNSUPPORTED)

    def test_skips_small_grid(self) -> None:
        expanded = expand_catalog_identities(
            (
                _observed("LargeBlockArmorBlock"),
                _observed("SmallBlockArmorBlock", cube_size="Small"),
            )
        )
        subtypes = [entry.subtype_id for entry in expanded.entries]
        self.assertEqual(subtypes, ["LargeBlockArmorBlock"])

    def test_invalid_derived_geometry_id_fails_closed(self) -> None:
        with self.assertRaises(CatalogValidationError) as ctx:
            expand_catalog_identities((_observed("2LeadingDigit"),))
        self.assertIn("lowercase ASCII letter", str(ctx.exception))

    def test_duplicate_input_subtype_fails(self) -> None:
        with self.assertRaises(CatalogValidationError) as ctx:
            expand_catalog_identities(
                (_observed("LargeBlockArmorBlock"), _observed("LargeBlockArmorBlock"))
            )
        self.assertIn("duplicate subtype_id", str(ctx.exception))

    def test_conflicting_observed_facts_fail(self) -> None:
        existing = load_default_catalog()
        with self.assertRaises(CatalogValidationError) as ctx:
            expand_catalog_identities(
                (_observed("LargeBlockArmorBlock", cube_topology="Slope"),),
                existing=existing,
            )
        self.assertIn("conflicting observed facts", str(ctx.exception))

    def test_roundtrip_loader_rejects_paths_and_keeps_schema(self) -> None:
        expanded = expand_catalog_identities(
            (
                _observed("LargeBlockArmorBlock"),
                _observed("LargeHeavyBlockArmorBlock"),
            )
        )
        data = catalog_to_data(expanded)
        self.assertEqual(data["schema_version"], CATALOG_SCHEMA_VERSION)
        serialized = json.dumps(data)
        self.assertNotIn("/home/", serialized)
        self.assertNotIn("C:\\", serialized)
        self.assertNotIn(".mwm", serialized.lower())
        self.assertNotIn(".fbx", serialized.lower())
        loaded = load_catalog_text(json.dumps(data), source="expanded")
        self.assertEqual(
            [entry.subtype_id for entry in loaded.entries],
            [entry.subtype_id for entry in expanded.entries],
        )

    def test_discovery_records_resolve_without_writing_paths(self) -> None:
        xml = (
            '<?xml version="1.0"?>'
            '<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            "<CubeBlocks>"
            "<Definition><Id><TypeId>CubeBlock</TypeId>"
            "<SubtypeId>LargeBlockArmorBlock</SubtypeId></Id>"
            "<CubeSize>Large</CubeSize><Size x=\"1\" y=\"1\" z=\"1\" />"
            "<BlockTopology>Cube</BlockTopology>"
            "<CubeDefinition><CubeTopology>Box</CubeTopology></CubeDefinition>"
            r"<Model>Models\Cubes\Large\armor.mwm</Model>"
            "</Definition>"
            "<Definition><Id><TypeId>CubeBlock</TypeId>"
            "<SubtypeId>LargeHeavyBlockArmorBlock</SubtypeId></Id>"
            "<CubeSize>Large</CubeSize><Size x=\"1\" y=\"1\" z=\"1\" />"
            "<BlockTopology>Cube</BlockTopology>"
            "<CubeDefinition><CubeTopology>Box</CubeTopology></CubeDefinition>"
            "</Definition>"
            "<Definition><Id><TypeId>CubeBlock</TypeId>"
            "<SubtypeId>SmallBlockArmorBlock</SubtypeId></Id>"
            "<CubeSize>Small</CubeSize><Size x=\"1\" y=\"1\" z=\"1\" />"
            "<BlockTopology>Cube</BlockTopology>"
            "<CubeDefinition><CubeTopology>Box</CubeTopology></CubeDefinition>"
            "</Definition>"
            "</CubeBlocks></Definitions>"
        )
        discovered = parse_cube_block_definitions_xml(
            xml,
            source="synthetic.sbc",
            source_kind="game",
            source_relative="Content/Data/CubeBlocks/synthetic.sbc",
        )
        identities = tuple(
            ObservedIdentity(
                subtype_id=item.subtype_id,
                observed=ObservedDefinition(
                    type_id=item.type_id,
                    cube_size=item.cube_size,
                    size=item.size,
                    block_topology=item.block_topology,
                    cube_topology=item.cube_topology,
                ),
            )
            for item in discovered
        )
        expanded = expand_catalog_identities(identities, existing=load_default_catalog())
        data = catalog_to_data(expanded)
        serialized = json.dumps(data)
        self.assertNotIn("Content/Data", serialized)
        self.assertNotIn(".mwm", serialized.lower())
        self.assertNotIn("synthetic.sbc", serialized)
        subtypes = [entry.subtype_id for entry in expanded.entries]
        self.assertIn("LargeHeavyBlockArmorBlock", subtypes)
        self.assertNotIn("SmallBlockArmorBlock", subtypes)

    def test_original_four_conversion_unchanged(self) -> None:
        catalog = load_default_catalog()
        ir = build_canonical_blueprint(parse_blueprint(_FIXTURE), catalog)
        self.assertEqual(len(ir.grid.blocks), 24)
        for block in ir.grid.blocks:
            self.assertIn(
                block.subtype_id,
                {
                    "LargeBlockArmorBlock",
                    "LargeBlockArmorSlope",
                    "LargeBlockArmorCorner",
                    "LargeBlockArmorCornerInv",
                },
            )
            self.assertEqual(block.support_status, SupportStatus.SUPPORTED)
            self.assertEqual(block.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)


if __name__ == "__main__":
    unittest.main()
