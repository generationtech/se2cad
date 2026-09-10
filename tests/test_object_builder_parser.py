"""S2C-12.3.1 vanilla object-builder parser compatibility."""

from __future__ import annotations

import unittest
from pathlib import Path

from se2cad.catalog import FILLER_GEOMETRY_ID, SupportStatus, load_default_catalog
from se2cad.ir import build_canonical_blueprint
from se2cad.library import UnknownGeometryError, all_library_records, lookup_recipe
from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    Direction,
    InvalidFieldError,
    MissingRequiredFieldError,
    UnsupportedBlueprintError,
    parse_blueprint_xml,
)
from se2cad.policy import (
    ConversionPolicy,
    ConversionRefusedError,
    convert_blueprint,
    convert_blueprint_from_xml,
)
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight_from_xml

PARSER_SOURCE = (
    Path(__file__).resolve().parents[1] / "src" / "se2cad" / "parser" / "blueprint.py"
)

FUNCTIONAL_BUILDERS = (
    "MyObjectBuilder_Thrust",
    "MyObjectBuilder_Reactor",
    "MyObjectBuilder_Cockpit",
    "MyObjectBuilder_BatteryBlock",
    "MyObjectBuilder_Conveyor",
    "MyObjectBuilder_Gyro",
)


def _document(blocks: str, *, identity: str = "object-builder-test") -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <DisplayName>{identity}</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <DisplayName>{identity}-grid</DisplayName>
          <CubeBlocks>
{blocks}
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _block(
    subtype: str = "LargeBlockArmorBlock",
    *,
    xsi_type: str | None = "MyObjectBuilder_CubeBlock",
    min_xml: str | None = '<Min x="1" y="2" z="-3" />',
    orientation_xml: str | None = '<BlockOrientation Forward="Down" Up="Forward" />',
    color_xml: str | None = '<ColorMaskHSV x="0" y="0.15" z="0.25" />',
    extra: str = "",
    element: str = "MyObjectBuilder_CubeBlock",
) -> str:
    type_attr = f' xsi:type="{xsi_type}"' if xsi_type is not None else ""
    parts = [f"            <{element}{type_attr}>"]
    if subtype is not None:
        parts.append(f"              <SubtypeName>{subtype}</SubtypeName>")
    if min_xml:
        parts.append(f"              {min_xml}")
    if orientation_xml:
        parts.append(f"              {orientation_xml}")
    if color_xml:
        parts.append(f"              {color_xml}")
    if extra:
        parts.append(f"              {extra}")
    parts.append(f"            </{element}>")
    return "\n".join(parts)


