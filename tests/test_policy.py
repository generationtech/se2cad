"""CAD-neutral strict and permissive conversion policy."""

from __future__ import annotations

import ast
import inspect
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    FILLER_GEOMETRY_ID,
    CatalogEntry,
    CellSize,
    DefinitionCatalog,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
    load_default_catalog,
)
from se2cad.library import (
    FILLER_HALF_EXTENT_MM,
    FILLER_OBSERVED_TOPOLOGY,
    filler_library_record,
    lookup_recipe,
)
from se2cad.parser import (
    AppearanceSupport,
    Direction,
    MalformedXmlError,
    UnsupportedBlueprintError,
)
from se2cad.policy import (
    ConversionPolicy,
    ConversionRefusedError,
    UnknownConversionPolicyError,
    convert_blueprint,
    convert_blueprint_from_path,
    convert_blueprint_from_xml,
)
from se2cad.policy.__main__ import main as policy_main
from se2cad.preflight import compute_conversion_preflight_from_xml
from se2cad.solidworks.artifacts import logical_part_filename
from se2cad.transform import cell_center_mm, rotation_from_forward_up

POLICY_ROOT = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "policy"
UNSUPPORTED_SUBTYPE = "LargeBlockUnsupportedProbe"
UNKNOWN_SUBTYPE = "NotACatalogSubtype"


