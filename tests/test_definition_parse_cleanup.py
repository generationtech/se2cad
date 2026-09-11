"""S2C-11.15.1 definition-parse and empty-subtype compatibility cleanup."""

from __future__ import annotations

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import CellSize, default_catalog_path, load_default_catalog
from se2cad.library import geometry_supports_chamfer, lookup_record
from se2cad.parser import (
    MissingRequiredFieldError,
    parse_blueprint_xml,
)
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight
from se2cad.solidworks.materialize import (
    demanded_untreated_geometry_ids,
    ensure_untreated_canonical_parts,
)
from se2cad.vanilla import (
    VANILLA_RUNTIME_EMPTY_TYPE_INFIX,
    VANILLA_RUNTIME_GEOMETRY_PREFIX,
    VanillaLookupError,
    VanillaResolveKind,
    clear_vanilla_runtime_state,
    coalesce_identical_scalar_texts,
    empty_subtype_placement_key,
    lookup_exact_subtype,
    lookup_unique_empty_subtype,
    resolve_vanilla_geometry,
    runtime_placement_key,
    vanilla_runtime_geometry_id,
    vanilla_runtime_geometry_id_for_empty_type,
)
from se2cad.vanilla.record import lookup_runtime_placement

from tests.test_vanilla_resolve import (
    _block,
    _config,
    _definition_xml,
    _document,
    _fake_generate,
    _write_cube_blocks,
    _write_fbx,
)

_PARSE_GAP_SUBTYPES = (
    "LadderShaft",
    "LargeBlockConsoleModule",
    "LargeBlockInsetWall",
    "LargeBlockSciFiWall",
)
_CUBETOPOLOGY_REMAINING = (
    "LargeBlockArmorHalfSlopeInverted",
    "LargeBlockArmorRoundSlope",
    "LargeBlockArmorRoundCorner",
)


def _child_size(x: str = "1", y: str = "1", z: str = "1") -> str:
    return (
        "      <Size>\n"
        f"        <X>{x}</X>\n"
        f"        <Y>{y}</Y>\n"
        f"        <Z>{z}</Z>\n"
        "      </Size>\n"
    )


def _child_offset(x: str = "0", y: str = "0", z: str = "0") -> str:
    return (
        "      <ModelOffset>\n"
        f"        <X>{x}</X>\n"
        f"        <Y>{y}</Y>\n"
        f"        <Z>{z}</Z>\n"
        "      </ModelOffset>\n"
    )


def _definition_without_size(
    subtype: str,
    *,
    extra: str,
    topology: str = "TriangleMesh",
    model: str = "Models\\Cubes\\Large\\light.mwm",
    type_id: str = "CubeBlock",
    cube_size: str = "Large",
    topologies: tuple[str, ...] | None = None,
) -> str:
    topology_xml = ""
    for token in topologies or (topology,):
        topology_xml += f"      <BlockTopology>{token}</BlockTopology>\n"
    return (
        "    <Definition>\n"
        "      <Id>\n"
        f"        <TypeId>{type_id}</TypeId>\n"
        f"        <SubtypeId>{subtype}</SubtypeId>\n"
        "      </Id>\n"
        f"      <CubeSize>{cube_size}</CubeSize>\n"
        f"{extra}"
        f"{topology_xml}"
        f"      <Model>{model}</Model>\n"
        "    </Definition>\n"
    )


def _empty_subtype_definition(
    type_id: str,
    *,
    cube_size: str = "Large",
    size: tuple[int, int, int] = (1, 1, 1),
    model: str = "Models\\Cubes\\Large\\GravityGenerator.mwm",
    subtype: str = "",
) -> str:
    return (
        "    <Definition>\n"
        "      <Id>\n"
        f"        <TypeId>{type_id}</TypeId>\n"
        f"        <SubtypeId>{subtype}</SubtypeId>\n"
        "      </Id>\n"
        f"      <CubeSize>{cube_size}</CubeSize>\n"
        f'      <Size x="{size[0]}" y="{size[1]}" z="{size[2]}" />\n'
        "      <BlockTopology>TriangleMesh</BlockTopology>\n"
        f"      <Model>{model}</Model>\n"
        "    </Definition>\n"
    )


