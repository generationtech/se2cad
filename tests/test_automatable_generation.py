"""S2C-11.4.1 automated generation for the automatable majority.

Ordinary tests cover recipe/plan construction and fail-closed paths
without SolidWorks.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from se2cad.catalog import SupportStatus, load_default_catalog
from se2cad.library import (
    AUTOMATABLE_CUBE_TOPOLOGIES,
    EDGE_TREATMENT_CHAMFER,
    REPRESENTATIVE_AUTOMATABLE_BINDINGS,
    UnknownGeometryError,
    UnsupportedTopologyError,
    lookup_recipe,
    original_library_geometry_ids,
    recipe_for_topology,
    representative_automatable_geometry_ids,
)
from se2cad.solidworks.errors import UnknownCanonicalPartError
from se2cad.solidworks.artifacts import (
    assert_overwrite_is_canonical,
    canonical_geometry_ids,
    is_canonical_artifact_filename,
    is_treated_artifact_filename,
    logical_part_filename,
    logical_treated_part_filename,
    part_artifact_path,
)
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.errors import GeneratedRootError
from se2cad.solidworks.generate import generate_canonical_parts
from se2cad.solidworks.recipe_plan import plan_from_recipe


_ORIGINAL = (
    "large_armor_block",
    "large_armor_slope",
    "large_armor_corner",
    "large_armor_corner_inv",
)
_REPRESENTATIVE = (
    "large_heavy_block_armor_block",
    "large_heavy_block_armor_slope",
    "large_heavy_block_armor_corner",
    "large_heavy_block_armor_corner_inv",
)
_TOPOLOGIES = ("Box", "Slope", "Corner", "InvCorner")


class TopologyRecipeTests(unittest.TestCase):
    def test_known_topologies_stamp_geometry_id_and_reuse_construction(self) -> None:
        self.assertEqual(AUTOMATABLE_CUBE_TOPOLOGIES, frozenset(_TOPOLOGIES))
        for geometry_id, cube_topology in zip(_ORIGINAL, _TOPOLOGIES, strict=True):
            original = lookup_recipe(geometry_id)
            stamped = recipe_for_topology("synthetic_" + geometry_id, cube_topology)
            self.assertEqual(stamped.geometry_id, "synthetic_" + geometry_id)
            self.assertEqual(stamped.solid_kind, original.solid_kind)
            self.assertEqual(stamped.vertices_mm, original.vertices_mm)
            self.assertEqual(stamped.faces, original.faces)
            self.assertEqual(stamped.construction, original.construction)
            self.assertEqual(
                stamped.orientation.observed_cube_topology, cube_topology
            )
            self.assertEqual(
                stamped.validation.volume_times_6_mm3,
                original.validation.volume_times_6_mm3,
            )

    def test_unknown_automatable_topology_fails_closed(self) -> None:
        with self.assertRaises(UnsupportedTopologyError) as ctx:
            recipe_for_topology("synthetic_slope2", "Slope2Base")
        self.assertIn("Slope2Base", str(ctx.exception))
        self.assertIn("no native construction", str(ctx.exception))

    def test_invalid_geometry_id_fails_closed(self) -> None:
        for bad in ("", "LargeBlockArmorBlock", "2leading", "has-dash"):
            with self.subTest(bad=bad):
                with self.assertRaises(UnknownGeometryError):
                    recipe_for_topology(bad, "Box")


class RepresentativeSubsetTests(unittest.TestCase):
    def test_representative_subset_is_recorded_and_larger_than_original_four(self) -> None:
        self.assertEqual(original_library_geometry_ids(), _ORIGINAL)
        self.assertEqual(canonical_geometry_ids(), _ORIGINAL)
        self.assertEqual(representative_automatable_geometry_ids(), _REPRESENTATIVE)
        self.assertEqual(
            REPRESENTATIVE_AUTOMATABLE_BINDINGS,
            tuple(zip(_REPRESENTATIVE, _TOPOLOGIES, strict=True)),
        )
        self.assertEqual(len(set(_ORIGINAL).intersection(_REPRESENTATIVE)), 0)

    def test_representative_recipes_match_original_topology_solids(self) -> None:
        for original_id, representative_id, topology in zip(
            _ORIGINAL, _REPRESENTATIVE, _TOPOLOGIES, strict=True
        ):
            original = lookup_recipe(original_id)
            representative = lookup_recipe(representative_id)
            self.assertEqual(representative.geometry_id, representative_id)
            self.assertEqual(representative.orientation.observed_cube_topology, topology)
            self.assertEqual(representative.solid_kind, original.solid_kind)
            self.assertEqual(representative.vertices_mm, original.vertices_mm)
            self.assertEqual(representative.construction, original.construction)
            self.assertEqual(
                representative.validation.volume_times_6_mm3,
                original.validation.volume_times_6_mm3,
            )
            self.assertNotEqual(representative.geometry_id, original.geometry_id)

    def test_packaged_representative_identities_are_supported(self) -> None:
        catalog = load_default_catalog()
        for geometry_id in _REPRESENTATIVE:
            matches = [
                entry
                for entry in catalog.entries
                if entry.geometry_id == geometry_id
            ]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].support_status, SupportStatus.SUPPORTED)
            self.assertEqual(matches[0].observed.cube_topology, lookup_recipe(geometry_id).orientation.observed_cube_topology)


class ConstructionPlanTests(unittest.TestCase):
    def test_representative_plans_are_identity_independent(self) -> None:
        for original_id, representative_id in zip(_ORIGINAL, _REPRESENTATIVE, strict=True):
            original = plan_from_recipe(lookup_recipe(original_id))
            representative = plan_from_recipe(lookup_recipe(representative_id))
            self.assertEqual(representative.geometry_id, representative_id)
            self.assertEqual(representative.solid_kind, original.solid_kind)
            self.assertEqual(representative.vertices_m, original.vertices_m)
            self.assertEqual(representative.expected.volume_m3, original.expected.volume_m3)
            self.assertEqual(
                representative.expected.center_of_mass_m,
                original.expected.center_of_mass_m,
            )
            self.assertEqual(
                representative.expected.bounding_box_min_m,
                original.expected.bounding_box_min_m,
            )
            self.assertEqual(
                representative.expected.bounding_box_max_m,
                original.expected.bounding_box_max_m,
            )


class ArtifactNamingTests(unittest.TestCase):
    def test_representative_ids_have_deterministic_filenames(self) -> None:
        for geometry_id in _REPRESENTATIVE:
            self.assertEqual(
                logical_part_filename(geometry_id), f"{geometry_id}.SLDPRT"
            )
            treated = logical_treated_part_filename(
                geometry_id, EDGE_TREATMENT_CHAMFER
            )
            self.assertEqual(treated, f"{geometry_id}_chamfer_50mm.SLDPRT")
            self.assertTrue(is_canonical_artifact_filename(f"{geometry_id}.SLDPRT"))
            self.assertTrue(is_treated_artifact_filename(treated))

    def test_unknown_id_still_has_no_artifact_name(self) -> None:
        with self.assertRaises(UnknownCanonicalPartError):
            logical_part_filename("synthetic_unknown_block")
        with self.assertRaises(UnknownCanonicalPartError):
            logical_treated_part_filename(
                "synthetic_unknown_block", EDGE_TREATMENT_CHAMFER
            )

    def test_overwrite_of_representative_artifact_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            owned = Path(tmp) / "large_heavy_block_armor_block.SLDPRT"
            owned.write_bytes(b"stub")
            assert_overwrite_is_canonical(owned)
            dest = part_artifact_path(Path(tmp), "large_heavy_block_armor_block")
            self.assertEqual(dest.name, "large_heavy_block_armor_block.SLDPRT")
            dest.relative_to(Path(tmp).resolve())


class FailClosedGenerationTests(unittest.TestCase):
    def test_empty_and_duplicate_geometry_ids_fail_before_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = SolidWorksBackendConfig(
                generated_root=Path(tmp).resolve(),
                part_template=None,
                visible=False,
                source="test",
            )
            with self.assertRaises(GeneratedRootError):
                generate_canonical_parts(config, geometry_ids=())
            with self.assertRaises(GeneratedRootError):
                generate_canonical_parts(
                    config,
                    geometry_ids=(
                        "large_heavy_block_armor_block",
                        "large_heavy_block_armor_block",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
