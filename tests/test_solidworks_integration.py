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
                f"{geometry_id}_chamfer.SLDPRT",
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
                f"{block.geometry_id}_chamfer.SLDPRT",
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


if __name__ == "__main__":
    unittest.main()