class ChildVectorParseTests(unittest.TestCase):
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

    def test_attribute_form_size_remains_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks.sbc", _definition_xml("AttrSize"))
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "AttrSize", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        assert result.runtime is not None
        self.assertEqual(result.runtime.placement.size, CellSize(1, 1, 1))

    def test_child_xyz_size_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size("ChildSize", extra=_child_size("1", "1", "1")),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "ChildSize", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        assert result.runtime is not None
        self.assertEqual(result.runtime.placement.size, CellSize(1, 1, 1))
        self.assertEqual(result.runtime.placement.model_offset.as_tuple(), (0.0, 0.0, 0.0))

    def test_child_model_offset_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "ChildOffset",
                    extra=_child_size() + _child_offset("0.5", "0", "-0.25"),
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "ChildOffset", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        assert result.runtime is not None
        self.assertEqual(
            result.runtime.placement.model_offset.as_tuple(), (0.5, 0.0, -0.25)
        )

    def test_missing_x_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "MissingX",
                    extra="      <Size>\n        <Y>1</Y>\n        <Z>1</Z>\n      </Size>\n",
                ),
            )
            hit = lookup_exact_subtype("MissingX", game)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertIsNone(hit.definition)
        self.assertIn("missing child", hit.unusable_reason or "")

    def test_missing_y_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "MissingY",
                    extra="      <Size>\n        <X>1</X>\n        <Z>1</Z>\n      </Size>\n",
                ),
            )
            hit = lookup_exact_subtype("MissingY", game)
        assert hit is not None
        self.assertIsNone(hit.definition)
        self.assertIn("missing child", hit.unusable_reason or "")

    def test_missing_z_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "MissingZ",
                    extra="      <Size>\n        <X>1</X>\n        <Y>1</Y>\n      </Size>\n",
                ),
            )
            hit = lookup_exact_subtype("MissingZ", game)
        assert hit is not None
        self.assertIsNone(hit.definition)
        self.assertIn("missing child", hit.unusable_reason or "")

    def test_duplicate_axis_conflict_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "DupAxis",
                    extra=(
                        "      <Size>\n"
                        "        <X>1</X>\n"
                        "        <X>2</X>\n"
                        "        <Y>1</Y>\n"
                        "        <Z>1</Z>\n"
                        "      </Size>\n"
                    ),
                ),
            )
            hit = lookup_exact_subtype("DupAxis", game)
        assert hit is not None
        self.assertIsNone(hit.definition)
        self.assertIn("duplicate", hit.unusable_reason or "")

    def test_malformed_numeric_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "BadNum", extra=_child_size("1", "nope", "1")
                ),
            )
            hit = lookup_exact_subtype("BadNum", game)
        assert hit is not None
        self.assertIsNone(hit.definition)
        self.assertIn("not an integer", hit.unusable_reason or "")

    def test_zero_and_negative_size_reject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size("ZeroSize", extra=_child_size("1", "0", "1"))
                + _definition_without_size(
                    "NegSize", extra=_child_size("1", "-1", "1")
                ),
            )
            zero = lookup_exact_subtype("ZeroSize", game)
            negative = lookup_exact_subtype("NegSize", game)
        assert zero is not None and negative is not None
        self.assertIsNone(zero.definition)
        self.assertIsNone(negative.definition)
        self.assertIn("must be >= 1", zero.unusable_reason or "")
        self.assertIn("must be >= 1", negative.unusable_reason or "")

    def test_arbitrary_child_collection_is_not_a_vector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            extra = (
                _child_size()
                + "      <Center>\n"
                "        <X>9</X>\n"
                "        <Y>9</Y>\n"
                "        <Z>9</Z>\n"
                "      </Center>\n"
            )
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size("NotAVector", extra=extra),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "NotAVector", self.catalog, game_root=game, sdk_root=sdk
            )
            hit = lookup_exact_subtype("NotAVector", game)
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        assert result.runtime is not None
        self.assertEqual(result.runtime.placement.model_offset.as_tuple(), (0.0, 0.0, 0.0))
        assert hit is not None and hit.definition is not None
        self.assertEqual(hit.definition.size, CellSize(1, 1, 1))


class DuplicateScalarTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_vanilla_runtime_state()
        self.catalog = load_default_catalog()

    def tearDown(self) -> None:
        clear_vanilla_runtime_state()

    def test_one_block_topology_works(self) -> None:
        nodes = [ET.fromstring("<BlockTopology>TriangleMesh</BlockTopology>")]
        self.assertEqual(
            coalesce_identical_scalar_texts(
                nodes, name="BlockTopology", source="one"
            ),
            "TriangleMesh",
        )

    def test_identical_triangle_mesh_duplicates_coalesce(self) -> None:
        nodes = [
            ET.fromstring("<BlockTopology>TriangleMesh</BlockTopology>"),
            ET.fromstring("<BlockTopology>TriangleMesh</BlockTopology>"),
        ]
        self.assertEqual(
            coalesce_identical_scalar_texts(
                nodes, name="BlockTopology", source="dup"
            ),
            "TriangleMesh",
        )

    def test_conflicting_triangle_mesh_and_cube_rejects(self) -> None:
        nodes = [
            ET.fromstring("<BlockTopology>TriangleMesh</BlockTopology>"),
            ET.fromstring("<BlockTopology>Cube</BlockTopology>"),
        ]
        with self.assertRaises(VanillaLookupError) as ctx:
            coalesce_identical_scalar_texts(
                nodes, name="BlockTopology", source="conflict"
            )
        self.assertIn("conflicting", str(ctx.exception))

    def test_malformed_empty_duplicate_rejects(self) -> None:
        nodes = [
            ET.fromstring("<BlockTopology>TriangleMesh</BlockTopology>"),
            ET.fromstring("<BlockTopology></BlockTopology>"),
        ]
        with self.assertRaises(VanillaLookupError) as ctx:
            coalesce_identical_scalar_texts(
                nodes, name="BlockTopology", source="empty-dup"
            )
        self.assertIn("empty", str(ctx.exception))

    def test_duplicate_cubesize_is_not_relaxed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            game.mkdir()
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                (
                    "    <Definition>\n"
                    "      <Id>\n"
                    "        <TypeId>CubeBlock</TypeId>\n"
                    "        <SubtypeId>TwoSizes</SubtypeId>\n"
                    "      </Id>\n"
                    "      <CubeSize>Large</CubeSize>\n"
                    "      <CubeSize>Large</CubeSize>\n"
                    '      <Size x="1" y="1" z="1" />\n'
                    "      <BlockTopology>TriangleMesh</BlockTopology>\n"
                    "      <Model>Models\\Cubes\\Large\\light.mwm</Model>\n"
                    "    </Definition>\n"
                ),
            )
            hit = lookup_exact_subtype("TwoSizes", game)
        assert hit is not None
        self.assertIsNone(hit.definition)
        self.assertIn("exactly one CubeSize", hit.unusable_reason or "")

    def test_definition_with_two_identical_topologies_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            game.mkdir()
            sdk.mkdir()
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "DupTopo",
                    extra='      <Size x="1" y="1" z="1" />\n',
                    topologies=("TriangleMesh", "TriangleMesh"),
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "DupTopo", load_default_catalog(), game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        assert result.runtime is not None
        self.assertEqual(result.runtime.catalog_entry.observed.block_topology, "TriangleMesh")


