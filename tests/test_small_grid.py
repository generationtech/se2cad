"""S2C-13.1.1 Small Grid semantic path.

Synthetic XML only. No SolidWorks. Large Grid fixture must stay unchanged.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from se2cad.catalog import (
    LARGE_GRID_CELL_PITCH_MM,
    SMALL_GRID_CELL_PITCH_MM,
    UnknownSubtypeError,
    cell_pitch_mm,
    load_default_catalog,
)
from se2cad.ir import build_canonical_blueprint
from se2cad.library import (
    CANONICAL_LOCAL_FRAME,
    lookup_recipe,
    lookup_record,
    recipe_for_topology,
    small_grid_library_geometry_ids,
)
from se2cad.parser import (
    GridCoordinate,
    GridSize,
    UnsupportedBlueprintError,
    parse_blueprint,
    parse_blueprint_xml,
)
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight
from se2cad.statistics import compute_blueprint_statistics
from se2cad.transform import cell_center_mm, legal_orientations, rotation_from_forward_up

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "acceptance"
    / "four-block-armor-asymmetric"
    / "bp.sbc"
)
_FIXTURE_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"

_SMALL_COUNTERPARTS = {
    "SmallBlockArmorBlock": "small_block_armor_block",
    "SmallBlockArmorSlope": "small_block_armor_slope",
    "SmallBlockArmorCorner": "small_block_armor_corner",
    "SmallBlockArmorCornerInv": "small_block_armor_corner_inv",
    "SmallHeavyBlockArmorBlock": "small_heavy_block_armor_block",
    "SmallHeavyBlockArmorSlope": "small_heavy_block_armor_slope",
    "SmallHeavyBlockArmorCorner": "small_heavy_block_armor_corner",
    "SmallHeavyBlockArmorCornerInv": "small_heavy_block_armor_corner_inv",
}


def _document(
    *,
    size: str = "Small",
    blocks: str,
    extra_grid: str = "",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="small-grid-test" />
      <DisplayName>small-grid-test</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>{size}</GridSizeEnum>
          <DisplayName>small-grid</DisplayName>
          <CubeBlocks>
{blocks}
          </CubeBlocks>
        </CubeGrid>
        {extra_grid}
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _block(
    subtype: str = "SmallBlockArmorBlock",
    *,
    min_xml: str = "",
    orientation_xml: str = "",
) -> str:
    parts = [
        "            <MyObjectBuilder_CubeBlock>",
        f"              <SubtypeName>{subtype}</SubtypeName>",
    ]
    if min_xml:
        parts.append(f"              {min_xml}")
    if orientation_xml:
        parts.append(f"              {orientation_xml}")
    parts.append("            </MyObjectBuilder_CubeBlock>")
    return "\n".join(parts)


class SmallGridPitchTests(unittest.TestCase):
    def test_named_small_grid_pitch_is_five_hundred_millimetres(self) -> None:
        self.assertEqual(SMALL_GRID_CELL_PITCH_MM, 500)
        self.assertEqual(LARGE_GRID_CELL_PITCH_MM, 2500)
        self.assertEqual(cell_pitch_mm("Small"), SMALL_GRID_CELL_PITCH_MM)
        self.assertEqual(cell_pitch_mm("Large"), LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(cell_pitch_mm(GridSize.SMALL.value), SMALL_GRID_CELL_PITCH_MM)

    def test_unknown_cube_size_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            cell_pitch_mm("Medium")


class SmallGridParseTests(unittest.TestCase):
    def test_single_small_grid_parses(self) -> None:
        parsed = parse_blueprint_xml(
            _document(blocks=_block(min_xml='<Min x="2" y="-1" z="0" />')),
            source="small-parse",
        )
        self.assertEqual(parsed.grid.grid_size, GridSize.SMALL)
        self.assertEqual(parsed.grid.block_count, 1)
        block = parsed.grid.blocks[0]
        self.assertEqual(block.subtype_id, "SmallBlockArmorBlock")
        self.assertEqual(block.min, GridCoordinate(2, -1, 0))

    def test_multiple_grids_still_fail_closed(self) -> None:
        extra = """
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>"""
        with self.assertRaises(UnsupportedBlueprintError) as ctx:
            parse_blueprint_xml(
                _document(blocks=_block(), extra_grid=extra),
                source="mixed-grids",
            )
        self.assertIn("multiple CubeGrid", str(ctx.exception))

    def test_small_subtype_is_not_aliased_to_large(self) -> None:
        catalog = load_default_catalog()
        small = catalog.lookup("SmallBlockArmorBlock")
        large = catalog.lookup("LargeBlockArmorBlock")
        self.assertEqual(small.observed.cube_size, "Small")
        self.assertEqual(large.observed.cube_size, "Large")
        self.assertNotEqual(small.geometry_id, large.geometry_id)
        self.assertNotEqual(small.subtype_id, large.subtype_id)
        with self.assertRaises(UnknownSubtypeError):
            catalog.lookup("smallblockarmorblock")


class SmallGridTransformTests(unittest.TestCase):
    def test_translations_use_small_grid_pitch(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(
            _document(blocks=_block(min_xml='<Min x="2" y="1" z="-3" />')),
            source="small-translate",
        )
        ir = build_canonical_blueprint(parsed, catalog)
        self.assertEqual(ir.grid.grid_size, GridSize.SMALL)
        pitch = SMALL_GRID_CELL_PITCH_MM
        self.assertEqual(
            ir.grid.blocks[0].position_mm.as_tuple(),
            (2 * pitch, pitch, -3 * pitch),
        )
        self.assertEqual(
            cell_center_mm(GridCoordinate(2, 1, -3), pitch).as_tuple(),
            (2 * pitch, pitch, -3 * pitch),
        )
        self.assertNotEqual(
            ir.grid.blocks[0].position_mm.as_tuple(),
            (2 * LARGE_GRID_CELL_PITCH_MM, LARGE_GRID_CELL_PITCH_MM, -3 * LARGE_GRID_CELL_PITCH_MM),
        )

    def test_twenty_four_orientations_remain_unique_on_small_grid(self) -> None:
        catalog = load_default_catalog()
        seen: dict[tuple[tuple[int, int, int], ...], object] = {}
        for index, (forward, up) in enumerate(legal_orientations()):
            xml = _document(
                blocks=_block(
                    orientation_xml=(
                        f'<BlockOrientation Forward="{forward.value}" '
                        f'Up="{up.value}" />'
                    )
                )
            )
            ir = build_canonical_blueprint(
                parse_blueprint_xml(xml, source=f"small-orient-{index}"),
                catalog,
            )
            rotation = ir.grid.blocks[0].rotation
            self.assertEqual(rotation, rotation_from_forward_up(forward, up))
            self.assertNotIn(rotation.columns, seen)
            seen[rotation.columns] = (forward, up)
        self.assertEqual(len(seen), 24)


class SmallGridRecipeTests(unittest.TestCase):
    def test_small_grid_recipes_scale_by_named_pitch(self) -> None:
        self.assertEqual(
            small_grid_library_geometry_ids(),
            tuple(_SMALL_COUNTERPARTS.values()),
        )
        large = lookup_record("large_armor_block")
        small = lookup_record("small_block_armor_block")
        self.assertEqual(small.grid_size, "Small")
        self.assertEqual(large.grid_size, "Large")
        self.assertEqual(small.frame.plus_x, CANONICAL_LOCAL_FRAME.plus_x)
        self.assertEqual(small.frame.plus_y, CANONICAL_LOCAL_FRAME.plus_y)
        self.assertEqual(small.frame.plus_z, CANONICAL_LOCAL_FRAME.plus_z)
        self.assertEqual(small.frame.half_extent_mm * 2, SMALL_GRID_CELL_PITCH_MM)
        self.assertEqual(large.frame.half_extent_mm * 2, LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(
            small.recipe.validation.volume_times_6_mm3 * (5**3),
            large.recipe.validation.volume_times_6_mm3,
        )
        stamped = recipe_for_topology(
            "synthetic_small_block",
            "Box",
            pitch_mm=SMALL_GRID_CELL_PITCH_MM,
        )
        self.assertEqual(stamped.vertices_mm, small.recipe.vertices_mm)

    def test_small_and_large_counterparts_stay_distinct(self) -> None:
        catalog = load_default_catalog()
        for subtype, geometry_id in _SMALL_COUNTERPARTS.items():
            entry = catalog.lookup(subtype)
            self.assertEqual(entry.geometry_id, geometry_id)
            self.assertEqual(entry.observed.cube_size, "Small")
            record = lookup_record(geometry_id)
            self.assertEqual(record.geometry_id, geometry_id)
            self.assertEqual(lookup_recipe(geometry_id).geometry_id, geometry_id)


class SmallGridPolicyReuseTests(unittest.TestCase):
    def test_preflight_and_strict_policy_reuse_existing_path(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(
            _document(blocks=_block()),
            source="small-policy",
        )
        report = compute_conversion_preflight(parsed, catalog)
        self.assertTrue(report.all_supported)
        self.assertEqual(report.blocks[0].catalog_outcome, CatalogOutcome.SUPPORTED)
        result = convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)
        self.assertEqual(result.ir.grid.grid_size, GridSize.SMALL)
        self.assertEqual(result.ir.grid.blocks[0].geometry_id, "small_block_armor_block")
        stats = compute_blueprint_statistics(parsed, catalog)
        self.assertEqual(stats.grid_size, GridSize.SMALL)
        self.assertEqual(stats.millimetre_size.x, SMALL_GRID_CELL_PITCH_MM)

    def test_unknown_small_grid_subtype_uses_existing_unknown_path(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(
            _document(blocks=_block("NotACatalogSubtype")),
            source="small-unknown",
        )
        report = compute_conversion_preflight(parsed, catalog)
        self.assertFalse(report.all_supported)
        self.assertEqual(report.blocks[0].catalog_outcome, CatalogOutcome.UNKNOWN)
        result = convert_blueprint(parsed, catalog, ConversionPolicy.PERMISSIVE)
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.subtype_id, "NotACatalogSubtype")
        self.assertEqual(block.geometry_id, "se2cad_unknown_filler")
        self.assertEqual(block.position_mm.as_tuple(), (0, 0, 0))


class LargeGridRegressionTests(unittest.TestCase):
    def test_acceptance_fixture_is_unchanged_and_still_large(self) -> None:
        digest = hashlib.sha256(_FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(digest, _FIXTURE_SHA256)
        parsed = parse_blueprint(_FIXTURE)
        self.assertEqual(parsed.grid.grid_size, GridSize.LARGE)
        ir = build_canonical_blueprint(parsed, load_default_catalog())
        self.assertEqual(ir.grid.grid_size, GridSize.LARGE)
        self.assertEqual(len(ir.grid.blocks), 24)
        self.assertEqual(
            ir.grid.blocks[0].position_mm.as_tuple()[0] % LARGE_GRID_CELL_PITCH_MM,
            0,
        )


class NoScatteredPitchLiteralTests(unittest.TestCase):
    def test_converter_sources_do_not_copy_small_or_large_pitch_literals(self) -> None:
        roots = [
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "ir",
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "transform",
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "library",
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "policy",
            Path(__file__).resolve().parents[1] / "src" / "se2cad" / "statistics",
        ]
        for root in roots:
            for path in root.glob("*.py"):
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"\b2500\b", msg=f"{path} copies 2500")
                self.assertNotRegex(text, r"\b500\b", msg=f"{path} copies 500")


if __name__ == "__main__":
    unittest.main()
