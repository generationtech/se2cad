"""Deterministic tests for the S2C-4.1.1 block-library recipes."""

from __future__ import annotations

import unittest

from se2cad.catalog import (
    LARGE_GRID_CELL_PITCH_MM,
    RecipeKind,
    load_default_catalog,
)
from se2cad.library import (
    CANONICAL_CELL_ENVELOPE,
    CANONICAL_LOCAL_FRAME,
    BoxConstruction,
    BoxMinusTetrahedronConstruction,
    PrismConstruction,
    SolidKind,
    TetrahedronConstruction,
    UnknownGeometryError,
    all_library_records,
    cell_half_extent_mm,
    lookup_recipe,
    lookup_record,
    signed_volume_times_6,
)
from se2cad.parser.model import Direction
from se2cad.transform import IDENTITY_ROTATION, rotation_from_forward_up
from se2cad.transform.directions import SE_DIRECTION_VECTORS

_CATALOG_GEOMETRY_IDS = (
    "large_armor_block",
    "large_armor_slope",
    "large_armor_corner",
    "large_armor_corner_inv",
)

_RIGHT_DOWN_FORWARD = (1, -1, -1)


def _half() -> int:
    return cell_half_extent_mm()


def _scale(signs: tuple[int, int, int]) -> tuple[int, int, int]:
    half = _half()
    return (signs[0] * half, signs[1] * half, signs[2] * half)


class CatalogResolutionTests(unittest.TestCase):
    def test_each_supported_catalog_geometry_id_resolves_to_exactly_one_recipe(self) -> None:
        catalog = load_default_catalog()
        supported_ids = [
            entry.geometry_id
            for entry in catalog.entries
            if entry.support_status.value == "supported"
        ]
        self.assertEqual(supported_ids, list(_CATALOG_GEOMETRY_IDS))
        records = all_library_records()
        self.assertEqual(len(records), 4)
        self.assertEqual([record.geometry_id for record in records], supported_ids)
        seen: set[str] = set()
        for geometry_id in supported_ids:
            recipe = lookup_recipe(geometry_id)
            self.assertEqual(recipe.geometry_id, geometry_id)
            self.assertNotIn(geometry_id, seen)
            seen.add(geometry_id)
        self.assertEqual(len(seen), 4)
        unsupported_ids = [
            entry.geometry_id
            for entry in catalog.entries
            if entry.support_status.value == "unsupported"
        ]
        self.assertTrue(unsupported_ids)
        for geometry_id in unsupported_ids:
            with self.assertRaises(UnknownGeometryError):
                lookup_recipe(geometry_id)

    def test_lookup_is_exact_and_fails_closed(self) -> None:
        exact = lookup_recipe("large_armor_block")
        self.assertEqual(exact.geometry_id, "large_armor_block")
        for wrong in (
            "LargeBlockArmorBlock",
            "large_armor_Block",
            "LARGE_ARMOR_BLOCK",
            "large_armor_block ",
            " unknown",
        ):
            with self.subTest(wrong=wrong):
                with self.assertRaises(UnknownGeometryError) as ctx:
                    lookup_recipe(wrong)
                self.assertIn(wrong, str(ctx.exception))


