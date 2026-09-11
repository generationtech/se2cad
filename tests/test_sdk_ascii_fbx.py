"""Ordinary tests for S2C-11.9.1 ASCII SDK-FBX conversion support."""

from __future__ import annotations

import hashlib
import json
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
    load_default_catalog,
)
from se2cad.library import geometry_supports_chamfer, lookup_record
from se2cad.parser import UnsupportedBlueprintError, parse_blueprint_xml
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.preflight import compute_conversion_preflight
from se2cad.solidworks.com_validate import PartValidation
from se2cad.solidworks.errors import CanonicalPartValidationError, SdkConversionError, SdkSourceError
from se2cad.solidworks.materialize import (
    demanded_untreated_geometry_ids,
    ensure_untreated_canonical_parts,
)
from se2cad.solidworks.sdk_ascii_fbx import (
    normalize_ascii_fbx_to_binary,
    validate_ascii_fbx,
)
from se2cad.solidworks.sdk_convert import (
    _exclusive_work_file,
    assert_imported_mesh_envelope,
    cleanup_work_dir,
    convert_sdk_mesh_to_stl,
    sdk_work_dir,
)
from se2cad.solidworks.sdk_fbx_format import (
    FBX_BINARY_MAGIC,
    FbxSourceKind,
    ascii_fbx_conversion_available,
    classify_sdk_fbx,
    require_usable_sdk_fbx,
)
from se2cad.solidworks.sdk_source import resolve_sdk_mesh_file
from se2cad.vanilla import (
    VanillaResolveKind,
    clear_vanilla_runtime_state,
    resolve_vanilla_geometry,
    vanilla_runtime_geometry_id,
)

from tests.test_vanilla_resolve import (
    _BATTERY,
    _LIGHT,
    _block,
    _config,
    _definition_xml,
    _document,
    _fake_generate,
    _write_cube_blocks,
    _write_fbx,
)

_CONVEYOR = "LargeBlockConveyor"
_GYRO = "LargeBlockGyro"
_BINARY_STUB = b"Kaydara FBX Binary  \x1a\x00"


def _minimal_ascii_fbx(
    *,
    version: int = 7200,
    vertices: tuple[float, ...] = (-1.0, -1.0, 0.0, 1.0, -1.0, 0.0, 0.0, 1.0, 0.0),
    indices: tuple[int, ...] = (0, 1, -3),
) -> str:
    vert_csv = ",".join(str(value) for value in vertices)
    ind_csv = ",".join(str(value) for value in indices)
    return (
        "; FBX 7.2.0 project file\n"
        "FBXHeaderExtension:  {\n"
        "\tFBXHeaderVersion: 1003\n"
        f"\tFBXVersion: {version}\n"
        "}\n"
        "GlobalSettings:  {\n"
        "\tVersion: 1000\n"
        "\tProperties70:  {\n"
        '\t\tP: "UpAxis", "int", "Integer", "",1\n'
        '\t\tP: "UnitScaleFactor", "double", "Number", "",1\n'
        "\t}\n"
        "}\n"
        "Objects:  {\n"
        '\tGeometry: 100, "Geometry::", "Mesh" {\n'
        f"\t\tVertices: *{len(vertices)} {{\n"
        f"\t\t\ta: {vert_csv}\n"
        "\t\t}\n"
        f"\t\tPolygonVertexIndex: *{len(indices)} {{\n"
        f"\t\t\ta: {ind_csv}\n"
        "\t\t}\n"
        "\t}\n"
        '\tModel: 200, "Model::Probe", "Mesh" {\n'
        "\t\tProperties70:  {\n"
        '\t\t\tP: "Lcl Translation", "Lcl Translation", "", "A",0,0,0\n'
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "Connections:  {\n"
        '\tC: "OO",100,200\n'
        '\tC: "OO",200,0\n'
        "}\n"
    )


def _write_ascii(sdk: Path, relative: str, text: str | None = None) -> Path:
    return _write_fbx(sdk, relative, (text or _minimal_ascii_fbx()).encode("utf-8"))


