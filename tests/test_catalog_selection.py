"""S2C-11.3.1 geometry provenance and recipe selection."""

from __future__ import annotations

import unittest

from se2cad.catalog import (
    CatalogEntry,
    CatalogValidationError,
    CellSize,
    DefinitionCatalog,
    ExceptionReason,
    GeometryClass,
    ObservedDefinition,
    ObservedIdentity,
    RecipeKind,
    SupportStatus,
    classify_observed,
    expand_catalog_identities,
    load_default_catalog,
    provenance_records,
    query_exception_records,
    select_catalog_recipes,
)
from se2cad.ir import build_canonical_blueprint
from se2cad.library import lookup_recipe
from se2cad.parser import parse_blueprint
from pathlib import Path

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "acceptance"
    / "four-block-armor-asymmetric"
    / "bp.sbc"
)


def _observed(
    *,
    type_id: str = "CubeBlock",
    cube_size: str = "Large",
    size: tuple[int, int, int] = (1, 1, 1),
    block_topology: str = "Cube",
    cube_topology: str | None = "Box",
) -> ObservedDefinition:
    return ObservedDefinition(
        type_id=type_id,
        cube_size=cube_size,
        size=CellSize(*size),
        block_topology=block_topology,
        cube_topology=cube_topology,
    )


def _entry(
    subtype_id: str,
    geometry_id: str,
    observed: ObservedDefinition,
    *,
    recipe_kind: RecipeKind = RecipeKind.UNSUPPORTED,
    support_status: SupportStatus = SupportStatus.UNSUPPORTED,
) -> CatalogEntry:
    return CatalogEntry(
        subtype_id=subtype_id,
        observed=observed,
        geometry_id=geometry_id,
        recipe_kind=recipe_kind,
        support_status=support_status,
    )


