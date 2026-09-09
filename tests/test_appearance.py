"""CAD-neutral ColorMaskHSV appearance on parser and IR (S2C-9.1.1)."""

from __future__ import annotations

import unittest
from pathlib import Path

from se2cad.catalog import SupportStatus, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    ColorMaskHSV,
    InvalidFieldError,
    MissingRequiredFieldError,
    parse_blueprint,
    parse_blueprint_xml,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"


def _one_block_xml(
    subtype: str = "LargeBlockArmorBlock",
    min_xml: str = "",
    orientation_xml: str = "",
    color_xml: str = "",
    extra_block: str = "",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="color-test" />
      <DisplayName>color-test</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <DisplayName>color-grid</DisplayName>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
              {min_xml}
              {orientation_xml}
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


class OmittedColorTests(unittest.TestCase):
    def test_omitted_colormaskhsv_is_evidenced_default(self) -> None:
        parsed = parse_blueprint_xml(_one_block_xml(), source="omitted-color")
        block = parsed.grid.blocks[0]
        self.assertFalse(block.color_serialized)
        self.assertEqual(block.appearance_support, AppearanceSupport.DEFAULT)
        self.assertEqual(block.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)
        self.assertEqual(block.color_mask_hsv.as_tuple(), (0.0, -1.0, 0.0))
        self.assertFalse(block.min_serialized)
        self.assertFalse(block.orientation_serialized)
        self.assertEqual((block.min.x, block.min.y, block.min.z), (0, 0, 0))
        self.assertEqual(block.forward.value, "Forward")
        self.assertEqual(block.up.value, "Up")

    def test_fixture_omits_color_and_keeps_identities(self) -> None:
        parsed = parse_blueprint(FIXTURE_PATH)
        self.assertEqual(len(parsed.grid.blocks), 24)
        for block in parsed.grid.blocks:
            self.assertFalse(block.color_serialized)
            self.assertEqual(block.appearance_support, AppearanceSupport.DEFAULT)
            self.assertEqual(block.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)


class ExplicitColorTests(unittest.TestCase):
    def test_explicit_colormaskhsv_is_carried(self) -> None:
        parsed = parse_blueprint_xml(
            _one_block_xml(color_xml='<ColorMaskHSV x="0.25" y="0.15" z="-0.2" />'),
            source="explicit-color",
        )
        block = parsed.grid.blocks[0]
        self.assertTrue(block.color_serialized)
        self.assertEqual(block.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(block.color_mask_hsv, ColorMaskHSV(0.25, 0.15, -0.2))

    def test_explicit_default_vector_is_serialized_not_omitted(self) -> None:
        parsed = parse_blueprint_xml(
            _one_block_xml(color_xml='<ColorMaskHSV x="0" y="-1" z="0" />'),
            source="explicit-default-color",
        )
        block = parsed.grid.blocks[0]
        self.assertTrue(block.color_serialized)
        self.assertEqual(block.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(block.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)

    def test_integer_tokens_are_accepted_as_floats(self) -> None:
        parsed = parse_blueprint_xml(
            _one_block_xml(color_xml='<ColorMaskHSV x="1" y="0" z="-1" />'),
            source="int-color",
        )
        self.assertEqual(
            parsed.grid.blocks[0].color_mask_hsv, ColorMaskHSV(1.0, 0.0, -1.0)
        )

    def test_explicit_color_does_not_change_omitted_min_or_orientation(self) -> None:
        parsed = parse_blueprint_xml(
            _one_block_xml(color_xml='<ColorMaskHSV x="0.2" y="0.1" z="0" />'),
            source="color-keeps-defaults",
        )
        block = parsed.grid.blocks[0]
        self.assertTrue(block.color_serialized)
        self.assertFalse(block.min_serialized)
        self.assertFalse(block.orientation_serialized)
        self.assertEqual((block.min.x, block.min.y, block.min.z), (0, 0, 0))
        self.assertEqual(block.forward.value, "Forward")
        self.assertEqual(block.up.value, "Up")


class MalformedColorTests(unittest.TestCase):
    def test_multiple_colormaskhsv_fail_closed(self) -> None:
        xml = _one_block_xml(
            color_xml=(
                '<ColorMaskHSV x="0" y="0" z="0" />'
                '<ColorMaskHSV x="1" y="0" z="0" />'
            )
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="multi-color")

    def test_nil_colormaskhsv_fails_closed(self) -> None:
        xml = _one_block_xml(
            color_xml='<ColorMaskHSV xsi:nil="true" x="0" y="-1" z="0" />'
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="nil-color")

    def test_child_elements_fail_closed(self) -> None:
        xml = _one_block_xml(
            color_xml="<ColorMaskHSV><x>0</x><y>-1</y><z>0</z></ColorMaskHSV>"
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="child-color")

    def test_missing_axis_fails_closed(self) -> None:
        xml = _one_block_xml(color_xml='<ColorMaskHSV x="0" y="-1" />')
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(xml, source="missing-axis")

    def test_extra_attribute_fails_closed(self) -> None:
        xml = _one_block_xml(
            color_xml='<ColorMaskHSV x="0" y="-1" z="0" w="1" />'
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="extra-attr")

    def test_non_numeric_fails_closed(self) -> None:
        xml = _one_block_xml(color_xml='<ColorMaskHSV x="red" y="-1" z="0" />')
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="non-numeric")

    def test_nan_and_infinity_fail_closed(self) -> None:
        for raw in ("nan", "NaN", "inf", "Infinity", "-inf"):
            xml = _one_block_xml(
                color_xml=f'<ColorMaskHSV x="{raw}" y="-1" z="0" />'
            )
            with self.assertRaises(InvalidFieldError, msg=raw):
                parse_blueprint_xml(xml, source=f"bad-float-{raw}")

    def test_whitespace_and_plus_fail_closed(self) -> None:
        for raw in (" 0", "0 ", "+0", "1_0"):
            xml = _one_block_xml(
                color_xml=f'<ColorMaskHSV x="{raw}" y="-1" z="0" />'
            )
            with self.assertRaises(InvalidFieldError, msg=repr(raw)):
                parse_blueprint_xml(xml, source=f"bad-token-{raw}")

    def test_malformed_color_does_not_invent_default(self) -> None:
        xml = _one_block_xml(color_xml='<ColorMaskHSV x="0" y="-1" z="oops" />')
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="invent-default")

    def test_overlong_and_overflow_tokens_fail_closed(self) -> None:
        overlong = "0." + ("1" * 32)
        xml = _one_block_xml(
            color_xml=f'<ColorMaskHSV x="{overlong}" y="-1" z="0" />'
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="overlong-color")
        xml = _one_block_xml(color_xml='<ColorMaskHSV x="1e999" y="-1" z="0" />')
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="overflow-color")