class AsciiFbxFormatTests(unittest.TestCase):
    def test_binary_fbx_remains_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.fbx"
            path.write_bytes(_BINARY_STUB)
            classified = classify_sdk_fbx(path)
            accepted = require_usable_sdk_fbx(path)
            self.assertEqual(classified.kind, FbxSourceKind.BINARY)
            self.assertEqual(accepted.kind, FbxSourceKind.BINARY)
            self.assertTrue(path.read_bytes().startswith(FBX_BINARY_MAGIC))

    def test_valid_ascii_is_eligible_only_when_conversion_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.fbx"
            path.write_text(_minimal_ascii_fbx(), encoding="utf-8")
            available = classify_sdk_fbx(path)
            self.assertEqual(available.kind, FbxSourceKind.ASCII)
            self.assertTrue(ascii_fbx_conversion_available())
            require_usable_sdk_fbx(path)
            with patch(
                "se2cad.solidworks.sdk_fbx_format.ascii_fbx_conversion_available",
                return_value=False,
            ):
                with self.assertRaises(SdkSourceError) as ctx:
                    require_usable_sdk_fbx(path)
        self.assertIn("ASCII FBX conversion is not available", str(ctx.exception))

    def test_invalid_truncated_and_random_text_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid = root / "header.fbx"
            invalid.write_text("; FBX 7.2.0 project file\n", encoding="utf-8")
            truncated = root / "truncated.fbx"
            truncated.write_text(
                _minimal_ascii_fbx().rsplit("PolygonVertexIndex", 1)[0],
                encoding="utf-8",
            )
            random_text = root / "random.fbx"
            random_text.write_text("this is not an fbx file at all\n", encoding="utf-8")
            self.assertEqual(classify_sdk_fbx(invalid).kind, FbxSourceKind.INVALID)
            self.assertEqual(classify_sdk_fbx(truncated).kind, FbxSourceKind.INVALID)
            self.assertEqual(classify_sdk_fbx(random_text).kind, FbxSourceKind.INVALID)
            for path in (invalid, truncated, random_text):
                with self.assertRaises(SdkSourceError):
                    require_usable_sdk_fbx(path)

    def test_classification_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "bin.fbx"
            ascii_path = Path(tmp) / "ascii.fbx"
            binary.write_bytes(_BINARY_STUB)
            ascii_path.write_text(_minimal_ascii_fbx(), encoding="utf-8")
            first = classify_sdk_fbx(binary)
            second = classify_sdk_fbx(ascii_path)
            self.assertEqual(classify_sdk_fbx(binary), first)
            self.assertEqual(classify_sdk_fbx(ascii_path), second)
            self.assertNotEqual(first.kind, second.kind)

    def test_ascii_path_traversal_is_impossible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = root / "official.fbx"
            source.write_text(_minimal_ascii_fbx(), encoding="utf-8")
            dest = root.parent / "escape.normalized.fbx"
            with self.assertRaises(SdkSourceError) as ctx:
                normalize_ascii_fbx_to_binary(source, dest, generated_root=root)
            self.assertIn("escapes", str(ctx.exception).lower())
            self.assertFalse(dest.exists())

    def test_original_sdk_fbx_is_never_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "official.fbx"
            payload = _minimal_ascii_fbx().encode("utf-8")
            source.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            dest = root / "normalized.fbx"
            report = normalize_ascii_fbx_to_binary(source, dest, generated_root=root)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)
            self.assertTrue(dest.read_bytes().startswith(FBX_BINARY_MAGIC))
            self.assertNotEqual(dest.resolve(), source.resolve())
            self.assertEqual(report.source_sha256, digest)
            self.assertEqual(validate_ascii_fbx(payload.decode("utf-8")), 7200)

    def test_intermediate_stays_under_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated"
            generated.mkdir()
            source = generated / "official.fbx"
            source.write_text(_minimal_ascii_fbx(), encoding="utf-8")
            dest = generated / "_se2cad_sdk_work" / "probe" / "probe.normalized.fbx"
            report = normalize_ascii_fbx_to_binary(source, dest, generated_root=generated)
            report.normalized_path.relative_to(generated.resolve())
            with self.assertRaises(SdkSourceError):
                normalize_ascii_fbx_to_binary(
                    source,
                    Path(tmp) / "outside.fbx",
                    generated_root=generated,
                )

    def test_conversion_errors_include_useful_diagnostics(self) -> None:
        with self.assertRaises(SdkSourceError) as ctx:
            validate_ascii_fbx("FBXHeaderExtension: {\n}\n")
        self.assertIn("FBXVersion", str(ctx.exception))


