"""Ordinary tests for S2C-11.8.1 demand-driven vanilla TriangleMesh resolution."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    AUTHORIZED_SDK_MESH_GEOMETRY_ID,
    AUTHORIZED_SDK_MESH_SUBTYPE_ID,
    FILLER_GEOMETRY_ID,
    RecipeKind,
    SupportStatus,
    default_catalog_path,
    load_default_catalog,
)
from se2cad.library import (
    SdkMeshRecipe,
    all_library_records,
    geometry_supports_chamfer,
    lookup_recipe,
    lookup_record,
)
from se2cad.parser import UnsupportedBlueprintError, parse_blueprint_xml
from se2cad.policy import ConversionPolicy, ConversionRefusedError, convert_blueprint
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight
from se2cad.solidworks import (
    has_qualified_untreated_builder,
    logical_part_filename,
)
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.errors import MissingCanonicalPartError, SdkSourceError
from se2cad.solidworks.materialize import (
    demanded_untreated_geometry_ids,
    ensure_untreated_canonical_parts,
)
from se2cad.solidworks.sdk_source import resolve_sdk_mesh_file
from se2cad.vanilla import (
    VANILLA_RUNTIME_GEOMETRY_PREFIX,
    VanillaLookupError,
    VanillaResolveKind,
    VanillaRootError,
    clear_vanilla_runtime_state,
    load_game_content_root,
    load_sdk_root,
    resolve_vanilla_geometry,
    vanilla_runtime_geometry_id,
)

_LIGHT = "LargeBlockFrontLight"
_BATTERY = "LargeBlockBatteryBlock"
_MODDED = "ModdedUnknownBlock"


def _document(blocks: str, identity: str = "se2cad-vanilla-probe") -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <CubeGrids>
        <CubeGrid>
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


def _block(
    subtype: str,
    *,
    xsi_type: str = "MyObjectBuilder_CubeBlock",
    min_xml: str = "",
    extra: str = "",
) -> str:
    pieces = [f"              <SubtypeName>{subtype}</SubtypeName>"]
    if min_xml:
        pieces.append(f"              {min_xml}")
    if extra:
        pieces.append(f"              {extra}")
    inner = "\n".join(pieces)
    return (
        f'            <MyObjectBuilder_CubeBlock xsi:type="{xsi_type}">\n'
        f"{inner}\n"
        "            </MyObjectBuilder_CubeBlock>"
    )


def _definition_xml(
    subtype: str,
    *,
    cube_size: str = "Large",
    size: tuple[int, int, int] = (1, 1, 1),
    topology: str = "TriangleMesh",
    model: str | None = "Models\\Cubes\\Large\\light.mwm",
    extra: str = "",
    type_id: str = "CubeBlock",
) -> str:
    model_xml = f"      <Model>{model}</Model>\n" if model is not None else ""
    return (
        "    <Definition>\n"
        "      <Id>\n"
        f"        <TypeId>{type_id}</TypeId>\n"
        f"        <SubtypeId>{subtype}</SubtypeId>\n"
        "      </Id>\n"
        f"      <CubeSize>{cube_size}</CubeSize>\n"
        f'      <Size x="{size[0]}" y="{size[1]}" z="{size[2]}" />\n'
        f"      <BlockTopology>{topology}</BlockTopology>\n"
        f"{model_xml}"
        f"{extra}"
        "    </Definition>\n"
    )


def _write_cube_blocks(game_root: Path, filename: str, definitions: str) -> Path:
    directory = game_root / "Data" / "CubeBlocks"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(
        '<?xml version="1.0"?>\n'
        "<Definitions>\n"
        "  <CubeBlocks>\n"
        f"{definitions}"
        "  </CubeBlocks>\n"
        "</Definitions>\n",
        encoding="utf-8",
    )
    return path


def _write_fbx(
    sdk_root: Path,
    relative: str,
    payload: bytes = b"Kaydara FBX Binary  \x1a\x00",
) -> Path:
    path = sdk_root.joinpath(*relative.replace("\\", "/").split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _config(root: Path) -> SolidWorksBackendConfig:
    return SolidWorksBackendConfig(
        generated_root=root.resolve(),
        part_template=None,
        visible=False,
        source="test",
    )


def _fake_generate(config, treatment=None, geometry_ids=None):
    for geometry_id in geometry_ids or ():
        name = logical_part_filename(geometry_id)
        (config.generated_root / name).write_bytes(b"generated")
    return ()


class VanillaResolveTests(unittest.TestCase):
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

    def _eligible_light(self, game: Path, sdk: Path) -> None:
        _write_cube_blocks(
            game,
            "CubeBlocks_Lights.sbc",
            _definition_xml(_LIGHT, model="Models\\Cubes\\Large\\light.mwm"),
        )
        _write_fbx(sdk, "Models/Cubes/Large/Light.FBX")
        _write_fbx(sdk, "Models/Cubes/Large/Light_Construction_1.fbx")
        _write_fbx(sdk, "Models/Cubes/Large/Light_LOD1.fbx")
        _write_fbx(sdk, "Models/Cubes/Large/BatteryLarge.fbx")

    def test_packaged_identities_bypass_runtime_resolution(self) -> None:
        result = resolve_vanilla_geometry("LargeBlockArmorBlock", self.catalog)
        self.assertEqual(result.kind, VanillaResolveKind.PACKAGED)
        self.assertEqual(result.catalog_entry.geometry_id, "large_armor_block")
        self.assertIsNone(result.runtime)

    def test_authorized_thruster_still_uses_hand_bind(self) -> None:
        result = resolve_vanilla_geometry(AUTHORIZED_SDK_MESH_SUBTYPE_ID, self.catalog)
        self.assertEqual(result.kind, VanillaResolveKind.PACKAGED)
        self.assertEqual(result.catalog_entry.geometry_id, AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        recipe = lookup_recipe(AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        self.assertIsInstance(recipe, SdkMeshRecipe)
        self.assertEqual(
            recipe.relative_source_stem, "Models/Cubes/Large/HydrogenThrusterSmall"
        )
        self.assertTrue(has_qualified_untreated_builder(AUTHORIZED_SDK_MESH_GEOMETRY_ID))
        self.assertFalse(geometry_supports_chamfer(AUTHORIZED_SDK_MESH_GEOMETRY_ID))

    def test_unknown_one_by_one_triangle_mesh_resolves_dynamically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            first = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
            second = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(first.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(second.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(first.runtime, second.runtime)
        self.assertEqual(
            first.runtime.geometry_id, vanilla_runtime_geometry_id(_LIGHT)
        )
        self.assertTrue(
            first.runtime.geometry_id.startswith(VANILLA_RUNTIME_GEOMETRY_PREFIX)
        )
        self.assertEqual(
            first.runtime.library_record.recipe.relative_source_stem,
            "Models/Cubes/Large/light",
        )
        self.assertEqual(first.runtime.sdk_source_relative, "Models/Cubes/Large/Light.FBX")
        self.assertFalse(first.runtime.library_record.chamfer_capable)
        self.assertEqual(first.runtime.catalog_entry.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(len(all_library_records()), 8)

    def test_runtime_record_is_not_persisted_into_packaged_catalog(self) -> None:
        path = default_catalog_path()
        before = path.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            resolve_vanilla_geometry(_LIGHT, self.catalog, game_root=game, sdk_root=sdk)
        after = path.read_text(encoding="utf-8")
        self.assertEqual(before, after)
        self.assertNotIn(VANILLA_RUNTIME_GEOMETRY_PREFIX, after)
        reloaded = load_default_catalog()
        subtypes = [entry.subtype_id for entry in reloaded.entries]
        self.assertNotIn(_LIGHT, subtypes)
        self.assertEqual(len(reloaded.entries), len(self.catalog.entries))

    def test_small_grid_and_cube_topology_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Mixed.sbc",
                _definition_xml("SmallBlockLight", cube_size="Small")
                + _definition_xml(
                    "LargeBlockArmorCube",
                    topology="Cube",
                    model=None,
                    extra="      <CubeDefinition><CubeTopology>Box</CubeTopology></CubeDefinition>\n",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            small = resolve_vanilla_geometry(
                "SmallBlockLight", self.catalog, game_root=game, sdk_root=sdk
            )
            cube = resolve_vanilla_geometry(
                "LargeBlockArmorCube", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(small.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("not Large", small.unresolved_reason)
        self.assertEqual(cube.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("TriangleMesh", cube.unresolved_reason)

    def test_eligible_multi_cell_triangle_mesh_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Wide.sbc",
                _definition_xml(
                    "LargeBlockWide",
                    size=(2, 1, 1),
                    model="Models\\Cubes\\Large\\wide.mwm",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/wide.fbx")
            wide = resolve_vanilla_geometry(
                "LargeBlockWide", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(wide.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(wide.runtime.catalog_entry.observed.size.x, 2)
        self.assertEqual(
            wide.runtime.geometry_id,
            vanilla_runtime_geometry_id("LargeBlockWide", wide.runtime.catalog_entry.observed.size),
        )
        self.assertFalse(
            wide.runtime.geometry_id.startswith(VANILLA_RUNTIME_GEOMETRY_PREFIX)
        )

    def test_missing_and_ambiguous_primary_model_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Models.sbc",
                _definition_xml("NoModelBlock", model=None)
                + _definition_xml(
                    "TwoModelBlock",
                    extra="      <Model>Models\\Cubes\\Large\\a.mwm</Model>\n"
                    "      <Model>Models\\Cubes\\Large\\b.mwm</Model>\n",
                    model=None,
                )
                + _definition_xml(
                    "SubpartBlock",
                    extra="      <Subparts><Subpart><Name>x</Name></Subpart></Subparts>\n",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/light.fbx")
            missing = resolve_vanilla_geometry(
                "NoModelBlock", self.catalog, game_root=game, sdk_root=sdk
            )
            ambiguous = resolve_vanilla_geometry(
                "TwoModelBlock", self.catalog, game_root=game, sdk_root=sdk
            )
            subparts = resolve_vanilla_geometry(
                "SubpartBlock", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertIn("missing", missing.unresolved_reason)
        self.assertIn("ambiguous", ambiguous.unresolved_reason)
        self.assertIn("subpart", subparts.unresolved_reason)

    def test_missing_game_and_sdk_roots_fail_clearly_where_needed(self) -> None:
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"SE2CAD_GAME_ROOT", "SE2CAD_SDK_ROOT"}
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("se2cad.vanilla.roots.discover_local_config", return_value=None):
                with self.assertRaises(VanillaRootError) as game_ctx:
                    load_game_content_root()
                with self.assertRaises(VanillaRootError) as sdk_ctx:
                    load_sdk_root()
                result = resolve_vanilla_geometry(_LIGHT, self.catalog)
        self.assertIn("game-content root", str(game_ctx.exception))
        self.assertIn("SDK root", str(sdk_ctx.exception))
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("game-content root is not configured", result.unresolved_reason)

    def test_eligible_without_sdk_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, _sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Lights.sbc",
                _definition_xml(_LIGHT),
            )
            env = {
                key: value
                for key, value in os.environ.items()
                if key not in {"SE2CAD_SDK_ROOT"}
            }
            with patch.dict(os.environ, env, clear=True):
                with patch(
                    "se2cad.vanilla.resolve.try_load_sdk_root", return_value=None
                ):
                    with self.assertRaises(VanillaRootError) as ctx:
                        resolve_vanilla_geometry(
                            _LIGHT, self.catalog, game_root=game
                        )
        self.assertIn("SDK root", str(ctx.exception))

    def test_missing_definition_remains_unknown_not_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks_Empty.sbc", "")
            result = resolve_vanilla_geometry(
                "NoSuchVanillaBlock", self.catalog, game_root=game, sdk_root=sdk
            )
            parsed = parse_blueprint_xml(
                _document(_block("NoSuchVanillaBlock")), source="missing-def"
            )
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                report = compute_conversion_preflight(parsed, self.catalog)
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertEqual(report.unknown_count, 1)
        self.assertEqual(report.supported_count, 0)
        self.assertEqual(report.blocks[0].catalog_outcome, CatalogOutcome.UNKNOWN)

    def test_duplicate_subtype_id_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            body = _definition_xml(_LIGHT)
            _write_cube_blocks(game, "CubeBlocks_A.sbc", body)
            _write_cube_blocks(game, "CubeBlocks_B.sbc", body)
            _write_fbx(sdk, "Models/Cubes/Large/Light.FBX")
            with self.assertRaises(VanillaLookupError) as ctx:
                resolve_vanilla_geometry(
                    _LIGHT, self.catalog, game_root=game, sdk_root=sdk
                )
        self.assertIn("duplicate SubtypeId", str(ctx.exception))

    def test_ascii_fbx_stays_unresolved_before_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks_Lights.sbc", _definition_xml(_LIGHT))
            path = _write_fbx(sdk, "Models/Cubes/Large/light.fbx", b"; FBX 7.2.0 project file\n")
            self.assertTrue(path.is_file())
            result = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertTrue(
            "not a valid ASCII FBX" in (result.unresolved_reason or "")
            or "not a binary FBX" in (result.unresolved_reason or ""),
            msg=result.unresolved_reason,
        )

    def test_missing_sdk_fbx_stays_unresolved_before_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(game, "CubeBlocks_Lights.sbc", _definition_xml(_LIGHT))
            result = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("is not a file", result.unresolved_reason)
        with self.assertRaises(Exception):
            lookup_record(vanilla_runtime_geometry_id(_LIGHT))

    def test_sdk_source_traversal_is_impossible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Escape.sbc",
                _definition_xml(
                    "EscapeBlock",
                    model="..\\..\\Windows\\evil.mwm",
                ),
            )
            result = resolve_vanilla_geometry(
                "EscapeBlock", self.catalog, game_root=game, sdk_root=sdk
            )
            recipe = lookup_recipe(AUTHORIZED_SDK_MESH_GEOMETRY_ID)
            with self.assertRaises(SdkSourceError):
                resolve_sdk_mesh_file(
                    SdkMeshRecipe(
                        geometry_id="vanilla_lg_1x1x1_escape_probe",
                        recipe_kind=RecipeKind.SDK_MESH_DIRECT,
                        subtype_id="EscapeBlock",
                        relative_source_stem="../../Windows/evil",
                        source_type="official_modsdk",
                        apply_imported_object_transforms=True,
                        additional_scale=1000.0,
                        rotation_xyz_deg=(90.0, 0.0, 0.0),
                        translation_mm=(0.0, 0.0, 0.0),
                    ),
                    sdk_root=sdk,
                )
        self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIsNotNone(recipe)

    def test_construction_and_lod_fbx_are_not_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            result = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
            source = resolve_sdk_mesh_file(
                result.runtime.library_record.recipe, sdk_root=sdk
            )
        self.assertEqual(source.name, "Light.FBX")
        self.assertNotIn("Construction", source.name)
        self.assertNotIn("LOD", source.name)

    def test_runtime_supported_builder_failure_does_not_become_filler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            parsed = parse_blueprint_xml(_document(_block(_LIGHT)), source="fail-closed")
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                result = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
            self.assertEqual(result.filler_count, 0)
            self.assertEqual(
                result.ir.grid.blocks[0].geometry_id,
                vanilla_runtime_geometry_id(_LIGHT),
            )
            self.assertEqual(
                result.ir.grid.blocks[0].support_status, SupportStatus.SUPPORTED
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
            self.assertEqual(
                result.ir.grid.blocks[0].geometry_id,
                vanilla_runtime_geometry_id(_LIGHT),
            )
            self.assertNotEqual(result.ir.grid.blocks[0].geometry_id, FILLER_GEOMETRY_ID)

    def test_multiple_instances_generate_one_part_and_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            _write_cube_blocks(
                game,
                "CubeBlocks_Energy.sbc",
                _definition_xml(
                    _BATTERY, model="Models\\Cubes\\Large\\BatteryLarge.mwm"
                ),
            )
            xml = _document(
                "\n".join(
                    [
                        _block("LargeBlockArmorBlock"),
                        _block(
                            AUTHORIZED_SDK_MESH_SUBTYPE_ID,
                            xsi_type="MyObjectBuilder_Thrust",
                            min_xml='<Min x="1" y="0" z="0" />',
                        ),
                        _block(_LIGHT, min_xml='<Min x="2" y="0" z="0" />'),
                        _block(_LIGHT, min_xml='<Min x="3" y="0" z="0" />'),
                        _block(
                            _LIGHT,
                            min_xml='<Min x="4" y="0" z="0" />',
                            extra='<ColorMaskHSV x="0" y="0.2" z="0.55" />',
                        ),
                    ]
                )
            )
            parsed = parse_blueprint_xml(xml, source="lazy-vanilla")
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
            ir = converted.ir
            light_id = vanilla_runtime_geometry_id(_LIGHT)
            self.assertEqual(
                demanded_untreated_geometry_ids(ir),
                ("large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID, light_id),
            )
            colors = [block.color_mask_hsv.as_tuple() for block in ir.grid.blocks if block.subtype_id == _LIGHT]
            self.assertEqual(len(set(colors)), 2)
            generated = Path(tmp) / "generated"
            generated.mkdir()
            config = _config(generated)
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ) as generate:
                first = ensure_untreated_canonical_parts(
                    config, demanded_untreated_geometry_ids(ir)
                )
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(
                generate.call_args.kwargs["geometry_ids"],
                ("large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID, light_id),
            )
            self.assertEqual(first.reused, ())
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ) as second_generate:
                second = ensure_untreated_canonical_parts(
                    config, demanded_untreated_geometry_ids(ir)
                )
            self.assertEqual(second_generate.call_count, 0)
            self.assertEqual(second.generated, ())
            self.assertEqual(
                second.reused,
                ("large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID, light_id),
            )

    def test_no_unrelated_fbx_is_accessed(self) -> None:
        opened: list[str] = []
        real_resolve = resolve_sdk_mesh_file

        def _spy(recipe, *, sdk_root=None):
            opened.append(recipe.relative_source_stem)
            return real_resolve(recipe, sdk_root=sdk_root)

        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            with patch(
                "se2cad.solidworks.sdk_source.resolve_sdk_mesh_file",
                side_effect=_spy,
            ):
                resolve_vanilla_geometry(
                    _LIGHT, self.catalog, game_root=game, sdk_root=sdk
                )
        self.assertEqual(opened, ["Models/Cubes/Large/light"])
        self.assertNotIn("Models/Cubes/Large/BatteryLarge", opened)

    def test_procedural_armor_and_unknown_modded_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            xml = _document(
                "\n".join(
                    [
                        _block("LargeBlockArmorSlope"),
                        _block(_LIGHT, min_xml='<Min x="1" y="0" z="0" />'),
                        _block(_MODDED, min_xml='<Min x="2" y="0" z="0" />'),
                    ]
                )
            )
            parsed = parse_blueprint_xml(xml, source="policy-mix")
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                report = compute_conversion_preflight(parsed, self.catalog)
                with self.assertRaises(ConversionRefusedError):
                    convert_blueprint(parsed, self.catalog, ConversionPolicy.STRICT)
                permitted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.PERMISSIVE
                )
                light_only = parse_blueprint_xml(
                    _document(_block(_LIGHT)), source="strict-light"
                )
                accepted = convert_blueprint(
                    light_only, self.catalog, ConversionPolicy.STRICT
                )
                unresolved_only = parse_blueprint_xml(
                    _document(_block(_MODDED)), source="strict-modded"
                )
                with self.assertRaises(ConversionRefusedError):
                    convert_blueprint(
                        unresolved_only, self.catalog, ConversionPolicy.STRICT
                    )
        self.assertEqual(report.supported_count, 2)
        self.assertEqual(report.unknown_count, 1)
        armor, light, modded = permitted.ir.grid.blocks
        self.assertEqual(armor.geometry_id, "large_armor_slope")
        self.assertEqual(light.geometry_id, vanilla_runtime_geometry_id(_LIGHT))
        self.assertEqual(modded.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(permitted.filler_count, 1)
        self.assertEqual(accepted.filler_count, 0)
        self.assertEqual(
            accepted.ir.grid.blocks[0].recipe_kind, RecipeKind.SDK_MESH_DIRECT
        )

    def test_small_grid_blueprint_behavior_unchanged(self) -> None:
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
              <SubtypeName>LargeBlockFrontLight</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="small-grid-vanilla")

    def test_malicious_subtype_does_not_become_a_path(self) -> None:
        identity = vanilla_runtime_geometry_id("LargeBlockFrontLight")
        self.assertNotIn("/", identity)
        self.assertNotIn("\\", identity)
        self.assertNotIn("..", identity)
        sneaky = vanilla_runtime_geometry_id("EvilBlock")
        self.assertEqual(sneaky, "vanilla_lg_1x1x1_evil_block")
        self.assertTrue(sneaky.startswith(VANILLA_RUNTIME_GEOMETRY_PREFIX))

    def test_empty_subtype_sibling_does_not_hide_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            empty = (
                "    <Definition>\n"
                "      <Id>\n"
                "        <TypeId>Conveyor</TypeId>\n"
                "        <SubtypeId></SubtypeId>\n"
                "      </Id>\n"
                "      <CubeSize>Large</CubeSize>\n"
                '      <Size x="1" y="1" z="1" />\n'
                "      <BlockTopology>TriangleMesh</BlockTopology>\n"
                "    </Definition>\n"
            )
            _write_cube_blocks(
                game,
                "CubeBlocks_Logistics.sbc",
                empty
                + _definition_xml(
                    "LargeBlockConveyor",
                    model="Models\\Cubes\\Large\\conveyor.mwm",
                    type_id="Conveyor",
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/conveyor.fbx")
            result = resolve_vanilla_geometry(
                "LargeBlockConveyor", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(result.runtime.subtype_id, "LargeBlockConveyor")

    def test_qualified_builder_is_false_until_resolution(self) -> None:
        geometry_id = vanilla_runtime_geometry_id(_LIGHT)
        self.assertFalse(has_qualified_untreated_builder(geometry_id))
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible_light(game, sdk)
            resolve_vanilla_geometry(_LIGHT, self.catalog, game_root=game, sdk_root=sdk)
        self.assertTrue(has_qualified_untreated_builder(geometry_id))
        with self.assertRaises(MissingCanonicalPartError):
            ensure_untreated_canonical_parts(
                _config(Path(tempfile.gettempdir()) / "se2cad-missing-unused"),
                ("not_a_bound_geometry",),
            )


if __name__ == "__main__":
    unittest.main()
