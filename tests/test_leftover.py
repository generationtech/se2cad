"""S2C-11.5.1 leftover workflow and support-status honesty."""

from __future__ import annotations

import json
import unittest

from se2cad.catalog import (
    COVERAGE_CLAIM_NOT_UNIVERSAL,
    CatalogEntry,
    CatalogValidationError,
    CellSize,
    DefinitionCatalog,
    EVIDENCED_RESIDUAL_TOPOLOGIES,
    ExceptionReason,
    GenerationOutcome,
    LeftoverKind,
    ObservedDefinition,
    ObservedIdentity,
    RecipeKind,
    SupportStatus,
    assert_leftover_honesty,
    assert_packaged_leftover_matches_catalog,
    conversion_may_report_supported,
    evaluate_leftover_set,
    load_default_catalog,
    load_leftover_text,
    stamp_automatable_remainder,
)
from se2cad.library import lookup_recipe


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


class PackagedLeftoverTests(unittest.TestCase):
    def test_packaged_leftover_matches_catalog_and_is_not_universal(self) -> None:
        leftover_set = assert_packaged_leftover_matches_catalog()
        self.assertEqual(leftover_set.coverage_claim, COVERAGE_CLAIM_NOT_UNIVERSAL)
        self.assertEqual(
            leftover_set.coverage_claim,
            "not_universal_vanilla",
        )
        catalog = load_default_catalog()
        self.assertEqual(
            [item.subtype_id for item in leftover_set.completed_automatable],
            [entry.subtype_id for entry in catalog.entries],
        )
        self.assertEqual(len(leftover_set.leftovers), 1)
        leftover = leftover_set.leftovers[0]
        self.assertEqual(leftover.kind, LeftoverKind.MISSING_CONSTRUCTION)
        self.assertEqual(leftover.cube_topology, "Slope2Base")
        self.assertIn(leftover.cube_topology, EVIDENCED_RESIDUAL_TOPOLOGIES)
        self.assertFalse(leftover.reported_as_supported)
        self.assertEqual(leftover.subtype_id, "")
        self.assertEqual(leftover.geometry_id, "")

    def test_packaged_supported_entries_may_report_supported_conversion(self) -> None:
        leftover_set = assert_packaged_leftover_matches_catalog()
        catalog = load_default_catalog()
        for entry in catalog.entries:
            self.assertTrue(conversion_may_report_supported(entry, leftover_set))
            lookup_recipe(entry.geometry_id)

    def test_packaged_remainder_is_already_stamped(self) -> None:
        self.assertEqual(stamp_automatable_remainder(load_default_catalog()), ())


