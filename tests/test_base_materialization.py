"""Ordinary tests for demand-driven qualified base-part materialization."""

from __future__ import annotations

import ast
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    FILLER_GEOMETRY_ID,
    SupportStatus,
    UnknownSubtypeError,
    expand_catalog_identities,
    geometry_id_for_subtype,
    load_default_catalog,
    stamp_automatable_remainder,
)
from se2cad.ir import build_canonical_blueprint, component_name_from_block
from se2cad.library import (
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_OFF,
    all_library_records,
    chamfer_treatment,
    filler_library_record,
    original_library_geometry_ids,
    representative_automatable_geometry_ids,
)
from se2cad.parser import parse_blueprint
from se2cad.policy import ConversionPolicy, ConversionRefusedError, convert_blueprint
from se2cad.solidworks import (
    GeneratedRootError,
    MissingCanonicalPartError,
    SolidWorksComError,
    artifact_path_for,
    canonical_geometry_ids,
    contained_destination,
    demanded_untreated_geometry_ids,
    has_qualified_untreated_builder,
    logical_part_filename,
    missing_untreated_geometry_ids,
    placements_from_ir,
)
from se2cad.solidworks.artifacts import logical_treated_part_filename
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.generate import generate_canonical_parts
from se2cad.solidworks.materialize import (
    ensure_untreated_canonical_parts,
    materialize_required_parts,
)
from se2cad.solidworks.__main__ import _treatment_from_argv


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "se2cad"
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
HIDDEN_ROUND_ALIASES = (
    "LargeRoundArmor_Slope",
    "LargeRoundArmor_Corner",
    "LargeRoundArmor_InvCorner",
)
_MATERIALIZE_AND_ASSEMBLE = (
    SRC_ROOT / "solidworks" / "materialize.py",
    SRC_ROOT / "solidworks" / "assemble.py",
    SRC_ROOT / "solidworks" / "generate.py",
    SRC_ROOT / "solidworks" / "placement.py",
)


def _fixture_ir():
    return build_canonical_blueprint(parse_blueprint(FIXTURE_PATH), load_default_catalog())


def _one_block_ir(subtype: str = "LargeBlockArmorBlock", identity: str = "se2cad-base-one"):
    xml = f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "one.sbc"
        path.write_text(xml, encoding="utf-8")
        parsed = parse_blueprint(path)
    return convert_blueprint(parsed, load_default_catalog()).ir


def _two_geometry_ir():
    xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-base-two" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorSlope</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "two.sbc"
        path.write_text(xml, encoding="utf-8")
        parsed = parse_blueprint(path)
    return convert_blueprint(parsed, load_default_catalog()).ir


def _mixed_unknown_xml(identity: str = "se2cad-base-mixed") -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>NotACatalogSubtype</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _mixed_unknown_parsed():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mixed.sbc"
        path.write_text(_mixed_unknown_xml(), encoding="utf-8")
        return parse_blueprint(path)


def _config(root: Path) -> SolidWorksBackendConfig:
    return SolidWorksBackendConfig(
        generated_root=root.resolve(),
        part_template=None,
        visible=False,
        source="test",
    )


def _fake_generate(config, treatment=None, geometry_ids=None):
    request = EDGE_TREATMENT_OFF if treatment is None else treatment
    requested = canonical_geometry_ids() if geometry_ids is None else geometry_ids
    for geometry_id in requested:
        if request.enabled:
            name = logical_treated_part_filename(geometry_id, request)
        else:
            name = logical_part_filename(geometry_id)
        (config.generated_root / name).write_bytes(b"generated")
    return ()


class QualifiedBuilderTests(unittest.TestCase):
    def test_current_library_and_filler_have_builders(self) -> None:
        for record in all_library_records():
            self.assertTrue(has_qualified_untreated_builder(record.geometry_id))
        self.assertTrue(has_qualified_untreated_builder(FILLER_GEOMETRY_ID))
        self.assertEqual(filler_library_record().geometry_id, FILLER_GEOMETRY_ID)

    def test_unknown_and_hidden_round_aliases_have_no_builder(self) -> None:
        self.assertFalse(has_qualified_untreated_builder("not_a_canonical_part"))
        catalog = load_default_catalog()
        for subtype in HIDDEN_ROUND_ALIASES:
            with self.subTest(subtype=subtype):
                with self.assertRaises(UnknownSubtypeError):
                    catalog.lookup(subtype)
                derived = geometry_id_for_subtype(subtype)
                self.assertFalse(has_qualified_untreated_builder(derived))
                self.assertNotEqual(derived, "large_armor_slope")
                self.assertNotEqual(derived, "large_armor_corner")
                self.assertNotEqual(derived, "large_armor_corner_inv")


