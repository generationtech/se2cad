"""S2C-11.11.1 demand-driven Large Grid multi-cell TriangleMesh runtime."""

from __future__ import annotations

import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    FILLER_GEOMETRY_ID,
    LARGE_GRID_CELL_PITCH_MM,
    CellSize,
    SupportStatus,
    default_catalog_path,
    load_default_catalog,
)
from se2cad.library import geometry_supports_chamfer, lookup_record
from se2cad.library.lookup import register_runtime_library_record
from se2cad.parser import (
    Direction,
    GridCoordinate,
    UnsupportedBlueprintError,
    parse_blueprint,
    parse_blueprint_xml,
)
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.solidworks.com_validate import PartValidation
from se2cad.solidworks.errors import CanonicalPartValidationError
from se2cad.solidworks.materialize import (
    demanded_untreated_geometry_ids,
    ensure_untreated_canonical_parts,
)
from se2cad.solidworks.sdk_convert import assert_imported_mesh_envelope
from se2cad.transform import (
    BlockPlacementDefinition,
    ModelOffset,
    cell_center_mm,
    occupied_max,
    occupancy_center_mm,
    placement_translation_mm,
    rotation_from_forward_up,
)
from se2cad.vanilla import (
    VANILLA_RUNTIME_GEOMETRY_PREFIX,
    VANILLA_RUNTIME_MULTICELL_PREFIX,
    VanillaResolveKind,
    clear_vanilla_runtime_state,
    resolve_vanilla_geometry,
    vanilla_runtime_geometry_id,
)
from se2cad.vanilla.record import lookup_runtime_placement, register_runtime_placement
from se2cad.vanilla.resolve import eligibility_reason
from se2cad.vanilla.lookup import TargetedDefinition

