"""Synthetic negative tests for the S2C-1.2.1 blueprint parser."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from se2cad.parser import (
    BlueprintParseError,
    InvalidFieldError,
    MalformedXmlError,
    MissingRequiredFieldError,
    UnsupportedBlueprintError,
    parse_blueprint,
    parse_blueprint_xml,
)


def _document(
    *,
    grids: str,
    extra_definitions: str = "",
    ship_count: int = 1,
    ship_type: str = "MyObjectBuilder_ShipBlueprintDefinition",
) -> str:
    ships = []
    for index in range(ship_count):
        ships.append(
            f"""    <ShipBlueprint xsi:type="{ship_type}">
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="neg-test-{index}" />
      <DisplayName>neg-test-{index}</DisplayName>
      <CubeGrids>
{grids}
      </CubeGrids>
      <WorkshopId>0</WorkshopId>
    </ShipBlueprint>"""
        )
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
{''.join(ships)}
  </ShipBlueprints>
  {extra_definitions}
</Definitions>
"""


def _large_grid(blocks: str, *, size: str = "Large", extra: str = "") -> str:
    return f"""        <CubeGrid>
          <GridSizeEnum>{size}</GridSizeEnum>
          <CubeBlocks>
{blocks}
          </CubeBlocks>
          <DisplayName>neg-grid</DisplayName>
          {extra}
        </CubeGrid>"""


def _block(
    subtype: str = "LargeBlockArmorBlock",
    *,
    min_xml: str | None = '<Min x="1" y="0" z="0" />',
    orientation_xml: str | None = None,
    xsi_type: str = "MyObjectBuilder_CubeBlock",
    extra: str = "",
) -> str:
    parts = [f'            <MyObjectBuilder_CubeBlock xsi:type="{xsi_type}">']
    if subtype is not None:
        parts.append(f"              <SubtypeName>{subtype}</SubtypeName>")
    if min_xml:
        parts.append(f"              {min_xml}")
    if orientation_xml:
        parts.append(f"              {orientation_xml}")
    if extra:
        parts.append(f"              {extra}")
    parts.append("            </MyObjectBuilder_CubeBlock>")
    return "\n".join(parts)


class NegativeParserTests(unittest.TestCase):
    def test_malformed_xml(self) -> None:
        with self.assertRaises(MalformedXmlError):
            parse_blueprint_xml("<Definitions><ShipBlueprints>", source="malformed")

    def test_doctype_and_entity_are_rejected(self) -> None:
        xml = """<?xml version="1.0"?>
<!DOCTYPE Definitions [<!ENTITY xxe "boom">]>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>&xxe;</ShipBlueprints>
</Definitions>
"""
        with self.assertRaises(MalformedXmlError):
            parse_blueprint_xml(xml, source="doctype")

    def test_internal_entity_expansion_is_not_performed(self) -> None:
        xml = '<!DOCTYPE foo [<!ENTITY x "secret-payload">]><root>&x;</root>'
        with self.assertRaises(MalformedXmlError):
            parse_blueprint_xml(xml, source="entity")

    def test_xinclude_is_rejected(self) -> None:
        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include href="/etc/passwd"/>
