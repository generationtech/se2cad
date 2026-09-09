"""SolidWorks-package ColorMaskHSV conversion and color-free part plans (S2C-9.2.1)."""

from __future__ import annotations

import ast
import unittest
from dataclasses import fields
from pathlib import Path

from se2cad.catalog import SupportStatus, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    ColorMaskHSV,
    parse_blueprint,
    parse_blueprint_xml,
)
from se2cad.solidworks import (
    SATURATION_DELTA,
    VALUE_DELTA,
    color_mask_hsv_to_rgb,
    hsv_offset_to_hsv,
    hsv_to_rgb,
    material_property_values,
    placements_from_ir,
    plan_from_recipe,
)
from se2cad.solidworks.artifacts import canonical_geometry_ids
from se2cad.solidworks.recipe_plan import ConstructionPlan, all_canonical_plans
from se2cad.library import lookup_recipe

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src" / "se2cad"
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"

# Omitted (0, -1, 0) + (0, 0.8, 0.45) clamped → HSV(0, 0, 0.45) → gray.
DEFAULT_RGB = (0.45, 0.45, 0.45)


def _one_block_xml(
    subtype: str = "LargeBlockArmorBlock",
    min_xml: str = "",
    color_xml: str = "",
    extra_block: str = "",
    identity: str = "color-test",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <DisplayName>{identity}</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <DisplayName>color-grid</DisplayName>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
              {min_xml}
              {color_xml}
            </MyObjectBuilder_CubeBlock>
            {extra_block}
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _extra_block(
    subtype: str,
    min_xml: str,
    color_xml: str = "",
) -> str:
    return f"""            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
              {min_xml}
              {color_xml}
            </MyObjectBuilder_CubeBlock>"""


class ConversionMathTests(unittest.TestCase):
    def test_published_deltas_match_wiki_hsvoffsettohv(self) -> None:
        self.assertEqual(SATURATION_DELTA, 0.8)
        self.assertEqual(VALUE_DELTA, 0.45)

    def test_omitted_default_is_medium_gray(self) -> None:
        self.assertEqual(hsv_offset_to_hsv(DEFAULT_COLOR_MASK_HSV), (0.0, 0.0, 0.45))
        self.assertEqual(color_mask_hsv_to_rgb(DEFAULT_COLOR_MASK_HSV), DEFAULT_RGB)

    def test_explicit_default_vector_converts_identically(self) -> None:
        explicit = ColorMaskHSV(0.0, -1.0, 0.0)
        self.assertEqual(
            color_mask_hsv_to_rgb(explicit),
            color_mask_hsv_to_rgb(DEFAULT_COLOR_MASK_HSV),
        )

    def test_primary_hues_at_full_chroma(self) -> None:
        # S = 0.2 + 0.8 = 1.0; V = 0.55 + 0.45 = 1.0
        self.assertEqual(color_mask_hsv_to_rgb(ColorMaskHSV(0.0, 0.2, 0.55)), (1.0, 0.0, 0.0))
        self.assertEqual(
            color_mask_hsv_to_rgb(ColorMaskHSV(1.0 / 3.0, 0.2, 0.55)),
            (0.0, 1.0, 0.0),
        )
        self.assertEqual(
            color_mask_hsv_to_rgb(ColorMaskHSV(2.0 / 3.0, 0.2, 0.55)),
            (0.0, 0.0, 1.0),
        )

    def test_zero_saturation_ignores_hue(self) -> None:
        self.assertEqual(hsv_to_rgb(0.3, 0.0, 0.7), (0.7, 0.7, 0.7))

    def test_out_of_range_saturation_and_value_are_clamped(self) -> None:
        self.assertEqual(hsv_offset_to_hsv(ColorMaskHSV(0.0, -2.0, 2.0)), (0.0, 0.0, 1.0))
        self.assertEqual(color_mask_hsv_to_rgb(ColorMaskHSV(0.0, -2.0, 2.0)), (1.0, 1.0, 1.0))

    def test_hue_wraps_into_unit_interval(self) -> None:
        self.assertEqual(hsv_offset_to_hsv(ColorMaskHSV(1.0, -1.0, 0.0))[0], 0.0)
        self.assertEqual(hsv_offset_to_hsv(ColorMaskHSV(-0.25, -1.0, 0.0))[0], 0.75)

    def test_material_property_values_are_nine_doubles_with_rgb_prefix(self) -> None:
        values = material_property_values((0.2, 0.4, 0.6))
        self.assertEqual(len(values), 9)
        self.assertEqual(values[:3], (0.2, 0.4, 0.6))
        self.assertEqual(values[7], 0.0)
        self.assertEqual(values[8], 0.0)

    def test_eight_bit_quantization_matches_live_solidworks_truncation(self) -> None:
        from se2cad.solidworks.appearance import quantize_rgb_8bit, rgb_close

        quantized = quantize_rgb_8bit(DEFAULT_RGB)
        self.assertEqual(quantized, (114 / 255.0, 114 / 255.0, 114 / 255.0))
        self.assertTrue(rgb_close(quantized, DEFAULT_RGB))
        self.assertEqual(material_property_values(DEFAULT_RGB)[:3], quantized)


class PlacementAppearanceTests(unittest.TestCase):
    def test_fixture_default_appearance_does_not_change_parts(self) -> None:
        ir = build_canonical_blueprint(parse_blueprint(FIXTURE_PATH), load_default_catalog())
        placements = placements_from_ir(ir)
        self.assertEqual(len(placements), 24)
        for item in placements:
            self.assertEqual(item.appearance_support, AppearanceSupport.DEFAULT)
            self.assertEqual(item.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)
            self.assertEqual(item.appearance_rgb, DEFAULT_RGB)
            self.assertEqual(item.part_filename, f"{item.geometry_id}.SLDPRT")

    def test_same_geometry_different_colors_share_part_file(self) -> None:
        xml = _one_block_xml(
            color_xml='<ColorMaskHSV x="0" y="0.2" z="0.55" />',
            extra_block=_extra_block(
                "LargeBlockArmorBlock",
                min_xml='<Min x="1" y="0" z="0" />',
                color_xml='<ColorMaskHSV x="0.33333334" y="0.2" z="0.55" />',
            ),
        )
        ir = build_canonical_blueprint(
            parse_blueprint_xml(xml, source="two-colors"),
            load_default_catalog(),
        )
        placements = placements_from_ir(ir)
        self.assertEqual(len(placements), 2)
        self.assertEqual(placements[0].geometry_id, placements[1].geometry_id)
        self.assertEqual(placements[0].part_filename, placements[1].part_filename)
        self.assertEqual(placements[0].part_filename, "large_armor_block.SLDPRT")
        self.assertEqual(placements[0].appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(placements[1].appearance_support, AppearanceSupport.EXPLICIT)
        self.assertNotEqual(placements[0].appearance_rgb, placements[1].appearance_rgb)
        self.assertEqual(placements[0].appearance_rgb, (1.0, 0.0, 0.0))
        self.assertTrue(
            abs(placements[1].appearance_rgb[1] - 1.0) < 1e-6
            and abs(placements[1].appearance_rgb[0]) < 1e-5
        )

    def test_geometry_support_stays_independent_of_converted_appearance(self) -> None:
        omitted = build_canonical_blueprint(
            parse_blueprint_xml(_one_block_xml(), source="omitted"),
            load_default_catalog(),
        )
        explicit = build_canonical_blueprint(
            parse_blueprint_xml(
                _one_block_xml(color_xml='<ColorMaskHSV x="0.5" y="0" z="0" />'),
                source="explicit",
            ),
            load_default_catalog(),
        )
        omitted_p = placements_from_ir(omitted)[0]
        explicit_p = placements_from_ir(explicit)[0]
        self.assertEqual(omitted.grid.blocks[0].support_status, SupportStatus.SUPPORTED)
        self.assertEqual(explicit.grid.blocks[0].support_status, SupportStatus.SUPPORTED)
        self.assertEqual(omitted_p.appearance_support, AppearanceSupport.DEFAULT)
        self.assertEqual(explicit_p.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(omitted_p.geometry_id, explicit_p.geometry_id)


class ColorFreePartPlanTests(unittest.TestCase):
    def test_construction_plans_have_no_appearance_fields(self) -> None:
        names = {item.name for item in fields(ConstructionPlan)}
        for forbidden in (
            "color",
            "appearance",
            "rgb",
            "color_mask_hsv",
            "appearance_rgb",
        ):
            self.assertNotIn(forbidden, names)
        for plan in all_canonical_plans():
            self.assertEqual(plan.geometry_id, lookup_recipe(plan.geometry_id).geometry_id)
            plan_from_recipe(lookup_recipe(plan.geometry_id))

    def test_part_generation_modules_do_not_mention_color(self) -> None:
        for relative in (
            "solidworks/recipe_plan.py",
            "solidworks/generate.py",
            "solidworks/com_construct.py",
        ):
            source = (SRC / relative).read_text(encoding="utf-8")
            for token in ("ColorMask", "appearance_rgb", "MaterialPropertyValues"):
                self.assertNotIn(token, source, msg=relative)

    def test_parser_and_ir_do_not_convert_to_rgb(self) -> None:
        for relative in ("parser/blueprint.py", "parser/model.py", "ir/convert.py", "ir/model.py"):
            tree = ast.parse(
                (SRC / relative).read_text(encoding="utf-8"),
                filename=str(SRC / relative),
            )
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            self.assertNotIn("se2cad.solidworks.appearance", imported)


class CanonicalGeometryStillFourTests(unittest.TestCase):
    def test_canonical_ids_unchanged(self) -> None:
        self.assertEqual(
            canonical_geometry_ids(),
            (
                "large_armor_block",
                "large_armor_slope",
                "large_armor_corner",
                "large_armor_corner_inv",
            ),
        )


if __name__ == "__main__":
    unittest.main()
