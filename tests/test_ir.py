"""IR construction, identity preservation, and backend neutrality."""

from __future__ import annotations

import unittest
from pathlib import Path

from se2cad.catalog import (
    LARGE_GRID_CELL_PITCH_MM,
    RecipeKind,
    SupportStatus,
    UnknownSubtypeError,
    load_default_catalog,
)
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    Direction,
    GridCoordinate,
    GridSize,
    parse_blueprint_xml,
)
from se2cad.transform import IDENTITY_ROTATION, InvalidOrientationError


def _one_block_xml(
    subtype: str = "LargeBlockArmorBlock",
    min_xml: str = "",
    orientation_xml: str = "",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="ir-test" />
      <DisplayName>ir-test</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <DisplayName>ir-grid</DisplayName>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
              {min_xml}
              {orientation_xml}
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


class IrConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()

    def test_omitted_orientation_is_identity_at_origin(self) -> None:
        parsed = parse_blueprint_xml(_one_block_xml())
        ir = build_canonical_blueprint(parsed, self.catalog)
        block = ir.grid.blocks[0]
        self.assertEqual(block.subtype_id, "LargeBlockArmorBlock")
        self.assertEqual(block.geometry_id, "large_armor_block")
        self.assertEqual(block.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
        self.assertEqual(block.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(block.grid_min, GridCoordinate(0, 0, 0))
        self.assertFalse(block.min_serialized)
        self.assertEqual(block.forward, Direction.FORWARD)
        self.assertEqual(block.up, Direction.UP)
        self.assertFalse(block.orientation_serialized)
        self.assertFalse(block.color_serialized)
        self.assertEqual(block.appearance_support, AppearanceSupport.DEFAULT)
        self.assertEqual(block.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)
        self.assertEqual(block.position_mm.as_tuple(), (0, 0, 0))
        self.assertEqual(block.rotation, IDENTITY_ROTATION)
        self.assertEqual(ir.identity_subtype, "ir-test")
        self.assertEqual(ir.grid.display_name, "ir-grid")
        self.assertEqual(ir.grid.grid_size, GridSize.LARGE)

    def test_subtype_and_geometry_id_survive_unchanged(self) -> None:
        mapping = {
            "LargeBlockArmorBlock": "large_armor_block",
            "LargeBlockArmorSlope": "large_armor_slope",
            "LargeBlockArmorCorner": "large_armor_corner",
            "LargeBlockArmorCornerInv": "large_armor_corner_inv",
        }
        for subtype, geometry_id in mapping.items():
            parsed = parse_blueprint_xml(_one_block_xml(subtype=subtype))
            ir = build_canonical_blueprint(parsed, self.catalog)
            block = ir.grid.blocks[0]
            self.assertEqual(block.subtype_id, subtype)
            self.assertEqual(block.geometry_id, geometry_id)
            self.assertIs(block.subtype_id, parsed.grid.blocks[0].subtype_id)

    def test_unknown_subtype_fails_closed(self) -> None:
        parsed = parse_blueprint_xml(_one_block_xml(subtype="SmallBlockArmorBlock"))
        with self.assertRaises(UnknownSubtypeError):
            build_canonical_blueprint(parsed, self.catalog)

    def test_signed_translation_is_exact(self) -> None:
        parsed = parse_blueprint_xml(
            _one_block_xml(min_xml='<Min x="2" y="1" z="-2" />')
        )
        ir = build_canonical_blueprint(parsed, self.catalog)
        pitch = LARGE_GRID_CELL_PITCH_MM
        self.assertEqual(
            ir.grid.blocks[0].position_mm.as_tuple(),
            (2 * pitch, pitch, -2 * pitch),
        )
        self.assertTrue(
            all(isinstance(c, int) for c in ir.grid.blocks[0].position_mm.as_tuple())
        )


class IrNeutralityTests(unittest.TestCase):
    def test_ir_and_transform_have_no_backend_types(self) -> None:
        roots = [
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "ir",
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "transform",
        ]
        forbidden_import = (
            r"(?m)^\s*(?:import|from)\s+(?:solidworks|win32com|pythoncom|blender|bpy)\b",
        )
        for root in roots:
            for path in root.glob("*.py"):
                text = path.read_text(encoding="utf-8")
                for pattern in forbidden_import:
                    self.assertNotRegex(text, pattern, msg=f"{path} matches {pattern}")

    def test_canonical_block_annotations_are_cad_neutral(self) -> None:
        from se2cad.ir.model import CanonicalBlock

        hints = CanonicalBlock.__annotations__
        joined = " ".join(str(value) for value in hints.values()).lower()
        self.assertNotIn("solidworks", joined)
        self.assertNotIn("com", joined)
        self.assertNotIn("sldprt", joined)


class InvalidOrientationThroughIrTests(unittest.TestCase):
    def test_direct_invalid_pair_cannot_be_placed(self) -> None:
        from se2cad.transform import rotation_from_forward_up

        with self.assertRaises(InvalidOrientationError):
            rotation_from_forward_up(Direction.UP, Direction.DOWN)


if __name__ == "__main__":
    unittest.main()