class EmptySubtypeIdentityTests(unittest.TestCase):
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

    def test_unique_empty_subtype_and_builder_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _empty_subtype_definition("GravityGenerator")
                + _definition_xml(
                    "LargeBlockGravityGeneratorSphere",
                    type_id="GravityGeneratorSphere",
                    model="Models\\Cubes\\Large\\other.mwm",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/GravityGenerator.fbx")
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type="MyObjectBuilder_GravityGenerator",
                game_root=game,
                sdk_root=sdk,
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(result.subtype_id, "")
        assert result.runtime is not None
        self.assertEqual(result.runtime.catalog_entry.subtype_id, "")
        self.assertEqual(result.runtime.catalog_entry.observed.type_id, "GravityGenerator")
        self.assertEqual(
            result.runtime.geometry_id,
            vanilla_runtime_geometry_id_for_empty_type("GravityGenerator"),
        )
        self.assertIn(VANILLA_RUNTIME_EMPTY_TYPE_INFIX, result.runtime.geometry_id)
        self.assertTrue(
            result.runtime.geometry_id.startswith(VANILLA_RUNTIME_GEOMETRY_PREFIX)
        )

    def test_ambiguous_empty_subtype_remains_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "a.sbc",
                _empty_subtype_definition("OxygenTank"),
            )
            _write_cube_blocks(
                game,
                "b.sbc",
                _empty_subtype_definition(
                    "OxygenTank", model="Models\\Cubes\\Large\\OxygenStorage.mwm"
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/GravityGenerator.fbx")
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type="MyObjectBuilder_OxygenTank",
                game_root=game,
                sdk_root=sdk,
            )
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("duplicate empty-SubtypeId", result.unresolved_reason or "")

    def test_missing_builder_type_remains_unresolved(self) -> None:
        result = resolve_vanilla_geometry("", self.catalog)
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("missing an object-builder type", result.unresolved_reason or "")

    def test_unknown_builder_remains_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks.sbc", _definition_xml("SomeBlock"))
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type="MyObjectBuilder_NotARealThing",
                game_root=game,
                sdk_root=sdk,
            )
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("no unique vanilla definition", result.unresolved_reason or "")

    def test_empty_subtype_does_not_match_nonempty_by_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_xml(
                    "OxygenTankSmall",
                    type_id="OxygenTank",
                    model="Models\\Cubes\\Large\\OxygenStorage.mwm",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/OxygenStorage.fbx")
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type="MyObjectBuilder_OxygenTank",
                game_root=game,
                sdk_root=sdk,
            )
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("no unique vanilla definition", result.unresolved_reason or "")

    def test_large_and_small_empty_subtype_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _empty_subtype_definition("OxygenGenerator")
                + _empty_subtype_definition(
                    "OxygenGenerator",
                    cube_size="Small",
                    model="Models\\Cubes\\Small\\OxygenGenerator.mwm",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/GravityGenerator.fbx")
            large = lookup_unique_empty_subtype(
                "OxygenGenerator", cube_size="Large", game_root=game
            )
            small = lookup_unique_empty_subtype(
                "OxygenGenerator", cube_size="Small", game_root=game
            )
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type="MyObjectBuilder_OxygenGenerator",
                game_root=game,
                sdk_root=sdk,
            )
        self.assertIsNotNone(large)
        self.assertIsNotNone(small)
        assert large is not None and small is not None
        self.assertEqual(large.cube_size, "Large")
        self.assertEqual(small.cube_size, "Small")
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)

    def test_modded_definitions_are_excluded_from_vanilla_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _empty_subtype_definition("GravityGenerator"),
            )
            _write_fbx(sdk, "Models/Cubes/Large/GravityGenerator.fbx")
            other = Path(tmp) / "mod"
            other.mkdir()
            _write_cube_blocks(
                other,
                "CubeBlocks.sbc",
                _empty_subtype_definition(
                    "GravityGenerator",
                    model="Models\\Cubes\\Large\\ModdedGravity.mwm",
                ),
            )
            vanilla = lookup_unique_empty_subtype(
                "GravityGenerator", cube_size="Large", game_root=game
            )
            modded = lookup_unique_empty_subtype(
                "GravityGenerator", cube_size="Large", game_root=other
            )
            self.assertIsNotNone(modded)
            assert modded is not None and modded.definition is not None
            self.assertNotEqual(
                vanilla.definition.primary_model if vanilla and vanilla.definition else None,
                modded.definition.primary_model,
            )
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type="MyObjectBuilder_GravityGenerator",
                game_root=game,
                sdk_root=sdk,
            )
        assert vanilla is not None and vanilla.definition is not None
        self.assertEqual(
            vanilla.definition.primary_model, "Models\\Cubes\\Large\\GravityGenerator.mwm"
        )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)

    def test_identity_key_is_deterministic_and_not_a_subtype(self) -> None:
        first = runtime_placement_key("", "MyObjectBuilder_GravityGenerator")
        second = runtime_placement_key("", "MyObjectBuilder_GravityGenerator")
        self.assertEqual(first, second)
        self.assertEqual(first, empty_subtype_placement_key("GravityGenerator"))
        self.assertNotEqual(first, "GravityGenerator")
        self.assertTrue(first.startswith("empty-type/"))

    def test_geometry_id_collision_fails_closed(self) -> None:
        identity = vanilla_runtime_geometry_id_for_empty_type("GravityGenerator")
        with patch(
            "se2cad.vanilla.identity.packaged_library_geometry_ids",
            return_value=frozenset({identity}),
        ):
            with self.assertRaises(ValueError) as ctx:
                vanilla_runtime_geometry_id_for_empty_type("GravityGenerator")
        self.assertIn("collides", str(ctx.exception))

    def test_nonempty_subtype_behavior_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks.sbc", _definition_xml("LargeBlockFrontLight"))
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            result = resolve_vanilla_geometry(
                "LargeBlockFrontLight",
                self.catalog,
                object_builder_type="MyObjectBuilder_LightingBlock",
                game_root=game,
                sdk_root=sdk,
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(
            result.runtime.geometry_id if result.runtime else None,
            vanilla_runtime_geometry_id("LargeBlockFrontLight"),
        )

    def test_parser_rejects_unidentified_empty_subtype(self) -> None:
        xml = _document(_block(""))
        with self.assertRaises(MissingRequiredFieldError) as ctx:
            parse_blueprint_xml(xml, source="unidentified-empty")
        self.assertIn("unidentified", str(ctx.exception))
        omitted = _document(
            '            <MyObjectBuilder_CubeBlock>\n'
            "              <SubtypeName />\n"
            "            </MyObjectBuilder_CubeBlock>"
        )
        with self.assertRaises(MissingRequiredFieldError):
            parse_blueprint_xml(omitted, source="omitted-builder-empty")

    def test_empty_subtype_component_name_uses_geometry_id(self) -> None:
        from se2cad.ir.naming import component_name_from_block
        from se2cad.ir.convert import canonical_block_from_parsed
        from se2cad.catalog.model import RecipeKind, SupportStatus
        from se2cad.transform.placement import QUALIFIED_ONE_BY_ONE_PLACEMENT

        xml = _document(_block("", xsi_type="MyObjectBuilder_GravityGenerator"))
        parsed = parse_blueprint_xml(xml, source="empty-name")
        block = canonical_block_from_parsed(
            parsed.grid.blocks[0],
            geometry_id="vanilla_lg_1x1x1_empty_gravity_generator",
            recipe_kind=RecipeKind.SDK_MESH_DIRECT,
            support_status=SupportStatus.SUPPORTED,
            pitch_mm=2500,
            placement=QUALIFIED_ONE_BY_ONE_PLACEMENT,
        )
        self.assertEqual(block.subtype_id, "")
        name = component_name_from_block(block)
        self.assertTrue(name.startswith("vanilla_lg_1x1x1_empty_gravity_generator"))
        self.assertNotIn("GravityGenerator_x", name)

    def test_object_builder_type_is_retained(self) -> None:
        xml = _document(
            _block("", xsi_type="MyObjectBuilder_GravityGenerator")
        )
        parsed = parse_blueprint_xml(xml, source="empty-gravity")
        block = parsed.grid.blocks[0]
        self.assertEqual(block.subtype_id, "")
        self.assertEqual(block.object_builder_type, "MyObjectBuilder_GravityGenerator")


class RuntimeEligibilityCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_vanilla_runtime_state()
        self.catalog = load_default_catalog()

    def tearDown(self) -> None:
        clear_vanilla_runtime_state()

    def test_parse_gap_identities_resolve_when_roots_configured(self) -> None:
        game = os.environ.get("SE2CAD_GAME_ROOT")
        sdk = os.environ.get("SE2CAD_SDK_ROOT")
        if not game or not sdk:
            from se2cad.vanilla.roots import (
                try_load_game_content_root,
                try_load_sdk_root,
            )

            game_root = try_load_game_content_root()
            sdk_root = try_load_sdk_root()
            if game_root is None or sdk_root is None:
                self.skipTest("operator game/SDK roots are not configured")
        else:
            game_root = Path(game)
            sdk_root = Path(sdk)
        for subtype_id in _PARSE_GAP_SUBTYPES:
            result = resolve_vanilla_geometry(
                subtype_id, self.catalog, game_root=game_root, sdk_root=sdk_root
            )
            self.assertEqual(
                result.kind,
                VanillaResolveKind.RUNTIME_VANILLA,
                msg=f"{subtype_id}: {result.unresolved_reason}",
            )
            assert result.runtime is not None
            self.assertEqual(result.runtime.catalog_entry.observed.block_topology, "TriangleMesh")
            self.assertGreaterEqual(result.runtime.placement.size.x, 1)
            self.assertFalse(geometry_supports_chamfer(result.runtime.geometry_id))
            record = lookup_record(result.runtime.geometry_id)
            self.assertFalse(record.chamfer_capable)

    def test_empty_subtype_builders_resolve_when_roots_configured(self) -> None:
        from se2cad.vanilla.roots import try_load_game_content_root, try_load_sdk_root

        game_root = try_load_game_content_root()
        sdk_root = try_load_sdk_root()
        if game_root is None or sdk_root is None:
            self.skipTest("operator game/SDK roots are not configured")
        builders = (
            "MyObjectBuilder_GravityGenerator",
            "MyObjectBuilder_OxygenTank",
            "MyObjectBuilder_OxygenGenerator",
        )
        for builder in builders:
            result = resolve_vanilla_geometry(
                "",
                self.catalog,
                object_builder_type=builder,
                game_root=game_root,
                sdk_root=sdk_root,
            )
            self.assertEqual(
                result.kind,
                VanillaResolveKind.RUNTIME_VANILLA,
                msg=f"{builder}: {result.unresolved_reason}",
            )
            assert result.runtime is not None
            self.assertEqual(result.runtime.catalog_entry.subtype_id, "")
            self.assertIn(VANILLA_RUNTIME_EMPTY_TYPE_INFIX, result.runtime.geometry_id)
            self.assertIsNotNone(lookup_runtime_placement(runtime_placement_key("", builder)))

    def test_demand_generation_reuses_empty_subtype_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            generated = Path(tmp) / "generated"
            game.mkdir()
            sdk.mkdir()
            generated.mkdir()
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _empty_subtype_definition("GravityGenerator"),
            )
            _write_fbx(sdk, "Models/Cubes/Large/GravityGenerator.fbx")
            xml = _document(
                "\n".join(
                    [
                        _block("", xsi_type="MyObjectBuilder_GravityGenerator"),
                        _block(
                            "",
                            xsi_type="MyObjectBuilder_GravityGenerator",
                            min_xml='<Min x="2" y="0" z="0" />',
                        ),
                    ]
                )
            )
            parsed = parse_blueprint_xml(xml, source="empty-reuse")
            with patch.dict(
                "os.environ",
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                preflight = compute_conversion_preflight(parsed, self.catalog)
                self.assertTrue(preflight.all_supported)
                self.assertEqual(preflight.supported_count, 2)
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
                geometry_ids = demanded_untreated_geometry_ids(converted.ir)
                self.assertEqual(len(geometry_ids), 1)
                config = _config(generated)
                with patch(
                    "se2cad.solidworks.generate.generate_canonical_parts",
                    side_effect=_fake_generate,
                ):
                    first = ensure_untreated_canonical_parts(config, geometry_ids)
                    second = ensure_untreated_canonical_parts(config, geometry_ids)
            self.assertEqual(first.generated, geometry_ids)
            self.assertEqual(first.reused, ())
            self.assertEqual(second.generated, ())
            self.assertEqual(second.reused, geometry_ids)
            self.assertFalse(geometry_supports_chamfer(geometry_ids[0]))

    def test_builder_failure_hard_fails_once_supported(self) -> None:
        from se2cad.catalog import FILLER_GEOMETRY_ID

        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            generated = Path(tmp) / "generated"
            game.mkdir()
            sdk.mkdir()
            generated.mkdir()
            _write_cube_blocks(
                game,
                "CubeBlocks.sbc",
                _definition_without_size(
                    "LadderShaft",
                    extra=_child_size(),
                    model="Models\\Cubes\\large\\LadderShaft.mwm",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/large/LadderShaft.fbx")
            xml = _document(_block("LadderShaft"))
            parsed = parse_blueprint_xml(xml, source="ladder-fail")
            with patch.dict(
                "os.environ",
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
                geometry_ids = demanded_untreated_geometry_ids(converted.ir)
                self.assertEqual(converted.ir.grid.blocks[0].geometry_id, geometry_ids[0])
                config = _config(generated)

                def _boom(*_args, **_kwargs):
                    raise RuntimeError("builder exploded")

                self.assertNotEqual(geometry_ids[0], FILLER_GEOMETRY_ID)
                with patch(
                    "se2cad.solidworks.generate.generate_canonical_parts",
                    side_effect=_boom,
                ):
                    with self.assertRaises(RuntimeError):
                        ensure_untreated_canonical_parts(config, geometry_ids)

    def test_cubetopology_round_and_small_grid_remain_unresolved(self) -> None:
        from se2cad.vanilla.roots import try_load_game_content_root, try_load_sdk_root

        game_root = try_load_game_content_root()
        sdk_root = try_load_sdk_root()
        if game_root is None or sdk_root is None:
            self.skipTest("operator game/SDK roots are not configured")
        for subtype_id in _CUBETOPOLOGY_REMAINING:
            result = resolve_vanilla_geometry(
                subtype_id, self.catalog, game_root=game_root, sdk_root=sdk_root
            )
            self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        small = resolve_vanilla_geometry(
            "SmallBlockArmorBlock",
            self.catalog,
            game_root=game_root,
            sdk_root=sdk_root,
        )
        self.assertEqual(small.kind, VanillaResolveKind.UNRESOLVED)

    def test_packaged_catalog_is_unchanged(self) -> None:
        catalog = load_default_catalog()
        self.assertEqual(len(catalog.entries), 13)
        packaged = default_catalog_path().read_text(encoding="utf-8")
        for token in _PARSE_GAP_SUBTYPES:
            self.assertNotIn(token, packaged)
        self.assertNotIn("GravityGenerator", packaged)
        self.assertNotIn("empty_", packaged)


class CoalesceHelperContractTests(unittest.TestCase):
    def test_helper_is_explicitly_identical_scalar_only(self) -> None:
        source = Path("src/se2cad/vanilla/lookup.py").read_text(encoding="utf-8")
        self.assertIn("Coalesce identical scalar duplicates", source)
        self.assertIn("coalesce_identical_scalar_texts", source)
        self.assertIn("_read_xyz_strings", source)
        self.assertIn("not a general child-collection vector parser", source)