class DemandAndReuseTests(unittest.TestCase):
    def test_missing_supported_part_is_generated_once(self) -> None:
        ir = _one_block_ir()
        demanded = demanded_untreated_geometry_ids(ir)
        self.assertEqual(demanded, ("large_armor_block",))
        self.assertEqual(len(ir.grid.blocks), 2)
        calls: list[tuple[object, tuple[str, ...] | None]] = []

        def generate(config, treatment=None, geometry_ids=None):
            calls.append((treatment, geometry_ids))
            return _fake_generate(config, treatment, geometry_ids)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            self.assertEqual(
                missing_untreated_geometry_ids(root, demanded), demanded
            )
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=generate,
            ):
                first = ensure_untreated_canonical_parts(config, demanded + demanded)
                second = ensure_untreated_canonical_parts(config, demanded)
            self.assertEqual(first.generated, ("large_armor_block",))
            self.assertEqual(first.reused, ())
            self.assertEqual(second.generated, ())
            self.assertEqual(second.reused, ("large_armor_block",))
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], EDGE_TREATMENT_OFF)
            self.assertEqual(calls[0][1], ("large_armor_block",))
            self.assertTrue((root / "large_armor_block.SLDPRT").is_file())

    def test_existing_supported_part_is_not_regenerated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "large_armor_block.SLDPRT"
            path.write_bytes(b"keep-me")
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=AssertionError("must not regenerate"),
            ):
                result = ensure_untreated_canonical_parts(
                    _config(root), ("large_armor_block",)
                )
            self.assertEqual(result.reused, ("large_armor_block",))
            self.assertEqual(result.generated, ())
            self.assertEqual(path.read_bytes(), b"keep-me")

    def test_only_required_supported_ids_are_generated(self) -> None:
        ir = _two_geometry_ir()
        demanded = demanded_untreated_geometry_ids(ir)
        self.assertEqual(demanded, ("large_armor_block", "large_armor_slope"))
        for extra in representative_automatable_geometry_ids():
            self.assertNotIn(extra, demanded)
        calls: list[tuple[str, ...] | None] = []

        def generate(config, treatment=None, geometry_ids=None):
            calls.append(geometry_ids)
            return _fake_generate(config, treatment, geometry_ids)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large_armor_block.SLDPRT").write_bytes(b"existing")
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=generate,
            ):
                result = materialize_required_parts(ir, _config(root), EDGE_TREATMENT_OFF)
            self.assertEqual(result.untreated.reused, ("large_armor_block",))
            self.assertEqual(result.untreated.generated, ("large_armor_slope",))
            self.assertEqual(result.treated.generated, ())
            self.assertEqual(calls, [("large_armor_slope",)])
            self.assertTrue((root / "large_armor_slope.SLDPRT").is_file())
            self.assertFalse((root / "large_armor_corner.SLDPRT").exists())
            self.assertFalse(
                (root / "large_heavy_block_armor_block.SLDPRT").exists()
            )
            self.assertFalse(any(root.glob("*_chamfer_*.SLDPRT")))

    def test_second_materialization_reuses_generated_bases(self) -> None:
        ir = _two_geometry_ir()
        with tempfile.TemporaryDirectory() as tmp:
            config = _config(Path(tmp))
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ):
                first = materialize_required_parts(ir, config, EDGE_TREATMENT_OFF)
                second = materialize_required_parts(ir, config, EDGE_TREATMENT_OFF)
            self.assertEqual(
                first.untreated.generated,
                ("large_armor_block", "large_armor_slope"),
            )
            self.assertEqual(second.untreated.generated, ())
            self.assertEqual(
                second.untreated.reused,
                ("large_armor_block", "large_armor_slope"),
            )