class AsciiVanillaResolveTests(unittest.TestCase):
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

    def _eligible(
        self,
        game: Path,
        sdk: Path,
        subtype: str,
        model: str,
        *,
        ascii_text: str | None = None,
        type_id: str = "CubeBlock",
    ) -> None:
        _write_cube_blocks(
            game,
            f"CubeBlocks_{subtype}.sbc",
            _definition_xml(subtype, model=model, type_id=type_id),
        )
        stem = Path(model.replace("\\", "/")).stem
        _write_ascii(sdk, f"Models/Cubes/Large/{stem}.fbx", ascii_text)

    def test_conveyor_resolves_without_hand_catalog_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible(
                game,
                sdk,
                _CONVEYOR,
                "Models\\Cubes\\Large\\conveyor.mwm",
                type_id="Conveyor",
            )
            result = resolve_vanilla_geometry(
                _CONVEYOR, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(result.runtime.subtype_id, _CONVEYOR)
        self.assertEqual(
            result.runtime.geometry_id, vanilla_runtime_geometry_id(_CONVEYOR)
        )
        self.assertNotIn(_CONVEYOR, [entry.subtype_id for entry in self.catalog.entries])
        self.assertFalse(result.runtime.library_record.chamfer_capable)

    def test_gyro_resolves_without_hand_catalog_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible(
                game,
                sdk,
                _GYRO,
                "Models\\Cubes\\Large\\gyroscope.mwm",
                type_id="Gyro",
            )
            result = resolve_vanilla_geometry(
                _GYRO, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(result.runtime.subtype_id, _GYRO)
        self.assertNotIn(_GYRO, [entry.subtype_id for entry in self.catalog.entries])

    def test_conveyor_supported_only_after_converter_capability_is_known(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible(
                game,
                sdk,
                _CONVEYOR,
                "Models\\Cubes\\Large\\conveyor.mwm",
                type_id="Conveyor",
            )
            with patch(
                "se2cad.solidworks.sdk_fbx_format.ascii_fbx_conversion_available",
                return_value=False,
            ):
                blocked = resolve_vanilla_geometry(
                    _CONVEYOR, self.catalog, game_root=game, sdk_root=sdk
                )
            clear_vanilla_runtime_state()
            allowed = resolve_vanilla_geometry(
                _CONVEYOR, self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(blocked.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("conversion is not available", blocked.unresolved_reason or "")
        self.assertEqual(allowed.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(allowed.runtime.catalog_entry.support_status, SupportStatus.SUPPORTED)

    def test_runtime_catalog_overlay_is_still_transient(self) -> None:
        from se2cad.catalog import default_catalog_path

        path = default_catalog_path()
        before = path.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible(
                game, sdk, _CONVEYOR, "Models\\Cubes\\Large\\conveyor.mwm", type_id="Conveyor"
            )
            resolve_vanilla_geometry(_CONVEYOR, self.catalog, game_root=game, sdk_root=sdk)
        after = path.read_text(encoding="utf-8")
        self.assertEqual(before, after)
        self.assertNotIn("vanilla_lg_1x1x1_large_block_conveyor", after)

    def test_existing_modded_unknown_remains_filler(self) -> None:
        xml = _document(_block("ModdedUnknownBlock"))
        parsed = parse_blueprint_xml(xml, source="modded")
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                permitted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.PERMISSIVE
                )
        self.assertEqual(permitted.ir.grid.blocks[0].geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(permitted.filler_count, 1)

    def test_multi_cell_ascii_resolves_when_conversion_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Wide.sbc",
                _definition_xml(
                    "LargeBlockLandingGear",
                    size=(1, 2, 3),
                    model="Models\\Cubes\\Large\\landing.mwm",
                ),
            )
            _write_ascii(sdk, "Models/Cubes/Large/landing.fbx")
            result = resolve_vanilla_geometry(
                "LargeBlockLandingGear", self.catalog, game_root=game, sdk_root=sdk
            )
        if ascii_fbx_conversion_available():
            self.assertEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)
            size = result.runtime.catalog_entry.observed.size
            self.assertEqual((size.x, size.y, size.z), (1, 2, 3))
        else:
            self.assertEqual(result.kind, VanillaResolveKind.UNRESOLVED)
            self.assertIn("ascii", (result.unresolved_reason or "").lower())

    def test_small_grid_and_cube_topology_remain_untouched(self) -> None:
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
              <SubtypeName>LargeBlockConveyor</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="small-ascii")
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Armor.sbc",
                _definition_xml(
                    "LargeBlockArmorCube",
                    topology="Cube",
                    model=None,
                    extra="      <CubeDefinition><CubeTopology>Box</CubeTopology></CubeDefinition>\n",
                ),
            )
            cube = resolve_vanilla_geometry(
                "LargeBlockArmorCube", self.catalog, game_root=game, sdk_root=sdk
            )
        self.assertEqual(cube.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIn("TriangleMesh", cube.unresolved_reason or "")

    def test_binary_sdk_mesh_identities_still_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            _write_cube_blocks(
                game,
                "CubeBlocks_Lights.sbc",
                _definition_xml(_LIGHT, model="Models\\Cubes\\Large\\light.mwm")
                + _definition_xml(
                    _BATTERY, model="Models\\Cubes\\Large\\BatteryLarge.mwm"
                ),
            )
            _write_fbx(sdk, "Models/Cubes/Large/Light.FBX")
            _write_fbx(sdk, "Models/Cubes/Large/BatteryLarge.fbx")
            light = resolve_vanilla_geometry(
                _LIGHT, self.catalog, game_root=game, sdk_root=sdk
            )
            battery = resolve_vanilla_geometry(
                _BATTERY, self.catalog, game_root=game, sdk_root=sdk
            )
            thrust = resolve_vanilla_geometry(AUTHORIZED_SDK_MESH_SUBTYPE_ID, self.catalog)
        self.assertEqual(light.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(battery.kind, VanillaResolveKind.RUNTIME_VANILLA)
        self.assertEqual(thrust.kind, VanillaResolveKind.PACKAGED)
        self.assertEqual(thrust.catalog_entry.geometry_id, AUTHORIZED_SDK_MESH_GEOMETRY_ID)

    def test_repeated_instances_generate_once_and_existing_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible(
                game, sdk, _CONVEYOR, "Models\\Cubes\\Large\\conveyor.mwm", type_id="Conveyor"
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
                        _block(
                            _CONVEYOR,
                            xsi_type="MyObjectBuilder_Conveyor",
                            min_xml='<Min x="2" y="0" z="0" />',
                        ),
                        _block(
                            _CONVEYOR,
                            xsi_type="MyObjectBuilder_Conveyor",
                            min_xml='<Min x="3" y="0" z="0" />',
                        ),
                    ]
                )
            )
            parsed = parse_blueprint_xml(xml, source="ascii-lazy")
            with patch.dict(
                os.environ,
                {"SE2CAD_GAME_ROOT": str(game), "SE2CAD_SDK_ROOT": str(sdk)},
            ):
                converted = convert_blueprint(
                    parsed, self.catalog, ConversionPolicy.STRICT
                )
            conveyor_id = vanilla_runtime_geometry_id(_CONVEYOR)
            self.assertEqual(
                demanded_untreated_geometry_ids(converted.ir),
                ("large_armor_block", AUTHORIZED_SDK_MESH_GEOMETRY_ID, conveyor_id),
            )
            generated = Path(tmp) / "generated"
            generated.mkdir()
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ) as generate:
                first = ensure_untreated_canonical_parts(
                    _config(generated), demanded_untreated_geometry_ids(converted.ir)
                )
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(first.reused, ())
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ) as second:
                reused = ensure_untreated_canonical_parts(
                    _config(generated), demanded_untreated_geometry_ids(converted.ir)
                )
            self.assertEqual(second.call_count, 0)
            self.assertEqual(reused.generated, ())
            self.assertIn(conveyor_id, reused.reused)

    def test_chamfer_remains_false_and_scale_sanity_still_holds(self) -> None:
        self.assertFalse(geometry_supports_chamfer(AUTHORIZED_SDK_MESH_GEOMETRY_ID))
        with tempfile.TemporaryDirectory() as tmp:
            game, sdk = self._roots(tmp)
            self._eligible(
                game, sdk, _CONVEYOR, "Models\\Cubes\\Large\\conveyor.mwm", type_id="Conveyor"
            )
            result = resolve_vanilla_geometry(
                _CONVEYOR, self.catalog, game_root=game, sdk_root=sdk
            )
            record = lookup_record(result.runtime.geometry_id)
        self.assertFalse(record.chamfer_capable)
        tiny = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-0.001, -0.001, -0.001),
            bounding_box_max_m=(0.001, 0.001, 0.001),
            volume_m3=1e-8,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        with self.assertRaises(CanonicalPartValidationError):
            assert_imported_mesh_envelope(tiny)