</Definitions>
"""
        with self.assertRaises(MalformedXmlError):
            parse_blueprint_xml(xml, source="xinclude")

    def test_zero_cube_grid(self) -> None:
        xml = _document(grids="")
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="zero-grid")

    def test_multiple_cube_grids(self) -> None:
        grids = "\n".join(
            [
                _large_grid(_block()),
                _large_grid(_block(min_xml='<Min x="2" y="0" z="0" />')),
            ]
        )
        xml = _document(grids=grids)
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="multi-grid")

    def test_nested_cube_grid(self) -> None:
        inner = _large_grid(_block())
        outer = _large_grid(_block(), extra=inner)
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(_document(grids=outer), source="nested-grid")

    def test_small_grid_rejected(self) -> None:
        xml = _document(grids=_large_grid(_block(), size="Small"))
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="small-grid")

    def test_missing_subtype(self) -> None:
        block = """            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>"""
        xml = _document(grids=_large_grid(block))
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(xml, source="missing-subtype")

    def test_empty_subtype(self) -> None:
        xml = _document(grids=_large_grid(_block(subtype="")))
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(xml, source="empty-subtype")

    def test_invalid_direction_token(self) -> None:
        xml = _document(
            grids=_large_grid(
                _block(orientation_xml='<BlockOrientation Forward="North" Up="Up" />')
            )
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="bad-direction")

    def test_non_orthogonal_orientation(self) -> None:
        xml = _document(
            grids=_large_grid(
                _block(orientation_xml='<BlockOrientation Forward="Up" Up="Down" />')
            )
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="non-orthogonal")

    def test_unsupported_block_builder_type(self) -> None:
        xml = _document(
            grids=_large_grid(_block(xsi_type="MyObjectBuilder_BatteryBlock"))
        )
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="battery-block")

    def test_malformed_cube_blocks_unknown_child(self) -> None:
        blocks = """            <NotACubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </NotACubeBlock>"""
        xml = _document(grids=_large_grid(blocks))
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="bad-cubeblocks")

    def test_mechanical_groups_rejected(self) -> None:
        xml = _document(
            grids=_large_grid(
                _block(),
                extra="<MechanicalGroups><Group /></MechanicalGroups>",
            )
        )
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="mechanical")

    def test_multiple_ship_blueprints(self) -> None:
        xml = _document(grids=_large_grid(_block()), ship_count=2)
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="multi-ship")

    def test_unsupported_definitions_child(self) -> None:
        xml = _document(
            grids=_large_grid(_block()),
            extra_definitions="<Prefabs />",
        )
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="prefabs")

    def test_missing_grid_size(self) -> None:
        grid = """        <CubeGrid>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>"""
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(_document(grids=grid), source="missing-grid-size")

    def test_invalid_min_token(self) -> None:
        xml = _document(
            grids=_large_grid(_block(min_xml='<Min x="1.5" y="0" z="0" />'))
        )
        with self.assertRaises(InvalidFieldError):
            parse_blueprint_xml(xml, source="float-min")

    def test_explicit_origin_min_is_marked_serialized(self) -> None:
        xml = _document(
            grids=_large_grid(_block(min_xml='<Min x="0" y="0" z="0" />'))
        )
        parsed = parse_blueprint_xml(xml, source="explicit-origin")
        block = parsed.grid.blocks[0]
        self.assertTrue(block.min_serialized)
        self.assertEqual((block.min.x, block.min.y, block.min.z), (0, 0, 0))

    def test_omitted_min_and_orientation_use_established_defaults(self) -> None:
        block = """            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>"""
        parsed = parse_blueprint_xml(_document(grids=_large_grid(block)), source="omitted")
        cube = parsed.grid.blocks[0]
        self.assertFalse(cube.min_serialized)
        self.assertEqual((cube.min.x, cube.min.y, cube.min.z), (0, 0, 0))
        self.assertFalse(cube.orientation_serialized)
        self.assertEqual(cube.forward.value, "Forward")
        self.assertEqual(cube.up.value, "Up")

    def test_path_parse_rejects_missing_file(self) -> None:
        with self.assertRaises(BlueprintParseError) as raised:
            parse_blueprint(Path("/tmp/se2cad-does-not-exist-s2c-1-2-1.sbc"))
        self.assertNotIsInstance(raised.exception, MalformedXmlError)

    def test_subblocks_are_rejected(self) -> None:
        xml = _document(
            grids=_large_grid(
                _block(extra="<SubBlocks><SubBlock /></SubBlocks>")
            )
        )
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="subblocks")

    def test_xml_values_do_not_open_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            canary = Path(tmp) / "canary.txt"
            canary.write_text("should-not-be-read", encoding="utf-8")
            xml = f"""<?xml version="1.0"?>
<!DOCTYPE Definitions [<!ENTITY xxe SYSTEM "{canary.as_uri()}">]>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>&xxe;</ShipBlueprints>
</Definitions>
"""
            with self.assertRaises(MalformedXmlError):
                parse_blueprint_xml(xml, source="xxe-file")
            self.assertEqual(canary.read_text(encoding="utf-8"), "should-not-be-read")

    def test_path_parse_round_trip_for_synthetic_file(self) -> None:
        xml = _document(grids=_large_grid(_block()))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bp.sbc"
            path.write_text(xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        self.assertEqual(parsed.identity_subtype, "neg-test-0")
        self.assertEqual(parsed.grid.block_count, 1)
        self.assertEqual(parsed.grid.blocks[0].subtype_id, "LargeBlockArmorBlock")


if __name__ == "__main__":
    unittest.main()