class AppearanceIndependenceTests(unittest.TestCase):
    def test_same_subtype_different_colors_share_geometry_id(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(
            _one_block_xml(
                color_xml='<ColorMaskHSV x="0.1" y="0.2" z="0.3" />',
                extra_block=_extra_block(
                    "LargeBlockArmorBlock",
                    min_xml='<Min x="1" y="0" z="0" />',
                    color_xml='<ColorMaskHSV x="0.9" y="-0.5" z="0.1" />',
                ),
            ),
            source="same-subtype-colors",
        )
        ir = build_canonical_blueprint(parsed, catalog)
        first, second = ir.grid.blocks
        self.assertEqual(first.subtype_id, second.subtype_id)
        self.assertEqual(first.geometry_id, second.geometry_id)
        self.assertEqual(first.geometry_id, "large_armor_block")
        self.assertEqual(first.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(second.support_status, SupportStatus.SUPPORTED)
        self.assertNotEqual(first.color_mask_hsv, second.color_mask_hsv)
        self.assertEqual(first.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(second.appearance_support, AppearanceSupport.EXPLICIT)

    def test_different_subtypes_same_color_keep_distinct_geometry(self) -> None:
        catalog = load_default_catalog()
        color = '<ColorMaskHSV x="0.4" y="0.1" z="-0.25" />'
        parsed = parse_blueprint_xml(
            _one_block_xml(
                subtype="LargeBlockArmorBlock",
                color_xml=color,
                extra_block=_extra_block(
                    "LargeBlockArmorSlope",
                    min_xml='<Min x="1" y="0" z="0" />',
                    color_xml=color,
                ),
            ),
            source="same-color-subtypes",
        )
        ir = build_canonical_blueprint(parsed, catalog)
        first, second = ir.grid.blocks
        self.assertEqual(first.color_mask_hsv, second.color_mask_hsv)
        self.assertNotEqual(first.geometry_id, second.geometry_id)
        self.assertEqual(first.geometry_id, "large_armor_block")
        self.assertEqual(second.geometry_id, "large_armor_slope")

    def test_appearance_support_is_independent_of_geometry_support(self) -> None:
        catalog = load_default_catalog()
        omitted = build_canonical_blueprint(
            parse_blueprint_xml(_one_block_xml()), catalog
        ).grid.blocks[0]
        explicit = build_canonical_blueprint(
            parse_blueprint_xml(
                _one_block_xml(color_xml='<ColorMaskHSV x="0.5" y="0" z="0" />')
            ),
            catalog,
        ).grid.blocks[0]
        self.assertEqual(omitted.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(explicit.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(omitted.appearance_support, AppearanceSupport.DEFAULT)
        self.assertEqual(explicit.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(omitted.geometry_id, explicit.geometry_id)

    def test_ir_copies_parser_appearance_without_reinterpretation(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(
            _one_block_xml(
                min_xml='<Min x="2" y="1" z="-2" />',
                orientation_xml='<BlockOrientation Forward="Down" Up="Forward" />',
                color_xml='<ColorMaskHSV x="0.75" y="-0.25" z="0.5" />',
            )
        )
        ir = build_canonical_blueprint(parsed, catalog)
        parsed_block = parsed.grid.blocks[0]
        canonical = ir.grid.blocks[0]
        self.assertEqual(canonical.color_mask_hsv, parsed_block.color_mask_hsv)
        self.assertEqual(canonical.color_serialized, parsed_block.color_serialized)
        self.assertEqual(
            canonical.appearance_support, parsed_block.appearance_support
        )
        self.assertEqual(canonical.grid_min, parsed_block.min)
        self.assertEqual(canonical.forward, parsed_block.forward)
        self.assertEqual(canonical.up, parsed_block.up)
        self.assertEqual(canonical.geometry_id, "large_armor_block")


if __name__ == "__main__":
    unittest.main()
