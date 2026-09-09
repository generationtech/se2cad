"""CAD-neutral optional block-edge treatment (S2C-10.1.1)."""

from __future__ import annotations

import math
import unittest

from se2cad.catalog import load_default_catalog
from se2cad.library import (
    CANONICAL_CELL_ENVELOPE,
    CANONICAL_LOCAL_FRAME,
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_MIN_VOLUME_RATIO,
    EDGE_TREATMENT_OFF,
    EDGE_TREATMENT_SETBACK_MM,
    InvalidSolidError,
    TreatmentError,
    all_library_records,
    apply_edge_treatment,
    bounding_box,
    lookup_recipe,
    mesh_edges,
    solid_from_recipe,
    solid_from_vertices_faces,
    volume_times_6,
)
from se2cad.library.solid import clip_solid_by_plane
from se2cad.library.treatment import EdgeTreatmentKind, EdgeTreatmentRequest

_CATALOG_GEOMETRY_IDS = (
    "large_armor_block",
    "large_armor_slope",
    "large_armor_corner",
    "large_armor_corner_inv",
)


def _box_solid(
    min_mm: tuple[int, int, int],
    max_mm: tuple[int, int, int],
):
    x0, y0, z0 = min_mm
    x1, y1, z1 = max_mm
    vertices = (
        (x0, y0, z0),
        (x1, y0, z0),
        (x0, y1, z0),
        (x1, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x0, y1, z1),
        (x1, y1, z1),
    )
    faces = (
        (1, 3, 7, 5),
        (4, 6, 2, 0),
        (2, 6, 7, 3),
        (0, 1, 5, 4),
        (5, 7, 6, 4),
        (0, 2, 3, 1),
    )
    return solid_from_vertices_faces(vertices, faces)


def _l_solid():
    """Concave L-prism with no catalog geometry_id."""
    vertices = (
        (0.0, 0.0, 0.0),
        (2000.0, 0.0, 0.0),
        (2000.0, 1000.0, 0.0),
        (1000.0, 1000.0, 0.0),
        (1000.0, 2000.0, 0.0),
        (0.0, 2000.0, 0.0),
        (0.0, 0.0, 1000.0),
        (2000.0, 0.0, 1000.0),
        (2000.0, 1000.0, 1000.0),
        (1000.0, 1000.0, 1000.0),
        (1000.0, 2000.0, 1000.0),
        (0.0, 2000.0, 1000.0),
    )
    faces = (
        (0, 5, 4, 3, 2, 1),
        (6, 7, 8, 9, 10, 11),
        (0, 1, 7, 6),
        (1, 2, 8, 7),
        (2, 3, 9, 8),
        (3, 4, 10, 9),
        (4, 5, 11, 10),
        (5, 0, 6, 11),
    )
    return solid_from_vertices_faces(vertices, faces)


class DefaultOffTests(unittest.TestCase):
    def test_omitted_and_explicit_off_leave_recipe_meshes_identical(self) -> None:
        for geometry_id in _CATALOG_GEOMETRY_IDS:
            solid = solid_from_recipe(lookup_recipe(geometry_id))
            omitted = apply_edge_treatment(solid)
            explicit = apply_edge_treatment(solid, EDGE_TREATMENT_OFF)
            for result in (omitted, explicit):
                with self.subTest(geometry_id=geometry_id, applied=result.applied):
                    self.assertFalse(result.applied)
                    self.assertIs(result.solid, solid)
                    self.assertEqual(result.treated_edge_count, 0)
                    self.assertEqual(result.solid.vertices, solid.vertices)
                    self.assertEqual(result.solid.faces, solid.faces)
                    self.assertEqual(result.volume_times_6, volume_times_6(solid))

    def test_lookup_recipe_stays_untreated_after_a_chamfer_request(self) -> None:
        before = lookup_recipe("large_armor_block")
        apply_edge_treatment(solid_from_recipe(before), EDGE_TREATMENT_CHAMFER)
        after = lookup_recipe("large_armor_block")
        self.assertEqual(after.geometry_id, "large_armor_block")
        self.assertEqual(after.vertices_mm, before.vertices_mm)
        self.assertEqual(after.faces, before.faces)
        self.assertEqual(
            after.validation.volume_times_6_mm3,
            before.validation.volume_times_6_mm3,
        )


