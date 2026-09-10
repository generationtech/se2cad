"""Deterministic Blender conversion for the one authorized SDK FBX.

Invoked only as ``blender --background --python this-file -- …``.
Not imported by the SE2CAD runtime package.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import traceback
from pathlib import Path

import bpy
from mathutils import Euler, Vector


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Authorized SDK FBX to STL")
    parser.add_argument("--fbx", required=True)
    parser.add_argument("--stl", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--apply-object-transforms", action="store_true")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--rx", type=float, default=0.0)
    parser.add_argument("--ry", type=float, default=0.0)
    parser.add_argument("--rz", type=float, default=0.0)
    parser.add_argument("--tx-mm", type=float, default=0.0)
    parser.add_argument("--ty-mm", type=float, default=0.0)
    parser.add_argument("--tz-mm", type=float, default=0.0)
    parser.add_argument("--repair-normals", action="store_true")
    return parser.parse_args(argv)


def _mesh_objects():
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def _scene_bbox(objs):
    mins = [None, None, None]
    maxs = [None, None, None]
    verts = 0
    tris = 0
    for obj in objs:
        mesh = obj.data
        verts += len(mesh.vertices)
        mesh.calc_loop_triangles()
        tris += len(mesh.loop_triangles)
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for i in range(3):
                value = float(world[i])
                mins[i] = value if mins[i] is None else min(mins[i], value)
                maxs[i] = value if maxs[i] is None else max(maxs[i], value)
    return {
        "mesh_object_count": len(objs),
        "vertex_count": verts,
        "triangle_count": tris,
        "min": mins,
        "max": maxs,
        "size": [
            maxs[i] - mins[i] if mins[i] is not None else None for i in range(3)
        ],
    }


def _select_meshes(meshes) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]


def _make_normals_consistent() -> None:
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    fbx = Path(args.fbx)
    stl = Path(args.stl)
    report_path = Path(args.report_json)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx))
    meshes = _mesh_objects()
    if not meshes:
        raise RuntimeError("FBX import produced no mesh objects")
    before = _scene_bbox(meshes)
    if args.apply_object_transforms:
        _select_meshes(meshes)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        meshes = _mesh_objects()
    _select_meshes(meshes)
    if len(meshes) > 1:
        bpy.ops.object.join()
        meshes = _mesh_objects()
        _select_meshes(meshes)
    joined = bpy.context.view_layer.objects.active
    joined.rotation_euler = Euler(
        (math.radians(args.rx), math.radians(args.ry), math.radians(args.rz)),
        "XYZ",
    )
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    if args.scale != 1.0:
        joined.scale = (args.scale, args.scale, args.scale)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    translation_m = (args.tx_mm / 1000.0, args.ty_mm / 1000.0, args.tz_mm / 1000.0)
    if any(value != 0.0 for value in translation_m):
        joined.location = translation_m
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    if args.repair_normals:
        _make_normals_consistent()
    after = _scene_bbox(_mesh_objects())
    stl.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.stl_export(
        filepath=str(stl),
        export_selected_objects=True,
        ascii_format=False,
        apply_modifiers=True,
    )
    report = {
        "fbx": str(fbx),
        "stl": str(stl),
        "before_m": before,
        "after_m": after,
        "applied_object_transforms": bool(args.apply_object_transforms),
        "additional_scale": args.scale,
        "rotation_xyz_deg": [args.rx, args.ry, args.rz],
        "translation_mm": [args.tx_mm, args.ty_mm, args.tz_mm],
        "normals_made_consistent": bool(args.repair_normals),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


def _fail(report_path: Path, exc: BaseException) -> int:
    print("SE2CAD_BLENDER_SCRIPT_FAILED", file=sys.stderr)
    traceback.print_exc()
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        (Path(str(report_path) + ".error.txt")).write_text(
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            encoding="utf-8",
        )
    except OSError:
        pass
    return 1


if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    report_hint = Path("blender_report.json")
    try:
        parsed = _parse_args(argv)
        report_hint = Path(parsed.report_json)
        raise SystemExit(main(argv))
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(_fail(report_hint, exc)) from exc
