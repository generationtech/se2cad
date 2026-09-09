"""CAD-neutral blueprint statistics: synthetic cases and neutrality."""

from __future__ import annotations

import ast
import io
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM, load_default_catalog
from se2cad.parser import (
    Direction,
    GridSize,
    MalformedXmlError,
    UnsupportedBlueprintError,
)
from se2cad.statistics import (
    NamedCount,
    OrientationCount,
    compute_blueprint_statistics_from_path,
    compute_blueprint_statistics_from_xml,
)
from se2cad.statistics.__main__ import main as statistics_main

STATS_ROOT = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "statistics"


def _document(
    blocks: str,
    *,
    identity: str = "stats-test",
    grid_name: str = "stats-grid",
    display_name: str = "stats-test",
    size: str = "Large",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <DisplayName>{display_name}</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>{size}</GridSizeEnum>
          <DisplayName>{grid_name}</DisplayName>
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
    min_xml: str = "",
    orientation_xml: str = "",
) -> str:
    parts = ["            <MyObjectBuilder_CubeBlock>", f"              <SubtypeName>{subtype}</SubtypeName>"]
    if min_xml:
        parts.append(f"              {min_xml}")
    if orientation_xml:
        parts.append(f"              {orientation_xml}")
    parts.append("            </MyObjectBuilder_CubeBlock>")
    return "\n".join(parts)


class StatisticsSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()

    def test_single_cell_identity_extent_and_full_coverage(self) -> None:
        stats = compute_blueprint_statistics_from_xml(
            _document(_block()), catalog=self.catalog, source="single-cell"
        )
        self.assertEqual(stats.identity_subtype, "stats-test")
        self.assertEqual(stats.display_name, "stats-test")
        self.assertEqual(stats.grid_display_name, "stats-grid")
        self.assertEqual(stats.grid_size, GridSize.LARGE)
        self.assertEqual(stats.block_count, 1)
        self.assertEqual(stats.cell_pitch_mm, LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(stats.subtype_counts, (NamedCount("LargeBlockArmorBlock", 1),))
        self.assertEqual(stats.geometry_id_counts, (NamedCount("large_armor_block", 1),))
        assert stats.cell_extents is not None
        self.assertEqual(stats.cell_extents.x.minimum, 0)
        self.assertEqual(stats.cell_extents.x.maximum, 0)
        self.assertEqual(stats.cell_extents.y.span_cells, 1)
        self.assertEqual(stats.cell_extents.z.span_cells, 1)
        assert stats.millimetre_size is not None
        self.assertEqual(
            (stats.millimetre_size.x, stats.millimetre_size.y, stats.millimetre_size.z),
            (LARGE_GRID_CELL_PITCH_MM,) * 3,
        )
        self.assertEqual(stats.occupancy.unique_min_cells, 1)
        self.assertEqual(stats.occupancy.bounding_box_cells, 1)
        self.assertEqual(stats.occupancy.coverage, Fraction(1, 1))
        self.assertEqual(stats.catalog_coverage.resolved_blocks, 1)
        self.assertEqual(stats.catalog_coverage.unresolved_blocks, 0)
        self.assertEqual(
            stats.orientation_counts,
            (OrientationCount(Direction.FORWARD, Direction.UP, 1),),
        )

    def test_negative_coordinates_keep_signs_and_use_pitch_constant(self) -> None:
        xml = _document(
            _block(min_xml='<Min x="-3" y="0" z="-2" />')
            + "\n"
            + _block(
                "LargeBlockArmorSlope",
                min_xml='<Min x="1" y="-4" z="2" />',
            )
        )
        stats = compute_blueprint_statistics_from_xml(
            xml, catalog=self.catalog, source="negative"
        )
        assert stats.cell_extents is not None
        self.assertEqual((stats.cell_extents.x.minimum, stats.cell_extents.x.maximum), (-3, 1))
        self.assertEqual((stats.cell_extents.y.minimum, stats.cell_extents.y.maximum), (-4, 0))
        self.assertEqual((stats.cell_extents.z.minimum, stats.cell_extents.z.maximum), (-2, 2))
        self.assertEqual(stats.cell_extents.x.span_cells, 5)
        self.assertEqual(stats.cell_extents.y.span_cells, 5)
        self.assertEqual(stats.cell_extents.z.span_cells, 5)
        assert stats.millimetre_size is not None
        self.assertEqual(stats.millimetre_size.x, 5 * LARGE_GRID_CELL_PITCH_MM)
        self.assertEqual(stats.occupancy.unique_min_cells, 2)
        self.assertEqual(stats.occupancy.bounding_box_cells, 125)
        self.assertEqual(stats.occupancy.coverage, Fraction(2, 125))

    def test_mixed_orientations_are_histogrammed(self) -> None:
        xml = _document(
            "\n".join(
                [
                    _block(),
                    _block(
                        min_xml='<Min x="1" y="0" z="0" />',
                        orientation_xml='<BlockOrientation Forward="Down" Up="Forward" />',
                    ),
                    _block(
                        min_xml='<Min x="2" y="0" z="0" />',
                        orientation_xml='<BlockOrientation Forward="Down" Up="Right" />',
                    ),
                    _block(
                        min_xml='<Min x="3" y="0" z="0" />',
                        orientation_xml='<BlockOrientation Forward="Down" Up="Forward" />',
                    ),
                ]
            )
        )
        stats = compute_blueprint_statistics_from_xml(
            xml, catalog=self.catalog, source="mixed-orient"
        )
        self.assertEqual(
            stats.orientation_counts,
            (
                OrientationCount(Direction.DOWN, Direction.FORWARD, 2),
                OrientationCount(Direction.DOWN, Direction.RIGHT, 1),
                OrientationCount(Direction.FORWARD, Direction.UP, 1),
            ),
        )

    def test_unknown_subtype_is_counted_not_dropped_or_aliased(self) -> None:
        xml = _document(
            _block()
            + "\n"
            + _block("NotACatalogSubtype", min_xml='<Min x="1" y="0" z="0" />')
            + "\n"
            + _block("NotACatalogSubtype", min_xml='<Min x="2" y="0" z="0" />')
        )
        stats = compute_blueprint_statistics_from_xml(
            xml, catalog=self.catalog, source="unknown-subtype"
        )
        self.assertEqual(stats.block_count, 3)
        self.assertEqual(
            stats.subtype_counts,
            (
                NamedCount("LargeBlockArmorBlock", 1),
                NamedCount("NotACatalogSubtype", 2),
            ),
        )
        self.assertEqual(stats.geometry_id_counts, (NamedCount("large_armor_block", 1),))
        self.assertEqual(stats.catalog_coverage.resolved_blocks, 1)
        self.assertEqual(stats.catalog_coverage.unresolved_blocks, 2)
        self.assertEqual(
            stats.catalog_coverage.unresolved_subtype_counts,
            (NamedCount("NotACatalogSubtype", 2),),
        )
        self.assertNotIn("unknown", [item.name for item in stats.geometry_id_counts])

    def test_empty_cube_blocks_do_not_invent_extents(self) -> None:
        stats = compute_blueprint_statistics_from_xml(
            _document(""), catalog=self.catalog, source="empty-blocks"
        )
        self.assertEqual(stats.block_count, 0)
        self.assertEqual(stats.subtype_counts, ())
        self.assertEqual(stats.geometry_id_counts, ())
        self.assertIsNone(stats.cell_extents)
        self.assertIsNone(stats.millimetre_size)
        self.assertEqual(stats.occupancy.unique_min_cells, 0)
        self.assertEqual(stats.occupancy.bounding_box_cells, 0)
        self.assertIsNone(stats.occupancy.coverage)

    def test_zero_grid_and_small_grid_fail_closed_via_parser(self) -> None:
        zero_grid = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="empty-illegal" />
      <CubeGrids>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with self.assertRaises(UnsupportedBlueprintError):
            compute_blueprint_statistics_from_xml(zero_grid, source="zero-grid")
        with self.assertRaises(UnsupportedBlueprintError):
            compute_blueprint_statistics_from_xml(
                _document(_block(), size="Small"), source="small-grid"
            )
        with self.assertRaises(MalformedXmlError):
            compute_blueprint_statistics_from_xml(
                "<Definitions><ShipBlueprints>", source="malformed"
            )

    def test_from_path_uses_parser_and_does_not_store_the_path(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )
        stats = compute_blueprint_statistics_from_path(fixture, self.catalog)
        self.assertEqual(stats.identity_subtype, "se2cad-test1")
        dumped = repr(stats)
        self.assertNotIn(str(fixture), dumped)
        self.assertNotIn("C:\\", dumped.replace("\\\\", "\\"))

    def test_missing_path_is_a_parser_error(self) -> None:
        from se2cad.parser import BlueprintParseError

        with self.assertRaises(BlueprintParseError):
            compute_blueprint_statistics_from_path(
                Path(__file__).resolve().parent / "no-such-blueprint.sbc"
            )

    def test_operator_entry_survives_legacy_console_encoding(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )

        class _Cp1252Stdout(io.StringIO):
            encoding = "cp1252"

            def write(self, s: str) -> int:
                s.encode("cp1252")
                return super().write(s)

        stdout = _Cp1252Stdout()
        with patch("sys.stdout", stdout):
            code = statistics_main([str(fixture)])
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("identity_subtype=se2cad-test1", text)
        self.assertIn("display_name=\\ue030Kolyma", text)
        self.assertNotIn("\ue030", text)

    def test_operator_entry_prints_fixture_counts_without_writing_files(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = statistics_main([str(fixture)])
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("identity_subtype=se2cad-test1", text)
        self.assertIn("block_count=24", text)
        self.assertIn("catalog_coverage=24/24 resolved", text)
        self.assertIn("occupancy_coverage=1/3", text)
        self.assertNotIn(str(fixture), text)

    def test_operator_entry_usage_and_parse_failure(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(statistics_main([]), 2)
        self.assertIn("usage: python -m se2cad.statistics", stdout.getvalue())
        stdout = io.StringIO()
        missing = Path(__file__).resolve().parent / "no-such-blueprint.sbc"
        with patch("sys.stdout", stdout):
            self.assertEqual(statistics_main([str(missing)]), 2)
        self.assertIn("not a file", stdout.getvalue())


class StatisticsNeutralityTests(unittest.TestCase):
    def test_statistics_source_has_no_backend_or_pitch_literals(self) -> None:
        forbidden_text = (
            "win32com",
            "pythoncom",
            ".sldprt",
            ".sldasm",
            ".mwm",
            "/home/",
            "C:\\",
        )
        for path in sorted(STATS_ROOT.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for token in forbidden_text:
                self.assertNotIn(token.lower(), lowered, msg=f"{path.name} mentions {token}")
            self.assertNotRegex(text, r"\b2500\b", msg=f"{path.name} copies 2500")
            self.assertNotRegex(text, r"\b24\b", msg=f"{path.name} bakes fixture count 24")

    def test_statistics_imports_are_stdlib_plus_parser_catalog(self) -> None:
        allowed_se2cad = {
            "se2cad.catalog",
            "se2cad.parser",
            "se2cad.parser.model",
            "se2cad.statistics.compute",
            "se2cad.statistics.model",
        }
        for path in sorted(STATS_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("se2cad."):
                        self.assertIn(node.module, allowed_se2cad, msg=path.name)

    def test_compute_does_not_require_ir_or_solidworks(self) -> None:
        parsed_source = (STATS_ROOT / "compute.py").read_text(encoding="utf-8")
        self.assertNotRegex(parsed_source, r"se2cad\.ir")
        self.assertNotRegex(parsed_source, r"se2cad\.solidworks")
        self.assertNotRegex(parsed_source, r"se2cad\.library")


if __name__ == "__main__":
    unittest.main()