class RecipeTreatmentTests(unittest.TestCase):
    def test_chamfer_is_present_and_stays_inside_the_cell_envelope(self) -> None:
        for record in all_library_records():
            untreated = solid_from_recipe(record.recipe)
            result = apply_edge_treatment(untreated, EDGE_TREATMENT_CHAMFER)
            with self.subTest(geometry_id=record.geometry_id):
                self.assertTrue(result.applied)
                self.assertGreater(result.treated_edge_count, 0)
                self.assertEqual(result.treated_edge_count, result.convex_edge_count)
                self.assertGreater(len(result.solid.faces), len(untreated.faces))
                self.assertLess(result.volume_times_6, volume_times_6(untreated))
                self.assertGreater(
                    result.volume_times_6 / volume_times_6(untreated),
                    EDGE_TREATMENT_MIN_VOLUME_RATIO,
                )
                self.assertIs(record.frame, CANONICAL_LOCAL_FRAME)
                self.assertEqual(record.placement.additional_offset_mm, (0, 0, 0))
                self.assertTrue(record.placement.insert_at_cell_center)
                untreated_bounds = bounding_box(untreated)
                for vertex in result.solid.vertices:
                    self.assertTrue(untreated_bounds.contains(vertex))
                    self.assertTrue(
                        CANONICAL_CELL_ENVELOPE.min_mm[0]
                        <= vertex[0]
                        <= CANONICAL_CELL_ENVELOPE.max_mm[0]
                    )
                    self.assertTrue(
                        CANONICAL_CELL_ENVELOPE.min_mm[1]
                        <= vertex[1]
                        <= CANONICAL_CELL_ENVELOPE.max_mm[1]
                    )
                    self.assertTrue(
                        CANONICAL_CELL_ENVELOPE.min_mm[2]
                        <= vertex[2]
                        <= CANONICAL_CELL_ENVELOPE.max_mm[2]
                    )

    def test_slope_treats_every_prism_edge(self) -> None:
        untreated = solid_from_recipe(lookup_recipe("large_armor_slope"))
        edges = mesh_edges(untreated)
        self.assertEqual(len(edges), 9)
        self.assertTrue(all(edge.convex for edge in edges))
        result = apply_edge_treatment(untreated, EDGE_TREATMENT_CHAMFER)
        self.assertEqual(result.treated_edge_count, 9)

    def test_library_records_do_not_gain_an_insert_offset(self) -> None:
        for record in all_library_records():
            apply_edge_treatment(solid_from_recipe(record.recipe), EDGE_TREATMENT_CHAMFER)
            self.assertEqual(record.placement.additional_offset_mm, (0, 0, 0))
            self.assertEqual(record.recipe.geometry_id, record.geometry_id)

    def test_block_face_interiors_remain_on_the_placement_envelope(self) -> None:
        untreated = solid_from_recipe(lookup_recipe("large_armor_block"))
        treated = apply_edge_treatment(untreated, EDGE_TREATMENT_CHAMFER).solid
        half = float(CANONICAL_LOCAL_FRAME.half_extent_mm)
        extrema = {0: [], 1: [], 2: []}
        for vertex in treated.vertices:
            for axis in range(3):
                extrema[axis].append(vertex[axis])
        for axis in range(3):
            self.assertAlmostEqual(max(extrema[axis]), half, places=5)
            self.assertAlmostEqual(min(extrema[axis]), -half, places=5)


