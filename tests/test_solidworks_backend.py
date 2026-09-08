"""CAD-neutral tests for the S2C-4.2.1 SolidWorks backend boundary."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM
from se2cad.library import SolidKind, lookup_recipe
from se2cad.solidworks import (
    GENERATED_ROOT_ENV,
    BoundPartLocator,
    GeneratedRootError,
    LogicalPartIdentity,
    SolidWorksBackendUnavailableError,
    SolidWorksConfigError,
    UnknownCanonicalPartError,
    artifact_path_for,
    canonical_geometry_ids,
    contained_destination,
    load_solidworks_backend_config,
    logical_part_filename,
    metres_to_mm,
    mm_to_metres,
    plan_from_recipe,
    point_mm_to_metres,
    solidworks_backend_available,
    solidworks_backend_status,
)
from se2cad.solidworks.artifacts import assert_overwrite_is_canonical
from se2cad.solidworks.locator import BoundPartLocator as BoundLocator
from se2cad.solidworks.recipe_plan import all_canonical_plans
from se2cad.solidworks.units import recipe_volume_m3


class NamingTests(unittest.TestCase):
    def test_filenames_are_deterministic_geometry_ids(self) -> None:
        expected = (
            ("large_armor_block", "large_armor_block.SLDPRT"),
            ("large_armor_slope", "large_armor_slope.SLDPRT"),
            ("large_armor_corner", "large_armor_corner.SLDPRT"),
            ("large_armor_corner_inv", "large_armor_corner_inv.SLDPRT"),
        )
        self.assertEqual(canonical_geometry_ids(), tuple(gid for gid, _ in expected))
        for geometry_id, filename in expected:
            self.assertEqual(logical_part_filename(geometry_id), filename)
            identity = LogicalPartIdentity.from_geometry_id(geometry_id)
            self.assertEqual(identity.geometry_id, geometry_id)
            self.assertEqual(identity.filename, filename)

    def test_unknown_geometry_id_has_no_artifact_name(self) -> None:
        with self.assertRaises(UnknownCanonicalPartError):
            logical_part_filename("LargeBlockArmorBlock")


class UnitConversionTests(unittest.TestCase):
    def test_millimetres_to_metres_is_explicit_and_exact_for_pitch(self) -> None:
        self.assertEqual(mm_to_metres(LARGE_GRID_CELL_PITCH_MM), 2.5)
        self.assertEqual(mm_to_metres(LARGE_GRID_CELL_PITCH_MM // 2), 1.25)
        self.assertEqual(metres_to_mm(2.5), float(LARGE_GRID_CELL_PITCH_MM))
        self.assertEqual(point_mm_to_metres((2500, -1250, 0)), (2.5, -1.25, 0.0))

    def test_recipe_volumes_match_metre_conversion(self) -> None:
        half = LARGE_GRID_CELL_PITCH_MM // 2
        h3 = half * half * half
        block = lookup_recipe("large_armor_block")
        self.assertEqual(block.validation.volume_times_6_mm3, 48 * h3)
        self.assertAlmostEqual(recipe_volume_m3(48 * h3), 15.625)
        self.assertAlmostEqual(
            recipe_volume_m3(lookup_recipe("large_armor_slope").validation.volume_times_6_mm3),
            7.8125,
        )


class GeneratedRootTests(unittest.TestCase):
    def test_destination_stays_inside_the_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "generated"
            dest = artifact_path_for(root, "large_armor_block")
            self.assertEqual(dest.name, "large_armor_block.SLDPRT")
            dest.relative_to(root.resolve())

    def test_path_escape_and_separators_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for filename in ("../escape.SLDPRT", "sub/dir.SLDPRT", r"sub\dir.SLDPRT"):
                with self.subTest(filename=filename):
                    with self.assertRaises(GeneratedRootError):
                        contained_destination(root, filename)

    def test_overwrite_of_unrelated_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            foreign = Path(tmp) / "notes.txt"
            foreign.write_text("no", encoding="utf-8")
            with self.assertRaises(GeneratedRootError):
                assert_overwrite_is_canonical(foreign)

    def test_overwrite_of_canonical_artifact_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            owned = Path(tmp) / "large_armor_block.SLDPRT"
            owned.write_bytes(b"stub")
            assert_overwrite_is_canonical(owned)


class ConfigTests(unittest.TestCase):
    def test_missing_generated_root_fails_closed(self) -> None:
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                GENERATED_ROOT_ENV,
                "SE2CAD_LOCAL_CONFIG",
                "SE2CAD_SOLIDWORKS_PART_TEMPLATE",
            }
        }
        with patch.dict(os.environ, env, clear=True):
            with tempfile.TemporaryDirectory() as tmp:
                with patch("se2cad.solidworks.config.Path.cwd", return_value=Path(tmp)):
                    with self.assertRaises(SolidWorksConfigError):
                        load_solidworks_backend_config()

    def test_environment_root_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            root.mkdir()
            with patch.dict(os.environ, {GENERATED_ROOT_ENV: str(root)}):
                config = load_solidworks_backend_config()
            self.assertEqual(config.generated_root, root.resolve())
            self.assertEqual(config.source, GENERATED_ROOT_ENV)

    def test_local_json_config_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "cache"
            root.mkdir()
            local = Path(tmp) / "se2cad.local.json"
            local.write_text(
                json.dumps({"generated_root": str(root), "visible": False}),
                encoding="utf-8",
            )
            env = {
                key: value
                for key, value in os.environ.items()
                if key != GENERATED_ROOT_ENV
            }
            env["SE2CAD_LOCAL_CONFIG"] = str(local)
            with patch.dict(os.environ, env, clear=True):
                config = load_solidworks_backend_config()
            self.assertEqual(config.generated_root, root.resolve())
            self.assertFalse(config.visible)

    def test_unknown_local_config_keys_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "se2cad.local.json"
            local.write_text(json.dumps({"steam_path": "C:\\\\game"}), encoding="utf-8")
            with patch.dict(os.environ, {"SE2CAD_LOCAL_CONFIG": str(local)}):
                with self.assertRaises(SolidWorksConfigError):
                    load_solidworks_backend_config()


class LocatorBindingTests(unittest.TestCase):
    def test_locator_cannot_bind_before_all_steps_succeed(self) -> None:
        identity = LogicalPartIdentity.from_geometry_id("large_armor_block")
        path = Path("large_armor_block.SLDPRT")
        with self.assertRaises(ValueError):
            BoundLocator(
                identity=identity,
                path=path,
                generated=True,
                validated=True,
                saved=True,
                reopened=False,
            )

    def test_bound_locator_keeps_logical_identity(self) -> None:
        identity = LogicalPartIdentity.from_geometry_id("large_armor_slope")
        locator = BoundPartLocator(
            identity=identity,
            path=Path("/tmp/large_armor_slope.SLDPRT"),
            generated=True,
            validated=True,
            saved=True,
            reopened=True,
        )
        self.assertEqual(locator.identity.filename, "large_armor_slope.SLDPRT")
        self.assertEqual(locator.identity.geometry_id, "large_armor_slope")


class AvailabilityTests(unittest.TestCase):
    def test_linux_backend_is_unavailable_without_raising_on_status(self) -> None:
        status = solidworks_backend_status()
        self.assertFalse(status.available)
        self.assertFalse(solidworks_backend_available())
        self.assertIn("Windows", status.reason)

    def test_generate_fails_closed_when_backend_is_unavailable(self) -> None:
        from se2cad.solidworks import generate_canonical_parts

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {GENERATED_ROOT_ENV: tmp}):
                with self.assertRaises(SolidWorksBackendUnavailableError):
                    generate_canonical_parts()


class RecipePlanTests(unittest.TestCase):
    def test_plans_consume_qualified_recipes_without_reinterpretation(self) -> None:
        plans = {plan.geometry_id: plan for plan in all_canonical_plans()}
        self.assertEqual(
            [plan.solid_kind for plan in all_canonical_plans()],
            [
                SolidKind.AXIS_ALIGNED_BOX,
                SolidKind.RIGHT_TRIANGULAR_PRISM,
                SolidKind.TETRAHEDRON,
                SolidKind.BOX_MINUS_TETRAHEDRON,
            ],
        )
        half_m = mm_to_metres(LARGE_GRID_CELL_PITCH_MM // 2)
        block = plans["large_armor_block"]
        self.assertIsNotNone(block.box)
        assert block.box is not None
        self.assertEqual(block.box.min_m, (-half_m, -half_m, -half_m))
        self.assertEqual(block.box.max_m, (half_m, half_m, half_m))
        self.assertEqual(block.expected.center_of_mass_m, (0.0, 0.0, 0.0))

        slope = plans["large_armor_slope"]
        recipe = lookup_recipe("large_armor_slope")
        self.assertEqual(
            slope.vertices_m,
            tuple(point_mm_to_metres(v) for v in recipe.vertices_mm),
        )
        self.assertEqual(slope.faces, recipe.faces)
        self.assertLess(slope.expected.center_of_mass_m[1] + slope.expected.center_of_mass_m[2], 0)

        corner = plans["large_armor_corner"]
        self.assertIsNotNone(corner.tetrahedron)
        assert corner.tetrahedron is not None
        self.assertEqual(len(corner.tetrahedron.vertices_m), 4)
        self.assertAlmostEqual(corner.expected.center_of_mass_m[0], 0.625)
        self.assertAlmostEqual(corner.expected.center_of_mass_m[1], -0.625)
        self.assertAlmostEqual(corner.expected.center_of_mass_m[2], -0.625)

        inv = plans["large_armor_corner_inv"]
        self.assertIsNotNone(inv.box_minus_tetrahedron)
        assert inv.box_minus_tetrahedron is not None
        self.assertEqual(inv.box_minus_tetrahedron.cut.vertices_m, corner.tetrahedron.vertices_m)
        self.assertAlmostEqual(
            inv.expected.volume_m3 + corner.expected.volume_m3,
            block.expected.volume_m3,
        )

    def test_plans_do_not_introduce_a_second_frame(self) -> None:
        for plan in all_canonical_plans():
            self.assertEqual(plan.expected.bounding_box_min_m, (-1.25, -1.25, -1.25))
            self.assertEqual(plan.expected.bounding_box_max_m, (1.25, 1.25, 1.25))


if __name__ == "__main__":
    unittest.main()