class CubeBlockUnchangedTests(unittest.TestCase):
    def test_explicit_cube_block_behavior_is_unchanged(self) -> None:
        parsed = parse_blueprint_xml(
            _document(_block()), source="explicit-cube-block"
        )
        block = parsed.grid.blocks[0]
        self.assertEqual(block.subtype_id, "LargeBlockArmorBlock")
        self.assertEqual(block.object_builder_type, "MyObjectBuilder_CubeBlock")
        self.assertEqual((block.min.x, block.min.y, block.min.z), (1, 2, -3))
        self.assertEqual(block.forward, Direction.DOWN)
        self.assertEqual(block.up, Direction.FORWARD)
        self.assertEqual(block.color_mask_hsv.as_tuple(), (0.0, 0.15, 0.25))
        self.assertEqual(block.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(block.source_index, 0)

    def test_omitted_xsi_type_defaults_to_cube_block(self) -> None:
        parsed = parse_blueprint_xml(
            _document(_block(xsi_type=None, min_xml="", orientation_xml="", color_xml="")),
            source="omitted-xsi",
        )
        block = parsed.grid.blocks[0]
        self.assertEqual(block.object_builder_type, "MyObjectBuilder_CubeBlock")
        self.assertFalse(block.min_serialized)
        self.assertFalse(block.orientation_serialized)
        self.assertFalse(block.color_serialized)
        self.assertEqual(block.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)
        self.assertEqual(block.forward, Direction.FORWARD)
        self.assertEqual(block.up, Direction.UP)


class FunctionalObjectBuilderTests(unittest.TestCase):
    def test_thrust_with_required_fields_parses(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
            )
        )
        parsed = parse_blueprint_xml(xml, source="thrust")
        block = parsed.grid.blocks[0]
        self.assertEqual(block.object_builder_type, "MyObjectBuilder_Thrust")
        self.assertEqual(block.subtype_id, "LargeBlockSmallHydrogenThrust")
        self.assertEqual((block.min.x, block.min.y, block.min.z), (1, 2, -3))
        self.assertEqual(block.forward, Direction.DOWN)
        self.assertEqual(block.up, Direction.FORWARD)
        self.assertEqual(block.color_mask_hsv.as_tuple(), (0.0, 0.15, 0.25))
        self.assertEqual(block.source_index, 0)

    def test_representative_functional_builders_parse_without_allowlist(self) -> None:
        parser_text = PARSER_SOURCE.read_text(encoding="utf-8")
        for builder in FUNCTIONAL_BUILDERS:
            self.assertNotIn(builder, parser_text)
            xml = _document(
                _block(f"{builder}Subtype", xsi_type=builder),
                identity=builder,
            )
            parsed = parse_blueprint_xml(xml, source=builder)
            block = parsed.grid.blocks[0]
            self.assertEqual(block.object_builder_type, builder)
            self.assertEqual(block.subtype_id, f"{builder}Subtype")
            self.assertEqual(block.source_index, 0)

    def test_fields_and_source_order_survive_mixed_builders(self) -> None:
        xml = _document(
            "\n".join(
                [
                    _block(
                        "LargeBlockArmorBlock",
                        xsi_type="MyObjectBuilder_CubeBlock",
                        min_xml='<Min x="0" y="0" z="0" />',
                    ),
                    _block(
                        "LargeBlockSmallHydrogenThrust",
                        xsi_type="MyObjectBuilder_Thrust",
                        min_xml='<Min x="1" y="0" z="0" />',
                        extra="<Enabled>true</Enabled>",
                    ),
                    _block(
                        "LargeBlockCockpitIndustrial",
                        xsi_type="MyObjectBuilder_Cockpit",
                        min_xml='<Min x="2" y="0" z="0" />',
                        orientation_xml='<BlockOrientation Forward="Left" Up="Up" />',
                    ),
                    _block(
                        "LargeBlockBatteryBlock",
                        xsi_type="MyObjectBuilder_BatteryBlock",
                        min_xml='<Min x="3" y="0" z="0" />',
                    ),
                ]
            )
        )
        parsed = parse_blueprint_xml(xml, source="mixed-order")
        self.assertEqual(len(parsed.grid.blocks), 4)
        expected = (
            ("LargeBlockArmorBlock", "MyObjectBuilder_CubeBlock", 0, 0),
            ("LargeBlockSmallHydrogenThrust", "MyObjectBuilder_Thrust", 1, 1),
            ("LargeBlockCockpitIndustrial", "MyObjectBuilder_Cockpit", 2, 2),
            ("LargeBlockBatteryBlock", "MyObjectBuilder_BatteryBlock", 3, 3),
        )
        for block, (subtype, builder, x, index) in zip(
            parsed.grid.blocks, expected, strict=True
        ):
            self.assertEqual(block.subtype_id, subtype)
            self.assertEqual(block.object_builder_type, builder)
            self.assertEqual(block.min.x, x)
            self.assertEqual(block.source_index, index)
        self.assertEqual(parsed.grid.blocks[2].forward, Direction.LEFT)
        self.assertEqual(parsed.grid.blocks[2].up, Direction.UP)


class PolicyAndPreflightBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()

    def test_unknown_functional_block_is_refused_by_strict_policy(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
            )
        )
        parsed = parse_blueprint_xml(xml, source="strict-thrust")
        self.assertEqual(parsed.grid.block_count, 1)
        with self.assertRaises(ConversionRefusedError) as ctx:
            convert_blueprint(
                parsed,
                self.catalog,
                ConversionPolicy.STRICT,
            )
        report = ctx.exception.preflight
        self.assertEqual(report.unknown_count, 1)
        self.assertEqual(report.supported_count, 0)
        self.assertEqual(report.blocks[0].subtype_id, "LargeBlockSmallHydrogenThrust")
        self.assertEqual(report.blocks[0].catalog_outcome, CatalogOutcome.UNKNOWN)

    def test_unknown_functional_block_becomes_permissive_filler(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
            )
        )
        result = convert_blueprint_from_xml(
            xml,
            catalog=self.catalog,
            policy=ConversionPolicy.PERMISSIVE,
            source="permissive-thrust",
        )
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.subtype_id, "LargeBlockSmallHydrogenThrust")
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(block.support_status, SupportStatus.UNSUPPORTED)
        self.assertEqual(block.source_index, 0)
        self.assertEqual((block.grid_min.x, block.grid_min.y, block.grid_min.z), (1, 2, -3))
        self.assertEqual(block.forward, Direction.DOWN)
        self.assertEqual(block.up, Direction.FORWARD)
        self.assertEqual(block.color_mask_hsv.as_tuple(), (0.0, 0.15, 0.25))
        self.assertEqual(result.filler_count, 1)

    def test_supported_armor_is_unchanged_beside_functional_block(self) -> None:
        xml = _document(
            "\n".join(
                [
                    _block(
                        "LargeBlockArmorSlope",
                        xsi_type="MyObjectBuilder_CubeBlock",
                        min_xml='<Min x="0" y="0" z="0" />',
                    ),
                    _block(
                        "LargeBlockGyro",
                        xsi_type="MyObjectBuilder_Gyro",
                        min_xml='<Min x="1" y="0" z="0" />',
                    ),
                ]
            )
        )
        parsed = parse_blueprint_xml(xml, source="armor-plus-gyro")
        result = convert_blueprint(
            parsed, self.catalog, ConversionPolicy.PERMISSIVE
        )
        armor, gyro = result.ir.grid.blocks
        self.assertEqual(armor.subtype_id, "LargeBlockArmorSlope")
        self.assertEqual(armor.geometry_id, "large_armor_slope")
        self.assertEqual(armor.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(gyro.subtype_id, "LargeBlockGyro")
        self.assertEqual(gyro.geometry_id, FILLER_GEOMETRY_ID)
        expected_armor = build_canonical_blueprint(
            parse_blueprint_xml(
                _document(
                    _block(
                        "LargeBlockArmorSlope",
                        min_xml='<Min x="0" y="0" z="0" />',
                    )
                ),
                source="armor-only",
            ),
            self.catalog,
        ).grid.blocks[0]
        self.assertEqual(armor.geometry_id, expected_armor.geometry_id)
        self.assertEqual(armor.rotation, expected_armor.rotation)

    def test_preflight_reports_functional_blocks_instead_of_parser_failing(self) -> None:
        xml = _document(
            "\n".join(
                [
                    _block("LargeBlockArmorBlock"),
                    _block(
                        "LargeBlockSmallHydrogenThrust",
                        xsi_type="MyObjectBuilder_Thrust",
                        min_xml='<Min x="4" y="0" z="0" />',
                    ),
                    _block(
                        "LargeBlockRadioAntenna",
                        xsi_type="MyObjectBuilder_RadioAntenna",
                        min_xml='<Min x="5" y="0" z="0" />',
                    ),
                ]
            )
        )
        report = compute_conversion_preflight_from_xml(
            xml, catalog=self.catalog, source="preflight-functional"
        )
        self.assertEqual(report.block_count, 3)
        self.assertEqual(report.supported_count, 1)
        self.assertEqual(report.unknown_count, 2)
        self.assertFalse(report.all_supported)
        self.assertEqual(report.blocks[1].subtype_id, "LargeBlockSmallHydrogenThrust")
        self.assertEqual(report.blocks[2].subtype_id, "LargeBlockRadioAntenna")
        self.assertIsNone(report.blocks[1].geometry_id)
        self.assertEqual(report.blocks[1].catalog_outcome, CatalogOutcome.UNKNOWN)


class FailClosedTests(unittest.TestCase):
    def test_malformed_min_on_thrust_is_rejected(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
                min_xml='<Min x="1.5" y="0" z="0" />',
            )
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="bad-thrust-min")

    def test_malformed_orientation_on_thrust_is_rejected(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
                orientation_xml='<BlockOrientation Forward="Up" Up="Down" />',
            )
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="bad-thrust-orient")

    def test_malformed_color_on_thrust_is_rejected(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
                color_xml='<ColorMaskHSV x="nan" y="0" z="0" />',
            )
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="bad-thrust-color")

    def test_missing_subtype_on_thrust_is_rejected(self) -> None:
        xml = _document(
            _block(None, xsi_type="MyObjectBuilder_Thrust")  # type: ignore[arg-type]
        )
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(xml, source="thrust-missing-subtype")

    def test_empty_subtype_on_thrust_is_rejected(self) -> None:
        xml = _document(_block("", xsi_type="MyObjectBuilder_Thrust"))
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(xml, source="thrust-empty-subtype")

    def test_non_block_element_is_rejected(self) -> None:
        xml = _document(
            _block(element="NotACubeBlock", xsi_type="MyObjectBuilder_Thrust")
        )
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="non-block-element")

    def test_structurally_invalid_xsi_types_are_rejected(self) -> None:
        invalid = (
            "",
            "Thrust",
            "MyObjectBuilder_",
            "MyObjectBuilder_Thrust Extra",
            "http://example.invalid/Thrust",
            "MyObjectBuilder-Thrust",
        )
        for token in invalid:
            with self.subTest(token=token):
                xml = _document(_block(xsi_type=token))
                with self.assertRaises(UnsupportedBlueprintError):
                    parse_blueprint_xml(xml, source=f"bad-xsi-{token!r}")

    def test_subblocks_on_functional_builder_remain_rejected(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
                extra="<SubBlocks><SubBlock /></SubBlocks>",
            )
        )
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="thrust-subblocks")

    def test_malformed_xml_is_still_rejected(self) -> None:
        from se2cad.parser import MalformedXmlError

        with self.assertRaises(MalformedXmlError):
            parse_blueprint_xml("<Definitions><ShipBlueprints>", source="malformed")