from tests.test_vanilla_resolve import (
    _LIGHT,
    _block,
    _config,
    _definition_xml,
    _document,
    _fake_generate,
    _write_cube_blocks,
    _write_fbx,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
SRC_ROOT = REPO_ROOT / "src" / "se2cad"
_BIG_RED_SUBTYPES = (
    "LargeBlockLandingGear",
    "LargeBlockLargeHydrogenThrust",
    "LargeHydrogenTank",
    "LargeBlockRadioAntenna",
    "LargeOreDetector",
)


def _eligible(game: Path, sdk: Path, subtype: str, size: tuple[int, int, int], model: str) -> None:
    _write_cube_blocks(
        game,
        f"CubeBlocks_{subtype}.sbc",
        _definition_xml(
            subtype,
            size=size,
            model=f"Models\\Cubes\\Large\\{model}.mwm",
        ),
    )
    _write_fbx(sdk, f"Models/Cubes/Large/{model}.fbx")


class MultiCellRuntimeResolveTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_vanilla_runtime_state()
        self.catalog = load_default_catalog()

    def tearDown(self) -> None:
        clear_vanilla_runtime_state()

    def _roots(self, tmp: str) -> tuple[Path, Path]:
        game = Path(tmp) / "game"
        sdk = Path(tmp) / "sdk"
        game.mkdir()
        sdk.mkdir()
        return game, sdk

    def test_existing_one_by_one_still_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks_Lights.sbc", _definition_xml(_LIGHT))
            _write_fbx(sdk, "Models/Cubes/Large/Light.FBX")
            result = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(
            result.runtime.geometry_id, vanilla_runtime_geometry_id(_LIGHT)
        )
        self.assertTrue(
            result.runtime.geometry_id.startswith(VANILLA_RUNTIME_GEOMETRY_PREFIX)
        )
        self.assertEqual(result.runtime.placement.size, CellSize(1, 1, 1))

    def test_eligible_size_shapes_resolve(self) -> None:
        cases = (
            ("LargeOreDetector", (1, 1, 2), "OreDetector"),
            ("LargeBlockLandingGear", (1, 2, 3), "LandingGear"),
            ("LargeHydrogenTank", (3, 3, 3), "HydrogenTank"),
            ("LargeBlockRadioAntenna", (1, 6, 2), "antenna"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            for subtype, size, model in cases:
                _eligible(game, sdk, subtype, size, model)
            results = {
                subtype: resolve_vanilla_geometry(
                    subtype, self.catalog, game_root=game, sdk_root=sdk
                )
                for subtype, _size, _model in cases
            }
        for subtype, size, _model in cases:
            result = results[subtype]
            self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA, subtype)
            observed = result.runtime.catalog_entry.observed.size
            self.assertEqual((observed.x, observed.y, observed.z), size)
            self.assertEqual(result.runtime.placement.size, CellSize(*size))
            self.assertTrue(result.runtime.placement.model_offset.is_zero())
            self.assertTrue(
                result.runtime.geometry_id.startswith(VANILLA_RUNTIME_MULTICELL_PREFIX)
            )
            self.assertFalse(
                result.runtime.geometry_id.startswith(VANILLA_RUNTIME_GEOMETRY_PREFIX)
            )
            self.assertFalse(result.runtime.library_record.chamfer_capable)
            self.assertFalse(geometry_supports_chamfer(result.runtime.geometry_id))

    def test_size_and_model_offset_propagate_exactly(self) -> None:
        extra = '      <ModelOffset x="1/4" y="0" z="-1/2" />\n'
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Offset.sbc",
                _definition_xml(
                    "LargeOffsetProbe",
                    size=(1, 1, 2),
                    model="Models\\Cubes\\Large\\offset.mwm",
                    extra=extra,
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/offset.fbx")
            result = resolve_vanilla_geometry(
                "LargeOffsetProbe", self.catalog, game_root=game, sdk_root=sdk
            )
            parsed = parse_blueprint_xml(
                _document(
                    _block(
                        "LargeOffsetProbe",
                        min_xml='<Min x="2" y="6" z="4" />',
                    )
                ),
                source="offset-probe",
            )
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(result.runtime.placement.size, CellSize(1, 1, 2))
        self.assertEqual(
            result.runtime.placement.model_offset,
            ModelOffset.from_metres("1/4", 0, "-1/2"),
        )
        placement = lookup_runtime_placement("LargeOffsetProbe")
        self.assertEqual(placement, result.runtime.placement)
        block = converted.ir.grid.blocks[0]
        rotation = rotation_from_forward_up(Direction.FORWARD, Direction.UP)
        self.assertEqual(
            block.position_mm,
            placement_translation_mm(
                GridCoordinate(2, 6, 4),
                result.runtime.placement,
                rotation,
            ),
        )
        self.assertNotEqual(block.position_mm, cell_center_mm(GridCoordinate(2, 6, 4)))

    def test_center_does_not_enter_placement(self) -> None:
        extra = (
            '      <ModelOffset x="0" y="0" z="0" />\n'
            '      <Center x="1" y="1" z="2" />\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Thrust.sbc",
                _definition_xml(
                    "LargeBlockLargeHydrogenThrust",
                    size=(3, 3, 3),
                    model="Models\\Cubes\\Large\\HydrogenThrusterLarge.mwm",
                    extra=extra,
                    type_id="Thrust",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/HydrogenThrusterLarge.fbx")
            parsed = parse_blueprint_xml(
                _document(
                    _block(
                        "LargeBlockLargeHydrogenThrust",
                        xsi_type="MyObjectBuilder_Thrust",
                        min_xml='<Min x="-1" y="7" z="4" />',
                    )
                ),
                source="center-ignored",
            )
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
        block = converted.ir.grid.blocks[0]
        rotation = rotation_from_forward_up(parsed.grid.blocks[0].forward, parsed.grid.blocks[0].up)
        occupancy = occupied_max(GridCoordinate(-1, 7, 4), CellSize(3, 3, 3), rotation)
        expected = occupancy_center_mm(GridCoordinate(-1, 7, 4), occupancy)
        self.assertEqual(block.position_mm, expected)
        wrong_center = (
            (-1 + 1) * LARGE_GRID_CELL_PITCH_MM,
            (7 + 1) * LARGE_GRID_CELL_PITCH_MM,
            (4 + 2) * LARGE_GRID_CELL_PITCH_MM,
        )
        self.assertNotEqual(block.position_mm.as_tuple(), wrong_center)
        self.assertNotIn("center", block.__dict__)

    def test_rotated_size_negative_min_and_half_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _eligible(game, sdk, "LargeBlockLandingGear", (1, 2, 3), "LandingGear")
            parsed = parse_blueprint_xml(
                _document(
                    _block(
                        "LargeBlockLandingGear",
                        min_xml='<Min x="-3" y="9" z="5" />',
                        extra=(
                            "<BlockOrientation Forward=\"Left\" Up=\"Down\" />"
                        ),
                    )
                ),
                source="rotated-gear",
            )
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
        block = converted.ir.grid.blocks[0]
        rotation = rotation_from_forward_up(Direction.LEFT, Direction.DOWN)
        maximum = occupied_max(GridCoordinate(-3, 9, 5), CellSize(1, 2, 3), rotation)
        expected = occupancy_center_mm(GridCoordinate(-3, 9, 5), maximum)
        self.assertEqual(block.position_mm, expected)
        self.assertEqual(block.rotation, rotation)
        self.assertEqual(expected.y % 1, 0)

    def test_small_grid_cube_topology_and_subparts_remain_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Rejects.sbc",
                _definition_xml("SmallBlockLight", cube_size="Small")
                + _definition_xml(
                    "LargeBlockArmorCube",
                    topology="Cube",
                    model=None,
                    extra="      <CubeDefinition><CubeTopology>Box</CubeTopology></CubeDefinition>\n",
                )
                + _definition_xml(
                    "SubpartBlock",
                    extra="      <Subparts><Subpart><Name>x</Name></Subpart></Subparts>\n",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            small = resolve_vanilla_geometry(
                "SmallBlockLight", self.catalog, game_root=game, sdk_root=sdk
            )
            cube = resolve_vanilla_geometry(
                "LargeBlockArmorCube", self.catalog, game_root=game, sdk_root=sdk
            )
            subparts = resolve_vanilla_geometry(
                "SubpartBlock", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertIn("not Large", small.unresolved_reason)
        self.assertIn("TriangleMesh", cube.unresolved_reason)
        self.assertIn("subpart", subparts.unresolved_reason)

    def test_malformed_and_nonpositive_size_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_BadSize.sbc",
                _definition_xml("FloatSize", extra="", model="Models\\Cubes\\Large\\a.mwm").replace(
                    'x="1"', 'x="1.5"'
                )
                + _definition_xml(
                    "ZeroSize",
                    size=(1, 1, 1),
                    model="Models\\Cubes\\Large\\b.mwm",
                ).replace('y="1"', 'y="0"')
                + _definition_xml(
                    "NegSize",
                    size=(1, 1, 1),
                    model="Models\\Cubes\\Large\\c.mwm",
                ).replace('z="1"', 'z="-2"'),
            )
            _write_fbx(sdk, "Models/Cubes/Large/a.fbx")
            _write_fbx(sdk, "Models/Cubes/Large/b.fbx")
            _write_fbx(sdk, "Models/Cubes/Large/c.fbx")
            floated = resolve_vanilla_geometry(
                "FloatSize", self.catalog, game_root=game, sdk_root=sdk
            )
            zeroed = resolve_vanilla_geometry(
                "ZeroSize", self.catalog, game_root=game, sdk_root=sdk
            )
            negative = resolve_vanilla_geometry(
                "NegSize", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(floated.kind, VanillaResolveKind.UNRESOLVED)
        self.assertEqual(zeroed.kind, VanillaResolveKind.UNRESOLVED)
        self.assertEqual(negative.kind, VanillaResolveKind.UNRESOLVED)

    def test_missing_and_ambiguous_sdk_remain_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Missing.sbc",
                _definition_xml(
                    "LargeMissingMesh",
                    size=(1, 1, 2),
                    model="Models\\Cubes\\Large\\missing.mwm",
                )
                + _definition_xml(
                    "LargeAmbiguousMesh",
                    size=(3, 3, 3),
                    extra="      <Model>Models\\Cubes\\Large\\a.mwm</Model>\n"
                    "      <Model>Models\\Cubes\\Large\\b.mwm</Model>\n",
                    model=None,
                ),
            )
            missing = resolve_vanilla_geometry(
                "LargeMissingMesh", self.catalog, game_root=game, sdk_root=sdk
            )
            ambiguous = resolve_vanilla_geometry(
                "LargeAmbiguousMesh", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(missing.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("is not a file", missing.unresolved_reason)
        self.assertEqual(ambiguous.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("ambiguous", ambiguous.unresolved_reason)

    def test_supported_builder_failure_does_not_become_filler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _eligible(game, sdk, "LargeOreDetector", (1, 1, 2), "OreDetector")
            parsed = parse_blueprint_xml(
                _document(_block("LargeOreDetector")), source="fail-closed"
            )
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                result = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
            generated = Path(tmp) / "generated"
            generated.mkdir()
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=RuntimeError("builder failed"),
            ):
                with self.assertRaises(RuntimeError):
                    ensure_untreated_canonical_parts(
                        _config(generated),
                        demanded_untreated_geometry_ids(result.ir),
                    )
        self.assertEqual(result.filler_count, 0)
        self.assertNotEqual(result.ir.grid.blocks[0].geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(
            result.ir.grid.blocks[0].support_status, SupportStatus.SUPPORTED
        )

    def test_repeated_instances_share_geometry_id_independent_of_pose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _eligible(game, sdk, "LargeBlockLandingGear", (1, 2, 3), "LandingGear")
            xml = _document(
                "\n".join(
                    [
                        _block(
                            "LargeBlockLandingGear",
                            min_xml='<Min x="2" y="6" z="4" />',
                        ),
                        _block(
                            "LargeBlockLandingGear",
                            min_xml='<Min x="-3" y="9" z="5" />',
                            extra='<BlockOrientation Forward="Left" Up="Up" />',
                        ),
                    ]
                )
            )
            parsed = parse_blueprint_xml(xml, source="two-gear")
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
                generated = Path(tmp) / "generated"
                generated.mkdir()
                with patch(
                    "se2cad.solidworks.generate.generate_canonical_parts",
                    side_effect=_fake_generate,
                ):
                    first = ensure_untreated_canonical_parts(
                        _config(generated),
                        demanded_untreated_geometry_ids(converted.ir),
                    )
                    second = ensure_untreated_canonical_parts(
                        _config(generated),
                        demanded_untreated_geometry_ids(converted.ir),
                    )
        first_id, second_id = (
            converted.ir.grid.blocks[0].geometry_id,
            converted.ir.grid.blocks[1].geometry_id,
        )
        self.assertEqual(first_id, second_id)
        self.assertEqual(
            first_id,
            vanilla_runtime_geometry_id(
                "LargeBlockLandingGear", CellSize(1, 2, 3)
            ),
        )
        self.assertNotIn("2_6_4", first_id)
        self.assertNotIn("left", first_id)
        self.assertEqual(first.generated, (first_id,))
        self.assertEqual(second.generated, ())
        self.assertEqual(second.reused, (first_id,))

    def test_old_one_by_one_cache_name_is_preserved(self) -> None:
        self.assertEqual(
            vanilla_runtime_geometry_id("LargeBlockFrontLight", CellSize(1, 1, 1)),
            "vanilla_lg_1x1x1_large_block_front_light",
        )
        self.assertEqual(
            vanilla_runtime_geometry_id("LargeBlockFrontLight"),
            "vanilla_lg_1x1x1_large_block_front_light",
        )
        self.assertEqual(
            vanilla_runtime_geometry_id("LargeBlockLandingGear", CellSize(1, 2, 3)),
            "vanilla_lg_large_block_landing_gear",
        )

    def test_geometry_collision_fails_closed(self) -> None:
        packaged = lookup_record("large_armor_block")
        with self.assertRaises(ValueError):
            register_runtime_library_record(packaged)
        first = BlockPlacementDefinition(
            size=CellSize(1, 2, 3), model_offset=ModelOffset.zero()
        )
        second = BlockPlacementDefinition(
            size=CellSize(3, 3, 3), model_offset=ModelOffset.zero()
        )
        register_runtime_placement("CollisionProbe", first)
        with self.assertRaises(ValueError):
            register_runtime_placement("CollisionProbe", second)

    def test_packaged_catalog_and_transient_records_are_not_persisted(self) -> None:
        path = default_catalog_path()
        before = path.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _eligible(game, sdk, "LargeOreDetector", (1, 1, 2), "OreDetector")
            resolve_vanilla_geometry(
                "LargeOreDetector", self.catalog, game_root=game, sdk_root=sdk
            )
        after = path.read_text(encoding="utf-8")
        self.assertEqual(before, after)
        self.assertNotIn("LargeOreDetector", after)
        self.assertNotIn(VANILLA_RUNTIME_MULTICELL_PREFIX, after)
        reloaded = load_default_catalog()
        self.assertEqual(len(reloaded.entries), len(self.catalog.entries))
        self.assertEqual(len(reloaded.entries), 13)

    def test_no_whole_install_materialization_in_runtime_modules(self) -> None:
        forbidden = (
            "stamp_automatable_remainder",
            "expand_catalog_identities",
        )
        for relative in (
            "solidworks/materialize.py",
            "solidworks/assemble.py",
            "vanilla/resolve.py",
        ):
            text = (SRC_ROOT / relative).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, msg=f"{relative} {token}")

    def test_no_subtype_specific_big_red_production_branch(self) -> None:
        production = []
        for path in SRC_ROOT.rglob("*.py"):
            if "test" in path.parts:
                continue
            production.append(path)
        for path in production:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            text = path.read_text(encoding="utf-8")
            for subtype in _BIG_RED_SUBTYPES:
                if subtype in text:
                    self.assertNotIn(
                        subtype,
                        text,
                        msg=f"{path} special-cases {subtype}",
                    )
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    snippet = ast.dump(node.test)
                    self.assertNotIn("LandingGear", snippet)
                    self.assertNotIn("RadioAntenna", snippet)

    def test_small_grid_blueprint_still_rejected(self) -> None:
        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="small" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Small</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockLandingGear</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="small-multicell")

    def test_acceptance_fixture_transforms_unchanged(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint(FIXTURE_PATH)
        from se2cad.ir import build_canonical_blueprint

        ir = build_canonical_blueprint(parsed, catalog)
        for parsed_block, block in zip(parsed.grid.blocks, ir.grid.blocks, strict=True):
            self.assertEqual(block.position_mm, cell_center_mm(parsed_block.min))


class SizeAwareEnvelopeTests(unittest.TestCase):
    def test_unit_limits_and_forgotten_scale_remain(self) -> None:
        small = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-0.25, -0.25, -0.1),
            bounding_box_max_m=(0.25, 0.25, 0.09),
            volume_m3=0.01,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        assert_imported_mesh_envelope(small)
        tiny = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-0.0013, -0.0013, -0.0013),
            bounding_box_max_m=(0.0013, 0.0013, 0.0013),
            volume_m3=1e-8,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        with self.assertRaises(CanonicalPartValidationError):
            assert_imported_mesh_envelope(tiny, CellSize(3, 3, 3))

    def test_legitimate_multicell_extents_are_accepted(self) -> None:
        thruster = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-3.75, -3.75, -3.75),
            bounding_box_max_m=(3.75, 3.75, 3.75),
            volume_m3=1.0,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        assert_imported_mesh_envelope(thruster, CellSize(3, 3, 3))
        antenna = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-1.25, 0.0, -2.5),
            bounding_box_max_m=(1.25, 15.0, 2.5),
            volume_m3=1.0,
            center_of_mass_m=(0.0, 7.5, 0.0),
        )
        assert_imported_mesh_envelope(antenna, CellSize(1, 6, 2))
        gear = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-1.3, -8.0, -3.8),
            bounding_box_max_m=(1.3, 0.2, 3.8),
            volume_m3=1.0,
            center_of_mass_m=(0.0, -3.9, 0.0),
        )
        assert_imported_mesh_envelope(gear, CellSize(1, 2, 3))
        detector = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-1.25, -1.25, -2.5),
            bounding_box_max_m=(1.25, 1.25, 2.5),
            volume_m3=0.2,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        assert_imported_mesh_envelope(detector, CellSize(1, 1, 2))

    def test_forgotten_scale_and_absurd_meshes_fail(self) -> None:
        forgotten = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-0.0075, -0.0075, -0.0075),
            bounding_box_max_m=(0.0075, 0.0075, 0.0075),
            volume_m3=1e-8,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        absurd = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-4000.0, -4000.0, -4000.0),
            bounding_box_max_m=(4000.0, 4000.0, 4000.0),
            volume_m3=1e9,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        with self.assertRaises(CanonicalPartValidationError):
            assert_imported_mesh_envelope(forgotten, CellSize(3, 3, 3))
        with self.assertRaises(CanonicalPartValidationError):
            assert_imported_mesh_envelope(absurd, CellSize(1, 6, 2))


class EligibilityBoundTests(unittest.TestCase):
    def test_oversized_occupancy_is_rejected(self) -> None:
        definition = TargetedDefinition(
            subtype_id="HugeBlock",
            type_id="CubeBlock",
            cube_size="Large",
            size=CellSize(33, 1, 1),
            block_topology="TriangleMesh",
            cube_topology=None,
            primary_model="Models\\Cubes\\Large\\huge.mwm",
            has_subparts=False,
            model_count=1,
            source_relative="Data/CubeBlocks/huge.sbc",
        )
        reason = eligibility_reason(definition)
        self.assertIsNotNone(reason)
        self.assertIn("occupancy bound", reason or "")


if __name__ == "__main__":
    unittest.main()