class ExceptionHonestyTests(unittest.TestCase):
    def test_unclassified_identity_cannot_report_supported(self) -> None:
        catalog = load_default_catalog()
        leftover_set = evaluate_leftover_set(
            catalog,
            observed_identities=(
                ObservedIdentity("UnknownFunctionalBlock", _observed()),
            ),
        )
        unclassified = [
            record
            for record in leftover_set.leftovers
            if record.kind is LeftoverKind.UNCLASSIFIED
        ]
        self.assertEqual(len(unclassified), 1)
        self.assertEqual(unclassified[0].subtype_id, "UnknownFunctionalBlock")
        self.assertFalse(unclassified[0].reported_as_supported)
        assert_leftover_honesty(leftover_set, catalog)

    def test_unsupported_recipe_kind_cannot_report_supported(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry("PendingArmor", "pending_armor", _observed()),
            )
        )
        leftover_set = evaluate_leftover_set(
            catalog, residual_topologies=frozenset()
        )
        self.assertEqual(len(leftover_set.leftovers), 1)
        leftover = leftover_set.leftovers[0]
        self.assertEqual(leftover.kind, LeftoverKind.UNSUPPORTED_RECIPE_KIND)
        self.assertFalse(leftover.reported_as_supported)
        self.assertFalse(
            conversion_may_report_supported(catalog.entries[0], leftover_set)
        )
        assert_leftover_honesty(leftover_set, catalog)

    def test_long_tail_cannot_report_supported(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "SyntheticTriangleMesh",
                    "synthetic_triangle_mesh",
                    _observed(block_topology="TriangleMesh", cube_topology=None),
                ),
            )
        )
        leftover_set = evaluate_leftover_set(
            catalog, residual_topologies=frozenset()
        )
        leftover = leftover_set.leftovers[0]
        self.assertEqual(leftover.kind, LeftoverKind.LONG_TAIL)
        self.assertEqual(leftover.exception_reason, ExceptionReason.TRIANGLE_MESH)
        self.assertFalse(leftover.reported_as_supported)
        self.assertFalse(
            conversion_may_report_supported(catalog.entries[0], leftover_set)
        )
        assert_leftover_honesty(leftover_set, catalog)

    def test_failed_generation_cannot_report_supported(self) -> None:
        catalog = load_default_catalog()
        leftover_set = evaluate_leftover_set(
            catalog,
            generation_outcomes=(
                GenerationOutcome(
                    "large_armor_block",
                    succeeded=False,
                    detail="validation failed",
                ),
            ),
        )
        failed = [
            record
            for record in leftover_set.leftovers
            if record.kind is LeftoverKind.FAILED_GENERATION
        ]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].geometry_id, "large_armor_block")
        self.assertFalse(failed[0].reported_as_supported)
        entry = catalog.lookup("LargeBlockArmorBlock")
        self.assertFalse(conversion_may_report_supported(entry, leftover_set))
        with self.assertRaises(CatalogValidationError) as ctx:
            assert_leftover_honesty(leftover_set, catalog)
        self.assertIn("must not be catalogued as supported", str(ctx.exception))

    def test_missing_construction_stays_listed(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "SyntheticSlope2",
                    "synthetic_slope2",
                    _observed(cube_topology="Slope2Base"),
                    recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
                ),
            )
        )
        leftover_set = evaluate_leftover_set(catalog)
        kinds = [record.kind for record in leftover_set.leftovers]
        self.assertIn(LeftoverKind.MISSING_CONSTRUCTION, kinds)
        slope2 = [
            record
            for record in leftover_set.leftovers
            if record.subtype_id == "SyntheticSlope2"
        ]
        self.assertEqual(len(slope2), 1)
        self.assertFalse(slope2[0].reported_as_supported)
        self.assertFalse(
            conversion_may_report_supported(catalog.entries[0], leftover_set)
        )
        self.assertEqual(stamp_automatable_remainder(catalog), ())

    def test_remainder_with_known_topology_is_stamped_not_supported(self) -> None:
        catalog = DefinitionCatalog(
            entries=(
                _entry(
                    "SyntheticExtraBox",
                    "synthetic_extra_box",
                    _observed(),
                    recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
                ),
            )
        )
        leftover_set = evaluate_leftover_set(
            catalog, residual_topologies=frozenset()
        )
        self.assertEqual(leftover_set.leftovers[0].kind, LeftoverKind.RESIDUAL_AUTOMATABLE)
        self.assertFalse(leftover_set.leftovers[0].reported_as_supported)
        stamped = stamp_automatable_remainder(catalog)
        self.assertEqual(len(stamped), 1)
        self.assertEqual(stamped[0].geometry_id, "synthetic_extra_box")
        self.assertEqual(stamped[0].orientation.observed_cube_topology, "Box")
        self.assertEqual(catalog.lookup("SyntheticExtraBox").support_status, SupportStatus.UNSUPPORTED)

    def test_supported_leftover_payload_fails_closed(self) -> None:
        payload = {
            "schema_version": 1,
            "coverage_claim": "not_universal_vanilla",
            "completed_automatable": [],
            "leftovers": [
                {
                    "kind": "long_tail",
                    "subtype_id": "PretendSupported",
                    "geometry_id": "pretend_supported",
                    "cube_topology": "",
                    "detail": "must fail",
                    "reported_as_supported": True,
                }
            ],
        }
        with self.assertRaises(CatalogValidationError) as ctx:
            load_leftover_text(json.dumps(payload), source="supported-leftover")
        self.assertIn("must be false", str(ctx.exception))

    def test_universal_coverage_claim_fails_closed(self) -> None:
        payload = {
            "schema_version": 1,
            "coverage_claim": "universal_vanilla",
            "completed_automatable": [],
            "leftovers": [],
        }
        with self.assertRaises(CatalogValidationError) as ctx:
            load_leftover_text(json.dumps(payload), source="universal")
        self.assertIn("coverage_claim", str(ctx.exception))

    def test_evaluate_rejects_smuggled_asset_tokens(self) -> None:
        catalog = load_default_catalog()
        with self.assertRaises(CatalogValidationError) as ctx:
            evaluate_leftover_set(
                catalog,
                observed_identities=(
                    ObservedIdentity(
                        r"Models\Cubes\Large\armor.mwm",
                        _observed(),
                    ),
                ),
            )
        self.assertIn("proprietary asset", str(ctx.exception))

    def test_asset_path_in_leftover_fails_closed(self) -> None:
        payload = {
            "schema_version": 1,
            "coverage_claim": "not_universal_vanilla",
            "completed_automatable": [],
            "leftovers": [
                {
                    "kind": "long_tail",
                    "subtype_id": "MeshBlock",
                    "geometry_id": "",
                    "cube_topology": "",
                    "detail": r"Models\Cubes\Large\armor.mwm",
                    "reported_as_supported": False,
                }
            ],
        }
        with self.assertRaises(CatalogValidationError) as ctx:
            load_leftover_text(json.dumps(payload), source="smuggled-mwm")
        self.assertIn("proprietary asset", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
