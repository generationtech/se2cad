"""Windows/SolidWorks 2026 integration tests.

Skipped tests are not qualification evidence. Set
SE2CAD_SOLIDWORKS_INTEGRATION=1 in the Windows VM to require a real run.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

INTEGRATION_ENV = "SE2CAD_SOLIDWORKS_INTEGRATION"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
)


def _integration_requested() -> bool:
    return os.environ.get(INTEGRATION_ENV, "").strip() in {"1", "true", "yes"}


@unittest.skipUnless(
    _integration_requested(),
    "set SE2CAD_SOLIDWORKS_INTEGRATION=1 in the Windows SolidWorks VM",
)
class SolidWorksIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from se2cad.solidworks.availability import require_solidworks_backend
        from se2cad.solidworks.config import load_solidworks_backend_config

        require_solidworks_backend()
        cls.config = load_solidworks_backend_config()

    def test_four_canonical_parts_generate_validate_save_and_reopen(self) -> None:
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.pipeline import resolve_recipes_from_blueprint

        resolved = resolve_recipes_from_blueprint(FIXTURE_PATH)
        self.assertEqual(len(resolved.geometry_ids), 4)

        with SolidWorksSession(self.config) as session:
            report = session_environment_report(session)
            self.assertTrue(report["solidworks_revision"])
            if not report["solidworks_revision"].startswith("34"):
                # SW 2026 is revision 34 (year - 1992). Record but do not
                # invent a second product; fail if this is clearly not 2026.
                self.assertIn(
                    "2026",
                    report["solidworks_revision"],
                    msg=f"expected SolidWorks 2026, got {report}",
                )

        results = generate_canonical_parts(self.config)
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertTrue(result.locator.path.is_file())
            self.assertTrue(result.locator.path.is_relative_to(self.config.generated_root))
            self.assertEqual(result.after_save.solid_body_count, 1)
            self.assertEqual(result.after_reopen.solid_body_count, 1)
            self.assertEqual(result.after_reopen.sheet_body_count, 0)
            self.assertEqual(result.locator.identity.filename, result.locator.path.name)

    def test_transform_placed_assembly_from_acceptance_fixture(self) -> None:
        from collections import Counter

        from se2cad.solidworks.assemble import generate_assembly
        from se2cad.solidworks.transform_pack import (
            arraydata_axes,
            arraydata_translation_m,
            solidworks_arraydata,
        )
        from se2cad.transform import IDENTITY_ROTATION, rotation_from_forward_up
        from se2cad.parser import Direction

        result = generate_assembly(FIXTURE_PATH, self.config)
        self.assertEqual(result.identity, "se2cad-test1")
        self.assertEqual(result.path.name, "se2cad-test1.SLDASM")
        self.assertTrue(result.path.is_file())
        self.assertTrue(result.path.is_relative_to(self.config.generated_root))
        self.assertEqual(len(result.placements), 24)
        self.assertEqual(len(result.after_save), 24)
        self.assertEqual(len(result.after_reopen), 24)
        self.assertEqual(
            Counter(item.placement.geometry_id for item in result.after_reopen),
            Counter(
                {
                    "large_armor_block": 9,
                    "large_armor_slope": 12,
                    "large_armor_corner": 2,
                    "large_armor_corner_inv": 1,
                }
            ),
        )

        by_min = {
            item.placement.grid_min: item for item in result.after_reopen
        }
        origin = by_min[(0, 0, 0)]
        self.assertEqual(origin.placement.part_filename, "large_armor_block.SLDPRT")
        self.assertTrue(origin.placement.rotation.is_identity())
        self.assertEqual(arraydata_translation_m(origin.arraydata), (0.0, 0.0, 0.0))
        self.assertEqual(arraydata_axes(origin.arraydata), IDENTITY_ROTATION.columns)

        neighbor = by_min[(1, 0, 0)]
        self.assertEqual(arraydata_translation_m(neighbor.arraydata), (2.5, 0.0, 0.0))

        down_forward = by_min[(0, 0, -1)]
        expected_df = rotation_from_forward_up(Direction.DOWN, Direction.FORWARD)
        self.assertEqual(arraydata_axes(down_forward.arraydata), expected_df.columns)
        self.assertEqual(arraydata_translation_m(down_forward.arraydata), (0.0, 0.0, -2.5))

        down_right = by_min[(1, 1, 0)]
        expected_dr = rotation_from_forward_up(Direction.DOWN, Direction.RIGHT)
        self.assertEqual(arraydata_axes(down_right.arraydata), expected_dr.columns)
        self.assertEqual(arraydata_translation_m(down_right.arraydata), (2.5, 2.5, 0.0))
        self.assertEqual(
            down_right.arraydata,
            solidworks_arraydata(expected_dr, (2500, 2500, 0)),
        )

        from se2cad.catalog import load_default_catalog
        from se2cad.ir import build_canonical_blueprint, component_name_from_block
        from se2cad.parser import parse_blueprint

        ir = build_canonical_blueprint(parse_blueprint(FIXTURE_PATH), load_default_catalog())
        save_by_index = {item.placement.source_index: item for item in result.after_save}
        reopen_by_index = {
            item.placement.source_index: item for item in result.after_reopen
        }
        self.assertEqual(len(save_by_index), 24)
        self.assertEqual(len(reopen_by_index), 24)
        omitted_identity = 0
        for block in ir.grid.blocks:
            saved = save_by_index[block.source_index]
            reopened = reopen_by_index[block.source_index]
            expected = solidworks_arraydata(
                block.rotation, block.position_mm.as_tuple()
            )
            self.assertEqual(reopened.placement.geometry_id, block.geometry_id)
            self.assertEqual(
                reopened.placement.part_filename, f"{block.geometry_id}.SLDPRT"
            )
            expected_name = component_name_from_block(block)
            self.assertEqual(reopened.placement.component_name, expected_name)
            self.assertEqual(reopened.component_name, expected_name)
            self.assertEqual(saved.component_name, expected_name)
            self.assertEqual(reopened.part_path.name, reopened.placement.part_filename)
            self.assertTrue(reopened.part_path.is_relative_to(self.config.generated_root))
            self.assertEqual(
                reopened.placement.grid_min,
                (block.grid_min.x, block.grid_min.y, block.grid_min.z),
            )
            self.assertEqual(arraydata_axes(reopened.arraydata), block.rotation.columns)
            self.assertEqual(reopened.arraydata, expected)
            self.assertEqual(saved.arraydata, reopened.arraydata)
            if not block.orientation_serialized:
                omitted_identity += 1
                self.assertTrue(block.rotation.is_identity())
                self.assertEqual(arraydata_axes(reopened.arraydata), IDENTITY_ROTATION.columns)
        self.assertEqual(omitted_identity, 15)

        from se2cad.parser import AppearanceSupport, DEFAULT_COLOR_MASK_HSV
        from se2cad.solidworks.appearance import color_mask_hsv_to_rgb, rgb_close

        default_rgb = color_mask_hsv_to_rgb(DEFAULT_COLOR_MASK_HSV)
        for block in ir.grid.blocks:
            reopened = reopen_by_index[block.source_index]
            self.assertEqual(reopened.appearance_support, AppearanceSupport.DEFAULT)
            self.assertTrue(rgb_close(reopened.appearance_rgb, default_rgb))
            self.assertTrue(reopened.geometry_applied)
            self.assertTrue(reopened.appearance_applied)

    def test_instance_appearance_two_colors_and_default(self) -> None:
        from se2cad.parser import AppearanceSupport, DEFAULT_COLOR_MASK_HSV
        from se2cad.solidworks.appearance import color_mask_hsv_to_rgb, rgb_close
        from se2cad.solidworks.assemble import generate_assembly
        from se2cad.solidworks.generate import generate_canonical_parts

        parts = generate_canonical_parts(self.config)
        part_hashes = {
            result.locator.path.name: hashlib.sha256(
                result.locator.path.read_bytes()
            ).hexdigest()
            for result in parts
        }
        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-color1" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
              <Min x="1" y="0" z="0" />
              <ColorMaskHSV x="0" y="0.2" z="0.55" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
              <Min x="2" y="0" z="0" />
              <ColorMaskHSV x="0.6666667" y="0.2" z="0.55" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            blueprint = Path(tmp) / "bp.sbc"
            blueprint.write_text(xml, encoding="utf-8")
            result = generate_assembly(blueprint, self.config)
        self.assertEqual(result.identity, "se2cad-color1")
        self.assertEqual(result.path.name, "se2cad-color1.SLDASM")
        self.assertEqual(len(result.after_reopen), 3)
        by_min = {item.placement.grid_min: item for item in result.after_reopen}
        expected = {
            (0, 0, 0): (AppearanceSupport.DEFAULT, color_mask_hsv_to_rgb(DEFAULT_COLOR_MASK_HSV)),
            (1, 0, 0): (AppearanceSupport.EXPLICIT, (1.0, 0.0, 0.0)),
            (2, 0, 0): (AppearanceSupport.EXPLICIT, (0.0, 0.0, 1.0)),
        }
        filenames = set()
        for cell, (support, rgb) in expected.items():
            item = by_min[cell]
            self.assertTrue(item.geometry_applied)
            self.assertTrue(item.appearance_applied)
            self.assertEqual(item.appearance_support, support)
            self.assertEqual(item.placement.part_filename, "large_armor_block.SLDPRT")
            self.assertTrue(
                rgb_close(item.appearance_rgb, rgb),
                msg=f"{cell} {item.appearance_rgb} != {rgb}",
            )
            filenames.add(item.part_path.name)
        self.assertEqual(filenames, {"large_armor_block.SLDPRT"})
        after_hashes = {
            name: hashlib.sha256((self.config.generated_root / name).read_bytes()).hexdigest()
            for name in part_hashes
        }
        self.assertEqual(after_hashes, part_hashes)

    def test_treated_and_untreated_canonical_parts(self) -> None:
        from se2cad.library import (
            CANONICAL_CELL_ENVELOPE,
            EDGE_TREATMENT_CHAMFER,
            EDGE_TREATMENT_MIN_VOLUME_RATIO,
            EDGE_TREATMENT_OFF,
        )
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.units import mm_to_metres

        untreated = generate_canonical_parts(self.config)
        self.assertEqual(len(untreated), 4)
        untreated_hashes = {}
        for result in untreated:
            self.assertEqual(result.treatment, EDGE_TREATMENT_OFF)
            self.assertFalse(result.treatment_applied)
            self.assertEqual(result.after_reopen.solid_body_count, 1)
            self.assertEqual(result.after_reopen.sheet_body_count, 0)
            self.assertEqual(
                result.locator.identity.filename,
                f"{result.locator.identity.geometry_id}.SLDPRT",
            )
            self.assertTrue(result.locator.path.is_relative_to(self.config.generated_root))
            untreated_hashes[result.locator.path.name] = hashlib.sha256(
                result.locator.path.read_bytes()
            ).hexdigest()

        treated = generate_canonical_parts(
            self.config, treatment=EDGE_TREATMENT_CHAMFER
        )
        self.assertEqual(len(treated), 4)
        half = mm_to_metres(CANONICAL_CELL_ENVELOPE.max_mm[0])
        for result, prior in zip(treated, untreated):
            geometry_id = result.locator.identity.geometry_id
            self.assertEqual(result.treatment, EDGE_TREATMENT_CHAMFER)
            self.assertTrue(result.treatment_applied)
            self.assertEqual(
                result.locator.identity.filename,
                f"{geometry_id}_chamfer_50mm.SLDPRT",
            )
            self.assertTrue(result.locator.path.is_file())
            self.assertTrue(result.locator.path.is_relative_to(self.config.generated_root))
            self.assertNotEqual(result.locator.path, prior.locator.path)
            self.assertEqual(result.after_save.solid_body_count, 1)
            self.assertEqual(result.after_reopen.solid_body_count, 1)
            self.assertEqual(result.after_reopen.sheet_body_count, 0)
            self.assertIsNotNone(result.untreated_after_construct)
            untreated_volume = result.untreated_after_construct.volume_m3
            treated_volume = result.after_reopen.volume_m3
            self.assertLess(treated_volume, untreated_volume)
            self.assertGreaterEqual(
                treated_volume / untreated_volume,
                EDGE_TREATMENT_MIN_VOLUME_RATIO,
            )
            self.assertGreaterEqual(result.after_reopen.bounding_box_min_m[0], -half - 1e-6)
            self.assertLessEqual(result.after_reopen.bounding_box_max_m[0], half + 1e-6)
            if (
                result.untreated_after_construct.face_count is not None
                and result.after_reopen.face_count is not None
            ):
                self.assertGreater(
                    result.after_reopen.face_count,
                    result.untreated_after_construct.face_count,
                )

        after_hashes = {
            name: hashlib.sha256((self.config.generated_root / name).read_bytes()).hexdigest()
            for name in untreated_hashes
        }
        self.assertEqual(after_hashes, untreated_hashes)

    def test_representative_automatable_parts_generate_validate_save_and_reopen(self) -> None:
        from se2cad.library import lookup_recipe, representative_automatable_geometry_ids
        from se2cad.solidworks.generate import generate_representative_automatable_parts
        from se2cad.solidworks.recipe_plan import plan_from_recipe
        from se2cad.solidworks.units import mm_to_metres

        expected_ids = representative_automatable_geometry_ids()
        self.assertEqual(len(expected_ids), 4)
        results = generate_representative_automatable_parts(self.config)
        self.assertEqual(len(results), 4)
        self.assertEqual(
            tuple(result.locator.identity.geometry_id for result in results),
            expected_ids,
        )
        half_m = mm_to_metres(lookup_recipe(expected_ids[0]).validation.bounding_box.max_mm[0])
        for result in results:
            plan = plan_from_recipe(lookup_recipe(result.locator.identity.geometry_id))
            self.assertTrue(result.locator.path.is_file())
            self.assertTrue(result.locator.path.is_relative_to(self.config.generated_root))
            self.assertEqual(
                result.locator.identity.filename,
                f"{result.locator.identity.geometry_id}.SLDPRT",
            )
            self.assertEqual(result.locator.identity.filename, result.locator.path.name)
            self.assertEqual(result.after_save.solid_body_count, 1)
            self.assertEqual(result.after_reopen.solid_body_count, 1)
            self.assertEqual(result.after_reopen.sheet_body_count, 0)
            self.assertAlmostEqual(
                result.after_reopen.volume_m3, plan.expected.volume_m3, places=5
            )
            self.assertGreaterEqual(result.after_reopen.bounding_box_min_m[0], -half_m - 1e-6)
            self.assertLessEqual(result.after_reopen.bounding_box_max_m[0], half_m + 1e-6)

    def test_treated_assembly_consumes_treated_siblings(self) -> None:
        from collections import Counter

        from se2cad.catalog import load_default_catalog
        from se2cad.ir import build_canonical_blueprint, component_name_from_block
        from se2cad.library import EDGE_TREATMENT_CHAMFER
        from se2cad.parser import AppearanceSupport, DEFAULT_COLOR_MASK_HSV, parse_blueprint
        from se2cad.solidworks.appearance import color_mask_hsv_to_rgb, rgb_close
        from se2cad.solidworks.assemble import generate_assembly
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.transform_pack import solidworks_arraydata

        untreated = generate_canonical_parts(self.config)
        untreated_hashes = {
            result.locator.path.name: hashlib.sha256(
                result.locator.path.read_bytes()
            ).hexdigest()
            for result in untreated
        }
        generate_canonical_parts(self.config, treatment=EDGE_TREATMENT_CHAMFER)

        treated_result = generate_assembly(
            FIXTURE_PATH, self.config, treatment=EDGE_TREATMENT_CHAMFER
        )
        self.assertEqual(treated_result.identity, "se2cad-test1")
        self.assertEqual(treated_result.path.name, "se2cad-test1.SLDASM")
        self.assertTrue(treated_result.path.is_relative_to(self.config.generated_root))
        self.assertEqual(len(treated_result.after_reopen), 24)
        self.assertEqual(
            Counter(item.placement.geometry_id for item in treated_result.after_reopen),
            Counter(
                {
                    "large_armor_block": 9,
                    "large_armor_slope": 12,
                    "large_armor_corner": 2,
                    "large_armor_corner_inv": 1,
                }
            ),
        )

        ir = build_canonical_blueprint(parse_blueprint(FIXTURE_PATH), load_default_catalog())
        default_rgb = color_mask_hsv_to_rgb(DEFAULT_COLOR_MASK_HSV)
        reopen_by_index = {
            item.placement.source_index: item for item in treated_result.after_reopen
        }
        save_by_index = {
            item.placement.source_index: item for item in treated_result.after_save
        }
        for block in ir.grid.blocks:
            reopened = reopen_by_index[block.source_index]
            saved = save_by_index[block.source_index]
            expected = solidworks_arraydata(
                block.rotation, block.position_mm.as_tuple()
            )
            self.assertEqual(reopened.placement.geometry_id, block.geometry_id)
            self.assertEqual(
                reopened.placement.part_filename,
                f"{block.geometry_id}_chamfer_50mm.SLDPRT",
            )
            expected_name = component_name_from_block(block)
            self.assertEqual(reopened.component_name, expected_name)
            self.assertEqual(saved.component_name, expected_name)
            self.assertNotIn("_chamfer", reopened.component_name)
            self.assertEqual(reopened.part_path.name, reopened.placement.part_filename)
            self.assertTrue(
                reopened.part_path.is_relative_to(self.config.generated_root)
            )
            self.assertEqual(reopened.arraydata, expected)
            self.assertEqual(saved.arraydata, reopened.arraydata)
            self.assertEqual(reopened.appearance_support, AppearanceSupport.DEFAULT)
            self.assertTrue(rgb_close(reopened.appearance_rgb, default_rgb))
            self.assertTrue(reopened.geometry_applied)
            self.assertTrue(reopened.appearance_applied)

        after_treated_hashes = {
            name: hashlib.sha256((self.config.generated_root / name).read_bytes()).hexdigest()
            for name in untreated_hashes
        }
        self.assertEqual(after_treated_hashes, untreated_hashes)

        untreated_result = generate_assembly(FIXTURE_PATH, self.config)
        self.assertEqual(len(untreated_result.after_reopen), 24)
        for item in untreated_result.after_reopen:
            self.assertEqual(
                item.placement.part_filename, f"{item.placement.geometry_id}.SLDPRT"
            )
            self.assertEqual(item.part_path.name, item.placement.part_filename)

    def test_permissive_filler_assembly_keeps_pose_and_distinct_part(self) -> None:
        import tempfile

        from se2cad.catalog import FILLER_GEOMETRY_ID, load_default_catalog
        from se2cad.ir import component_name_from_block
        from se2cad.parser import Direction, parse_blueprint
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.transform_pack import (
            arraydata_axes,
            arraydata_translation_m,
            solidworks_arraydata,
        )
        from se2cad.transform import rotation_from_forward_up

        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-filler-probe" />
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
              <BlockOrientation Forward="Down" Up="Forward" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "filler-probe.sbc"
            path.write_text(xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        result = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.PERMISSIVE
        )
        self.assertEqual(result.ir.grid.block_count, 2)
        self.assertEqual(result.filler_count, 1)
        generate_canonical_parts(
            self.config,
            geometry_ids=("large_armor_block", FILLER_GEOMETRY_ID),
        )
        assembled = generate_assembly_from_ir(result.ir, self.config)
        self.assertEqual(assembled.identity, "se2cad-filler-probe")
        self.assertEqual(assembled.path.name, "se2cad-filler-probe.SLDASM")
        self.assertTrue(assembled.path.is_relative_to(self.config.generated_root))
        self.assertEqual(len(assembled.after_reopen), 2)
        armor, filler = assembled.after_reopen
        self.assertEqual(armor.placement.geometry_id, "large_armor_block")
        self.assertEqual(armor.placement.part_filename, "large_armor_block.SLDPRT")
        self.assertEqual(filler.placement.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(filler.placement.part_filename, "se2cad_unknown_filler.SLDPRT")
        self.assertEqual(filler.placement.subtype_id, "NotACatalogSubtype")
        self.assertNotEqual(filler.part_path.name, armor.part_path.name)
        expected_rotation = rotation_from_forward_up(Direction.DOWN, Direction.FORWARD)
        self.assertEqual(arraydata_translation_m(filler.arraydata), (2.5, 0.0, 0.0))
        self.assertEqual(arraydata_axes(filler.arraydata), expected_rotation.columns)
        ir_filler = result.ir.grid.blocks[1]
        self.assertEqual(
            filler.arraydata,
            solidworks_arraydata(ir_filler.rotation, ir_filler.position_mm.as_tuple()),
        )
        self.assertEqual(
            filler.component_name, component_name_from_block(ir_filler)
        )
        self.assertTrue(filler.geometry_applied)

    def test_configurable_chamfer_is_demand_driven_and_reusable(self) -> None:
        from se2cad.catalog import FILLER_GEOMETRY_ID, load_default_catalog
        from se2cad.library import chamfer_treatment
        from se2cad.parser import parse_blueprint
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.generate import generate_canonical_parts

        root = self.config.generated_root
        with SolidWorksSession(self.config) as session:
            start_report = session_environment_report(session)
            start_documents = int(session.app.GetDocumentCount)
        untreated_path = root / "large_armor_block.SLDPRT"
        if not untreated_path.is_file():
            generate_canonical_parts(
                self.config, geometry_ids=("large_armor_block",)
            )
        untreated_hash = hashlib.sha256(untreated_path.read_bytes()).hexdigest()

        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-chamfer-75" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chamfer-75.sbc"
            path.write_text(xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        ir = convert_blueprint(parsed, load_default_catalog()).ir
        first = generate_assembly_from_ir(ir, self.config, chamfer_treatment(75))
        part_75 = root / "large_armor_block_chamfer_75mm.SLDPRT"
        self.assertTrue(part_75.is_file())
        self.assertEqual(
            first.after_reopen[0].part_path.name,
            "large_armor_block_chamfer_75mm.SLDPRT",
        )
        self.assertEqual(first.treatment_report.requested_setback_mm, 75)
        self.assertEqual(first.treatment_report.treated_component_count, 1)
        self.assertEqual(first.treatment_report.untreated_fallback_component_count, 0)
        self.assertNotIn("_chamfer", first.after_reopen[0].component_name)
        self.assertFalse(
            any(root.glob("large_heavy_block_*_chamfer_75mm.SLDPRT"))
        )
        hash_75 = hashlib.sha256(part_75.read_bytes()).hexdigest()

        second = generate_assembly_from_ir(ir, self.config, chamfer_treatment(75))
        self.assertEqual(hashlib.sha256(part_75.read_bytes()).hexdigest(), hash_75)
        self.assertEqual(
            second.after_reopen[0].part_path.name,
            "large_armor_block_chamfer_75mm.SLDPRT",
        )
        self.assertEqual(
            hashlib.sha256(untreated_path.read_bytes()).hexdigest(),
            untreated_hash,
        )

        fifty = generate_assembly_from_ir(ir, self.config, chamfer_treatment(50))
        part_50 = root / "large_armor_block_chamfer_50mm.SLDPRT"
        self.assertTrue(part_50.is_file())
        self.assertEqual(
            fifty.after_reopen[0].part_path.name,
            "large_armor_block_chamfer_50mm.SLDPRT",
        )
        self.assertNotEqual(
            hashlib.sha256(part_50.read_bytes()).hexdigest(),
            hash_75,
        )
        self.assertEqual(
            hashlib.sha256(untreated_path.read_bytes()).hexdigest(),
            untreated_hash,
        )

        filler_xml = """<?xml version="1.0"?>
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
            path.write_text(filler_xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        fallback_ir = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.PERMISSIVE
        ).ir
        generate_canonical_parts(
            self.config, geometry_ids=(FILLER_GEOMETRY_ID,)
        )
        fallback = generate_assembly_from_ir(
            fallback_ir, self.config, chamfer_treatment(75)
        )
        self.assertEqual(len(fallback.after_reopen), 2)
        by_geometry = {
            item.placement.geometry_id: item for item in fallback.after_reopen
        }
        self.assertEqual(
            by_geometry["large_armor_block"].part_path.name,
            "large_armor_block_chamfer_75mm.SLDPRT",
        )
        self.assertEqual(
            by_geometry[FILLER_GEOMETRY_ID].part_path.name,
            "se2cad_unknown_filler.SLDPRT",
        )
        self.assertEqual(fallback.treatment_report.treated_component_count, 1)
        self.assertEqual(fallback.treatment_report.untreated_fallback_component_count, 1)
        self.assertEqual(
            fallback.treatment_report.fallbacks[0].geometry_id, FILLER_GEOMETRY_ID
        )
        self.assertEqual(
            fallback.treatment_report.fallbacks[0].subtype_id, "NotACatalogSubtype"
        )
        self.assertFalse((root / "se2cad_unknown_filler_chamfer_75mm.SLDPRT").exists())
        self.assertEqual(
            hashlib.sha256(untreated_path.read_bytes()).hexdigest(),
            untreated_hash,
        )

        with SolidWorksSession(self.config) as session:
            end_report = session_environment_report(session)
            end_documents = int(session.app.GetDocumentCount)
        self.assertTrue(start_report["solidworks_revision"])
        self.assertEqual(end_report["started_application"], "False")
        self.assertEqual(end_documents, start_documents)

    def test_demand_driven_base_parts_are_generated_and_reused(self) -> None:
        import shutil

        from se2cad.catalog import FILLER_GEOMETRY_ID, load_default_catalog
        from se2cad.library import chamfer_treatment
        from se2cad.parser import parse_blueprint
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.config import SolidWorksBackendConfig

        probe_root = self.config.generated_root / "s2c-11.6.1-probe"
        if probe_root.exists():
            shutil.rmtree(probe_root)
        probe_root.mkdir(parents=True)
        probe_config = SolidWorksBackendConfig(
            generated_root=probe_root.resolve(),
            part_template=self.config.part_template,
            visible=self.config.visible,
            source="s2c-11.6.1-probe",
        )
        with SolidWorksSession(probe_config) as session:
            start_report = session_environment_report(session)
            start_documents = int(session.app.GetDocumentCount)

        one_xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-base-lazy" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        two_xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-base-two" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorSlope</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        mixed_xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-base-filler" />
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
            one_path = Path(tmp) / "one.sbc"
            two_path = Path(tmp) / "two.sbc"
            mixed_path = Path(tmp) / "mixed.sbc"
            one_path.write_text(one_xml, encoding="utf-8")
            two_path.write_text(two_xml, encoding="utf-8")
            mixed_path.write_text(mixed_xml, encoding="utf-8")
            catalog = load_default_catalog()
            one_ir = convert_blueprint(parse_blueprint(one_path), catalog).ir
            two_ir = convert_blueprint(parse_blueprint(two_path), catalog).ir
            mixed_ir = convert_blueprint(
                parse_blueprint(mixed_path), catalog, ConversionPolicy.PERMISSIVE
            ).ir

        base = probe_root / "large_armor_block.SLDPRT"
        self.assertFalse(base.exists())
        first = generate_assembly_from_ir(one_ir, probe_config)
        self.assertTrue(base.is_file())
        self.assertEqual(first.materialization_report.untreated.generated, ("large_armor_block",))
        self.assertEqual(first.materialization_report.untreated.reused, ())
        self.assertEqual(first.after_reopen[0].part_path.name, "large_armor_block.SLDPRT")
        self.assertTrue(first.after_reopen[0].part_path.is_relative_to(probe_root))
        first_hash = hashlib.sha256(base.read_bytes()).hexdigest()

        second = generate_assembly_from_ir(one_ir, probe_config)
        self.assertEqual(hashlib.sha256(base.read_bytes()).hexdigest(), first_hash)
        self.assertEqual(second.materialization_report.untreated.generated, ())
        self.assertEqual(second.materialization_report.untreated.reused, ("large_armor_block",))
        self.assertEqual(second.after_reopen[0].part_path.name, "large_armor_block.SLDPRT")

        slope = probe_root / "large_armor_slope.SLDPRT"
        self.assertFalse(slope.exists())
        two = generate_assembly_from_ir(two_ir, probe_config)
        self.assertTrue(slope.is_file())
        self.assertEqual(two.materialization_report.untreated.reused, ("large_armor_block",))
        self.assertEqual(two.materialization_report.untreated.generated, ("large_armor_slope",))
        self.assertEqual(len(two.after_reopen), 2)
        self.assertFalse((probe_root / "large_armor_corner.SLDPRT").exists())
        self.assertFalse((probe_root / "large_heavy_block_armor_block.SLDPRT").exists())
        self.assertFalse(any(probe_root.glob("*_chamfer_*.SLDPRT")))
        self.assertEqual(hashlib.sha256(base.read_bytes()).hexdigest(), first_hash)

        corner_xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-base-chamfer" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorCorner</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            corner_path = Path(tmp) / "corner.sbc"
            corner_path.write_text(corner_xml, encoding="utf-8")
            corner_ir = convert_blueprint(
                parse_blueprint(corner_path), load_default_catalog()
            ).ir
        corner = probe_root / "large_armor_corner.SLDPRT"
        corner_treated = probe_root / "large_armor_corner_chamfer_50mm.SLDPRT"
        self.assertFalse(corner.exists())
        self.assertFalse(corner_treated.exists())
        bootstrapped = generate_assembly_from_ir(
            corner_ir, probe_config, chamfer_treatment(50)
        )
        self.assertTrue(corner.is_file())
        self.assertTrue(corner_treated.is_file())
        self.assertEqual(
            bootstrapped.materialization_report.untreated.generated,
            ("large_armor_corner",),
        )
        self.assertEqual(
            bootstrapped.materialization_report.treated.generated,
            ("large_armor_corner",),
        )
        self.assertEqual(
            bootstrapped.after_reopen[0].part_path.name,
            "large_armor_corner_chamfer_50mm.SLDPRT",
        )
        self.assertFalse((probe_root / "large_armor_corner_chamfer.SLDPRT").exists())

        filler = probe_root / "se2cad_unknown_filler.SLDPRT"
        self.assertFalse(filler.exists())
        mixed = generate_assembly_from_ir(mixed_ir, probe_config)
        self.assertTrue(filler.is_file())
        self.assertEqual(len(mixed.after_reopen), 2)
        self.assertEqual(
            mixed.materialization_report.substituted_geometry_ids, (FILLER_GEOMETRY_ID,)
        )
        by_geometry = {
            item.placement.geometry_id: item for item in mixed.after_reopen
        }
        self.assertEqual(by_geometry["large_armor_block"].part_path.name, "large_armor_block.SLDPRT")
        self.assertEqual(
            by_geometry[FILLER_GEOMETRY_ID].part_path.name,
            "se2cad_unknown_filler.SLDPRT",
        )
        self.assertNotEqual(
            by_geometry[FILLER_GEOMETRY_ID].part_path.name,
            by_geometry["large_armor_block"].part_path.name,
        )

        chamfer_part = probe_root / "large_armor_block_chamfer_75mm.SLDPRT"
        if chamfer_part.exists():
            chamfer_part.unlink()
        chamfered = generate_assembly_from_ir(one_ir, probe_config, chamfer_treatment(75))
        self.assertTrue(chamfer_part.is_file())
        self.assertEqual(
            chamfered.materialization_report.untreated.reused, ("large_armor_block",)
        )
        self.assertEqual(chamfered.materialization_report.untreated.generated, ())
        self.assertEqual(
            chamfered.materialization_report.treated.generated, ("large_armor_block",)
        )
        self.assertEqual(
            chamfered.after_reopen[0].part_path.name,
            "large_armor_block_chamfer_75mm.SLDPRT",
        )
        self.assertEqual(hashlib.sha256(base.read_bytes()).hexdigest(), first_hash)
        self.assertFalse((probe_root / "large_armor_block_chamfer.SLDPRT").exists())

        with SolidWorksSession(probe_config) as session:
            end_report = session_environment_report(session)
            end_documents = int(session.app.GetDocumentCount)
        self.assertTrue(start_report["solidworks_revision"])
        self.assertEqual(end_report["started_application"], "False")
        self.assertEqual(end_documents, start_documents)
        self.assertEqual(start_report["solidworks_revision"], end_report["solidworks_revision"])

    def test_sdk_mesh_thrust_minimal_probe_generates_and_reuses(self) -> None:
        from se2cad.catalog import AUTHORIZED_SDK_MESH_GEOMETRY_ID, load_default_catalog
        from se2cad.parser import Direction, parse_blueprint
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.config import SolidWorksBackendConfig
        from se2cad.solidworks.transform_pack import (
            arraydata_axes,
            arraydata_translation_m,
        )
        from se2cad.transform import rotation_from_forward_up

        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-ob-probe" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_Thrust">
              <SubtypeName>LargeBlockSmallHydrogenThrust</SubtypeName>
              <Min x="1" y="0" z="0" />
              <BlockOrientation Forward="Down" Up="Forward" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ob-probe.sbc"
            path.write_text(xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        self.assertEqual(parsed.grid.blocks[1].object_builder_type, "MyObjectBuilder_Thrust")
        result = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.STRICT
        )
        self.assertEqual(result.ir.grid.block_count, 2)
        self.assertEqual(result.filler_count, 0)
        probe_root = Path("generated") / "s2c-11.7.1-min-probe"
        if probe_root.exists():
            for leftover in probe_root.glob("*"):
                leftover.unlink()
        probe_config = SolidWorksBackendConfig(
            generated_root=probe_root.resolve(),
            part_template=self.config.part_template,
            visible=self.config.visible,
            source="s2c-11.7.1-ob-probe",
        )
        assembled = generate_assembly_from_ir(result.ir, probe_config)
        self.assertEqual(assembled.identity, "se2cad-ob-probe")
        self.assertEqual(len(assembled.after_reopen), 2)
        self.assertEqual(
            assembled.materialization_report.untreated.generated,
            ("large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID),
        )
        by_geometry = {
            item.placement.geometry_id: item for item in assembled.after_reopen
        }
        self.assertEqual(
            set(by_geometry),
            {"large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID},
        )
        armor = by_geometry["large_armor_block"]
        thrust = by_geometry[AUTHORIZED_SDK_MESH_GEOMETRY_ID]
        self.assertEqual(armor.placement.part_filename, "large_armor_block.SLDPRT")
        self.assertEqual(
            thrust.placement.part_filename,
            "large_block_small_hydrogen_thrust.SLDPRT",
        )
        self.assertEqual(thrust.placement.subtype_id, "LargeBlockSmallHydrogenThrust")
        self.assertEqual(arraydata_translation_m(thrust.arraydata), (2.5, 0.0, 0.0))
        self.assertEqual(
            arraydata_axes(thrust.arraydata),
            rotation_from_forward_up(Direction.DOWN, Direction.FORWARD).columns,
        )
        reused = generate_assembly_from_ir(result.ir, probe_config)
        self.assertEqual(reused.materialization_report.untreated.generated, ())
        self.assertEqual(
            set(reused.materialization_report.untreated.reused),
            {"large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID},
        )

    def test_spaced_assembly_identity_saves_derived_filename(self) -> None:
        from se2cad.parser import parse_blueprint
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.catalog import load_default_catalog
        from se2cad.solidworks.artifacts import logical_assembly_filename
        from se2cad.solidworks.assemble import generate_assembly_from_ir

        identity = "se2cad name probe"
        xml = f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "name-probe.sbc"
            path.write_text(xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        self.assertEqual(parsed.identity_subtype, identity)
        result = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.STRICT
        )
        self.assertEqual(result.ir.identity_subtype, identity)
        assembled = generate_assembly_from_ir(result.ir, self.config)
        self.assertEqual(assembled.identity, identity)
        self.assertEqual(assembled.path.name, logical_assembly_filename(identity))
        self.assertNotEqual(assembled.path.name, f"{identity}.SLDASM")
        self.assertTrue(assembled.path.is_relative_to(self.config.generated_root))
        self.assertEqual(len(assembled.after_reopen), 1)
        self.assertEqual(
            assembled.after_reopen[0].part_path.name, "large_armor_block.SLDPRT"
        )

    def test_planar_cube_topology_parts_generate_validate_save_and_reopen(self) -> None:
        import shutil

        from se2cad.library import (
            lookup_recipe,
            planar_cube_topology_geometry_ids,
        )
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.config import SolidWorksBackendConfig
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.recipe_plan import plan_from_recipe

        probe_root = self.config.generated_root / "s2c-11.13.1-parts"
        if probe_root.exists():
            shutil.rmtree(probe_root)
        probe_root.mkdir(parents=True)
        probe_config = SolidWorksBackendConfig(
            generated_root=probe_root.resolve(),
            part_template=self.config.part_template,
            visible=self.config.visible,
            source="s2c-11.13.1-parts",
        )
        geometry_ids = planar_cube_topology_geometry_ids()
        with SolidWorksSession(probe_config) as session:
            start_documents = int(session.app.GetDocumentCount)
            report = session_environment_report(session)
            self.assertTrue(report["solidworks_revision"])
        results = generate_canonical_parts(probe_config, geometry_ids=geometry_ids)
        self.assertEqual(len(results), 4)
        for result in results:
            plan = plan_from_recipe(lookup_recipe(result.locator.identity.geometry_id))
            self.assertTrue(result.locator.path.is_file())
            self.assertTrue(result.locator.path.is_relative_to(probe_root.resolve()))
            self.assertEqual(result.after_save.solid_body_count, 1)
            self.assertEqual(result.after_reopen.solid_body_count, 1)
            self.assertEqual(result.after_reopen.sheet_body_count, 0)
            self.assertAlmostEqual(
                result.after_reopen.volume_m3, plan.expected.volume_m3, places=5
            )
        from se2cad.solidworks.materialize import ensure_untreated_canonical_parts

        reuse = ensure_untreated_canonical_parts(probe_config, geometry_ids)
        self.assertEqual(reuse.generated, ())
        self.assertEqual(set(reuse.reused), set(geometry_ids))
        with SolidWorksSession(probe_config) as session:
            self.assertEqual(int(session.app.GetDocumentCount), start_documents)

    def test_planar_cube_topology_targeted_fixture_assembles_and_reuses(self) -> None:
        import shutil
        from collections import Counter

        from se2cad.catalog import load_default_catalog
        from se2cad.ir import component_name_from_block
        from se2cad.parser import Direction, parse_blueprint_xml
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.appearance import color_mask_hsv_to_rgb, rgb_close
        from se2cad.solidworks.config import SolidWorksBackendConfig
        from se2cad.solidworks.transform_pack import (
            arraydata_axes,
            arraydata_translation_m,
        )
        from se2cad.transform import IDENTITY_ROTATION, rotation_from_forward_up

        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-planar-probe" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorSlope2Base</SubtypeName>
              <ColorMaskHSV x="0.0" y="0.0" z="0.0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorSlope2Base</SubtypeName>
              <Min x="1" y="0" z="0" />
              <BlockOrientation Forward="Right" Up="Up" />
              <ColorMaskHSV x="0.2" y="0.0" z="0.0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorSlope2Tip</SubtypeName>
              <Min x="-2" y="0" z="3" />
              <ColorMaskHSV x="0.0" y="0.5" z="0.0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorSlope2Tip</SubtypeName>
              <Min x="-2" y="1" z="3" />
              <BlockOrientation Forward="Down" Up="Forward" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeHalfArmorBlock</SubtypeName>
              <Min x="0" y="-1" z="0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeHeavyHalfArmorBlock</SubtypeName>
              <Min x="0" y="-1" z="1" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        probe_root = self.config.generated_root / "s2c-11.13.1-fixture"
        if probe_root.exists():
            shutil.rmtree(probe_root)
        probe_root.mkdir(parents=True)
        probe_config = SolidWorksBackendConfig(
            generated_root=probe_root.resolve(),
            part_template=self.config.part_template,
            visible=self.config.visible,
            source="s2c-11.13.1-fixture",
        )
        parsed = parse_blueprint_xml(xml, source="planar-probe")
        result = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.STRICT
        )
        self.assertEqual(len(result.ir.grid.blocks), 6)
        self.assertEqual(result.filler_count, 0)
        with SolidWorksSession(probe_config) as session:
            start_documents = int(session.app.GetDocumentCount)
            session_environment_report(session)
        assembled = generate_assembly_from_ir(result.ir, probe_config)
        self.assertEqual(len(assembled.after_reopen), 6)
        self.assertEqual(
            Counter(assembled.materialization_report.untreated.generated),
            Counter(
                {
                    "large_block_armor_slope2_base": 1,
                    "large_block_armor_slope2_tip": 1,
                    "large_half_armor_block": 1,
                    "large_heavy_half_armor_block": 1,
                }
            ),
        )
        names = [component_name_from_block(block) for block in result.ir.grid.blocks]
        self.assertEqual(len(set(names)), 6)
        tip = result.ir.grid.blocks[2]
        self.assertEqual(tip.position_mm.as_tuple(), (-5000, 0, 7500))
        by_min = {item.placement.grid_min: item for item in assembled.after_reopen}
        self.assertEqual(len(by_min), 6)
        reopen_tip = by_min[(-2, 0, 3)]
        self.assertEqual(reopen_tip.placement.geometry_id, "large_block_armor_slope2_tip")
        self.assertEqual(
            arraydata_translation_m(reopen_tip.arraydata),
            (-5.0, 0.0, 7.5),
        )
        self.assertEqual(arraydata_axes(reopen_tip.arraydata), IDENTITY_ROTATION.columns)
        self.assertEqual(IDENTITY_ROTATION.determinant(), 1)
        rotated_base = by_min[(1, 0, 0)]
        expected_right_up = rotation_from_forward_up(Direction.RIGHT, Direction.UP)
        self.assertEqual(expected_right_up.determinant(), 1)
        self.assertEqual(
            arraydata_translation_m(rotated_base.arraydata),
            (2.5, 0.0, 0.0),
        )
        self.assertEqual(arraydata_axes(rotated_base.arraydata), expected_right_up.columns)
        rotated_tip = by_min[(-2, 1, 3)]
        expected_down_forward = rotation_from_forward_up(
            Direction.DOWN, Direction.FORWARD
        )
        self.assertEqual(expected_down_forward.determinant(), 1)
        self.assertEqual(
            arraydata_translation_m(rotated_tip.arraydata),
            (-5.0, 2.5, 7.5),
        )
        self.assertEqual(
            arraydata_axes(rotated_tip.arraydata), expected_down_forward.columns
        )
        self.assertEqual(
            by_min[(0, -1, 0)].placement.geometry_id, "large_half_armor_block"
        )
        self.assertEqual(
            by_min[(0, -1, 1)].placement.geometry_id,
            "large_heavy_half_armor_block",
        )
        for item in assembled.after_reopen:
            self.assertEqual(item.placement.rotation.determinant(), 1)
            self.assertEqual(item.component_name, item.placement.component_name)
            self.assertNotIn("trapezoidal", item.component_name)
            self.assertNotIn("HalfBox", item.component_name)
            self.assertTrue(item.appearance_applied)
        self.assertTrue(
            rgb_close(
                by_min[(1, 0, 0)].appearance_rgb,
                color_mask_hsv_to_rgb(result.ir.grid.blocks[1].color_mask_hsv),
            )
        )
        reused = generate_assembly_from_ir(result.ir, probe_config)
        self.assertEqual(reused.materialization_report.untreated.generated, ())
        self.assertEqual(len(reused.materialization_report.untreated.reused), 4)
        with SolidWorksSession(probe_config) as session:
            self.assertEqual(int(session.app.GetDocumentCount), start_documents)

    def test_definition_parse_cleanup_targeted_fixture_assembles_and_reuses(self) -> None:
        import shutil

        from se2cad.catalog import FILLER_GEOMETRY_ID, load_default_catalog
        from se2cad.ir import component_name_from_block
        from se2cad.library import lookup_record
        from se2cad.library.model import SdkMeshRecipe
        from se2cad.parser import Direction, parse_blueprint_xml
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.preflight import compute_conversion_preflight
        from se2cad.solidworks.appearance import color_mask_hsv_to_rgb, rgb_close
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.com_bind import com_get
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.config import SolidWorksBackendConfig
        from se2cad.solidworks.transform_pack import (
            arraydata_translation_m,
            solidworks_arraydata,
        )
        from se2cad.transform.placement import (
            MILLIMETRES_PER_METRE,
            occupancy_center_mm,
            occupied_max,
        )
        from se2cad.vanilla import (
            VANILLA_RUNTIME_EMPTY_TYPE_INFIX,
            VanillaResolveKind,
            clear_vanilla_runtime_state,
            empty_subtype_placement_key,
            lookup_unique_empty_subtype,
            resolve_vanilla_geometry,
            try_load_game_content_root,
            type_id_from_object_builder,
        )
        from se2cad.vanilla.record import lookup_runtime_placement

        parse_gap = (
            "LadderShaft",
            "LargeBlockConsoleModule",
            "LargeBlockInsetWall",
            "LargeBlockSciFiWall",
        )
        empty_builders = (
            "MyObjectBuilder_GravityGenerator",
            "MyObjectBuilder_OxygenTank",
            "MyObjectBuilder_OxygenGenerator",
        )
        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-defparse-probe" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LadderShaft</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LadderShaft</SubtypeName>
              <Min x="4" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockConsoleModule</SubtypeName>
              <Min x="0" y="4" z="0" />
              <BlockOrientation Forward="Right" Up="Up" />
              <ColorMaskHSV x="0.2" y="0.0" z="0.0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockInsetWall</SubtypeName>
              <Min x="8" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockSciFiWall</SubtypeName>
              <Min x="0" y="0" z="4" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_GravityGenerator">
              <SubtypeName></SubtypeName>
              <Min x="8" y="4" z="0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_OxygenTank">
              <SubtypeName></SubtypeName>
              <Min x="4" y="2" z="8" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_OxygenGenerator">
              <SubtypeName></SubtypeName>
              <Min x="8" y="0" z="8" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        clear_vanilla_runtime_state()
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(xml, source="defparse-probe")
        self.assertEqual(parsed.grid.grid_size.value, "Large")
        self.assertEqual(len(parsed.grid.blocks), 8)
        self.assertEqual(
            [block.subtype_id for block in parsed.grid.blocks],
            [
                "LadderShaft",
                "LadderShaft",
                "LargeBlockConsoleModule",
                "LargeBlockInsetWall",
                "LargeBlockSciFiWall",
                "",
                "",
                "",
            ],
        )
        self.assertEqual(
            [block.object_builder_type for block in parsed.grid.blocks[5:]],
            list(empty_builders),
        )
        for empty_block in parsed.grid.blocks[5:]:
            self.assertEqual(empty_block.subtype_id, "")
            self.assertFalse(empty_block.subtype_id)

        resolved_by_key: dict[str, object] = {}
        for subtype_id in parse_gap:
            result = resolve_vanilla_geometry(subtype_id, catalog)
            self.assertEqual(
                result.kind,
                VanillaResolveKind.RUNTIME_VANILLA,
                msg=f"{subtype_id}: {result.unresolved_reason}",
            )
            assert result.runtime is not None
            self.assertEqual(result.runtime.catalog_entry.subtype_id, subtype_id)
            self.assertNotIn(VANILLA_RUNTIME_EMPTY_TYPE_INFIX, result.runtime.geometry_id)
            resolved_by_key[subtype_id] = result.runtime
        for builder in empty_builders:
            result = resolve_vanilla_geometry(
                "", catalog, object_builder_type=builder
            )
            self.assertEqual(
                result.kind,
                VanillaResolveKind.RUNTIME_VANILLA,
                msg=f"{builder}: {result.unresolved_reason}",
            )
            assert result.runtime is not None
            type_id = type_id_from_object_builder(builder)
            game_root = try_load_game_content_root()
            self.assertIsNotNone(game_root, msg="SE2CAD_GAME_ROOT or local game_root is required")
            hit = lookup_unique_empty_subtype(
                type_id, cube_size="Large", game_root=game_root
            )
            self.assertIsNotNone(hit)
            self.assertEqual(result.runtime.catalog_entry.subtype_id, "")
            self.assertIn(VANILLA_RUNTIME_EMPTY_TYPE_INFIX, result.runtime.geometry_id)
            self.assertNotEqual(result.runtime.geometry_id, type_id)
            self.assertNotEqual(result.runtime.catalog_entry.subtype_id, type_id)
            self.assertIsNotNone(
                lookup_runtime_placement(empty_subtype_placement_key(type_id))
            )
            resolved_by_key[builder] = result.runtime
        self.assertEqual(len(resolved_by_key), 7)

        preflight = compute_conversion_preflight(parsed, catalog)
        self.assertEqual(preflight.block_count, 8)
        self.assertEqual(preflight.supported_count, 8)
        self.assertEqual(preflight.unknown_count, 0)
        self.assertEqual(preflight.unsupported_count, 0)
        self.assertTrue(preflight.all_supported)
        converted = convert_blueprint(
            parsed, catalog, ConversionPolicy.STRICT
        )
        self.assertEqual(len(converted.ir.grid.blocks), 8)
        self.assertEqual(converted.filler_count, 0)
        self.assertNotIn(
            FILLER_GEOMETRY_ID,
            [block.geometry_id for block in converted.ir.grid.blocks],
        )
        expected_geometry_ids = {
            runtime.geometry_id for runtime in resolved_by_key.values()
        }
        self.assertEqual(len(expected_geometry_ids), 7)
        actual_geometry_ids = {block.geometry_id for block in converted.ir.grid.blocks}
        self.assertEqual(actual_geometry_ids, expected_geometry_ids)
        for block in converted.ir.grid.blocks[5:]:
            self.assertEqual(block.subtype_id, "")
            self.assertIn(VANILLA_RUNTIME_EMPTY_TYPE_INFIX, block.geometry_id)
            self.assertNotIn(block.geometry_id, parse_gap)

        probe_root = self.config.generated_root / "s2c-11.15.1-live"
        probe_config = SolidWorksBackendConfig(
            generated_root=probe_root.resolve(),
            part_template=self.config.part_template,
            visible=self.config.visible,
            source="s2c-11.15.1-live",
        )

        def _stl_prefs(session: object) -> tuple[int, int, bool]:
            constants = session.constants
            return (
                int(
                    session.app.GetUserPreferenceIntegerValue(
                        int(constants.swImportStlVrmlModelType)
                    )
                ),
                int(
                    session.app.GetUserPreferenceIntegerValue(
                        int(constants.swImportStlVrmlUnits)
                    )
                ),
                bool(
                    session.app.GetUserPreferenceToggle(
                        int(constants.swImportAutoRunImportDiagnostics)
                    )
                ),
            )

        try:
            with SolidWorksSession(probe_config) as session:
                start_report = session_environment_report(session)
                docs = com_get(session.app, "GetDocuments") or ()
                for doc in docs:
                    path = str(com_get(doc, "GetPathName") or "")
                    if "s2c-11.15.1-live" in path.replace("\\", "/"):
                        session.close_doc(doc)
                start_documents = int(session.app.GetDocumentCount)
                start_prefs = _stl_prefs(session)
        except Exception as exc:
            self.fail(
                "SolidWorks session is unusable before the targeted "
                f"S2C-11.15.1 probe: {exc}"
            )
        self.assertTrue(
            start_report["solidworks_revision"],
            msg=f"empty RevisionNumber; host is unusable: {start_report}",
        )
        if probe_root.exists():
            shutil.rmtree(probe_root)
        probe_root.mkdir(parents=True)
        for geometry_id in expected_geometry_ids:
            leftover = probe_root / f"{geometry_id}.SLDPRT"
            self.assertFalse(leftover.exists(), msg=leftover)

        first = generate_assembly_from_ir(converted.ir, probe_config)
        self.assertEqual(first.identity, "se2cad-defparse-probe")
        self.assertTrue(first.path.is_file())
        self.assertTrue(first.path.is_relative_to(probe_root.resolve()))
        self.assertEqual(len(first.placements), 8)
        self.assertEqual(len(first.after_save), 8)
        self.assertEqual(len(first.after_reopen), 8)
        self.assertEqual(first.materialization_report.substituted_geometry_ids, ())
        self.assertEqual(converted.filler_count, 0)
        generated = first.materialization_report.untreated.generated
        reused = first.materialization_report.untreated.reused
        self.assertEqual(set(generated), expected_geometry_ids)
        self.assertEqual(reused, ())
        self.assertEqual(len(generated), 7)
        self.assertEqual(len(set(generated)), 7)

        ladder_id = resolved_by_key["LadderShaft"].geometry_id
        ladder_items = [
            item
            for item in first.after_reopen
            if item.placement.geometry_id == ladder_id
        ]
        self.assertEqual(len(ladder_items), 2)
        self.assertEqual(
            ladder_items[0].placement.part_filename,
            ladder_items[1].placement.part_filename,
        )
        self.assertEqual(ladder_items[0].part_path, ladder_items[1].part_path)
        self.assertTrue(ladder_items[0].part_path.is_file())

        # Production generate already imported each STL, read the
        # graphics-body envelope, and reopened the SLDPRT. A second
        # stacked OpenDoc sweep after that long batch disconnected COM
        # (RPC_E_DISCONNECTED) on this host; do not repeat it.
        for geometry_id in generated:
            part_path = probe_root / f"{geometry_id}.SLDPRT"
            self.assertTrue(part_path.is_file(), msg=geometry_id)
            self.assertGreater(part_path.stat().st_size, 10_000, msg=geometry_id)
            recipe = lookup_record(geometry_id).recipe
            self.assertIsInstance(recipe, SdkMeshRecipe)
            occupancy = recipe.occupancy_size
            self.assertGreaterEqual(min(occupancy.x, occupancy.y, occupancy.z), 1)

        reopen_by_index = {
            item.placement.source_index: item for item in first.after_reopen
        }
        save_by_index = {
            item.placement.source_index: item for item in first.after_save
        }
        self.assertEqual(len(reopen_by_index), 8)
        for block in converted.ir.grid.blocks:
            saved = save_by_index[block.source_index]
            reopened = reopen_by_index[block.source_index]
            expected = solidworks_arraydata(
                block.rotation, block.position_mm.as_tuple()
            )
            self.assertEqual(reopened.placement.geometry_id, block.geometry_id)
            self.assertEqual(
                reopened.placement.part_filename, f"{block.geometry_id}.SLDPRT"
            )
            self.assertEqual(reopened.part_path.name, reopened.placement.part_filename)
            self.assertTrue(reopened.part_path.is_relative_to(probe_root.resolve()))
            self.assertEqual(reopened.component_name, component_name_from_block(block))
            self.assertEqual(saved.component_name, reopened.component_name)
            self.assertEqual(reopened.arraydata, expected)
            self.assertEqual(saved.arraydata, expected)
            self.assertEqual(reopened.placement.rotation.determinant(), 1)
            self.assertTrue(reopened.geometry_applied)
            self.assertTrue(reopened.appearance_applied)
            self.assertTrue(
                rgb_close(
                    reopened.appearance_rgb,
                    color_mask_hsv_to_rgb(block.color_mask_hsv),
                )
            )
            self.assertNotEqual(reopened.placement.geometry_id, FILLER_GEOMETRY_ID)

        tank = converted.ir.grid.blocks[6]
        generator = converted.ir.grid.blocks[7]
        for block, label in ((tank, "OxygenTank"), (generator, "OxygenGenerator")):
            recipe = lookup_record(block.geometry_id).recipe
            self.assertIsInstance(recipe, SdkMeshRecipe)
            max_cell = occupied_max(block.grid_min, recipe.occupancy_size, block.rotation)
            center = occupancy_center_mm(block.grid_min, max_cell)
            min_only = occupancy_center_mm(block.grid_min, block.grid_min)
            self.assertNotEqual(
                center.as_tuple(),
                min_only.as_tuple(),
                msg=f"{label} occupancy equals Min-cell center",
            )
            self.assertEqual(block.position_mm.as_tuple(), center.as_tuple())
            expected_m = tuple(
                value / MILLIMETRES_PER_METRE for value in center.as_tuple()
            )
            self.assertEqual(
                arraydata_translation_m(reopen_by_index[block.source_index].arraydata),
                expected_m,
            )

        self.assertEqual(
            converted.ir.grid.blocks[2].forward, Direction.RIGHT
        )
        self.assertEqual(first.path.suffix.lower(), ".sldasm")

        warm = generate_assembly_from_ir(converted.ir, probe_config)
        self.assertEqual(warm.materialization_report.untreated.generated, ())
        self.assertEqual(
            set(warm.materialization_report.untreated.reused),
            expected_geometry_ids,
        )
        self.assertEqual(len(warm.after_reopen), 8)
        self.assertEqual(warm.materialization_report.substituted_geometry_ids, ())
        warm_by_index = {
            item.placement.source_index: item for item in warm.after_reopen
        }
        for block in converted.ir.grid.blocks:
            first_item = reopen_by_index[block.source_index]
            warm_item = warm_by_index[block.source_index]
            self.assertEqual(warm_item.arraydata, first_item.arraydata)
            self.assertEqual(warm_item.component_name, first_item.component_name)
            self.assertEqual(warm_item.appearance_rgb, first_item.appearance_rgb)
            self.assertEqual(
                warm_item.placement.geometry_id, first_item.placement.geometry_id
            )
            self.assertEqual(warm_item.part_path, first_item.part_path)

        try:
            with SolidWorksSession(probe_config) as session:
                end_report = session_environment_report(session)
                end_documents = int(session.app.GetDocumentCount)
                end_prefs = _stl_prefs(session)
        except Exception as exc:
            self.fail(
                "SolidWorks session is unusable after the targeted "
                f"S2C-11.15.1 probe: {exc}"
            )
        self.assertEqual(end_documents, start_documents)
        self.assertEqual(
            end_report["solidworks_revision"], start_report["solidworks_revision"]
        )
        self.assertEqual(end_prefs, start_prefs)

    def test_sdk_fbx_frame_remote_control_and_battery_generate_and_reopen(self) -> None:
        import shutil

        from se2cad.catalog import load_default_catalog
        from se2cad.library.model import SdkMeshRecipe
        from se2cad.parser import parse_blueprint_xml
        from se2cad.policy import ConversionPolicy, convert_blueprint
        from se2cad.preflight import compute_conversion_preflight
        from se2cad.solidworks.assemble import generate_assembly_from_ir
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.config import SolidWorksBackendConfig
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.transform_pack import solidworks_arraydata
        from se2cad.vanilla import (
            VanillaResolveKind,
            clear_vanilla_runtime_state,
            resolve_vanilla_geometry,
        )

        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-fbx-frame-probe" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockRemoteControl</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockBatteryBlock</SubtypeName>
              <Min x="2" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeSymbolB</SubtypeName>
              <Min x="4" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockFrontLight</SubtypeName>
              <Min x="0" y="2" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        clear_vanilla_runtime_state()
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(xml, source="fbx-frame-probe")
        expected = {
            "LargeBlockRemoteControl": "vanilla_lg_1x1x1_large_block_remote_control",
            "LargeBlockBatteryBlock": "vanilla_lg_1x1x1_large_block_battery_block",
            "LargeSymbolB": "vanilla_lg_1x1x1_large_symbol_b",
            "LargeBlockFrontLight": "vanilla_lg_1x1x1_large_block_front_light",
        }
        for subtype_id, geometry_id in expected.items():
            result = resolve_vanilla_geometry(subtype_id, catalog)
            self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA, msg=subtype_id)
            assert result.runtime is not None
            self.assertEqual(result.runtime.geometry_id, geometry_id)
            self.assertIsInstance(result.runtime.library_record.recipe, SdkMeshRecipe)
        preflight = compute_conversion_preflight(parsed, catalog)
        self.assertEqual(preflight.supported_count, 4)
        self.assertEqual(preflight.unknown_count, 0)
        converted = convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)
        self.assertEqual(converted.filler_count, 0)
        probe_root = self.config.generated_root / "s2c-11.16.1-live"
        if probe_root.exists():
            shutil.rmtree(probe_root)
        probe_config = SolidWorksBackendConfig(
            generated_root=probe_root.resolve(),
            part_template=self.config.part_template,
            visible=self.config.visible,
            source="s2c-11.16.1-live",
        )
        with SolidWorksSession(probe_config) as session:
            start_report = session_environment_report(session)
            start_documents = int(session.app.GetDocumentCount)
            self.assertTrue(str(start_report["solidworks_revision"]).startswith("34"))
        generated_parts = generate_canonical_parts(
            probe_config, geometry_ids=tuple(expected.values())
        )
        self.assertEqual(len(generated_parts), 4)
        bounds = {}
        for part in generated_parts:
            self.assertTrue(part.locator.generated)
            bounds[part.locator.identity.geometry_id] = (
                part.after_reopen.bounding_box_min_m,
                part.after_reopen.bounding_box_max_m,
            )
        first = generate_assembly_from_ir(converted.ir, probe_config)
        self.assertEqual(len(first.after_reopen), 4)
        self.assertEqual(first.materialization_report.untreated.generated, ())
        self.assertEqual(
            set(first.materialization_report.untreated.reused),
            set(expected.values()),
        )
        remote_min, remote_max = bounds[expected["LargeBlockRemoteControl"]]
        remote_size = tuple(remote_max[i] - remote_min[i] for i in range(3))
        self.assertLess(remote_max[0], 1.60)
        self.assertGreater(remote_min[0], -1.60)
        self.assertLess(remote_size[0], 3.00)
        battery_min, battery_max = bounds[expected["LargeBlockBatteryBlock"]]
        self.assertLess(abs((battery_min[0] + battery_max[0]) / 2.0), 0.15)
        self.assertLess(abs((battery_min[1] + battery_max[1]) / 2.0), 0.15)
        self.assertLess(abs((battery_min[2] + battery_max[2]) / 2.0), 0.15)
        reopen_by_index = {
            item.placement.source_index: item for item in first.after_reopen
        }
        for block in converted.ir.grid.blocks:
            item = reopen_by_index[block.source_index]
            self.assertEqual(
                item.arraydata,
                solidworks_arraydata(block.rotation, block.position_mm.as_tuple()),
            )
            self.assertEqual(item.placement.geometry_id, block.geometry_id)
        warm = generate_assembly_from_ir(converted.ir, probe_config)
        self.assertEqual(warm.materialization_report.untreated.generated, ())
        self.assertEqual(set(warm.materialization_report.untreated.reused), set(expected.values()))
        self.assertEqual(len(warm.after_reopen), 4)
        warm_by_index = {
            item.placement.source_index: item for item in warm.after_reopen
        }
        for source_index, first_item in reopen_by_index.items():
            warm_item = warm_by_index[source_index]
            self.assertEqual(warm_item.arraydata, first_item.arraydata)
            self.assertEqual(warm_item.part_path, first_item.part_path)
        with SolidWorksSession(probe_config) as session:
            end_documents = int(session.app.GetDocumentCount)
            end_report = session_environment_report(session)
        self.assertEqual(end_documents, start_documents)
        self.assertEqual(
            end_report["solidworks_revision"], start_report["solidworks_revision"]
        )


if __name__ == "__main__":
    unittest.main()