def _document(
    blocks: str,
    *,
    identity: str = "policy-test",
    grid_name: str = "policy-grid",
    display_name: str = "policy-test",
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


class FillerIdentityTests(unittest.TestCase):
    def test_filler_is_distinct_from_supported_armor(self) -> None:
        self.assertEqual(FILLER_GEOMETRY_ID, "se2cad_unknown_filler")
        self.assertNotEqual(FILLER_GEOMETRY_ID, "large_armor_block")
        catalog = load_default_catalog()
        self.assertTrue(
            all(entry.geometry_id != FILLER_GEOMETRY_ID for entry in catalog.entries)
        )
        self.assertTrue(
            all(entry.subtype_id != FILLER_GEOMETRY_ID for entry in catalog.entries)
        )
        recipe = lookup_recipe(FILLER_GEOMETRY_ID)
        armor = lookup_recipe("large_armor_block")
        self.assertEqual(recipe.geometry_id, FILLER_GEOMETRY_ID)
        self.assertNotEqual(recipe.vertices_mm, armor.vertices_mm)
        self.assertLess(
            recipe.validation.volume_times_6_mm3,
            armor.validation.volume_times_6_mm3,
        )
        self.assertEqual(recipe.orientation.observed_cube_topology, FILLER_OBSERVED_TOPOLOGY)
        self.assertNotIn(FILLER_OBSERVED_TOPOLOGY, ("Box", "Slope", "Corner", "InvCorner"))
        half = FILLER_HALF_EXTENT_MM
        self.assertEqual(recipe.construction.min_mm, (-half, -half, -half))
        record = filler_library_record()
        self.assertEqual(record.geometry_id, FILLER_GEOMETRY_ID)
        self.assertIsNone(record.placement.part_locator)
        self.assertEqual(record.placement.additional_offset_mm, (0, 0, 0))
        self.assertEqual(
            logical_part_filename(FILLER_GEOMETRY_ID),
            "se2cad_unknown_filler.SLDPRT",
        )
        self.assertNotEqual(
            logical_part_filename(FILLER_GEOMETRY_ID),
            logical_part_filename("large_armor_block"),
        )


class StrictPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()
        cls.mixed_catalog = _unsupported_catalog()

    def test_default_policy_is_strict(self) -> None:
        signature = inspect.signature(convert_blueprint)
        self.assertEqual(
            signature.parameters["policy"].default, ConversionPolicy.STRICT
        )
        xml = _document(_block(UNKNOWN_SUBTYPE))
        with self.assertRaises(ConversionRefusedError) as ctx:
            convert_blueprint_from_xml(xml, catalog=self.catalog, source="default-strict")
        self.assertIs(ctx.exception.preflight.all_supported, False)
        self.assertEqual(ctx.exception.preflight.unknown_count, 1)
        self.assertIn("unknown_count=1", str(ctx.exception))
        self.assertIn(UNKNOWN_SUBTYPE, str(ctx.exception))

    def test_strict_fails_on_one_unknown_and_does_not_emit_ir(self) -> None:
        xml = _document(
            _block()
            + "\n"
            + _block(UNKNOWN_SUBTYPE, min_xml='<Min x="1" y="0" z="0" />')
        )
        with self.assertRaises(ConversionRefusedError) as ctx:
            convert_blueprint_from_xml(
                xml,
                catalog=self.catalog,
                policy=ConversionPolicy.STRICT,
                source="one-unknown",
            )
        report = ctx.exception.preflight
        self.assertEqual(report.block_count, 2)
        self.assertEqual(report.unknown_count, 1)
        self.assertEqual(report.supported_count, 1)
        self.assertFalse(report.all_supported)
        self.assertIn("strict conversion refused", str(ctx.exception))

    def test_strict_fails_on_catalog_unsupported(self) -> None:
        xml = _document(_block(UNSUPPORTED_SUBTYPE))
        with self.assertRaises(ConversionRefusedError) as ctx:
            convert_blueprint_from_xml(
                xml,
                catalog=self.mixed_catalog,
                policy=ConversionPolicy.STRICT,
                source="unsupported",
            )
        self.assertEqual(ctx.exception.preflight.unsupported_count, 1)
        self.assertEqual(ctx.exception.preflight.unknown_count, 0)
        self.assertIn(UNSUPPORTED_SUBTYPE, str(ctx.exception))

    def test_strict_all_supported_matches_catalog_resolve(self) -> None:
        from se2cad.ir import build_canonical_blueprint
        from se2cad.parser import parse_blueprint_xml

        xml = _document(_block())
        parsed = parse_blueprint_xml(xml, source="all-supported")
        result = convert_blueprint(parsed, self.catalog, ConversionPolicy.STRICT)
        expected = build_canonical_blueprint(parsed, self.catalog)
        self.assertEqual(result.ir, expected)
        self.assertEqual(result.filler_count, 0)
        self.assertTrue(result.preflight.all_supported)

    def test_unknown_policy_token_fails_closed(self) -> None:
        with self.assertRaises(UnknownConversionPolicyError):
            convert_blueprint_from_xml(
                _document(_block()),
                catalog=self.catalog,
                policy="maybe",  # type: ignore[arg-type]
                source="bad-policy",
            )


class PermissivePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()
        cls.mixed_catalog = _unsupported_catalog()

    def test_permissive_emits_n_ir_instances_for_n_blocks(self) -> None:
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
        preflight = compute_conversion_preflight_from_xml(
            xml, catalog=self.mixed_catalog, source="mixed-n"
        )
        result = convert_blueprint_from_xml(
            xml,
            catalog=self.mixed_catalog,
            policy=ConversionPolicy.PERMISSIVE,
            source="mixed-n",
        )
        self.assertEqual(result.ir.grid.block_count, 4)
        self.assertEqual(result.ir.grid.block_count, preflight.block_count)
        self.assertEqual(len(result.ir.grid.blocks), 4)
        self.assertEqual(result.filler_count, 2)
        self.assertEqual(
            result.filler_count, preflight.unknown_count + preflight.unsupported_count
        )
        self.assertEqual(result.preflight, preflight)
        subtypes = [block.subtype_id for block in result.ir.grid.blocks]
        self.assertEqual(
            subtypes,
            [
                "LargeBlockArmorBlock",
                UNKNOWN_SUBTYPE,
                UNSUPPORTED_SUBTYPE,
                "LargeBlockArmorSlope",
            ],
        )
        self.assertEqual(
            [block.source_index for block in result.ir.grid.blocks],
            [0, 1, 2, 3],
        )

    def test_filler_identity_and_support_do_not_claim_armor(self) -> None:
        xml = _document(
            _block(UNKNOWN_SUBTYPE, min_xml='<Min x="-1" y="2" z="-3" />')
        )
        result = convert_blueprint_from_xml(
            xml,
            catalog=self.catalog,
            policy=ConversionPolicy.PERMISSIVE,
            source="filler-identity",
        )
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.subtype_id, UNKNOWN_SUBTYPE)
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertNotEqual(block.geometry_id, "large_armor_block")
        self.assertEqual(block.support_status, SupportStatus.UNSUPPORTED)
        self.assertEqual(block.recipe_kind, RecipeKind.UNSUPPORTED)
        self.assertEqual(result.filler_count, 1)

    def test_permissive_pose_matches_transform_engine(self) -> None:
        xml = _document(
            _block(
                UNKNOWN_SUBTYPE,
                min_xml='<Min x="-1" y="2" z="-3" />',
                orientation_xml='<BlockOrientation Forward="Down" Up="Forward" />',
            )
        )
        result = convert_blueprint_from_xml(
            xml,
            catalog=self.catalog,
            policy=ConversionPolicy.PERMISSIVE,
            source="filler-pose",
        )
        block = result.ir.grid.blocks[0]
        catalog = load_default_catalog()
        self.assertEqual(
            block.position_mm,
            cell_center_mm(block.grid_min, catalog.large_grid_cell_pitch_mm),
        )
        self.assertEqual(
            block.rotation,
            rotation_from_forward_up(Direction.DOWN, Direction.FORWARD),
        )
        self.assertEqual((block.grid_min.x, block.grid_min.y, block.grid_min.z), (-1, 2, -3))
        self.assertEqual(block.forward, Direction.DOWN)
        self.assertEqual(block.up, Direction.FORWARD)

    def test_appearance_is_preserved_on_filler(self) -> None:
        xml = _document(
            _block(
                UNKNOWN_SUBTYPE,
                color_xml='<ColorMaskHSV x="1" y="0" z="0" />',
            )
        )
        result = convert_blueprint_from_xml(
            xml,
            catalog=self.catalog,
            policy=ConversionPolicy.PERMISSIVE,
            source="filler-color",
        )
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.appearance_support, AppearanceSupport.EXPLICIT)
        self.assertEqual(block.color_mask_hsv.h, 1.0)
        self.assertTrue(block.color_serialized)
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(block.support_status, SupportStatus.UNSUPPORTED)

    def test_catalog_unsupported_uses_filler_not_catalog_geometry(self) -> None:
        xml = _document(_block(UNSUPPORTED_SUBTYPE))
        result = convert_blueprint_from_xml(
            xml,
            catalog=self.mixed_catalog,
            policy=ConversionPolicy.PERMISSIVE,
            source="unsupported-filler",
        )
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.subtype_id, UNSUPPORTED_SUBTYPE)
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertNotEqual(block.geometry_id, "large_unsupported_probe")
        self.assertEqual(block.support_status, SupportStatus.UNSUPPORTED)

    def test_malformed_documents_fail_closed_via_parser(self) -> None:
        with self.assertRaises(UnsupportedBlueprintError):
            convert_blueprint_from_xml(
                _document(_block(), size="Small"),
                policy=ConversionPolicy.PERMISSIVE,
                source="small-grid",
            )
        with self.assertRaises(MalformedXmlError):
            convert_blueprint_from_xml(
                "<Definitions><ShipBlueprints>",
                policy=ConversionPolicy.PERMISSIVE,
                source="malformed",
            )