class FailClosedAndPolicyTests(unittest.TestCase):
    def test_qualified_builder_generation_failure_is_not_filler(self) -> None:
        ir = _one_block_ir()
        parsed = _mixed_unknown_parsed()
        catalog = load_default_catalog()
        with tempfile.TemporaryDirectory() as tmp:
            config = _config(Path(tmp))
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=SolidWorksComError("supported generation failed"),
            ):
                with self.assertRaises(SolidWorksComError) as ctx:
                    materialize_required_parts(ir, config, EDGE_TREATMENT_OFF)
            self.assertIn("supported generation failed", str(ctx.exception))
            self.assertFalse((Path(tmp) / "se2cad_unknown_filler.SLDPRT").exists())
            with self.assertRaises(ConversionRefusedError):
                convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)
            permitted = convert_blueprint(
                parsed, catalog, ConversionPolicy.PERMISSIVE
            )
            self.assertEqual(permitted.filler_count, 1)
            self.assertEqual(
                permitted.ir.grid.blocks[1].geometry_id, FILLER_GEOMETRY_ID
            )
            self.assertEqual(
                permitted.ir.grid.blocks[1].support_status, SupportStatus.UNSUPPORTED
            )

    def test_generation_without_usable_file_fails_closed(self) -> None:
        def generate(config, treatment=None, geometry_ids=None):
            return ()

        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=generate,
            ):
                with self.assertRaises(MissingCanonicalPartError) as ctx:
                    ensure_untreated_canonical_parts(
                        _config(Path(tmp)), ("large_armor_block",)
                    )
            self.assertIn("produced no usable canonical part", str(ctx.exception))
            self.assertFalse((Path(tmp) / "se2cad_unknown_filler.SLDPRT").exists())

    def test_missing_without_builder_does_not_improvise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MissingCanonicalPartError) as ctx:
                ensure_untreated_canonical_parts(
                    _config(Path(tmp)), ("not_a_canonical_part",)
                )
            self.assertIn("no qualified untreated builder", str(ctx.exception))
            self.assertFalse(any(Path(tmp).iterdir()))

    def test_hidden_round_aliases_are_not_planar_geometry(self) -> None:
        parsed_xml = f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="se2cad-round-alias" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{HIDDEN_ROUND_ALIASES[0]}</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        catalog = load_default_catalog()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alias.sbc"
            path.write_text(parsed_xml, encoding="utf-8")
            parsed = parse_blueprint(path)
        with self.assertRaises(ConversionRefusedError):
            convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)
        permitted = convert_blueprint(parsed, catalog, ConversionPolicy.PERMISSIVE)
        block = permitted.ir.grid.blocks[0]
        self.assertEqual(block.subtype_id, HIDDEN_ROUND_ALIASES[0])
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertNotEqual(block.geometry_id, "large_armor_slope")
        placement = placements_from_ir(permitted.ir)[0]
        self.assertEqual(placement.part_filename, "se2cad_unknown_filler.SLDPRT")


class CatalogAndRuntimeBoundaryTests(unittest.TestCase):
    def test_catalog_support_is_unchanged(self) -> None:
        catalog = load_default_catalog()
        self.assertEqual(len(catalog.entries), 9)
        self.assertEqual(stamp_automatable_remainder(catalog), ())
        supported = {
            entry.geometry_id
            for entry in catalog.entries
            if entry.support_status is SupportStatus.SUPPORTED
        }
        self.assertEqual(
            supported,
            {
                "large_armor_block",
                "large_armor_slope",
                "large_armor_corner",
                "large_armor_corner_inv",
                "large_heavy_block_armor_block",
                "large_heavy_block_armor_slope",
                "large_heavy_block_armor_corner",
                "large_heavy_block_armor_corner_inv",
                "large_block_small_hydrogen_thrust",
            },
        )
        self.assertNotIn(FILLER_GEOMETRY_ID, {entry.geometry_id for entry in catalog.entries})

    def test_runtime_does_not_stamp_or_scan_install(self) -> None:
        forbidden = (
            "stamp_automatable_remainder",
            "expand_catalog_identities",
            "SE2CAD_GAME_ROOT",
            "SE2CAD_SDK_ROOT",
            "SE2CAD-SE",
            "OriginalContent",
        )
        for path in _MATERIALIZE_AND_ASSEMBLE:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, msg=f"{path.name} mentions {token}")
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.append(node.module)
                for module in modules:
                    self.assertFalse(module.startswith("se2cad.discovery"))
                    self.assertNotEqual(module, "se2cad.catalog.leftover")

    def test_explicit_part_generation_default_stays_original_four(self) -> None:
        self.assertEqual(_treatment_from_argv([]), EDGE_TREATMENT_OFF)
        many = inspect.signature(generate_canonical_parts)
        self.assertIsNone(many.parameters["geometry_ids"].default)
        self.assertEqual(canonical_geometry_ids(), original_library_geometry_ids())

    def test_expand_is_not_required_to_materialize_current_set(self) -> None:
        catalog = load_default_catalog()
        expanded = expand_catalog_identities((), existing=catalog)
        self.assertEqual(len(expanded.entries), 9)


