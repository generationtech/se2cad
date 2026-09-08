"""CAD-neutral tests for the S2C-4.2.1 SolidWorks backend boundary."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM
from se2cad.library import SolidKind, lookup_recipe
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.com_construct import (
    _feature_cut_dir_keeps_point,
    _hypotenuse_and_apex,
    _yz_profile_to_right_plane_sketch,
)
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
from se2cad.solidworks.com_session import (
    SolidWorksSession,
    _FALLBACK_CONSTANTS,
    _attach_sldworks,
    _solidworks_constants,
)
from se2cad.solidworks.config import (
    PART_TEMPLATE_ENV,
    VISIBLE_ENV,
    SolidWorksBackendConfig,
)
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
                if key
                not in {GENERATED_ROOT_ENV, PART_TEMPLATE_ENV, VISIBLE_ENV}
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
        for pywin32_present in (False, True):
            with self.subTest(pywin32_present=pywin32_present):
                with patch("se2cad.solidworks.availability._windows", return_value=False):
                    with patch(
                        "se2cad.solidworks.availability._pywin32_present",
                        return_value=pywin32_present,
                    ):
                        status = solidworks_backend_status()
                        self.assertFalse(status.available)
                        self.assertFalse(status.windows)
                        self.assertFalse(solidworks_backend_available())
                        self.assertIn("Windows", status.reason)

    def test_windows_without_pywin32_is_unavailable(self) -> None:
        with patch("se2cad.solidworks.availability._windows", return_value=True):
            with patch("se2cad.solidworks.availability._pywin32_present", return_value=False):
                status = solidworks_backend_status()
                self.assertFalse(status.available)
                self.assertTrue(status.windows)
                self.assertFalse(status.python_com_modules)
                self.assertFalse(solidworks_backend_available())
                self.assertIn("pywin32", status.reason)

    def test_windows_with_pywin32_is_available_without_opening_solidworks(self) -> None:
        with patch("se2cad.solidworks.availability._windows", return_value=True):
            with patch("se2cad.solidworks.availability._pywin32_present", return_value=True):
                status = solidworks_backend_status()
                self.assertTrue(status.available)
                self.assertTrue(status.windows)
                self.assertTrue(status.python_com_modules)
                self.assertTrue(solidworks_backend_available())
                self.assertIn("not opened", status.reason)

    def test_live_status_matches_process_predicates_without_raising(self) -> None:
        status = solidworks_backend_status()
        self.assertEqual(status.windows, sys.platform == "win32")
        self.assertEqual(
            status.available,
            status.windows and status.python_com_modules,
        )
        self.assertEqual(solidworks_backend_available(), status.available)

    def test_generate_fails_closed_when_backend_is_unavailable(self) -> None:
        from se2cad.solidworks import generate_canonical_parts

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {GENERATED_ROOT_ENV: tmp}):
                with patch("se2cad.solidworks.availability._windows", return_value=False):
                    with self.assertRaises(SolidWorksBackendUnavailableError):
                        generate_canonical_parts()


class SessionAttachTests(unittest.TestCase):
    def test_attach_uses_running_instance_without_ensuredispatch(self) -> None:
        class FakeClient:
            @staticmethod
            def GetActiveObject(progid: str) -> str:
                if progid != "SldWorks.Application":
                    raise AssertionError(progid)
                return "ACTIVE"

            @staticmethod
            def Dispatch(progid: str) -> str:
                raise AssertionError("Dispatch must not run when a session is active")

        app, started = _attach_sldworks(FakeClient())
        self.assertEqual(app, "ACTIVE")
        self.assertFalse(started)

    def test_attach_dispatches_when_no_running_instance(self) -> None:
        class FakeClient:
            @staticmethod
            def GetActiveObject(progid: str) -> str:
                raise RuntimeError("no ROT entry")

            @staticmethod
            def Dispatch(progid: str) -> str:
                if progid != "SldWorks.Application":
                    raise AssertionError(progid)
                return "STARTED"

        app, started = _attach_sldworks(FakeClient())
        self.assertEqual(app, "STARTED")
        self.assertTrue(started)

    def test_attach_does_not_require_gencache_ensuredispatch(self) -> None:
        class FakeClient:
            @staticmethod
            def GetActiveObject(progid: str) -> str:
                return "ACTIVE"

            class gencache:
                @staticmethod
                def EnsureDispatch(obj: object) -> object:
                    raise TypeError("makepy cannot run")

        app, started = _attach_sldworks(FakeClient())
        self.assertEqual(app, "ACTIVE")
        self.assertFalse(started)

    def test_constants_fall_back_when_typelib_is_unavailable(self) -> None:
        class Empty:
            class constants:
                pass

        constants = _solidworks_constants(Empty())
        self.assertEqual(constants.swDefaultTemplatePart, 8)
        self.assertEqual(constants.swDocPART, 1)
        self.assertEqual(constants.swOpenDocOptions_Silent, 1)
        self.assertEqual(constants.swSaveAsCurrentVersion, 0)
        self.assertEqual(constants.swSaveAsOptions_Silent, 1)
        self.assertEqual(constants.swSolidBody, _FALLBACK_CONSTANTS["swSolidBody"])
        self.assertEqual(constants.swEndCondThroughAll, 1)
        self.assertEqual(constants.swStartSketchPlane, 0)
        self.assertEqual(constants.swRefPlaneReferenceConstraint_Coincident, 4)
        with self.assertRaises(AttributeError):
            getattr(constants, "swNotARealEnum")

    def test_generated_constants_win_over_fallbacks(self) -> None:
        class Generated:
            swDocPART = 99

        class Client:
            constants = Generated()

        constants = _solidworks_constants(Client())
        self.assertEqual(constants.swDocPART, 99)
        self.assertEqual(constants.swDefaultTemplatePart, 8)

    def test_com_get_reads_property_without_calling_cdispatch(self) -> None:
        class FakeDispatch:
            _oleobj_ = object()

            def __call__(self) -> None:
                raise OSError(-2147352573, "Member not found.")

        feature = FakeDispatch()
        model = type("Model", (), {"FirstFeature": feature})()
        self.assertIs(com_get(model, "FirstFeature"), feature)

    def test_com_get_calls_zero_argument_methods(self) -> None:
        model = type("Model", (), {"GetTitle": lambda self: "Part1"})()
        self.assertEqual(com_get(model, "GetTitle"), "Part1")

    def test_revision_accepts_property_or_method(self) -> None:
        session = SolidWorksSession(
            config=SolidWorksBackendConfig(
                generated_root=Path("."),
                part_template=None,
                visible=False,
                source="test",
            )
        )
        session.app = type("App", (), {"RevisionNumber": "34.3.2"})()
        self.assertEqual(session.revision(), "34.3.2")
        session.app = type("App", (), {"RevisionNumber": lambda self: "34.0.0"})()
        self.assertEqual(session.revision(), "34.0.0")


class RightPlaneSketchMappingTests(unittest.TestCase):
    def test_yz_profile_maps_to_live_right_plane_sketch_axes(self) -> None:
        self.assertEqual(_yz_profile_to_right_plane_sketch(0.2, 0.1), (-0.1, 0.2, 0.0))
        self.assertEqual(_yz_profile_to_right_plane_sketch(-1.25, 1.25), (-1.25, -1.25, 0.0))
        self.assertEqual(_yz_profile_to_right_plane_sketch(1.25, -1.25), (1.25, 1.25, 0.0))


class ConstructionSignatureTests(unittest.TestCase):
    def test_feature_extrusion2_uses_live_2026_arity(self) -> None:
        import ast

        path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "solidworks"
            / "com_construct.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "FeatureExtrusion2"
            ):
                self.assertEqual(len(node.args), 23)
                return
        self.fail("FeatureExtrusion2 call not found")

    def test_feature_cut4_uses_live_2026_arity(self) -> None:
        import ast

        path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "solidworks"
            / "com_construct.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "FeatureCut4"
            ):
                self.assertEqual(len(node.args), 27)
                return
        self.fail("FeatureCut4 call not found")

    def test_hypotenuse_cut_consumes_qualified_recipe_face(self) -> None:
        corner = plan_from_recipe(lookup_recipe("large_armor_corner"))
        assert corner.tetrahedron is not None
        hypotenuse, apex = _hypotenuse_and_apex(corner.tetrahedron)
        self.assertEqual(hypotenuse, lookup_recipe("large_armor_corner").faces[-1])
        self.assertEqual(hypotenuse, (0, 2, 3))
        self.assertEqual(apex, 1)
        p0, p1, p2 = (corner.tetrahedron.vertices_m[i] for i in hypotenuse)
        keep = corner.tetrahedron.vertices_m[apex]
        self.assertTrue(_feature_cut_dir_keeps_point(p0, p1, p2, keep))
        inv = plan_from_recipe(lookup_recipe("large_armor_corner_inv"))
        assert inv.box_minus_tetrahedron is not None
        self.assertEqual(
            inv.box_minus_tetrahedron.cut.faces[-1],
            hypotenuse,
        )


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