class AsciiConvertHostTests(unittest.TestCase):
    def test_blender_exit_zero_without_output_is_failure(self) -> None:
        recipe = lookup_record(AUTHORIZED_SDK_MESH_GEOMETRY_ID).recipe
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            sdk = generated / "sdk"
            source = sdk / "Models" / "Cubes" / "Large" / "HydrogenThrusterSmall.fbx"
            source.parent.mkdir(parents=True)
            source.write_bytes(_BINARY_STUB)
            work = sdk_work_dir(generated, recipe.geometry_id)
            completed = type("C", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source.resolve(),
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch("se2cad.solidworks.sdk_convert.subprocess.run", return_value=completed):
                with self.assertRaises(SdkConversionError) as ctx:
                    convert_sdk_mesh_to_stl(recipe, work)
        self.assertIn("did not write the intermediate mesh", str(ctx.exception))
        self.assertIn("no diagnostic output", str(ctx.exception))

    def test_blender_script_exception_text_is_surfaced(self) -> None:
        recipe = lookup_record(AUTHORIZED_SDK_MESH_GEOMETRY_ID).recipe
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            source = generated / "HydrogenThrusterSmall.fbx"
            source.write_bytes(_BINARY_STUB)
            work = sdk_work_dir(generated, recipe.geometry_id)
            work.mkdir(parents=True)
            captured = (
                "Traceback (most recent call last):\n"
                "  File \"blender_fbx_to_stl.py\", line 1, in <module>\n"
                "RuntimeError: boom\n"
                "SE2CAD_BLENDER_SCRIPT_FAILED\n"
            )
            completed = type("C", (), {"returncode": 0, "stdout": "", "stderr": captured})()
            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source.resolve(),
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch("se2cad.solidworks.sdk_convert.subprocess.run", return_value=completed):
                with self.assertRaises(SdkConversionError) as ctx:
                    convert_sdk_mesh_to_stl(recipe, work)
        self.assertIn("script exception", str(ctx.exception))
        self.assertIn("RuntimeError: boom", str(ctx.exception))

    def test_intermediate_must_exist_and_binary_skips_ascii_path(self) -> None:
        recipe = lookup_record(AUTHORIZED_SDK_MESH_GEOMETRY_ID).recipe
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            source = generated / "HydrogenThrusterSmall.fbx"
            source.write_bytes(_BINARY_STUB)
            work = sdk_work_dir(generated, recipe.geometry_id)
            calls: list[str] = []

            def _forbidden(*_args, **_kwargs):
                calls.append("ascii")
                raise AssertionError("binary FBX must not use ASCII normalization")

            completed = type("C", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source.resolve(),
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch(
                "se2cad.solidworks.sdk_convert.subprocess.run",
                return_value=completed,
            ), patch(
                "se2cad.solidworks.sdk_ascii_fbx.normalize_ascii_fbx_to_binary",
                side_effect=_forbidden,
            ):
                with self.assertRaises(SdkConversionError):
                    convert_sdk_mesh_to_stl(recipe, work)
        self.assertEqual(calls, [])

    def test_ascii_conversion_writes_normalized_file_before_blender(self) -> None:
        from se2cad.library.model import SdkMeshRecipe
        from se2cad.catalog.model import RecipeKind as RK

        recipe = SdkMeshRecipe(
            geometry_id="vanilla_lg_1x1x1_probe_mesh",
            recipe_kind=RK.SDK_MESH_DIRECT,
            subtype_id="ProbeMesh",
            relative_source_stem="Models/Cubes/Large/probe",
            source_type="official_modsdk",
            apply_imported_object_transforms=True,
            additional_scale=1000.0,
            rotation_xyz_deg=(90.0, 0.0, 0.0),
            translation_mm=(0.0, 0.0, 0.0),
        )
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            sdk = generated / "sdk"
            source = _write_ascii(sdk, "Models/Cubes/Large/probe.fbx")
            work = sdk_work_dir(generated, recipe.geometry_id)
            seen: list[str] = []

            def _run(command, **_kwargs):
                seen.append(command[command.index("--fbx") + 1])
                stl = Path(command[command.index("--stl") + 1])
                report = Path(command[command.index("--report-json") + 1])
                stl.write_bytes(b"solid")
                report.write_text(json.dumps({"ok": True}), encoding="utf-8")
                return type("C", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source.resolve(),
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch("se2cad.solidworks.sdk_convert.subprocess.run", side_effect=_run):
                result = convert_sdk_mesh_to_stl(recipe, work)
            self.assertEqual(result.source_kind, "ascii")
            self.assertTrue(result.blender_fbx_path.is_file())
            self.assertTrue(result.blender_fbx_path.read_bytes().startswith(FBX_BINARY_MAGIC))
            self.assertEqual(seen, [str(result.blender_fbx_path)])
            self.assertNotEqual(result.blender_fbx_path.resolve(), source.resolve())
            self.assertIn("ascii_normalization", result.blender_report)

    def test_normal_repair_flag_is_deterministic_in_script(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "solidworks"
            / "blender_fbx_to_stl.py"
        )
        text = script.read_text(encoding="utf-8")
        self.assertIn("normals_make_consistent", text)
        self.assertIn("--repair-normals", text)
        self.assertIn("SE2CAD_BLENDER_SCRIPT_FAILED", text)
        self.assertIn("normals_made_consistent", text)

    def test_binary_blender_command_skips_normal_repair(self) -> None:
        recipe = lookup_record(AUTHORIZED_SDK_MESH_GEOMETRY_ID).recipe
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            source = generated / "HydrogenThrusterSmall.fbx"
            source.write_bytes(_BINARY_STUB)
            work = sdk_work_dir(generated, recipe.geometry_id)
            seen: list[list[str]] = []

            def _run(command, **_kwargs):
                seen.append(list(command))
                stl = Path(command[command.index("--stl") + 1])
                report = Path(command[command.index("--report-json") + 1])
                stl.write_bytes(b"solid")
                report.write_text(json.dumps({"ok": True}), encoding="utf-8")
                return type("C", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source.resolve(),
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch("se2cad.solidworks.sdk_convert.subprocess.run", side_effect=_run):
                convert_sdk_mesh_to_stl(recipe, work)
        self.assertEqual(len(seen), 1)
        self.assertNotIn("--repair-normals", seen[0])

    def test_ascii_blender_command_requests_normal_repair(self) -> None:
        from se2cad.library.model import SdkMeshRecipe
        from se2cad.catalog.model import RecipeKind as RK

        recipe = SdkMeshRecipe(
            geometry_id="vanilla_lg_1x1x1_probe_mesh",
            recipe_kind=RK.SDK_MESH_DIRECT,
            subtype_id="ProbeMesh",
            relative_source_stem="Models/Cubes/Large/probe",
            source_type="official_modsdk",
            apply_imported_object_transforms=True,
            additional_scale=1000.0,
            rotation_xyz_deg=(90.0, 0.0, 0.0),
            translation_mm=(0.0, 0.0, 0.0),
        )
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            sdk = generated / "sdk"
            source = _write_ascii(sdk, "Models/Cubes/Large/probe.fbx")
            work = sdk_work_dir(generated, recipe.geometry_id)
            seen: list[list[str]] = []

            def _run(command, **_kwargs):
                seen.append(list(command))
                stl = Path(command[command.index("--stl") + 1])
                report = Path(command[command.index("--report-json") + 1])
                stl.write_bytes(b"solid")
                report.write_text(json.dumps({"ok": True}), encoding="utf-8")
                return type("C", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source.resolve(),
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch("se2cad.solidworks.sdk_convert.subprocess.run", side_effect=_run):
                convert_sdk_mesh_to_stl(recipe, work)
        self.assertEqual(len(seen), 1)
        self.assertIn("--repair-normals", seen[0])

    def test_no_whole_sdk_conversion_occurs(self) -> None:
        opened: list[str] = []
        real = resolve_sdk_mesh_file

        def _spy(recipe, *, sdk_root=None):
            opened.append(recipe.relative_source_stem)
            return real(recipe, sdk_root=sdk_root)

        catalog = load_default_catalog()
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            game.mkdir()
            sdk.mkdir()
            _write_cube_blocks(
                game,
                "CubeBlocks_Logistics.sbc",
                _definition_xml(
                    _CONVEYOR,
                    model="Models\\Cubes\\Large\\conveyor.mwm",
                    type_id="Conveyor",
                )
                + _definition_xml(
                    "LargeBlockConveyorTube",
                    model="Models\\Cubes\\Large\\conveyorTube.mwm",
                    type_id="Conveyor",
                ),
            )
            _write_ascii(sdk, "Models/Cubes/Large/conveyor.fbx")
            _write_ascii(sdk, "Models/Cubes/Large/conveyorTube.fbx")
            with patch(
                "se2cad.solidworks.sdk_source.resolve_sdk_mesh_file",
                side_effect=_spy,
            ):
                resolve_vanilla_geometry(
                    _CONVEYOR, catalog, game_root=game, sdk_root=sdk
                )
        self.assertEqual(opened, ["Models/Cubes/Large/conveyor"])
        self.assertNotIn("Models/Cubes/Large/conveyorTube", opened)

    def test_locked_intermediate_uses_alternate_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            locked = work / "part.stl"
            locked.write_bytes(b"old")
            with locked.open("r+b"):
                chosen = _exclusive_work_file(work, "part", ".stl")
            self.assertEqual(chosen.name, "part.2.stl")
            self.assertTrue(locked.exists())
            self.assertFalse(chosen.exists())
            chosen.write_bytes(b"new")

    def test_cleanup_ignores_locked_leftover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            work = sdk_work_dir(generated, "probe_lock")
            work.mkdir(parents=True)
            leftover = work / "probe_lock.stl"
            leftover.write_bytes(b"old")
            with leftover.open("r+b"):
                cleanup_work_dir(work, generated)
            self.assertTrue(leftover.exists())


if __name__ == "__main__":
    unittest.main()
