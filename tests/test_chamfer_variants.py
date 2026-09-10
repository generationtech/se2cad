"""Ordinary tests for configurable demand-driven chamfer variants (S2C-10.4.1)."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import FILLER_GEOMETRY_ID, UnknownSubtypeError, load_default_catalog
from se2cad.ir import build_canonical_blueprint, component_name_from_block
from se2cad.library import (
    CHAMFER_SETBACK_MAX_MM,
    CHAMFER_SETBACK_MIN_MM,
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_OFF,
    EDGE_TREATMENT_SETBACK_MM,
    TreatmentError,
    all_library_records,
    apply_edge_treatment,
    chamfer_size_token,
    chamfer_treatment,
    filler_library_record,
    geometry_supports_chamfer,
    lookup_recipe,
    parse_chamfer_mm_token,
    representative_automatable_geometry_ids,
    solid_from_recipe,
    validate_chamfer_setback_mm,
)
from se2cad.parser import parse_blueprint
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.solidworks import (
    GeneratedRootError,
    MissingCanonicalPartError,
    SolidWorksComError,
    is_treated_artifact_filename,
    logical_part_filename,
    logical_treated_part_filename,
    part_artifact_path,
    placements_from_ir,
    require_canonical_part_files,
    treated_artifact_key,
)
from se2cad.solidworks.artifacts import assert_overwrite_is_canonical, contained_destination
from se2cad.solidworks.assemble import _parse_assemble_argv, _request_from_cli_flags
from se2cad.solidworks.generate import generate_one_canonical_part
from se2cad.solidworks.placement import (
    CHAMFER_UNAVAILABLE_REASON,
    demanded_treated_geometry_ids,
    missing_treated_geometry_ids,
    resolved_assembly_part_filename,
    treatment_report_from_ir,
)
from se2cad.solidworks.__main__ import _treatment_from_argv


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"


def _fixture_ir():
    return build_canonical_blueprint(parse_blueprint(FIXTURE_PATH), load_default_catalog())


def _permissive_mixed_ir():
    xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-chamfer-fallback" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>NotACatalogSubtype</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fallback.sbc"
        path.write_text(xml, encoding="utf-8")
        parsed = parse_blueprint(path)
    return convert_blueprint(
        parsed, load_default_catalog(), ConversionPolicy.PERMISSIVE
    ).ir


class ChamferSizeValidationTests(unittest.TestCase):
    def test_default_chamfer_is_50mm(self) -> None:
        self.assertEqual(EDGE_TREATMENT_SETBACK_MM, 50)
        self.assertEqual(EDGE_TREATMENT_CHAMFER.setback_mm, 50)
        self.assertEqual(chamfer_treatment().setback_mm, 50)
        self.assertEqual(chamfer_size_token(50), "50mm")

    def test_alternate_valid_size_is_distinct(self) -> None:
        request = chamfer_treatment(75)
        self.assertEqual(request.setback_mm, 75)
        self.assertNotEqual(request, EDGE_TREATMENT_CHAMFER)
        self.assertEqual(chamfer_size_token(75), "75mm")

    def test_inclusive_boundaries_are_accepted(self) -> None:
        self.assertEqual(validate_chamfer_setback_mm(CHAMFER_SETBACK_MIN_MM), 5.0)
        self.assertEqual(validate_chamfer_setback_mm(CHAMFER_SETBACK_MAX_MM), 250.0)
        self.assertEqual(chamfer_size_token(5), "5mm")
        self.assertEqual(chamfer_size_token(250), "250mm")

    def test_values_outside_range_are_rejected_without_clamping(self) -> None:
        with self.assertRaises(TreatmentError) as low:
            validate_chamfer_setback_mm(4)
        with self.assertRaises(TreatmentError) as high:
            validate_chamfer_setback_mm(251)
        self.assertIn("4", str(low.exception))
        self.assertIn("251", str(high.exception))
        self.assertNotIn("clamped", str(low.exception).lower())

    def test_nan_and_infinity_are_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(TreatmentError):
                    validate_chamfer_setback_mm(value)
        for token in ("nan", "NaN", "inf", "+inf", "-inf"):
            with self.subTest(token=token):
                with self.assertRaises(TreatmentError):
                    parse_chamfer_mm_token(token)


class ChamferCliTests(unittest.TestCase):
    def test_assemble_default_size_when_chamfer_omits_mm(self) -> None:
        parsed = _parse_assemble_argv(
            [str(FIXTURE_PATH), "--edge-treatment", "chamfer"]
        )
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed[1], EDGE_TREATMENT_CHAMFER)
        self.assertEqual(parsed[1].setback_mm, 50)

    def test_assemble_accepts_explicit_size(self) -> None:
        parsed = _parse_assemble_argv(
            [str(FIXTURE_PATH), "--edge-treatment", "chamfer", "--chamfer-mm", "75"]
        )
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed[1], chamfer_treatment(75))

    def test_assemble_rejects_chamfer_mm_without_chamfer(self) -> None:
        self.assertIsNone(
            _parse_assemble_argv([str(FIXTURE_PATH), "--chamfer-mm", "50"])
        )
        self.assertIsNone(
            _parse_assemble_argv(
                [str(FIXTURE_PATH), "--edge-treatment", "off", "--chamfer-mm", "50"]
            )
        )
        with self.assertRaises(TreatmentError):
            _request_from_cli_flags(None, "50")

    def test_assemble_rejects_invalid_sizes(self) -> None:
        for value in ("4", "251", "nan", "inf"):
            with self.subTest(value=value):
                self.assertIsNone(
                    _parse_assemble_argv(
                        [
                            str(FIXTURE_PATH),
                            "--edge-treatment",
                            "chamfer",
                            "--chamfer-mm",
                            value,
                        ]
                    )
                )

    def test_part_generation_entry_stays_narrow(self) -> None:
        self.assertEqual(_treatment_from_argv([]), EDGE_TREATMENT_OFF)
        self.assertEqual(
            _treatment_from_argv(["--edge-treatment", "chamfer"]),
            EDGE_TREATMENT_CHAMFER,
        )
        self.assertEqual(
            _treatment_from_argv(
                ["--edge-treatment", "chamfer", "--chamfer-mm", "75"]
            ),
            chamfer_treatment(75),
        )
        with self.assertRaises(SystemExit):
            _treatment_from_argv(["--chamfer-mm", "50"])
        with self.assertRaises(SystemExit):
            _treatment_from_argv(
                ["--edge-treatment", "chamfer", "--chamfer-mm", "4"]
            )


class TreatedArtifactIdentityTests(unittest.TestCase):
    def test_shared_key_is_size_specific_and_deterministic(self) -> None:
        default = treated_artifact_key("large_armor_block", EDGE_TREATMENT_CHAMFER)
        alt = treated_artifact_key("large_armor_block", chamfer_treatment(75))
        self.assertEqual(default, "large_armor_block_chamfer_50mm")
        self.assertEqual(alt, "large_armor_block_chamfer_75mm")
        self.assertEqual(
            logical_treated_part_filename(
                "large_armor_block", EDGE_TREATMENT_CHAMFER
            ),
            "large_armor_block_chamfer_50mm.SLDPRT",
        )
        self.assertEqual(
            logical_treated_part_filename(
                "large_heavy_block_armor_slope", chamfer_treatment(100)
            ),
            "large_heavy_block_armor_slope_chamfer_100mm.SLDPRT",
        )
        self.assertNotIn("v1", default)
        self.assertNotIn("algo", default)

    def test_different_sizes_are_different_artifacts(self) -> None:
        fifty = logical_treated_part_filename(
            "large_armor_block", chamfer_treatment(50)
        )
        seventy_five = logical_treated_part_filename(
            "large_armor_block", chamfer_treatment(75)
        )
        self.assertNotEqual(fifty, seventy_five)
        self.assertTrue(is_treated_artifact_filename(fifty))
        self.assertTrue(is_treated_artifact_filename(seventy_five))

    def test_generic_chamfer_name_is_not_a_treated_artifact(self) -> None:
        self.assertFalse(is_treated_artifact_filename("large_armor_block_chamfer.SLDPRT"))
        self.assertFalse(
            is_treated_artifact_filename("large_armor_block_chamfer_999mm.SLDPRT")
        )
        self.assertFalse(is_treated_artifact_filename("notes_chamfer_50mm.SLDPRT"))

    def test_path_tokens_cannot_smuggle_into_artifact_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = part_artifact_path(
                root, "large_armor_block", chamfer_treatment(75)
            )
            self.assertEqual(destination.name, "large_armor_block_chamfer_75mm.SLDPRT")
            destination.relative_to(root.resolve())
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "../large_armor_block_chamfer_50mm.SLDPRT")
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "sub/large_armor_block_chamfer_50mm.SLDPRT")
            self.assertFalse(
                is_treated_artifact_filename("../large_armor_block_chamfer_50mm.SLDPRT")
            )
            stale = root / "large_armor_block_chamfer.SLDPRT"
            stale.write_bytes(b"old")
            with self.assertRaises(GeneratedRootError):
                assert_overwrite_is_canonical(stale)


class ChamferCapabilityTests(unittest.TestCase):
    def test_qualified_constructions_are_chamfer_capable(self) -> None:
        for record in all_library_records():
            self.assertTrue(record.chamfer_capable, msg=record.geometry_id)
            self.assertTrue(geometry_supports_chamfer(record.geometry_id))
        self.assertTrue(geometry_supports_chamfer("large_heavy_block_armor_block"))

    def test_filler_is_explicitly_not_chamfer_capable(self) -> None:
        filler = filler_library_record()
        self.assertEqual(filler.geometry_id, FILLER_GEOMETRY_ID)
        self.assertFalse(filler.chamfer_capable)
        self.assertFalse(geometry_supports_chamfer(FILLER_GEOMETRY_ID))
        self.assertEqual(filler.recipe_kind.value, "native_procedural")

    def test_capability_is_not_catalog_support(self) -> None:
        catalog = load_default_catalog()
        armor = catalog.lookup("LargeBlockArmorBlock")
        self.assertEqual(armor.support_status.value, "supported")
        self.assertTrue(geometry_supports_chamfer(armor.geometry_id))
        with self.assertRaises(UnknownSubtypeError):
            catalog.lookup("NotACatalogSubtype")
        self.assertFalse(geometry_supports_chamfer(FILLER_GEOMETRY_ID))


class DemandDrivenResolutionTests(unittest.TestCase):
    def test_untreated_assembly_is_unchanged(self) -> None:
        ir = _fixture_ir()
        omitted = placements_from_ir(ir)
        off = placements_from_ir(ir, EDGE_TREATMENT_OFF)
        report = treatment_report_from_ir(ir)
        self.assertEqual(demanded_treated_geometry_ids(ir), ())
        self.assertEqual(report.requested_kind, "off")
        self.assertEqual(report.treated_component_count, 0)
        self.assertEqual(report.untreated_fallback_component_count, 0)
        for item, prior, block in zip(omitted, off, ir.grid.blocks, strict=True):
            self.assertEqual(item.part_filename, f"{item.geometry_id}.SLDPRT")
            self.assertEqual(item.part_filename, prior.part_filename)
            self.assertEqual(item.component_name, component_name_from_block(block))
            self.assertNotIn("_chamfer", item.component_name)

    def test_demand_lists_only_blueprint_geometry(self) -> None:
        ir = _fixture_ir()
        demanded = demanded_treated_geometry_ids(ir, EDGE_TREATMENT_CHAMFER)
        self.assertEqual(
            set(demanded),
            {
                "large_armor_block",
                "large_armor_slope",
                "large_armor_corner",
                "large_armor_corner_inv",
            },
        )
        for extra in representative_automatable_geometry_ids():
            self.assertNotIn(extra, demanded)
        self.assertNotIn(FILLER_GEOMETRY_ID, demanded)

    def test_same_size_is_reused_and_other_size_is_not(self) -> None:
        ir = _fixture_ir()
        demanded = demanded_treated_geometry_ids(ir, EDGE_TREATMENT_CHAMFER)
        alt = chamfer_treatment(75)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for geometry_id in demanded:
                (root / f"{geometry_id}_chamfer_50mm.SLDPRT").write_bytes(b"fifty")
            self.assertEqual(
                missing_treated_geometry_ids(root, demanded, EDGE_TREATMENT_CHAMFER),
                (),
            )
            self.assertEqual(
                missing_treated_geometry_ids(root, demanded, alt),
                demanded,
            )

    def test_old_generic_name_is_not_reused(self) -> None:
        demanded = ("large_armor_block",)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large_armor_block_chamfer.SLDPRT").write_bytes(b"stale")
            (root / "large_armor_block.SLDPRT").write_bytes(b"untreated")
            self.assertEqual(
                missing_treated_geometry_ids(
                    root, demanded, EDGE_TREATMENT_CHAMFER
                ),
                demanded,
            )
            with self.assertRaises(MissingCanonicalPartError) as ctx:
                require_canonical_part_files(
                    root, EDGE_TREATMENT_CHAMFER, geometry_ids=demanded
                )
            self.assertIn("large_armor_block_chamfer_50mm.SLDPRT", str(ctx.exception))
            self.assertNotIn("resolved untreated", str(ctx.exception).lower())

    def test_capable_missing_treated_does_not_resolve_untreated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large_armor_block.SLDPRT").write_bytes(b"untreated")
            with self.assertRaises(MissingCanonicalPartError) as ctx:
                require_canonical_part_files(
                    root,
                    EDGE_TREATMENT_CHAMFER,
                    geometry_ids=("large_armor_block",),
                )
            message = str(ctx.exception)
            self.assertIn("large_armor_block_chamfer_50mm.SLDPRT", message)
            found = require_canonical_part_files(
                root, EDGE_TREATMENT_OFF, geometry_ids=("large_armor_block",)
            )
            self.assertEqual(found["large_armor_block"].name, "large_armor_block.SLDPRT")


class UnsupportedChamferFallbackTests(unittest.TestCase):
    def test_non_capable_geometry_uses_untreated_and_is_reported(self) -> None:
        ir = _permissive_mixed_ir()
        request = chamfer_treatment(75)
        placements = placements_from_ir(ir, request)
        report = treatment_report_from_ir(ir, request)
        demanded = demanded_treated_geometry_ids(ir, request)
        self.assertEqual(len(placements), 2)
        self.assertEqual(placements[0].part_filename, "large_armor_block_chamfer_75mm.SLDPRT")
        self.assertEqual(placements[1].part_filename, "se2cad_unknown_filler.SLDPRT")
        self.assertEqual(placements[1].geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(placements[1].subtype_id, "NotACatalogSubtype")
        self.assertNotIn("_chamfer", placements[1].component_name)
        self.assertEqual(demanded, ("large_armor_block",))
        self.assertEqual(report.requested_kind, "chamfer")
        self.assertEqual(report.requested_setback_mm, 75)
        self.assertEqual(report.treated_component_count, 1)
        self.assertEqual(report.untreated_fallback_component_count, 1)
        self.assertEqual(len(report.fallbacks), 1)
        fallback = report.fallbacks[0]
        self.assertEqual(fallback.subtype_id, "NotACatalogSubtype")
        self.assertEqual(fallback.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(fallback.requested_setback_mm, 75)
        self.assertEqual(fallback.reason, CHAMFER_UNAVAILABLE_REASON)

    def test_fallback_lookup_uses_untreated_filler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large_armor_block_chamfer_50mm.SLDPRT").write_bytes(b"treated")
            (root / "se2cad_unknown_filler.SLDPRT").write_bytes(b"filler")
            found = require_canonical_part_files(
                root,
                EDGE_TREATMENT_CHAMFER,
                geometry_ids=("large_armor_block", FILLER_GEOMETRY_ID),
            )
            self.assertEqual(
                found["large_armor_block"].name,
                "large_armor_block_chamfer_50mm.SLDPRT",
            )
            self.assertEqual(
                found[FILLER_GEOMETRY_ID].name, "se2cad_unknown_filler.SLDPRT"
            )
            self.assertFalse(
                (root / "se2cad_unknown_filler_chamfer_50mm.SLDPRT").exists()
            )

    def test_transforms_and_names_stay_on_the_ir(self) -> None:
        ir = _permissive_mixed_ir()
        default = placements_from_ir(ir)
        treated = placements_from_ir(ir, EDGE_TREATMENT_CHAMFER)
        for left, right, block in zip(default, treated, ir.grid.blocks, strict=True):
            self.assertEqual(left.component_name, right.component_name)
            self.assertEqual(left.component_name, component_name_from_block(block))
            self.assertEqual(left.position_mm, right.position_mm)
            self.assertEqual(left.rotation, right.rotation)
            self.assertEqual(left.appearance_rgb, right.appearance_rgb)
            self.assertNotIn("chamfer", left.component_name)
            self.assertNotIn("50mm", right.component_name)


class CapableGenerationFailureTests(unittest.TestCase):
    def test_explicit_generation_refuses_non_capable_geometry(self) -> None:
        from se2cad.solidworks.config import SolidWorksBackendConfig

        with tempfile.TemporaryDirectory() as tmp:
            config = SolidWorksBackendConfig(
                generated_root=Path(tmp).resolve(),
                part_template=None,
                visible=False,
                source="test",
            )
            with self.assertRaises(SolidWorksComError) as ctx:
                generate_one_canonical_part(
                    object(),
                    FILLER_GEOMETRY_ID,
                    config,
                    treatment=EDGE_TREATMENT_CHAMFER,
                )
            self.assertIn("not chamfer-capable", str(ctx.exception))
            self.assertFalse(
                any(Path(tmp).glob("se2cad_unknown_filler_chamfer_*.SLDPRT"))
            )

    def test_capable_generation_failure_is_not_swallowed(self) -> None:
        ir = _fixture_ir()
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.config import SolidWorksBackendConfig

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = SolidWorksBackendConfig(
                generated_root=root.resolve(),
                part_template=None,
                visible=False,
                source="test",
            )
            for geometry_id in (
                "large_armor_block",
                "large_armor_slope",
                "large_armor_corner",
                "large_armor_corner_inv",
            ):
                (root / f"{geometry_id}.SLDPRT").write_bytes(b"untreated")
            with patch(
                "se2cad.solidworks.assemble.require_solidworks_backend",
                return_value=None,
            ), patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=SolidWorksComError("treated generation failed"),
            ):
                with self.assertRaises(SolidWorksComError) as ctx:
                    generate_assembly_from_ir(ir, config, EDGE_TREATMENT_CHAMFER)
            self.assertIn("treated generation failed", str(ctx.exception))
            self.assertFalse(any(root.glob("*_chamfer_*.SLDPRT")))
            self.assertEqual(
                resolved_assembly_part_filename(
                    "large_armor_block", EDGE_TREATMENT_CHAMFER
                ),
                "large_armor_block_chamfer_50mm.SLDPRT",
            )


class CadNeutralSizedTreatmentTests(unittest.TestCase):
    def test_alternate_size_changes_volume_without_changing_recipe(self) -> None:
        recipe = lookup_recipe("large_armor_block")
        solid = solid_from_recipe(recipe)
        fifty = apply_edge_treatment(solid, EDGE_TREATMENT_CHAMFER)
        seventy_five = apply_edge_treatment(solid, chamfer_treatment(75))
        self.assertTrue(fifty.applied)
        self.assertTrue(seventy_five.applied)
        self.assertLess(seventy_five.volume_times_6, fifty.volume_times_6)
        self.assertEqual(lookup_recipe("large_armor_block").vertices_mm, recipe.vertices_mm)

    def test_resolved_filename_never_uses_untreated_for_capable_chamfer(self) -> None:
        self.assertEqual(
            resolved_assembly_part_filename(
                "large_armor_block", EDGE_TREATMENT_CHAMFER
            ),
            logical_treated_part_filename("large_armor_block", EDGE_TREATMENT_CHAMFER),
        )
        self.assertEqual(
            resolved_assembly_part_filename("large_armor_block", EDGE_TREATMENT_OFF),
            logical_part_filename("large_armor_block"),
        )


if __name__ == "__main__":
    unittest.main()
