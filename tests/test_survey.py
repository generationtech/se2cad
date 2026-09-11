"""Ordinary tests for S2C-11.12.1 compatibility survey classification."""

from __future__ import annotations

import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import load_default_catalog
from se2cad.parser import parse_blueprint_xml
from se2cad.survey import (
    CompatibilityOutcome,
    RootCause,
    SourceDocumentKind,
    classify_root_cause,
    compute_compatibility_survey_from_path,
    inspect_document_structure,
    outcome_from_resolve,
    wrap_prefab_as_ship_blueprint,
)
from se2cad.survey.classify import solvability_for
from se2cad.survey.evidence import empty_identity_evidence
from se2cad.survey.__main__ import main as survey_main
from se2cad.vanilla import (
    VanillaResolveKind,
    clear_vanilla_runtime_state,
    resolve_vanilla_geometry,
)
from se2cad.vanilla.resolve import eligibility_reason


def _ship_document(blocks: str, identity: str = "survey-probe") -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <DisplayName>{identity}</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <DisplayName>{identity}-grid</DisplayName>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
{blocks}
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _block(subtype: str) -> str:
    return (
        '            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">\n'
        f"              <SubtypeName>{subtype}</SubtypeName>\n"
        "              <Min x=\"0\" y=\"0\" z=\"0\" />\n"
        "            </MyObjectBuilder_CubeBlock>"
    )


def _prefab_document(*, grid_size: str = "Large", blocks: str, identity: str = "SurveyPrefab") -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Prefabs>
    <Prefab>
      <Id Type="MyObjectBuilder_PrefabDefinition" Subtype="{identity}" />
      <DisplayName>Survey Prefab</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>{grid_size}</GridSizeEnum>
          <CubeBlocks>
{blocks}
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </Prefab>
  </Prefabs>
