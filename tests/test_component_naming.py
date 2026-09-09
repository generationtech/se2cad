"""CAD-neutral component names from IR fields (S2C-8.1.1)."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from se2cad.catalog import load_default_catalog
from se2cad.ir import (
    COMPONENT_NAME_MAX_LENGTH,
    ComponentNameError,
    build_canonical_blueprint,
    component_name,
    component_name_from_block,
    component_names_from_blocks,
)
from se2cad.parser import Direction, GridCoordinate, parse_blueprint, parse_blueprint_xml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
NAMING_ROOT = REPO_ROOT / "src" / "se2cad" / "ir"


def _one_block_xml(
    subtype: str = "LargeBlockArmorBlock",
    min_xml: str = "",
    orientation_xml: str = "",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="name-test" />
      <DisplayName>name-test</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <DisplayName>name-grid</DisplayName>
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


class ComponentNameFunctionTests(unittest.TestCase):
    def test_identity_encoding_is_stable_and_human_readable(self) -> None:
        name = component_name(
            "LargeBlockArmorBlock",
            (0, 0, 0),
            Direction.FORWARD,
            Direction.UP,
            0,
        )
        self.assertEqual(name, "LargeBlockArmorBlock_x0_y0_z0_Forward_Up_0")

    def test_grid_coordinate_and_tuple_min_are_equivalent(self) -> None:
        from_tuple = component_name(
            "LargeBlockArmorSlope",
            (1, 2, -3),
            "Down",
            "Forward",
            7,
        )
        from_coord = component_name(
            "LargeBlockArmorSlope",
            GridCoordinate(1, 2, -3),
            Direction.DOWN,
            Direction.FORWARD,
            7,
        )
        self.assertEqual(from_tuple, from_coord)
        self.assertEqual(from_tuple, "LargeBlockArmorSlope_x1_y2_z-3_Down_Forward_7")

    def test_same_subtype_at_different_cells_does_not_collide(self) -> None:
        a = component_name(
            "LargeBlockArmorBlock", (0, 0, 0), Direction.FORWARD, Direction.UP, 0
        )
        b = component_name(
            "LargeBlockArmorBlock", (1, 0, 0), Direction.FORWARD, Direction.UP, 1
        )
        self.assertNotEqual(a, b)
        self.assertIn("x0", a)
        self.assertIn("x1", b)

    def test_omitted_and_explicit_identity_orientation_match(self) -> None:
        catalog = load_default_catalog()
        omitted = build_canonical_blueprint(
            parse_blueprint_xml(_one_block_xml()), catalog
        ).grid.blocks[0]
        explicit = build_canonical_blueprint(
            parse_blueprint_xml(
                _one_block_xml(
                    orientation_xml=(
                        '<BlockOrientation Forward="Forward" Up="Up" />'
                    )
                )
            ),
            catalog,
        ).grid.blocks[0]
        self.assertFalse(omitted.orientation_serialized)
        self.assertTrue(explicit.orientation_serialized)
        self.assertEqual(omitted.forward, explicit.forward)
        self.assertEqual(omitted.up, explicit.up)
        self.assertEqual(
            component_name_from_block(omitted),
            component_name_from_block(explicit),
        )
        self.assertEqual(
            component_name_from_block(omitted),
            "LargeBlockArmorBlock_x0_y0_z0_Forward_Up_0",
        )

    def test_explicit_non_identity_orientation_is_encoded(self) -> None:
        catalog = load_default_catalog()
        block = build_canonical_blueprint(
            parse_blueprint_xml(
                _one_block_xml(
                    min_xml="<Min x=\"0\" y=\"0\" z=\"-1\" />",
                    orientation_xml=(
                        '<BlockOrientation Forward="Down" Up="Forward" />'
                    ),
                )
            ),
            catalog,
        ).grid.blocks[0]
        self.assertEqual(
            component_name_from_block(block),
            "LargeBlockArmorBlock_x0_y0_z-1_Down_Forward_0",
        )

    def test_unsafe_subtype_characters_are_rejected(self) -> None:
        unsafe = (
            "",
            "../escape",
            "a/b",
            r"a\b",
            "has space",
            "ünicode",
            "foo.SLDPRT",
            "C:temp",
            "-leading",
            "1LeadingDigit",
            "path@host",
            "virt^ual",
            "LargeBlockArmorBlock-1",
        )
        for subtype in unsafe:
            with self.subTest(subtype=subtype):
                with self.assertRaises(ComponentNameError):
                    component_name(
                        subtype, (0, 0, 0), Direction.FORWARD, Direction.UP, 0
                    )

    def test_invalid_orientation_index_and_min_are_rejected(self) -> None:
        with self.assertRaises(ComponentNameError):
            component_name(
                "LargeBlockArmorBlock", (0, 0, 0), "North", Direction.UP, 0
            )
        with self.assertRaises(ComponentNameError):
            component_name(
                "LargeBlockArmorBlock", (0, 0, 0), Direction.FORWARD, Direction.UP, -1
            )
        with self.assertRaises(ComponentNameError):
            component_name(
                "LargeBlockArmorBlock", (0, 0, 0), Direction.FORWARD, Direction.UP, True
            )
        with self.assertRaises(ComponentNameError):
            component_name(
                "LargeBlockArmorBlock", (0, 0), Direction.FORWARD, Direction.UP, 0
            )

    def test_truncation_keeps_unique_source_index_suffix(self) -> None:
        long_subtype = "A" + ("b" * 120)
        name = component_name(
            long_subtype, (0, 0, 0), Direction.FORWARD, Direction.UP, 42
        )
        self.assertEqual(len(name), COMPONENT_NAME_MAX_LENGTH)
        self.assertTrue(name.endswith("_42"))
        self.assertTrue(name.startswith("Abb"))
        other = component_name(
            long_subtype, (9, 9, 9), Direction.DOWN, Direction.RIGHT, 43
        )
        self.assertNotEqual(name, other)
        self.assertTrue(other.endswith("_43"))

    def test_name_does_not_contain_paths_or_geometry_id(self) -> None:
        name = component_name(
            "LargeBlockArmorCornerInv",
            (5, 2, -2),
            Direction.BACKWARD,
            Direction.DOWN,
            23,
        )
        self.assertEqual(
            name, "LargeBlockArmorCornerInv_x5_y2_z-2_Backward_Down_23"
        )
        for token in ("/", "\\", "C:", ".SLDPRT", "large_armor", "/home/"):
            self.assertNotIn(token, name)

    def test_naming_source_has_no_pitch_or_backend_literals(self) -> None:
        text = (NAMING_ROOT / "naming.py").read_text(encoding="utf-8")
        self.assertNotIn("2500", text)
        self.assertNotIn("win32com", text)
        self.assertNotIn("pythoncom", text)
        self.assertNotIn(".SLDPRT", text)


class FixtureComponentNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        parsed = parse_blueprint(FIXTURE_PATH)
        cls.ir = build_canonical_blueprint(parsed, load_default_catalog())
        cls.names = component_names_from_blocks(cls.ir.grid.blocks)

    def test_fixture_names_are_unique_and_stable(self) -> None:
        self.assertEqual(len(self.names), 24)
        self.assertEqual(len(set(self.names)), 24)
        self.assertEqual(
            self.names,
            component_names_from_blocks(self.ir.grid.blocks),
        )
        for name, block in zip(self.names, self.ir.grid.blocks, strict=True):
            self.assertEqual(name, component_name_from_block(block))
            self.assertLessEqual(len(name), COMPONENT_NAME_MAX_LENGTH)
            self.assertTrue(name.endswith(f"_{block.source_index}"))

    def test_duplicate_identity_fails_closed(self) -> None:
        with self.assertRaises(ComponentNameError):
            component_names_from_blocks(
                (self.ir.grid.blocks[0], self.ir.grid.blocks[0])
            )


class NamingNeutralityTests(unittest.TestCase):
    def test_ir_naming_imports_are_cad_neutral(self) -> None:
        path = NAMING_ROOT / "naming.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertNotIn("win32com", imported)
        self.assertNotIn("pythoncom", imported)
        self.assertNotIn("se2cad.solidworks", imported)


if __name__ == "__main__":
    unittest.main()
