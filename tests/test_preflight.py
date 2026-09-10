"""CAD-neutral conversion preflight: synthetic cases and neutrality."""

from __future__ import annotations

import ast
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    CatalogEntry,
    CellSize,
    DefinitionCatalog,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
    load_default_catalog,
)
from se2cad.parser import (
    AppearanceSupport,
    GridSize,
    MalformedXmlError,
    UnsupportedBlueprintError,
)
from se2cad.preflight import (
    CatalogOutcome,
    compute_conversion_preflight_from_path,
    compute_conversion_preflight_from_xml,
)
from se2cad.preflight.__main__ import main as preflight_main
from se2cad.statistics import NamedCount

PREFLIGHT_ROOT = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "preflight"
UNSUPPORTED_SUBTYPE = "LargeBlockUnsupportedProbe"
UNKNOWN_SUBTYPE = "NotACatalogSubtype"


def _document(
    blocks: str,
    *,
    identity: str = "preflight-test",
    grid_name: str = "preflight-grid",
    display_name: str = "preflight-test",
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
    color_xml: str = "",
) -> str:
    parts = [
        "            <MyObjectBuilder_CubeBlock>",
        f"              <SubtypeName>{subtype}</SubtypeName>",
    ]
    if min_xml:
        parts.append(f"              {min_xml}")
    if orientation_xml:
        parts.append(f"              {orientation_xml}")
    if color_xml:
        parts.append(f"              {color_xml}")
    parts.append("            </MyObjectBuilder_CubeBlock>")
    return "\n".join(parts)


def _unsupported_catalog() -> DefinitionCatalog:
    default = load_default_catalog()
    extra = CatalogEntry(
        subtype_id=UNSUPPORTED_SUBTYPE,
        observed=ObservedDefinition(
            type_id="CubeBlock",
            cube_size="Large",
            size=CellSize(1, 1, 1),
            block_topology="Cube",
            cube_topology="Box",
        ),
        geometry_id="large_unsupported_probe",
        recipe_kind=RecipeKind.UNSUPPORTED,
        support_status=SupportStatus.UNSUPPORTED,
    )
    return DefinitionCatalog(entries=default.entries + (extra,))


class PreflightSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()
        cls.mixed_catalog = _unsupported_catalog()

    def test_single_supported_block_is_clean(self) -> None:
        report = compute_conversion_preflight_from_xml(
            _document(_block()), catalog=self.catalog, source="single-supported"
        )
        self.assertEqual(report.identity_subtype, "preflight-test")
        self.assertEqual(report.display_name, "preflight-test")
        self.assertEqual(report.grid_display_name, "preflight-grid")
        self.assertEqual(report.grid_size, GridSize.LARGE)
        self.assertEqual(report.block_count, 1)
        self.assertEqual(report.supported_count, 1)
        self.assertEqual(report.unsupported_count, 0)
        self.assertEqual(report.unknown_count, 0)
        self.assertTrue(report.all_supported)
        self.assertEqual(len(report.blocks), 1)
        block = report.blocks[0]
        self.assertEqual(block.source_index, 0)
        self.assertEqual(block.subtype_id, "LargeBlockArmorBlock")
        self.assertEqual((block.grid_min.x, block.grid_min.y, block.grid_min.z), (0, 0, 0))
        self.assertEqual(block.catalog_outcome, CatalogOutcome.SUPPORTED)
        self.assertEqual(block.geometry_id, "large_armor_block")
        self.assertEqual(block.geometry_support, SupportStatus.SUPPORTED)
        self.assertEqual(block.appearance_support, AppearanceSupport.DEFAULT)

    def test_unknown_subtype_is_not_aliased_or_dropped(self) -> None:
        xml = _document(
            _block()
            + "\n"
            + _block(UNKNOWN_SUBTYPE, min_xml='<Min x="1" y="0" z="0" />')
            + "\n"
            + _block(UNKNOWN_SUBTYPE, min_xml='<Min x="2" y="0" z="0" />')
        )
        report = compute_conversion_preflight_from_xml(
            xml, catalog=self.catalog, source="unknown-subtype"
        )
        self.assertEqual(report.block_count, 3)
        self.assertEqual(len(report.blocks), 3)
        self.assertEqual(report.supported_count, 1)
        self.assertEqual(report.unknown_count, 2)
        self.assertEqual(report.unsupported_count, 0)
        self.assertFalse(report.all_supported)
        self.assertEqual(
            report.unknown_subtype_counts,
            (NamedCount(UNKNOWN_SUBTYPE, 2),),
        )
        unknown = report.blocks[1]
        self.assertEqual(unknown.source_index, 1)
        self.assertEqual(unknown.subtype_id, UNKNOWN_SUBTYPE)
        self.assertEqual((unknown.grid_min.x, unknown.grid_min.y, unknown.grid_min.z), (1, 0, 0))
        self.assertEqual(unknown.catalog_outcome, CatalogOutcome.UNKNOWN)
        self.assertIsNone(unknown.geometry_id)
        self.assertIsNone(unknown.geometry_support)
        self.assertNotEqual(unknown.geometry_id, "large_armor_block")
        self.assertNotEqual(unknown.catalog_outcome, CatalogOutcome.SUPPORTED)
        self.assertNotEqual(unknown.catalog_outcome, CatalogOutcome.UNSUPPORTED)

    def test_catalog_unsupported_is_distinct_from_unknown(self) -> None:
        xml = _document(
            _block(UNSUPPORTED_SUBTYPE, min_xml='<Min x="-1" y="2" z="-3" />')
        )
        report = compute_conversion_preflight_from_xml(
            xml, catalog=self.mixed_catalog, source="catalog-unsupported"
        )
        self.assertEqual(report.block_count, 1)
        self.assertEqual(report.supported_count, 0)
        self.assertEqual(report.unsupported_count, 1)
        self.assertEqual(report.unknown_count, 0)
        self.assertFalse(report.all_supported)
        self.assertEqual(
            report.unsupported_subtype_counts,
            (NamedCount(UNSUPPORTED_SUBTYPE, 1),),
        )
        block = report.blocks[0]
        self.assertEqual(block.catalog_outcome, CatalogOutcome.UNSUPPORTED)
        self.assertEqual(block.geometry_id, "large_unsupported_probe")
        self.assertEqual(block.geometry_support, SupportStatus.UNSUPPORTED)
        self.assertNotEqual(block.geometry_id, "large_armor_block")
        self.assertEqual((block.grid_min.x, block.grid_min.y, block.grid_min.z), (-1, 2, -3))

    def test_mixed_document_keeps_every_block_and_outcome(self) -> None:
        xml = _document(
            "\n".join(
                [
                    _block(min_xml='<Min x="0" y="0" z="0" />'),
                    _block(UNKNOWN_SUBTYPE, min_xml='<Min x="1" y="0" z="0" />'),
                    _block(UNSUPPORTED_SUBTYPE, min_xml='<Min x="2" y="0" z="0" />'),
                    _block(
                        "LargeBlockArmorSlope",
                        min_xml='<Min x="3" y="0" z="0" />',
                        orientation_xml='<BlockOrientation Forward="Down" Up="Forward" />',
                    ),
                ]
            )
        )
        report = compute_conversion_preflight_from_xml(
            xml, catalog=self.mixed_catalog, source="mixed-document"
        )
        self.assertEqual(report.block_count, 4)
        self.assertEqual(len(report.blocks), 4)
        self.assertEqual(report.supported_count, 2)
        self.assertEqual(report.unknown_count, 1)
        self.assertEqual(report.unsupported_count, 1)
        self.assertFalse(report.all_supported)
        outcomes = tuple(block.catalog_outcome for block in report.blocks)
        self.assertEqual(
            outcomes,
            (
                CatalogOutcome.SUPPORTED,
                CatalogOutcome.UNKNOWN,
                CatalogOutcome.UNSUPPORTED,
                CatalogOutcome.SUPPORTED,
            ),
        )
        self.assertEqual(
            [block.source_index for block in report.blocks],
            [0, 1, 2, 3],
        )
        self.assertEqual(report.blocks[3].subtype_id, "LargeBlockArmorSlope")
        self.assertEqual(report.blocks[3].geometry_id, "large_armor_slope")

    def test_geometry_and_appearance_flags_are_independent(self) -> None:
        xml = _document(
            "\n".join(
                [
                    _block(
                        color_xml='<ColorMaskHSV x="1" y="0" z="0" />',
                    ),
                    _block(
                        UNKNOWN_SUBTYPE,
                        min_xml='<Min x="1" y="0" z="0" />',
                        color_xml='<ColorMaskHSV x="0" y="0" z="1" />',
                    ),
                    _block(
                        UNSUPPORTED_SUBTYPE,
                        min_xml='<Min x="2" y="0" z="0" />',
                    ),
                ]
            )
        )
        report = compute_conversion_preflight_from_xml(
            xml, catalog=self.mixed_catalog, source="independent-flags"
        )
        supported, unknown, unsupported = report.blocks
        self.assertEqual(supported.catalog_outcome, CatalogOutcome.SUPPORTED)
        self.assertEqual(supported.geometry_support, SupportStatus.SUPPORTED)
        self.assertEqual(supported.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(unknown.catalog_outcome, CatalogOutcome.UNKNOWN)
        self.assertIsNone(unknown.geometry_support)
        self.assertEqual(unknown.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(unsupported.catalog_outcome, CatalogOutcome.UNSUPPORTED)
        self.assertEqual(unsupported.geometry_support, SupportStatus.UNSUPPORTED)
        self.assertEqual(unsupported.appearance_support, AppearanceSupport.DEFAULT)

    def test_empty_cube_blocks_are_vacuously_all_supported(self) -> None:
        report = compute_conversion_preflight_from_xml(
            _document(""), catalog=self.catalog, source="empty-blocks"
        )
        self.assertEqual(report.block_count, 0)
        self.assertEqual(report.blocks, ())
        self.assertTrue(report.all_supported)
        self.assertEqual(report.supported_count, 0)
        self.assertEqual(report.unknown_count, 0)
        self.assertEqual(report.unsupported_count, 0)

    def test_malformed_and_unsupported_documents_fail_closed_via_parser(self) -> None:
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
            compute_conversion_preflight_from_xml(zero_grid, source="zero-grid")
        with self.assertRaises(UnsupportedBlueprintError):
            compute_conversion_preflight_from_xml(
                _document(_block(), size="Small"), source="small-grid"
            )
        with self.assertRaises(MalformedXmlError):
            compute_conversion_preflight_from_xml(
                "<Definitions><ShipBlueprints>", source="malformed"
            )

    def test_from_path_does_not_store_the_path(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )
        report = compute_conversion_preflight_from_path(fixture, self.catalog)
        self.assertEqual(report.identity_subtype, "se2cad-test1")
        dumped = repr(report)
        self.assertNotIn(str(fixture), dumped)
        self.assertNotIn("C:\\", dumped.replace("\\\\", "\\"))

    def test_missing_path_is_a_parser_error(self) -> None:
        from se2cad.parser import BlueprintParseError

        with self.assertRaises(BlueprintParseError):
            compute_conversion_preflight_from_path(
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
            code = preflight_main([str(fixture)])
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("identity_subtype=se2cad-test1", text)
        self.assertIn("display_name=\\ue030Kolyma", text)
        self.assertNotIn("\ue030", text)
        self.assertIn("all_supported=true", text)
        self.assertIn("conversion_performed=false", text)

    def test_operator_entry_exit_zero_is_not_conversion_success(self) -> None:
        xml = _document(_block(UNKNOWN_SUBTYPE))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unknown.sbc"
            path.write_text(xml, encoding="utf-8")
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                code = preflight_main([str(path)])
            self.assertEqual(code, 0)
            text = stdout.getvalue()
            self.assertIn("all_supported=false", text)
            self.assertIn("unknown_count=1", text)
            self.assertIn("conversion_performed=false", text)
            self.assertIn(f"catalog_outcome={CatalogOutcome.UNKNOWN.value}", text)
            self.assertNotIn(str(path), text)

    def test_operator_entry_usage_and_parse_failure(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(preflight_main([]), 2)
        self.assertIn("usage: python -m se2cad.preflight", stdout.getvalue())
        stdout = io.StringIO()
        missing = Path(__file__).resolve().parent / "no-such-blueprint.sbc"
        with patch("sys.stdout", stdout):
            self.assertEqual(preflight_main([str(missing)]), 2)
        self.assertIn("not a file", stdout.getvalue())


class PreflightNeutralityTests(unittest.TestCase):
    def test_preflight_source_has_no_backend_or_pitch_literals(self) -> None:
        forbidden_text = (
            "win32com",
            "pythoncom",
            ".sldprt",
            ".sldasm",
            ".mwm",
            "/home/",
            "C:\\",
        )
        for path in sorted(PREFLIGHT_ROOT.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for token in forbidden_text:
                self.assertNotIn(token.lower(), lowered, msg=f"{path.name} mentions {token}")
            self.assertNotRegex(text, r"\b2500\b", msg=f"{path.name} copies 2500")
            self.assertNotRegex(text, r"\b24\b", msg=f"{path.name} bakes fixture count 24")

    def test_preflight_imports_are_stdlib_plus_parser_catalog_statistics(self) -> None:
        allowed_se2cad = {
            "se2cad.catalog",
            "se2cad.catalog.model",
            "se2cad.parser",
            "se2cad.parser.model",
            "se2cad.preflight.compute",
            "se2cad.preflight.model",
            "se2cad.statistics.model",
            "se2cad.vanilla.resolve",
        }
        for path in sorted(PREFLIGHT_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("se2cad."):
                        self.assertIn(node.module, allowed_se2cad, msg=path.name)

    def test_compute_does_not_require_ir_or_solidworks(self) -> None:
        parsed_source = (PREFLIGHT_ROOT / "compute.py").read_text(encoding="utf-8")
        self.assertNotRegex(parsed_source, r"se2cad\.ir")
        self.assertNotRegex(parsed_source, r"se2cad\.solidworks")
        self.assertNotRegex(parsed_source, r"se2cad\.library")
        self.assertNotRegex(parsed_source, r"se2cad\.discovery")


if __name__ == "__main__":
    unittest.main()
