"""Focused tests for multi-node SDK FBX frame preservation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog.model import RecipeKind
from se2cad.library.model import SdkMeshRecipe
from se2cad.solidworks.errors import SdkConversionError
from se2cad.solidworks.sdk_convert import convert_sdk_mesh_to_stl, sdk_work_dir
from se2cad.solidworks.sdk_fbx_frame import (
    AmbiguousFbxFrameError,
    ImportedMeshNode,
    inherited_root_translations_to_neutralize,
)

_BLENDER_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "se2cad"
    / "solidworks"
    / "blender_fbx_to_stl.py"
)
_BINARY_STUB = b"Kaydara FBX Binary  \x1a\x00"


def _node(
    name: str,
    *,
    parent: str | None = None,
    translation=(0.0, 0.0, 0.0),
    center=(0.0, 0.0, 0.0),
    size=(2.5, 2.0, 2.0),
) -> ImportedMeshNode:
    return ImportedMeshNode(
        name=name,
        parent_name=parent,
        world_translation=translation,
        world_mesh_center=center,
        world_mesh_size=size,
    )


def _recipe(geometry_id: str = "vanilla_lg_1x1x1_frame_probe") -> SdkMeshRecipe:
    return SdkMeshRecipe(
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.SDK_MESH_DIRECT,
        subtype_id="FrameProbe",
        relative_source_stem="Models/Cubes/Large/FrameProbe",
        source_type="official_modsdk",
        apply_imported_object_transforms=True,
        additional_scale=1000.0,
        rotation_xyz_deg=(90.0, 0.0, 0.0),
        translation_mm=(0.0, 0.0, 0.0),
    )


class SdkFbxFrameRuleTests(unittest.TestCase):
    def test_baked_root_plus_local_child_neutralizes_inherited_translation(self) -> None:
        parent_t = (1.272, 0.478, 0.610)
        nodes = (
            _node("RootBody", translation=parent_t, center=(0.0, 0.0, 0.0)),
            _node(
                "ChildDetail",
                parent="RootBody",
                translation=parent_t,
                center=parent_t,
                size=(2.48, 2.48, 2.48),
            ),
        )
        corrections = inherited_root_translations_to_neutralize(nodes)
        self.assertEqual(corrections, {"ChildDetail": parent_t})
        old_joined_max_x = parent_t[0] + 1.24
        new_child_center = tuple(
            parent_t[i] - corrections["ChildDetail"][i] for i in range(3)
        )
        self.assertGreater(old_joined_max_x, 2.4)
        self.assertAlmostEqual(new_child_center[0], 0.0, places=9)
        self.assertAlmostEqual(new_child_center[1], 0.0, places=9)
        self.assertAlmostEqual(new_child_center[2], 0.0, places=9)

    def test_origin_centered_multi_node_is_unchanged(self) -> None:
        nodes = (
            _node("BatteryRoot", translation=(0.0, 0.0, 0.0), center=(0.0, 0.0, 0.0)),
            _node(
                "Panel",
                parent="BatteryRoot",
                translation=(0.0, 0.0, 1.1),
                center=(0.0, 0.0, 1.1),
                size=(2.0, 2.0, 0.2),
            ),
            _node(
                "Pipes",
                parent="BatteryRoot",
                translation=(0.8, 0.0, 0.0),
                center=(0.8, 0.0, 0.0),
                size=(0.2, 0.2, 1.5),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_single_node_path_is_unchanged(self) -> None:
        nodes = (
            _node(
                "Symbol",
                translation=(27.8, -0.55, -1.25),
                center=(0.0, 0.0, -1.175),
                size=(1.55, 1.10, 0.15),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_local_space_offset_root_keeps_inherited_child_transform(self) -> None:
        parent_t = (0.80, 0.0, 0.0)
        nodes = (
            _node(
                "OffsetRoot",
                translation=parent_t,
                center=parent_t,
                size=(1.2, 1.2, 1.2),
            ),
            _node(
                "Child",
                parent="OffsetRoot",
                translation=(0.90, 0.0, 0.0),
                center=(0.90, 0.0, 0.0),
                size=(0.3, 0.3, 0.3),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_ambiguous_root_frame_is_not_corrected(self) -> None:
        nodes = (
            _node(
                "OddRoot",
                translation=(1.3, 0.0, 0.0),
                center=(0.0, 0.9, 0.0),
                size=(2.0, 2.0, 2.0),
            ),
            _node(
                "Child",
                parent="OddRoot",
                translation=(1.3, 0.0, 0.0),
                center=(1.3, 0.0, 0.0),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_origin_centered_combined_world_is_not_corrected(self) -> None:
        parent_t = (0.0, 0.0, -3.75)
        nodes = (
            _node(
                "TankRoot",
                translation=parent_t,
                center=(0.0, 0.0, 0.0),
                size=(7.5, 7.5, 7.5),
            ),
            _node(
                "Cage",
                parent="TankRoot",
                translation=parent_t,
                center=(0.0, 0.0, 0.2),
                size=(7.4, 7.4, 7.2),
            ),
            _node(
                "Port",
                parent="TankRoot",
                translation=(0.0, 0.0, 3.6),
                center=(0.0, 0.0, 3.6),
                size=(1.0, 1.0, 0.4),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_front_light_style_partial_offset_root_is_not_corrected(self) -> None:
        nodes = (
            _node(
                "Light",
                translation=(0.0, 0.428, 0.0),
                center=(0.0, -0.189, 0.0),
                size=(2.46, 2.12, 2.46),
            ),
            _node(
                "Fixture",
                parent="Light",
                translation=(0.0, 0.0, 0.0),
                center=(0.0, 0.8, 0.0),
                size=(0.4, 0.4, 0.4),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_tiny_origin_root_with_translation_is_not_corrected(self) -> None:
        nodes = (
            _node(
                "TinyRoot",
                translation=(1.2, 0.0, 0.0),
                center=(0.0, 0.0, 0.0),
                size=(0.05, 0.05, 0.05),
            ),
            _node(
                "Child",
                parent="TinyRoot",
                translation=(1.2, 0.0, 0.0),
                center=(1.2, 0.0, 0.0),
            ),
        )
        self.assertEqual(inherited_root_translations_to_neutralize(nodes), {})

    def test_duplicate_names_fail_closed(self) -> None:
        nodes = (
            _node("Same"),
            _node("Same", parent="Other"),
        )
        with self.assertRaises(AmbiguousFbxFrameError):
            inherited_root_translations_to_neutralize(nodes)

    def test_rule_is_deterministic(self) -> None:
        parent_t = (1.1, 0.2, 0.4)
        nodes = [
            _node("RootBody", translation=parent_t, center=(0.01, -0.02, 0.0)),
            _node(
                "ChildB",
                parent="RootBody",
                translation=parent_t,
                center=parent_t,
            ),
            _node(
                "ChildA",
                parent="RootBody",
                translation=parent_t,
                center=parent_t,
            ),
        ]
        first = inherited_root_translations_to_neutralize(nodes)
        second = inherited_root_translations_to_neutralize(list(reversed(nodes)))
        self.assertEqual(first, second)
        self.assertEqual(set(first), {"ChildA", "ChildB"})


class SdkFbxConversionContractTests(unittest.TestCase):
    def test_conversion_does_not_modify_source_and_stays_under_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated"
            generated.mkdir()
            source = Path(tmp) / "RemoteControl.fbx"
            source.write_bytes(_BINARY_STUB)
            before = source.read_bytes()
            before_hash = hashlib.sha256(before).hexdigest()
            work = sdk_work_dir(generated, "vanilla_lg_1x1x1_frame_probe")
            recipe = _recipe()
            report = {
                "fbx": str(source),
                "stl": "",
                "applied_object_transforms": True,
                "additional_scale": 1000.0,
                "rotation_xyz_deg": [90.0, 0.0, 0.0],
                "translation_mm": [0.0, 0.0, 0.0],
            }

            def _fake_run(command, **_kwargs):
                stl = Path(command[command.index("--stl") + 1])
                report_path = Path(command[command.index("--report-json") + 1])
                self.assertIn("--apply-object-transforms", command)
                self.assertEqual(command[command.index("--scale") + 1], "1000.0")
                self.assertEqual(command[command.index("--rx") + 1], "90.0")
                self.assertEqual(command[command.index("--ry") + 1], "0.0")
                self.assertEqual(command[command.index("--rz") + 1], "0.0")
                stl.write_bytes(b"solid se2cad\nendsolid se2cad\n")
                payload = dict(report)
                payload["stl"] = str(stl)
                report_path.write_text(json.dumps(payload), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source,
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch(
                "se2cad.solidworks.sdk_convert.subprocess.run",
                side_effect=_fake_run,
            ):
                result = convert_sdk_mesh_to_stl(recipe, work)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before_hash)
            self.assertTrue(result.intermediate_stl.is_relative_to(generated))
            self.assertEqual(result.blender_report["additional_scale"], 1000.0)
            self.assertEqual(result.blender_report["rotation_xyz_deg"], [90.0, 0.0, 0.0])

    def test_duplicate_mesh_names_fail_closed_through_blender_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated"
            generated.mkdir()
            source = Path(tmp) / "probe.fbx"
            source.write_bytes(_BINARY_STUB)
            work = sdk_work_dir(generated, "vanilla_lg_1x1x1_frame_probe")
            with patch(
                "se2cad.solidworks.sdk_convert.resolve_sdk_mesh_file",
                return_value=source,
            ), patch(
                "se2cad.solidworks.sdk_convert.resolve_blender_exe",
                return_value=Path("blender"),
            ), patch(
                "se2cad.solidworks.sdk_convert.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    ["blender"],
                    1,
                    "",
                    "SE2CAD_BLENDER_SCRIPT_FAILED\nimported mesh node names are not unique\n",
                ),
            ):
                with self.assertRaises(SdkConversionError) as ctx:
                    convert_sdk_mesh_to_stl(_recipe(), work)
            self.assertIn("not unique", str(ctx.exception).lower())


def _blender_exe() -> Path | None:
    env = os.environ.get("SE2CAD_BLENDER_EXE")
    if env:
        path = Path(env)
        if path.is_file():
            return path
    from shutil import which

    found = which("blender")
    return Path(found) if found else None


@unittest.skipUnless(_blender_exe() is not None, "Blender executable is required")
class SdkFbxFrameBlenderHostTests(unittest.TestCase):
    def test_blender_host_baked_root_child_matches_block_frame(self) -> None:
        blender = _blender_exe()
        assert blender is not None
        script = """