class CanonicalFrameTests(unittest.TestCase):
    def test_instance_transform_rotates_local_geometry_without_translation(self) -> None:
        half = _half()
        local_rdf = (half, -half, -half)
        corner = lookup_recipe("large_armor_corner")
        self.assertIn(local_rdf, corner.vertices_mm)
        self.assertEqual(IDENTITY_ROTATION.apply(local_rdf), local_rdf)
        rotated = rotation_from_forward_up(Direction.DOWN, Direction.FORWARD)
        self.assertEqual(rotated.columns, ((1, 0, 0), (0, 0, -1), (0, 1, 0)))
        self.assertEqual(rotated.apply(local_rdf), (half, -half, half))
        for vertex in corner.vertices_mm:
            image = rotated.apply(vertex)
            self.assertTrue(all(isinstance(c, int) for c in image))
            self.assertTrue(all(abs(c) == half for c in image))

    def test_recipes_use_qualified_canonical_frame(self) -> None:
        frame = CANONICAL_LOCAL_FRAME
        self.assertEqual(frame.plus_x, SE_DIRECTION_VECTORS[Direction.RIGHT])
        self.assertEqual(frame.plus_y, SE_DIRECTION_VECTORS[Direction.UP])
        self.assertEqual(frame.plus_z, SE_DIRECTION_VECTORS[Direction.BACKWARD])
        self.assertEqual(frame.plus_x, (1, 0, 0))
        self.assertEqual(frame.plus_y, (0, 1, 0))
        self.assertEqual(frame.plus_z, (0, 0, 1))
        self.assertEqual(frame.plus_x_meaning, "Right")
        self.assertEqual(frame.plus_y_meaning, "Up")
        self.assertEqual(frame.plus_z_meaning, "Backward")
        self.assertEqual(frame.origin_meaning, "cell_center")
        self.assertEqual(frame.units, "millimetre")
        for record in all_library_records():
            self.assertIs(record.frame, CANONICAL_LOCAL_FRAME)
            self.assertEqual(record.placement.additional_offset_mm, (0, 0, 0))
            self.assertTrue(record.placement.insert_at_cell_center)
            self.assertIsNone(record.placement.part_locator)

    def test_dimensions_use_authoritative_large_grid_pitch(self) -> None:
        half = cell_half_extent_mm()
        self.assertEqual(half * 2, LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(CANONICAL_LOCAL_FRAME.half_extent_mm, half)
        self.assertEqual(
            CANONICAL_CELL_ENVELOPE.min_mm, (-half, -half, -half)
        )
        self.assertEqual(
            CANONICAL_CELL_ENVELOPE.max_mm, (half, half, half)
        )
        for record in all_library_records():
            self.assertEqual(record.grid_size, "Large")
            self.assertEqual(record.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            box = record.recipe.validation.bounding_box
            self.assertEqual(box.min_mm, (-half, -half, -half))
            self.assertEqual(box.max_mm, (half, half, half))


class EnvelopeAndBoundingBoxTests(unittest.TestCase):
    def test_vertices_stay_inside_the_cell_envelope(self) -> None:
        for record in all_library_records():
            for vertex in record.recipe.vertices_mm:
                self.assertTrue(
                    CANONICAL_CELL_ENVELOPE.contains(vertex),
                    msg=f"{record.geometry_id} vertex {vertex} leaves envelope",
                )
                self.assertTrue(all(isinstance(c, int) for c in vertex))

    def test_expected_bounding_boxes_are_exact(self) -> None:
        half = _half()
        expected = ((-half, -half, -half), (half, half, half))
        for geometry_id in _CATALOG_GEOMETRY_IDS:
            box = lookup_recipe(geometry_id).validation.bounding_box
            self.assertEqual((box.min_mm, box.max_mm), expected)


class DistinctSolidTests(unittest.TestCase):
    def test_four_solids_remain_distinct(self) -> None:
        recipes = [lookup_recipe(gid) for gid in _CATALOG_GEOMETRY_IDS]
        kinds = [recipe.solid_kind for recipe in recipes]
        self.assertEqual(
            kinds,
            [
                SolidKind.AXIS_ALIGNED_BOX,
                SolidKind.RIGHT_TRIANGULAR_PRISM,
                SolidKind.TETRAHEDRON,
                SolidKind.BOX_MINUS_TETRAHEDRON,
            ],
        )
        vertex_sets = [frozenset(recipe.vertices_mm) for recipe in recipes]
        self.assertEqual(len(set(vertex_sets)), 4)
        volumes = [recipe.validation.volume_times_6_mm3 for recipe in recipes]
        self.assertEqual(len(set(volumes)), 4)
        topologies = [
            recipe.orientation.observed_cube_topology for recipe in recipes
        ]
        self.assertEqual(topologies, ["Box", "Slope", "Corner", "InvCorner"])

    def test_volumes_match_cube_half_tetra_and_complement(self) -> None:
        half = _half()
        h3 = half * half * half
        block = lookup_recipe("large_armor_block")
        slope = lookup_recipe("large_armor_slope")
        corner = lookup_recipe("large_armor_corner")
        inv = lookup_recipe("large_armor_corner_inv")
        self.assertEqual(block.validation.volume_times_6_mm3, 48 * h3)
        self.assertEqual(slope.validation.volume_times_6_mm3, 24 * h3)
        self.assertEqual(corner.validation.volume_times_6_mm3, 8 * h3)
        self.assertEqual(inv.validation.volume_times_6_mm3, 40 * h3)
        self.assertEqual(
            corner.validation.volume_times_6_mm3
            + inv.validation.volume_times_6_mm3,
            block.validation.volume_times_6_mm3,
        )
        self.assertEqual(
            slope.validation.volume_times_6_mm3 * 2,
            block.validation.volume_times_6_mm3,
        )


class ConstructionSufficiencyTests(unittest.TestCase):
    def test_recipes_carry_deterministic_construction_data(self) -> None:
        half = _half()
        block = lookup_recipe("large_armor_block")
        self.assertIsInstance(block.construction, BoxConstruction)
        assert isinstance(block.construction, BoxConstruction)
        self.assertEqual(block.construction.min_mm, (-half, -half, -half))
        self.assertEqual(block.construction.max_mm, (half, half, half))
        self.assertEqual(block.validation.vertex_count, 8)
        self.assertEqual(block.validation.face_count, 6)

        slope = lookup_recipe("large_armor_slope")
        self.assertIsInstance(slope.construction, PrismConstruction)
        assert isinstance(slope.construction, PrismConstruction)
        self.assertEqual(slope.construction.profile_plane, "YZ")
        self.assertEqual(slope.construction.extrusion_axis, "X")
        self.assertEqual(slope.construction.extrusion_min_mm, -half)
        self.assertEqual(slope.construction.extrusion_max_mm, half)
        self.assertEqual(
            slope.construction.profile_yz_mm,
            ((half, -half), (-half, -half), (-half, half)),
        )
        self.assertEqual(slope.validation.vertex_count, 6)
        self.assertEqual(slope.validation.face_count, 5)

        corner = lookup_recipe("large_armor_corner")
        self.assertIsInstance(corner.construction, TetrahedronConstruction)
        assert isinstance(corner.construction, TetrahedronConstruction)
        self.assertEqual(len(corner.construction.vertices_mm), 4)
        self.assertEqual(set(corner.construction.vertices_mm), set(corner.vertices_mm))
        self.assertEqual(corner.validation.vertex_count, 4)
        self.assertEqual(corner.validation.face_count, 4)

        inv = lookup_recipe("large_armor_corner_inv")
        self.assertIsInstance(inv.construction, BoxMinusTetrahedronConstruction)
        assert isinstance(inv.construction, BoxMinusTetrahedronConstruction)
        self.assertEqual(inv.construction.box, block.construction)
        self.assertEqual(inv.construction.cut, corner.construction)
        self.assertEqual(inv.validation.vertex_count, 7)
        self.assertEqual(inv.validation.face_count, 7)

    def test_face_windings_are_outward_and_closed(self) -> None:
        for record in all_library_records():
            recipe = record.recipe
            recomputed = signed_volume_times_6(recipe.vertices_mm, recipe.faces)
            self.assertEqual(recomputed, recipe.validation.volume_times_6_mm3)
            self.assertGreater(recomputed, 0)


class TopologyOrientationTests(unittest.TestCase):
    def test_identity_slope_occupies_forward_down_half(self) -> None:
        slope = lookup_recipe("large_armor_slope")
        verts = set(slope.vertices_mm)
        half = _half()
        self.assertIn(_scale((-1, 1, -1)), verts)
        self.assertIn(_scale((1, -1, 1)), verts)
        self.assertNotIn(_scale((-1, 1, 1)), verts)
        self.assertNotIn(_scale((1, 1, 1)), verts)
        for x, y, z in slope.vertices_mm:
            self.assertLessEqual(y + z, 0)
        self.assertEqual(slope.orientation.full_faces, ("Forward", "Down"))
        self.assertTrue(all(abs(x) == half for x, _y, _z in slope.vertices_mm))

    def test_identity_corner_is_right_down_forward_tetrahedron(self) -> None:
        corner = lookup_recipe("large_armor_corner")
        verts = set(corner.vertices_mm)
        self.assertEqual(len(verts), 4)
        self.assertIn(_scale(_RIGHT_DOWN_FORWARD), verts)
        self.assertIn(_scale((1, 1, -1)), verts)
        self.assertIn(_scale((-1, -1, -1)), verts)
        self.assertIn(_scale((1, -1, 1)), verts)
        self.assertNotIn(_scale((-1, 1, 1)), verts)
        self.assertEqual(
            corner.orientation.distinguishing_cube_corner_signs,
            _RIGHT_DOWN_FORWARD,
        )

    def test_identity_inv_corner_is_cube_minus_that_tetrahedron(self) -> None:
        cube = set(lookup_recipe("large_armor_block").vertices_mm)
        corner = set(lookup_recipe("large_armor_corner").vertices_mm)
        inv = set(lookup_recipe("large_armor_corner_inv").vertices_mm)
        missing = _scale(_RIGHT_DOWN_FORWARD)
        self.assertEqual(inv, cube - {missing})
        self.assertEqual(len(cube & corner), 4)
        self.assertEqual(len(inv & corner), 3)
        self.assertNotIn(missing, inv)
        self.assertEqual(
            lookup_recipe("large_armor_corner_inv").orientation.full_faces,
            ("Up", "Left", "Backward"),
        )


class CatalogBindingTests(unittest.TestCase):
    def test_library_records_bind_catalog_identities_not_subtypes(self) -> None:
        catalog = load_default_catalog()
        for entry in catalog.entries:
            self.assertNotEqual(entry.geometry_id, entry.subtype_id)
            if entry.support_status.value != "supported":
                with self.assertRaises(UnknownGeometryError):
                    lookup_record(entry.geometry_id)
                continue
            record = lookup_record(entry.geometry_id)
            self.assertEqual(record.geometry_id, entry.geometry_id)
            self.assertEqual(record.recipe_kind, entry.recipe_kind)
            self.assertEqual(
                record.observed_cube_topology, entry.observed.cube_topology
            )


if __name__ == "__main__":
    unittest.main()