class NoScopeExpansionTests(unittest.TestCase):
    def test_packaged_catalog_is_unchanged(self) -> None:
        catalog = load_default_catalog()
        self.assertEqual(len(catalog.entries), 8)
        self.assertEqual(
            [entry.subtype_id for entry in catalog.entries],
            [
                "LargeBlockArmorBlock",
                "LargeBlockArmorSlope",
                "LargeBlockArmorCorner",
                "LargeBlockArmorCornerInv",
                "LargeHeavyBlockArmorBlock",
                "LargeHeavyBlockArmorSlope",
                "LargeHeavyBlockArmorCorner",
                "LargeHeavyBlockArmorCornerInv",
            ],
        )
        self.assertTrue(
            all(entry.observed.cube_size == "Large" for entry in catalog.entries)
        )

    def test_no_new_geometry_recipes(self) -> None:
        records = all_library_records()
        self.assertEqual(len(records), 8)
        lookup_recipe("large_armor_block")
        lookup_recipe(FILLER_GEOMETRY_ID)
        with self.assertRaises(UnknownGeometryError):
            lookup_recipe("large_block_small_hydrogen_thrust")

    def test_object_builder_type_is_not_a_geometry_id(self) -> None:
        xml = _document(
            _block(
                "LargeBlockSmallHydrogenThrust",
                xsi_type="MyObjectBuilder_Thrust",
            )
        )
        result = convert_blueprint_from_xml(
            xml,
            catalog=load_default_catalog(),
            policy=ConversionPolicy.PERMISSIVE,
            source="no-cad-identity",
        )
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertNotEqual(block.geometry_id, "MyObjectBuilder_Thrust")
        self.assertNotEqual(block.geometry_id, block.subtype_id)
        self.assertFalse(hasattr(block, "object_builder_type"))

    def test_small_grid_is_still_rejected(self) -> None:
        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="small" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Small</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_Thrust">
              <SubtypeName>SmallBlockSmallHydrogenThrust</SubtypeName>
              <Min x="0" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="small-grid-thrust")


if __name__ == "__main__":
    unittest.main()