</Definitions>
"""


def _definition_xml(
    subtype: str,
    *,
    cube_size: str = "Large",
    size: tuple[int, int, int] = (1, 1, 1),
    topology: str = "TriangleMesh",
    model: str | None = "Models\\Cubes\\Large\\light.mwm",
    extra: str = "",
) -> str:
    model_xml = f"      <Model>{model}</Model>\n" if model is not None else ""
    return (
        "    <Definition>\n"
        "      <Id>\n"
        "        <TypeId>CubeBlock</TypeId>\n"
        f"        <SubtypeId>{subtype}</SubtypeId>\n"
        "      </Id>\n"
        f"      <CubeSize>{cube_size}</CubeSize>\n"
        f'      <Size x="{size[0]}" y="{size[1]}" z="{size[2]}" />\n'
        f"      <BlockTopology>{topology}</BlockTopology>\n"
        f"{model_xml}{extra}"
        "    </Definition>\n"
    )


def _write_cube_blocks(game_root: Path, filename: str, definitions: str) -> None:
    directory = game_root / "Data" / "CubeBlocks"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        '<?xml version="1.0"?>\n'
        "<Definitions>\n"
        "  <CubeBlocks>\n"
        f"{definitions}"
        "  </CubeBlocks>\n"
        "</Definitions>\n",
        encoding="utf-8",
    )


def _write_fbx(sdk_root: Path, relative: str) -> None:
    path = sdk_root.joinpath(*relative.replace("\\", "/").split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"Kaydara FBX Binary  \x1a\x00")


def _evidence(*, topology: str | None = None, cube_topology: str | None = None, mwm=None, fbx=None):
    evidence = empty_identity_evidence(
        "Probe",
        1,
        eligibility=None,
        cause=None,
    )
    return type(evidence)(
        **{
            **evidence.__dict__,
            "block_topology": topology,
            "cube_topology": cube_topology,
            "game_mwm_exists": mwm,
            "sdk_fbx_exists": fbx,
        }
    )


class SurveyClassifyTests(unittest.TestCase):
    def test_reason_strings_map_to_concrete_causes(self) -> None:
        cases = (
            (
                "CubeSize 'Small' is not Large",
                _evidence(),
                RootCause.SMALL_GRID_NOT_ACTIVATED,
            ),
            (
                "BlockTopology 'Cube' is not TriangleMesh",
                _evidence(topology="Cube", cube_topology="Box"),
                RootCause.CUBETOPOLOGY_NOT_SUPPORTED,
            ),
            (
                "CubeTopology identities are not eligible for this resolver",
                _evidence(cube_topology="Slope2Base"),
                RootCause.CUBETOPOLOGY_NOT_SUPPORTED,
            ),
            (
                "BlockTopology 'Other' is not TriangleMesh",
                _evidence(topology="Other"),
                RootCause.NON_TRIANGLE_MESH_TOPOLOGY,
            ),
            (
                "definition requires subpart or composite handling",
                _evidence(),
                RootCause.DEFINITION_SUBPARTS_PRESENT,
            ),
            (
                "primary Model is missing",
                _evidence(),
                RootCause.NO_PRIMARY_MODEL,
            ),
            (
                "primary Model is ambiguous",
                _evidence(),
                RootCause.MULTIPLE_OR_AMBIGUOUS_PRIMARY_MODEL,
            ),
            (
                "vanilla definition not found",
                _evidence(),
                RootCause.MODDED_OR_NONVANILLA,
            ),
            (
                "authorized SDK source is not a file: Models/Cubes/Large/x.fbx",
                _evidence(mwm=True, fbx=False),
                RootCause.MWM_ONLY,
            ),
            (
                "authorized SDK source is not a file: Models/Cubes/Large/x.fbx",
                _evidence(mwm=False, fbx=False),
                RootCause.SDK_FBX_MISSING,
            ),
            (
                "ambiguous sdk path 'Light.fbx'",
                _evidence(),
                RootCause.SDK_FBX_AMBIGUOUS,
            ),
            (
                "not a usable binary or ascii fbx",
                _evidence(),
                RootCause.FBX_FORMAT_UNSUPPORTED,
            ),
            (
                "block size 0x1x1 is not a positive cell triple",
                _evidence(),
                RootCause.INVALID_OR_PATHOLOGICAL_SIZE,
            ),
            (
                "empty SubtypeName uses object-builder default "
                "MyObjectBuilder_GravityGenerator; production parser fails closed",
                _evidence(),
                RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT,
            ),
        )
        for reason, evidence, expected in cases:
            with self.subTest(reason=reason):
                self.assertEqual(
                    classify_root_cause(
                        outcome=CompatibilityOutcome.UNKNOWN_UNRESOLVED,
                        unresolved_reason=reason,
                        evidence=evidence,
                    ),
                    expected,
                )

    def test_supported_outcomes_have_no_cause(self) -> None:
        evidence = _evidence()
        self.assertIsNone(
            classify_root_cause(
                outcome=CompatibilityOutcome.SUPPORTED_PACKAGED,
                unresolved_reason=None,
                evidence=evidence,
            )
        )
        self.assertIsNone(
            classify_root_cause(
                outcome=CompatibilityOutcome.SUPPORTED_RUNTIME_VANILLA,
                unresolved_reason=None,
                evidence=evidence,
            )
        )
        self.assertEqual(
            classify_root_cause(
                outcome=CompatibilityOutcome.UNSUPPORTED_KNOWN,
                unresolved_reason=None,
                evidence=evidence,
            ),
            RootCause.EXISTING_POLICY_UNSUPPORTED,
        )

    def test_solvability_labels_are_explicit(self) -> None:
        label, text = solvability_for(RootCause.CUBETOPOLOGY_NOT_SUPPORTED)
        self.assertIn("EXISTING_ARCHITECTURE", label.value)
        self.assertIn("Box", text)
        label, text = solvability_for(RootCause.DEFINITION_SUBPARTS_PRESENT)
        self.assertEqual(label.value, "REQUIRES_NEW_ARCHITECTURE")
        self.assertIn("Subparts", text)


class SurveyIntakeTests(unittest.TestCase):
    def test_prefab_wrap_parses_through_existing_parser(self) -> None:
        xml = _prefab_document(blocks=_block("LargeBlockArmorBlock"))
        wrapped = wrap_prefab_as_ship_blueprint(xml, source="prefab-probe")
        parsed = parse_blueprint_xml(wrapped, source="prefab-probe")
        self.assertEqual(parsed.identity_subtype, "SurveyPrefab")
        self.assertEqual(parsed.display_name, "Survey Prefab")
        self.assertEqual(len(parsed.grid.blocks), 1)
        self.assertEqual(parsed.grid.blocks[0].subtype_id, "LargeBlockArmorBlock")

    def test_empty_subtype_is_recorded_and_other_blocks_still_classify(self) -> None:
        xml = _prefab_document(
            blocks="\n".join(
                [
                    _block("LargeBlockArmorBlock"),
                    (
                        '            <MyObjectBuilder_CubeBlock '
                        'xsi:type="MyObjectBuilder_GravityGenerator">\n'
                        "              <SubtypeName />\n"
                        "              <Min x=\"1\" y=\"0\" z=\"0\" />\n"
                        "            </MyObjectBuilder_CubeBlock>"
                    ),
                ]
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty-subtype.sbc"
            path.write_text(xml, encoding="utf-8")
            survey = compute_compatibility_survey_from_path(path)
            self.assertIsNotNone(survey.structural.parser_error)
            self.assertIn("SubtypeName is required", survey.structural.parser_error or "")
            self.assertEqual(survey.block_count, 2)
            self.assertEqual(survey.packaged_instance_count, 1)
            empty = [
                item
                for item in survey.identities
                if item.root_cause is RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT
            ]
            self.assertEqual(len(empty), 1)
            self.assertIn("GravityGenerator", empty[0].subtype_id)

    def test_small_grid_prefab_is_recorded_not_wrapped_as_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.sbc"
            path.write_text(
                _prefab_document(
                    grid_size="Small",
                    blocks=_block("SmallBlockArmorBlock"),
                    identity="SmallProbe",
                ),
                encoding="utf-8",
            )
            structural = inspect_document_structure(path)
            self.assertEqual(structural.kind, SourceDocumentKind.PREFAB)
            self.assertTrue(structural.has_non_large_grid)
            self.assertFalse(structural.wrapped_for_parser)
            survey = compute_compatibility_survey_from_path(path)
            self.assertIsNone(survey.parsed_grid_size)
            self.assertEqual(survey.supported_instance_count, 0)
            self.assertIn("non-Large Grid", " ".join(survey.parser_warnings))


class SurveyComputeTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_vanilla_runtime_state()
        self.catalog = load_default_catalog()

    def tearDown(self) -> None:
        clear_vanilla_runtime_state()

    def test_packaged_armor_and_unknown_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.sbc"
            path.write_text(
                _ship_document(
                    "\n".join(
                        [
                            _block("LargeBlockArmorBlock"),
                            _block("LargeBlockArmorBlock"),
                            _block("ModdedUnknownBlock"),
                        ]
                    )
                ),
                encoding="utf-8",
            )
            with patch.dict("os.environ", {"SE2CAD_GAME_ROOT": "", "SE2CAD_SDK_ROOT": ""}):
                survey = compute_compatibility_survey_from_path(path, self.catalog)
            packaged = [
                item
                for item in survey.identities
                if item.outcome is CompatibilityOutcome.SUPPORTED_PACKAGED
            ]
            unknown = [
                item
                for item in survey.identities
                if item.outcome is CompatibilityOutcome.UNKNOWN_UNRESOLVED
            ]
            self.assertEqual(survey.packaged_instance_count, 2)
            self.assertEqual(survey.packaged_unique_count, 1)
            self.assertEqual(survey.unknown_unresolved_instance_count, 1)
            self.assertEqual(packaged[0].subtype_id, "LargeBlockArmorBlock")
            self.assertEqual(unknown[0].subtype_id, "ModdedUnknownBlock")
            self.assertEqual(unknown[0].root_cause, RootCause.OTHER_EVIDENCED_CAUSE)
            self.assertEqual(survey.cumulative.current_supported_percent, 66.67)

    def test_runtime_resolve_is_classified_separately_from_packaged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            game.mkdir()
            sdk.mkdir()
            _write_cube_blocks(
                game,
                "CubeBlocks_Lights.sbc",
                _definition_xml("LargeBlockFrontLight"),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            path = Path(tmp) / "light.sbc"
            path.write_text(
                _ship_document(_block("LargeBlockFrontLight")),
                encoding="utf-8",
            )
            env = {
                "SE2CAD_GAME_ROOT": str(game),
                "SE2CAD_SDK_ROOT": str(sdk),
            }
            with patch.dict("os.environ", env, clear=False):
                survey = compute_compatibility_survey_from_path(path, self.catalog)
            self.assertEqual(survey.runtime_unique_count, 1)
            self.assertEqual(survey.packaged_unique_count, 0)
            self.assertEqual(
                survey.identities[0].outcome,
                CompatibilityOutcome.SUPPORTED_RUNTIME_VANILLA,
            )
            self.assertIsNone(survey.identities[0].root_cause)

    def test_omitted_blocktopology_with_cubedefinition_is_cubetopology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            game.mkdir()
            sdk.mkdir()
            extra = (
                "      <CubeDefinition>\n"
                "        <CubeTopology>StandaloneBox</CubeTopology>\n"
                "      </CubeDefinition>\n"
            )
            _write_cube_blocks(
                game,
                "CubeBlocks_Walls.sbc",
                "    <Definition>\n"
                "      <Id>\n"
                "        <TypeId>CubeBlock</TypeId>\n"
                "        <SubtypeId>LargeBlockInteriorWall</SubtypeId>\n"
                "      </Id>\n"
                "      <CubeSize>Large</CubeSize>\n"
                '      <Size x="1" y="1" z="1" />\n'
                f"{extra}"
                "    </Definition>\n",
            )
            path = Path(tmp) / "wall.sbc"
            path.write_text(
                _ship_document(_block("LargeBlockInteriorWall")),
                encoding="utf-8",
            )
            env = {
                "SE2CAD_GAME_ROOT": str(game),
                "SE2CAD_SDK_ROOT": str(sdk),
            }
            with patch.dict("os.environ", env, clear=False):
                survey = compute_compatibility_survey_from_path(path, self.catalog)
            self.assertEqual(survey.supported_instance_count, 0)
            self.assertEqual(
                survey.identities[0].root_cause,
                RootCause.CUBETOPOLOGY_NOT_SUPPORTED,
            )
            self.assertEqual(survey.identities[0].evidence.cube_topology, "StandaloneBox")

    def test_cube_topology_unknown_does_not_become_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            game.mkdir()
            sdk.mkdir()
            extra = (
                "      <CubeDefinition>\n"
                "        <CubeTopology>Box</CubeTopology>\n"
                "      </CubeDefinition>\n"
            )
            _write_cube_blocks(
                game,
                "CubeBlocks_Armor.sbc",
                _definition_xml(
                    "LargeBlockArmorRoundSlope",
                    topology="Cube",
                    model=None,
                    extra=extra,
                ),
            )
            path = Path(tmp) / "round_slope.sbc"
            path.write_text(
                _ship_document(_block("LargeBlockArmorRoundSlope")),
                encoding="utf-8",
            )
            env = {
                "SE2CAD_GAME_ROOT": str(game),
                "SE2CAD_SDK_ROOT": str(sdk),
            }
            with patch.dict("os.environ", env, clear=False):
                resolved = resolve_vanilla_geometry(
                    "LargeBlockArmorRoundSlope", self.catalog
                )
                survey = compute_compatibility_survey_from_path(path, self.catalog)
            self.assertEqual(resolved.kind, VanillaResolveKind.UNRESOLVED)
            self.assertIsNotNone(eligibility_reason)
            self.assertEqual(survey.supported_instance_count, 0)
            self.assertEqual(
                survey.identities[0].root_cause,
                RootCause.CUBETOPOLOGY_NOT_SUPPORTED,
            )

    def test_percentages_use_block_and_unresolved_denominators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "counts.sbc"
            path.write_text(
                _ship_document(
                    "\n".join(
                        [_block("LargeBlockArmorBlock")] * 3
                        + [_block("ModA"), _block("ModB")]
                    )
                ),
                encoding="utf-8",
            )
            survey = compute_compatibility_survey_from_path(path, self.catalog)
            self.assertEqual(survey.block_count, 5)
            self.assertEqual(survey.supported_instance_count, 3)
            self.assertEqual(survey.unknown_unresolved_instance_count, 2)
            self.assertEqual(survey.cumulative.current_supported_percent, 60.0)
            self.assertEqual(len(survey.cause_impacts), 1)
            self.assertEqual(survey.cause_impacts[0].percent_of_all_blocks, 40.0)
            self.assertEqual(
                survey.cause_impacts[0].percent_of_unresolved_instances, 100.0
            )

    def test_operator_entry_does_not_hard_code_a_survey_ship(self) -> None:
        source = Path(__file__).resolve().parents[1] / "src" / "se2cad" / "survey"
        text = "\n".join(
            path.read_text(encoding="utf-8") for path in source.glob("*.py")
        )
        self.assertNotIn("RST6Salvador", text)
        self.assertNotIn("Big Red", text)
        self.assertNotIn("bigred", text.lower())

    def test_operator_entry_writes_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "armor.sbc"
            path.write_text(
                _ship_document(_block("LargeBlockArmorBlock")),
                encoding="utf-8",
            )
            out = Path(tmp) / "report.md"
            with patch("sys.stdout", new=StringIO()) as stdout:
                code = survey_main([str(path), "--markdown", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.is_file())
            body = out.read_text(encoding="utf-8")
            self.assertIn("SUPPORTED_PACKAGED", body)
            self.assertIn("support_granted=false", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