class ClassifyObservedTests(unittest.TestCase):
    def test_cube_topology_armor_is_automatable_not_supported(self) -> None:
        for topology in ("Box", "Slope", "Corner", "InvCorner", "Slope2Base"):
            with self.subTest(topology=topology):
                classification = classify_observed(_observed(cube_topology=topology))
                self.assertEqual(classification.geometry_class, GeometryClass.AUTOMATABLE)
                self.assertEqual(classification.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
                self.assertIsNone(classification.exception_reason)
                self.assertIn("support is not implied", classification.decision_note)

    def test_triangle_mesh_is_long_tail(self) -> None:
        classification = classify_observed(
            _observed(block_topology="TriangleMesh", cube_topology=None)
        )
        self.assertEqual(classification.geometry_class, GeometryClass.LONG_TAIL)
        self.assertEqual(classification.recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(classification.exception_reason, ExceptionReason.TRIANGLE_MESH)

    def test_missing_cube_topology_is_long_tail(self) -> None:
        classification = classify_observed(_observed(cube_topology=None))
        self.assertEqual(classification.exception_reason, ExceptionReason.MISSING_CUBE_TOPOLOGY)
        self.assertEqual(classification.recipe_kind, RecipeKind.UNSUPPORTED)

    def test_unusual_block_topology_is_not_triangle_mesh(self) -> None:
        classification = classify_observed(
            _observed(block_topology="Other", cube_topology=None)
        )
        self.assertEqual(
            classification.exception_reason, ExceptionReason.UNUSUAL_BLOCK_TOPOLOGY
        )
        self.assertNotEqual(classification.exception_reason, ExceptionReason.TRIANGLE_MESH)

    def test_unusual_type_id_is_not_collapsed_to_triangle_mesh(self) -> None:
        classification = classify_observed(_observed(type_id="Thrust"))
        self.assertEqual(classification.exception_reason, ExceptionReason.UNUSUAL_TYPE_ID)
        self.assertNotEqual(classification.exception_reason, ExceptionReason.TRIANGLE_MESH)

    def test_small_grid_is_not_activated(self) -> None:
        classification = classify_observed(_observed(cube_size="Small"))
        self.assertEqual(
            classification.exception_reason, ExceptionReason.SMALL_GRID_NOT_ACTIVATED
        )
        self.assertEqual(classification.recipe_kind, RecipeKind.UNSUPPORTED)


class SelectCatalogRecipesTests(unittest.TestCase):
    def test_packaged_identities_are_explicit_and_automatable(self) -> None:
        catalog = load_default_catalog()
        report = select_catalog_recipes(catalog)
        self.assertEqual(len(report.catalog.entries), len(catalog.entries))
        self.assertEqual(report.exceptions, ())
        original = {
            "LargeBlockArmorBlock",
            "LargeBlockArmorSlope",
            "LargeBlockArmorCorner",
            "LargeBlockArmorCornerInv",
        }
        expanded = {
            "LargeHeavyBlockArmorBlock",
            "LargeHeavyBlockArmorSlope",
            "LargeHeavyBlockArmorCorner",
            "LargeHeavyBlockArmorCornerInv",
        }
        for entry, record in zip(report.catalog.entries, report.provenance):
            self.assertIsNotNone(entry.recipe_kind)
            self.assertIsNotNone(entry.support_status)
            self.assertEqual(record.subtype_id, entry.subtype_id)
            self.assertEqual(record.geometry_class, GeometryClass.AUTOMATABLE)
            self.assertEqual(record.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertIsNone(record.exception_reason)
            if entry.subtype_id in original or entry.subtype_id in expanded:
                self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)
            else:
                self.fail(f"unexpected packaged subtype {entry.subtype_id!r}")

    def test_selection_does_not_grant_or_revoke_packaged_support(self) -> None:
        catalog = load_default_catalog()
        report = select_catalog_recipes(catalog)
        for subtype in (
            "LargeHeavyBlockArmorBlock",
            "LargeHeavyBlockArmorSlope",
            "LargeHeavyBlockArmorCorner",
            "LargeHeavyBlockArmorCornerInv",
        ):
            before = catalog.lookup(subtype)
            entry = report.catalog.lookup(subtype)
            self.assertEqual(entry.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertEqual(entry.support_status, before.support_status)
            self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)
            recipe = lookup_recipe(entry.geometry_id)
            self.assertEqual(recipe.geometry_id, entry.geometry_id)

    def test_expand_then_select_does_not_grant_support(self) -> None:
        expanded = expand_catalog_identities(
            (_observed_identity("LargeBlockArmorBlock"),)
        )
        self.assertEqual(
            expanded.lookup("LargeBlockArmorBlock").recipe_kind,
            RecipeKind.UNSUPPORTED,
        )
        report = select_catalog_recipes(expanded)
        entry = report.catalog.lookup("LargeBlockArmorBlock")
        self.assertEqual(entry.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
        self.assertEqual(entry.support_status, SupportStatus.UNSUPPORTED)
        self.assertEqual(report.exceptions, ())

    def test_triangle_mesh_exception_is_queryable(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "SyntheticTriangleMesh",
                    "synthetic_triangle_mesh",
                    _observed(block_topology="TriangleMesh", cube_topology=None),
                ),
            )
        )
        report = select_catalog_recipes(catalog)
        self.assertEqual(len(report.exceptions), 1)
        exception = report.exceptions[0]
        self.assertEqual(exception.subtype_id, "SyntheticTriangleMesh")
        self.assertEqual(exception.reason, ExceptionReason.TRIANGLE_MESH)
        self.assertFalse(exception.reported_as_supported)
        queried = query_exception_records(report.catalog)
        self.assertEqual(queried, report.exceptions)
        entry = report.catalog.lookup("SyntheticTriangleMesh")
        self.assertEqual(entry.recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(entry.support_status, SupportStatus.UNSUPPORTED)

    def test_query_does_not_rewrite_unselected_recipe_kind(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "PendingArmor",
                    "pending_armor",
                    _observed(),
                ),
            )
        )
        exceptions = query_exception_records(catalog)
        provenance = provenance_records(catalog)
        self.assertEqual(exceptions, ())
        self.assertEqual(catalog.lookup("PendingArmor").recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(provenance[0].recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(provenance[0].geometry_class, GeometryClass.AUTOMATABLE)

    def test_supported_long_tail_fails_closed(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "PretendSupportedMesh",
                    "pretend_supported_mesh",
                    _observed(block_topology="TriangleMesh", cube_topology=None),
                    recipe_kind=RecipeKind.HAND_AUTHORED,
                    support_status=SupportStatus.SUPPORTED,
                ),
            )
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            select_catalog_recipes(catalog)
        self.assertIn("must not be supported", str(ctx.exception))

    def test_sdk_mesh_recipe_fails_closed(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "KeenMeshBlock",
                    "keen_mesh_block",
                    _observed(block_topology="TriangleMesh", cube_topology=None),
                    recipe_kind=RecipeKind.SDK_MESH_DIRECT,
                ),
            )
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            select_catalog_recipes(catalog)
        self.assertIn("ADR-004", str(ctx.exception))

    def test_conflicting_recorded_recipe_fails_closed(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "HandArmor",
                    "hand_armor",
                    _observed(),
                    recipe_kind=RecipeKind.HAND_AUTHORED,
                ),
            )
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            select_catalog_recipes(catalog)
        self.assertIn("conflicts", str(ctx.exception))

    def test_original_four_conversion_unchanged(self) -> None:
        catalog = select_catalog_recipes(load_default_catalog()).catalog
        ir = build_canonical_blueprint(parse_blueprint(_FIXTURE), catalog)
        self.assertEqual(len(ir.grid.blocks), 24)
        for block in ir.grid.blocks:
            self.assertEqual(block.support_status, SupportStatus.SUPPORTED)
            self.assertEqual(block.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)

    def test_selection_is_idempotent_on_packaged_catalog(self) -> None:
        first = select_catalog_recipes(load_default_catalog())
        second = select_catalog_recipes(first.catalog)
        self.assertEqual(first.catalog.entries, second.catalog.entries)
        self.assertEqual(first.exceptions, second.exceptions)


def _observed_identity(subtype_id: str) -> ObservedIdentity:
    return ObservedIdentity(subtype_id=subtype_id, observed=_observed())


class CatalogSelectionIndependenceTests(unittest.TestCase):
    def test_selection_module_is_library_build_only(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "catalog"
            / "selection.py"
        )
        text = path.read_text(encoding="utf-8")
        for token in (
            "se2cad.parser",
            "se2cad.discovery",
            "solidworks",
            "win32com",
            "blender",
            "subprocess",
        ):
            self.assertNotIn(token, text)
        self.assertNotIn(".mwm", text.lower())
        self.assertNotIn(".fbx", text.lower())


if __name__ == "__main__":
    unittest.main()