class PolicyOperatorTests(unittest.TestCase):
    def test_operator_strict_success_and_refusal(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(policy_main([str(fixture)]), 0)
        text = stdout.getvalue()
        self.assertIn("policy=strict", text)
        self.assertIn("conversion_performed=true", text)
        self.assertIn("filler_count=0", text)
        self.assertIn("ir_block_count=24", text)
        self.assertNotIn(str(fixture), text)

        xml = _document(_block(UNKNOWN_SUBTYPE))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unknown.sbc"
            path.write_text(xml, encoding="utf-8")
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                self.assertEqual(policy_main([str(path)]), 2)
            refused = stdout.getvalue()
            self.assertIn("all_supported=false", refused)
            self.assertIn("unknown_count=1", refused)
            self.assertIn("policy=strict", refused)
            self.assertIn("conversion_performed=false", refused)
            self.assertNotIn(str(path), refused)
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                self.assertEqual(
                    policy_main([str(path), "--policy", "permissive"]), 0
                )
            permitted = stdout.getvalue()
            self.assertIn("policy=permissive", permitted)
            self.assertIn("conversion_performed=true", permitted)
            self.assertIn("filler_count=1", permitted)
            self.assertIn(f"geometry_id={FILLER_GEOMETRY_ID}", permitted)
            self.assertIn(f"support_status={SupportStatus.UNSUPPORTED.value}", permitted)
            self.assertNotIn(str(path), permitted)

    def test_operator_usage_and_unknown_policy_flag(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(policy_main([]), 2)
        self.assertIn("usage: python -m se2cad.policy", stdout.getvalue())
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(
                policy_main(["blueprint.sbc", "--policy", "maybe"]), 2
            )
        self.assertIn("usage: python -m se2cad.policy", stdout.getvalue())

    def test_from_path_does_not_store_the_path(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
        )
        result = convert_blueprint_from_path(fixture)
        dumped = repr(result.preflight)
        self.assertNotIn(str(fixture), dumped)
        self.assertNotIn("C:\\", dumped.replace("\\\\", "\\"))
        self.assertFalse(hasattr(result, "blueprint_path"))
        self.assertFalse(hasattr(result, "path"))


class PolicyNeutralityTests(unittest.TestCase):
    def test_policy_source_has_no_backend_or_pitch_literals(self) -> None:
        forbidden_text = (
            "win32com",
            "pythoncom",
            ".sldprt",
            ".sldasm",
            ".mwm",
            "/home/",
            "C:\\",
        )
        for path in sorted(POLICY_ROOT.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for token in forbidden_text:
                self.assertNotIn(token.lower(), lowered, msg=f"{path.name} mentions {token}")
            self.assertNotRegex(text, r"\b2500\b", msg=f"{path.name} copies 2500")

    def test_policy_imports_stay_cad_neutral(self) -> None:
        allowed_se2cad = {
            "se2cad.catalog",
            "se2cad.catalog.constants",
            "se2cad.catalog.model",
            "se2cad.ir.convert",
            "se2cad.ir.model",
            "se2cad.parser",
            "se2cad.parser.model",
            "se2cad.policy.convert",
            "se2cad.policy.errors",
            "se2cad.policy.model",
            "se2cad.preflight",
            "se2cad.preflight.model",
            "se2cad.statistics.model",
        }
        for path in sorted(POLICY_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("se2cad."):
                        self.assertIn(node.module, allowed_se2cad, msg=path.name)

    def test_convert_does_not_require_solidworks_or_library(self) -> None:
        parsed_source = (POLICY_ROOT / "convert.py").read_text(encoding="utf-8")
        self.assertNotRegex(parsed_source, r"se2cad\.solidworks")
        self.assertNotRegex(parsed_source, r"se2cad\.library")
        self.assertNotRegex(parsed_source, r"se2cad\.discovery")


if __name__ == "__main__":
    unittest.main()