import json
import sys
import traceback
from pathlib import Path

import bpy
from mathutils import Vector

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    spec_path = Path(sys.argv[sys.argv.index("--") + 1])
    import importlib.util
    spec = importlib.util.spec_from_file_location("blender_fbx_to_stl", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parent_t = Vector((1.272, 0.478, 0.610))
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    root = bpy.context.active_object
    root.name = "RootBody"
    for vert in root.data.vertices:
        vert.co -= parent_t
    root.location = parent_t
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=parent_t)
    child = bpy.context.active_object
    child.name = "ChildDetail"
    child.parent = root
    child.matrix_parent_inverse = root.matrix_world.inverted()
    meshes = [root, child]
    old = [float(x) for x in (mod._scene_bbox(meshes)["max"])]
    applied = mod._neutralize_inherited_root_translations(meshes)
    new = [float(x) for x in (mod._scene_bbox(meshes)["max"])]
    print("SE2CAD_FRAME_HOST_RESULT " + json.dumps({
        "old_max": old,
        "new_max": new,
        "applied": applied,
    }), flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "host_frame_test.py"
            path.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                [
                    str(blender),
                    "--background",
                    "--python",
                    str(path),
                    "--",
                    str(_BLENDER_SCRIPT),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        captured = "\n".join(
            part for part in (completed.stdout, completed.stderr) if part
        )
        self.assertEqual(completed.returncode, 0, msg=captured)
        lines = [
            line
            for line in captured.splitlines()
            if line.startswith("SE2CAD_FRAME_HOST_RESULT")
        ]
        self.assertTrue(lines, msg=captured)
        payload = json.loads(lines[-1].split(" ", 1)[1])
        self.assertGreater(payload["old_max"][0], 1.7)
        self.assertLess(payload["new_max"][0], 1.3)
        self.assertEqual(len(payload["applied"]), 1)
        self.assertEqual(payload["applied"][0]["name"], "ChildDetail")
