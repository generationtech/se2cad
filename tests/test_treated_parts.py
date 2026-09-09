"""Ordinary tests for optional treated canonical-part generation (S2C-10.2.1)."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from se2cad.library import (
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_MIN_VOLUME_RATIO,
    EDGE_TREATMENT_OFF,
    EdgeTreatmentKind,
    EdgeTreatmentRequest,
    apply_edge_treatment,
    lookup_recipe,
    solid_from_recipe,
)
from se2cad.solidworks import (
    GeneratedRootError,
    UnknownCanonicalPartError,
    artifact_path_for,
    canonical_geometry_ids,
    is_treated_artifact_filename,
    logical_part_filename,
    logical_treated_part_filename,
    part_artifact_path,
    placements_from_ir,
    treated_artifact_path_for,
)
from se2cad.solidworks.artifacts import (
    TREATED_PART_STEM_SUFFIX,
    assert_overwrite_is_canonical,
)
from se2cad.solidworks.com_validate import (
    PartValidation,
    assert_matches_treatment_contract,
)
from se2cad.solidworks.generate import generate_canonical_parts, generate_one_canonical_part
from se2cad.solidworks.recipe_plan import plan_from_recipe
from se2cad.solidworks.units import volume_mm3_to_m3


_GEOM = (
    "large_armor_block",
    "large_armor_slope",
    "large_armor_corner",
    "large_armor_corner_inv",
)


class TreatedArtifactNamingTests(unittest.TestCase):
    def test_treated_filenames_are_deterministic_siblings(self) -> None:
        self.assertEqual(TREATED_PART_STEM_SUFFIX, "_chamfer")
        self.assertEqual(canonical_geometry_ids(), _GEOM)
        for geometry_id in _GEOM:
            untreated = logical_part_filename(geometry_id)
            treated = logical_treated_part_filename(
                geometry_id, EDGE_TREATMENT_CHAMFER
            )
            self.assertEqual(untreated, f"{geometry_id}.SLDPRT")
            self.assertEqual(treated, f"{geometry_id}_chamfer_50mm.SLDPRT")
            self.assertNotEqual(untreated, treated)
            self.assertTrue(is_treated_artifact_filename(treated))
            self.assertFalse(is_treated_artifact_filename(untreated))

    def test_off_and_unknown_ids_have_no_treated_filename(self) -> None:
        with self.assertRaises(UnknownCanonicalPartError):
            logical_treated_part_filename("large_armor_block", EDGE_TREATMENT_OFF)
        with self.assertRaises(UnknownCanonicalPartError):
            logical_treated_part_filename("LargeBlockArmorBlock", EDGE_TREATMENT_CHAMFER)

    def test_default_part_path_stays_the_untreated_canonical_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "generated"
            for geometry_id in _GEOM:
                default = part_artifact_path(root, geometry_id)
                omitted = part_artifact_path(root, geometry_id, None)
                off = part_artifact_path(root, geometry_id, EDGE_TREATMENT_OFF)
                treated = part_artifact_path(
                    root, geometry_id, EDGE_TREATMENT_CHAMFER
                )
                self.assertEqual(default, artifact_path_for(root, geometry_id))
                self.assertEqual(default, omitted)
                self.assertEqual(default, off)
                self.assertEqual(default.name, f"{geometry_id}.SLDPRT")
                self.assertEqual(treated.name, f"{geometry_id}_chamfer_50mm.SLDPRT")
                self.assertNotEqual(treated, default)
                treated.relative_to(root.resolve())


class TreatedOverwriteTests(unittest.TestCase):
    def test_treated_overwrite_of_untreated_canonical_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            owned = Path(tmp) / "large_armor_block.SLDPRT"
            owned.write_bytes(b"untreated")
            assert_overwrite_is_canonical(owned)
            destination = part_artifact_path(
                Path(tmp), "large_armor_block", EDGE_TREATMENT_CHAMFER
            )
            self.assertNotEqual(destination, owned)
            self.assertFalse(destination.exists())

    def test_treated_sibling_may_overwrite_its_own_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sibling = Path(tmp) / "large_armor_slope_chamfer_50mm.SLDPRT"
            sibling.write_bytes(b"prior")
            assert_overwrite_is_canonical(sibling)
            self.assertEqual(
                treated_artifact_path_for(
                    Path(tmp), "large_armor_slope", EDGE_TREATMENT_CHAMFER
                ),
                sibling,
            )

    def test_foreign_file_overwrite_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            foreign = Path(tmp) / "notes_chamfer.SLDPRT"
            foreign.write_bytes(b"no")
            self.assertFalse(is_treated_artifact_filename(foreign.name))
            with self.assertRaises(GeneratedRootError):
                assert_overwrite_is_canonical(foreign)


class DefaultPathUnchangedTests(unittest.TestCase):
    def test_generate_signatures_default_to_untreated(self) -> None:
        one = inspect.signature(generate_one_canonical_part)
        many = inspect.signature(generate_canonical_parts)
        self.assertIsNone(one.parameters["treatment"].default)
        self.assertIsNone(many.parameters["treatment"].default)

    def test_recipe_plans_remain_untreated_construction(self) -> None:
        for geometry_id in _GEOM:
            recipe = lookup_recipe(geometry_id)
            plan = plan_from_recipe(recipe)
            self.assertEqual(plan.geometry_id, geometry_id)
            self.assertEqual(plan.vertices_m, tuple(
                (v[0] / 1000.0, v[1] / 1000.0, v[2] / 1000.0)
                for v in recipe.vertices_mm
            ))
            fields = set(plan.__dataclass_fields__)
            self.assertNotIn("treatment", fields)
            self.assertNotIn("chamfer", fields)

    def test_placement_still_uses_untreated_filenames(self) -> None:
        from se2cad.catalog import load_default_catalog
        from se2cad.ir import build_canonical_blueprint
        from se2cad.parser import parse_blueprint

        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )
        ir = build_canonical_blueprint(parse_blueprint(fixture), load_default_catalog())
        placements = placements_from_ir(ir)
        self.assertEqual(len(placements), 24)
        for item in placements:
            self.assertEqual(item.part_filename, f"{item.geometry_id}.SLDPRT")
            self.assertFalse(is_treated_artifact_filename(item.part_filename))

    def test_default_conversion_modules_do_not_enable_treatment(self) -> None:
        backend = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "solidworks"
        tokens = (
            "EDGE_TREATMENT_CHAMFER",
            "apply_equal_setback_chamfer",
            "logical_treated_part_filename",
        )
        for name in (
            "recipe_plan.py",
            "pipeline.py",
            "com_construct.py",
        ):
            text = (backend / name).read_text(encoding="utf-8")
            for token in tokens:
                self.assertNotIn(token, text, msg=name)


class TreatmentContractOrdinaryTests(unittest.TestCase):
    def test_cad_neutral_expected_volumes_stay_below_the_bound(self) -> None:
        for geometry_id in _GEOM:
            untreated = lookup_recipe(geometry_id)
            result = apply_edge_treatment(
                solid_from_recipe(untreated), EDGE_TREATMENT_CHAMFER
            )
            self.assertTrue(result.applied)
            ratio = result.volume_times_6 / untreated.validation.volume_times_6_mm3
            self.assertLess(ratio, 1.0)
            self.assertGreaterEqual(ratio, EDGE_TREATMENT_MIN_VOLUME_RATIO)
            self.assertGreater(volume_mm3_to_m3(result.volume_times_6 / 6.0), 0.0)

    def test_treatment_contract_rejects_unchanged_volume(self) -> None:
        untreated = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-1.25, -1.25, -1.25),
            bounding_box_max_m=(1.25, 1.25, 1.25),
            volume_m3=15.625,
            center_of_mass_m=(0.0, 0.0, 0.0),
            face_count=6,
        )
        with self.assertRaises(Exception):
            assert_matches_treatment_contract(
                untreated,
                untreated,
                envelope_min_m=untreated.bounding_box_min_m,
                envelope_max_m=untreated.bounding_box_max_m,
            )

    def test_treatment_contract_accepts_a_valid_chamfered_box(self) -> None:
        untreated = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-1.25, -1.25, -1.25),
            bounding_box_max_m=(1.25, 1.25, 1.25),
            volume_m3=15.625,
            center_of_mass_m=(0.0, 0.0, 0.0),
            face_count=6,
        )
        treated_volume = 15.625 * 0.997648
        treated = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-1.25, -1.25, -1.25),
            bounding_box_max_m=(1.25, 1.25, 1.25),
            volume_m3=treated_volume,
            center_of_mass_m=(0.0, 0.0, 0.0),
            face_count=18,
        )
        assert_matches_treatment_contract(
            untreated,
            treated,
            envelope_min_m=untreated.bounding_box_min_m,
            envelope_max_m=untreated.bounding_box_max_m,
        )

    def test_operator_entry_requests_treatment_only_when_enabled(self) -> None:
        from se2cad.solidworks.__main__ import _treatment_from_argv

        self.assertEqual(_treatment_from_argv([]), EDGE_TREATMENT_OFF)
        self.assertEqual(_treatment_from_argv(["--edge-treatment", "off"]), EDGE_TREATMENT_OFF)
        self.assertEqual(
            _treatment_from_argv(["--edge-treatment", "chamfer"]),
            EDGE_TREATMENT_CHAMFER,
        )
        with self.assertRaises(SystemExit):
            _treatment_from_argv(["--edge-treatment", "fillet"])
        with self.assertRaises(SystemExit):
            _treatment_from_argv(["--help"])

    def test_chamfer_request_is_the_only_enabled_kind(self) -> None:
        self.assertFalse(EDGE_TREATMENT_OFF.enabled)
        self.assertTrue(EDGE_TREATMENT_CHAMFER.enabled)
        self.assertEqual(
            EDGE_TREATMENT_CHAMFER.kind,
            EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK,
        )
        self.assertIsInstance(
            EdgeTreatmentRequest(kind=EdgeTreatmentKind.OFF),
            EdgeTreatmentRequest,
        )


if __name__ == "__main__":
    unittest.main()