class PlacementAndPathTests(unittest.TestCase):
    def test_names_transforms_and_appearance_stay_on_the_ir(self) -> None:
        ir = _fixture_ir()
        omitted = placements_from_ir(ir)
        off = placements_from_ir(ir, EDGE_TREATMENT_OFF)
        for item, prior, block in zip(omitted, off, ir.grid.blocks, strict=True):
            self.assertEqual(item.part_filename, f"{item.geometry_id}.SLDPRT")
            self.assertEqual(item.part_filename, prior.part_filename)
            self.assertEqual(item.component_name, component_name_from_block(block))
            self.assertEqual(item.position_mm, block.position_mm.as_tuple())
            self.assertEqual(item.rotation, block.rotation)
            self.assertEqual(item.appearance_rgb, prior.appearance_rgb)
            self.assertNotIn("_chamfer", item.component_name)

    def test_generated_root_containment_remains_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = artifact_path_for(root, "large_armor_block")
            destination.relative_to(root.resolve())
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "../large_armor_block.SLDPRT")
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "sub/large_armor_block.SLDPRT")


class ChamferOrderingTests(unittest.TestCase):
    def test_chamfer_generates_missing_base_then_size_specific_sibling(self) -> None:
        ir = _one_block_ir()
        request = chamfer_treatment(75)
        calls: list[tuple[object, tuple[str, ...] | None]] = []

        def generate(config, treatment=None, geometry_ids=None):
            calls.append((treatment, geometry_ids))
            return _fake_generate(config, treatment, geometry_ids)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=generate,
            ):
                report = materialize_required_parts(ir, _config(root), request)
            self.assertEqual(
                [treatment for treatment, _ids in calls],
                [EDGE_TREATMENT_OFF, request],
            )
            self.assertEqual(calls[0][1], ("large_armor_block",))
            self.assertEqual(calls[1][1], ("large_armor_block",))
            self.assertEqual(report.untreated.generated, ("large_armor_block",))
            self.assertEqual(report.treated.generated, ("large_armor_block",))
            self.assertTrue((root / "large_armor_block.SLDPRT").is_file())
            self.assertTrue((root / "large_armor_block_chamfer_75mm.SLDPRT").is_file())
            self.assertFalse((root / "large_armor_block_chamfer.SLDPRT").exists())

    def test_chamfer_does_not_regenerate_existing_base(self) -> None:
        ir = _one_block_ir()
        calls: list[object] = []

        def generate(config, treatment=None, geometry_ids=None):
            calls.append(treatment)
            return _fake_generate(config, treatment, geometry_ids)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large_armor_block.SLDPRT").write_bytes(b"base")
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=generate,
            ):
                report = materialize_required_parts(
                    ir, _config(root), EDGE_TREATMENT_CHAMFER
                )
            self.assertEqual(calls, [EDGE_TREATMENT_CHAMFER])
            self.assertEqual(report.untreated.reused, ("large_armor_block",))
            self.assertEqual(report.untreated.generated, ())
            self.assertEqual((root / "large_armor_block.SLDPRT").read_bytes(), b"base")

    def test_untreated_assembly_does_not_generate_chamfer_siblings(self) -> None:
        ir = _fixture_ir()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ):
                report = materialize_required_parts(ir, _config(root), EDGE_TREATMENT_OFF)
            self.assertEqual(report.treated.generated, ())
            self.assertEqual(report.treated.reused, ())
            self.assertFalse(any(root.glob("*_chamfer_*.SLDPRT")))

    def test_permissive_filler_is_lazily_materialized_when_required(self) -> None:
        parsed = _mixed_unknown_parsed()
        ir = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.PERMISSIVE
        ).ir
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ):
                report = materialize_required_parts(ir, _config(root), EDGE_TREATMENT_OFF)
            self.assertEqual(
                report.untreated.generated,
                ("large_armor_block", FILLER_GEOMETRY_ID),
            )
            self.assertEqual(report.substituted_geometry_ids, (FILLER_GEOMETRY_ID,))
            self.assertTrue((root / "se2cad_unknown_filler.SLDPRT").is_file())
            self.assertFalse(any(root.glob("se2cad_unknown_filler_chamfer_*.SLDPRT")))


if __name__ == "__main__":
    unittest.main()