class IdentityFreeApplicabilityTests(unittest.TestCase):
    def test_generic_box_is_treated_without_a_geometry_id(self) -> None:
        solid = _box_solid((-1000, -800, -600), (1000, 800, 600))
        self.assertTrue(not hasattr(solid, "geometry_id"))
        off = apply_edge_treatment(solid, EDGE_TREATMENT_OFF)
        on = apply_edge_treatment(solid, EDGE_TREATMENT_CHAMFER)
        self.assertFalse(off.applied)
        self.assertTrue(on.applied)
        self.assertEqual(on.convex_edge_count, 12)
        self.assertEqual(on.treated_edge_count, 12)
        self.assertLess(on.volume_times_6, off.volume_times_6)
        self.assertTrue(bounding_box(solid).contains_bounds(on.bounding_box))

    def test_l_prism_classifies_concave_edges_without_a_geometry_id(self) -> None:
        solid = _l_solid()
        edges = mesh_edges(solid)
        concave = [edge for edge in edges if not edge.convex]
        convex = [edge for edge in edges if edge.convex]
        self.assertEqual(len(edges), 18)
        self.assertEqual(len(concave), 1)
        self.assertEqual(len(convex), 17)
        off = apply_edge_treatment(solid, EDGE_TREATMENT_OFF)
        self.assertFalse(off.applied)
        self.assertEqual(off.convex_edge_count, 17)
        self.assertEqual(off.treated_edge_count, 0)
        self.assertTrue(not hasattr(solid, "geometry_id"))

    def test_applicability_is_not_a_four_id_allowlist(self) -> None:
        catalog_ids = {entry.geometry_id for entry in load_default_catalog().entries}
        self.assertTrue(set(_CATALOG_GEOMETRY_IDS).issubset(catalog_ids))
        solid = _box_solid((0, 0, 0), (2000, 1600, 1200))
        result = apply_edge_treatment(solid, EDGE_TREATMENT_CHAMFER)
        self.assertTrue(result.applied)
        for geometry_id in _CATALOG_GEOMETRY_IDS:
            self.assertNotEqual(solid.vertices, solid_from_recipe(lookup_recipe(geometry_id)).vertices)


class FailClosedTests(unittest.TestCase):
    def test_tiny_solid_rejects_the_named_setback(self) -> None:
        solid = _box_solid((0, 0, 0), (40, 40, 40))
        apply_edge_treatment(solid, EDGE_TREATMENT_OFF)
        with self.assertRaises(TreatmentError) as ctx:
            apply_edge_treatment(solid, EDGE_TREATMENT_CHAMFER)
        self.assertIn("consumes a convex edge", str(ctx.exception))

    def test_open_mesh_is_rejected(self) -> None:
        with self.assertRaises(InvalidSolidError):
            solid_from_vertices_faces(
                ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                ((0, 1, 2),),
            )

    def test_unknown_kind_cannot_be_constructed(self) -> None:
        with self.assertRaises(ValueError):
            EdgeTreatmentKind("fillet")
        self.assertEqual(EDGE_TREATMENT_OFF.kind, EdgeTreatmentKind.OFF)
        self.assertEqual(
            EDGE_TREATMENT_CHAMFER.kind,
            EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK,
        )
        self.assertEqual(EDGE_TREATMENT_SETBACK_MM, 50)


class SinglePlaneClipTests(unittest.TestCase):
    def test_one_cube_edge_chamfer_matches_prism_volume(self) -> None:
        solid = _box_solid((-200, -200, -200), (200, 200, 200))
        original = volume_times_6(solid) / 6.0
        treated = clip_solid_by_plane(
            solid,
            (1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0),
            (150.0, 200.0, 0.0),
        )
        removed = original - volume_times_6(treated) / 6.0
        self.assertAlmostEqual(removed, 0.5 * 50.0 * 50.0 * 400.0, places=3)


class LibraryIdentityTests(unittest.TestCase):
    def test_treatment_does_not_add_catalog_or_library_identities(self) -> None:
        catalog = load_default_catalog()
        before = [entry.geometry_id for entry in catalog.entries]
        self.assertEqual(
            [entry.geometry_id for entry in load_default_catalog().entries],
            before,
        )
        self.assertEqual(
            [record.geometry_id for record in all_library_records()],
            list(_CATALOG_GEOMETRY_IDS),
        )
        request = EdgeTreatmentRequest(kind=EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK)
        self.assertTrue(request.enabled)

    def test_treatment_modules_do_not_name_the_four_armor_ids(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "library"
        for name in ("solid.py", "treatment.py"):
            text = (root / name).read_text(encoding="utf-8")
            for geometry_id in _CATALOG_GEOMETRY_IDS:
                self.assertNotIn(geometry_id, text, msg=name)

    def test_default_conversion_modules_do_not_request_treatment(self) -> None:
        from pathlib import Path

        backend = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "solidworks"
        tokens = (
            "apply_edge_treatment",
            "EDGE_TREATMENT_CHAMFER",
            "EDGE_TREATMENT_SETBACK_MM",
            "apply_equal_setback_chamfer",
        )
        for name in (
            "recipe_plan.py",
            "pipeline.py",
            "com_construct.py",
        ):
            text = (backend / name).read_text(encoding="utf-8")
            for token in tokens:
                self.assertNotIn(token, text, msg=name)


if __name__ == "__main__":
    unittest.main()
