"""Demand-driven conversion of the one authorized SDK FBX to a SLDPRT."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from se2cad.catalog.constants import LARGE_GRID_CELL_PITCH_MM
from se2cad.catalog.model import CellSize
from se2cad.library.model import SdkMeshRecipe
from se2cad.solidworks.artifacts import resolve_generated_root
from se2cad.transform.placement import MILLIMETRES_PER_METRE, require_cell_size
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.com_session import SolidWorksSession
from se2cad.solidworks.com_validate import PartValidation, read_part_validation
from se2cad.solidworks.errors import CanonicalPartValidationError, SdkConversionError
from se2cad.solidworks.sdk_fbx_format import FbxSourceKind, classify_sdk_fbx
from se2cad.solidworks.sdk_source import resolve_sdk_mesh_file

BLENDER_EXE_ENV = "SE2CAD_BLENDER_EXE"
_BLENDER_SCRIPT = Path(__file__).with_name("blender_fbx_to_stl.py")
_WORK_DIR_NAME = "_se2cad_sdk_work"
_BLENDER_OUTPUT_LIMIT = 16_384
_BLENDER_FAILURE_MARKERS = (
    "Traceback (most recent call last)",
    "SE2CAD_BLENDER_SCRIPT_FAILED",
    "Error: ASCII FBX files are not supported",
)
# Catch forgotten millimetre scale (the unscaled thruster was ~0.0026 m).
# 1x1x1 placement does not require the mesh to fill the cell.
_MIN_AXIS_M = 0.05
_UNIT_MAX_AXIS_M = 6.0
_UNIT_MAX_CENTER_OFFSET_M = 2.0
_PROTRUSION_CELLS = 1
_UNIT_CELL = CellSize(1, 1, 1)


@dataclass(frozen=True)
class SdkConversionReport:
    source_path: Path
    intermediate_stl: Path
    blender_report: dict[str, object]
    source_kind: str
    blender_fbx_path: Path


def resolve_blender_exe() -> Path:
    """Return the Blender executable. Fail closed when it is missing."""
    env = os.environ.get(BLENDER_EXE_ENV)
    if env:
        path = Path(env).expanduser()
        if not path.is_file():
            raise SdkConversionError(
                f"{BLENDER_EXE_ENV} does not point to a file: {path}"
            )
        return path.resolve()
    found = shutil.which("blender")
    if found:
        return Path(found).resolve()
    raise SdkConversionError(
        "Blender executable is required: set "
        f"{BLENDER_EXE_ENV} or place blender on PATH"
    )


def convert_sdk_mesh_to_stl(
    recipe: SdkMeshRecipe,
    work_dir: Path,
    *,
    sdk_root: Path | None = None,
) -> SdkConversionReport:
    """Run the bounded Blender conversion into ``work_dir``."""
    if not isinstance(recipe, SdkMeshRecipe):
        raise SdkConversionError("SDK mesh conversion requires an SDK-mesh recipe")
    source = resolve_sdk_mesh_file(recipe, sdk_root=sdk_root)
    work = work_dir.expanduser().resolve()
    generated_root = _generated_root_from_work(work)
    work.mkdir(parents=True, exist_ok=True)
    classified = classify_sdk_fbx(source)
    blender_fbx = source
    normalization = None
    if classified.kind is FbxSourceKind.ASCII:
        from se2cad.solidworks.sdk_ascii_fbx import normalize_ascii_fbx_to_binary

        blender_fbx = work / f"{recipe.geometry_id}.normalized.fbx"
        try:
            normalization = normalize_ascii_fbx_to_binary(
                source, blender_fbx, generated_root=generated_root
            )
        except Exception as exc:
            raise SdkConversionError(
                f"ASCII FBX conversion failed for {source.name}: {exc}"
            ) from exc
        if blender_fbx.resolve() == source.resolve():
            raise SdkConversionError("ASCII FBX conversion would overwrite the official SDK FBX")
    elif classified.kind is not FbxSourceKind.BINARY:
        raise SdkConversionError(
            classified.reason
            or f"SDK source is not a usable FBX: {source.name}"
        )
    stl = _exclusive_work_file(work, recipe.geometry_id, ".stl")
    report_path = _exclusive_work_file(work, recipe.geometry_id, ".convert.json")
    blender = resolve_blender_exe()
    command = [
        str(blender),
        "--background",
        "--python",
        str(_BLENDER_SCRIPT),
        "--",
        "--fbx",
        str(blender_fbx),
        "--stl",
        str(stl),
        "--report-json",
        str(report_path),
        "--scale",
        str(recipe.additional_scale),
        "--rx",
        str(recipe.rotation_xyz_deg[0]),
        "--ry",
        str(recipe.rotation_xyz_deg[1]),
        "--rz",
        str(recipe.rotation_xyz_deg[2]),
        "--tx-mm",
        str(recipe.translation_mm[0]),
        "--ty-mm",
        str(recipe.translation_mm[1]),
        "--tz-mm",
        str(recipe.translation_mm[2]),
    ]
    if recipe.apply_imported_object_transforms:
        command.append("--apply-object-transforms")
    if classified.kind is FbxSourceKind.ASCII:
        command.append("--repair-normals")
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise SdkConversionError(f"Blender could not be started: {exc}") from exc
    captured = _blender_captured_text(completed.stdout, completed.stderr)
    script_error = _blender_script_failure_text(captured, report_path)
    if completed.returncode != 0:
        raise SdkConversionError(
            f"Blender conversion failed with exit {completed.returncode}: "
            f"{script_error or captured or 'no diagnostic output'}"
        )
    if script_error:
        raise SdkConversionError(
            f"Blender reported a script exception after exit {completed.returncode}: "
            f"{script_error}"
        )
    if not stl.is_file():
        extra = f": {captured}" if captured else ": no diagnostic output"
        raise SdkConversionError(
            f"Blender did not write the intermediate mesh: {stl}{extra}"
        )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SdkConversionError(
            f"Blender conversion report is unreadable: {exc}"
        ) from exc
    if not isinstance(report, dict):
        raise SdkConversionError("Blender conversion report must be an object")
    report = dict(report)
    report["source_fbx"] = str(source)
    report["blender_fbx"] = str(blender_fbx)
    report["source_kind"] = classified.kind.value
    if normalization is not None:
        report["ascii_normalization"] = {
            "source_sha256": normalization.source_sha256,
            "normalized_path": str(normalization.normalized_path),
            "version": normalization.version,
            "geometry_count": normalization.geometry_count,
            "model_count": normalization.model_count,
            "vertex_values": normalization.vertex_values,
            "polygon_index_values": normalization.polygon_index_values,
        }
    return SdkConversionReport(
        source_path=source,
        intermediate_stl=stl,
        blender_report=report,
        source_kind=classified.kind.value,
        blender_fbx_path=blender_fbx,
    )


def sdk_work_dir(generated_root: Path, geometry_id: str) -> Path:
    """Contained working directory under the generated root."""
    root = resolve_generated_root(generated_root)
    work = (root / _WORK_DIR_NAME / geometry_id).resolve()
    try:
        work.relative_to(root)
    except ValueError:
        raise SdkConversionError(
            f"SDK work path {work} escapes generated root {root}"
        ) from None
    return work


def import_stl_as_part(
    session: SolidWorksSession,
    stl_path: Path,
) -> Any:
    """Import the intermediate STL as a SolidWorks part document."""
    try:
        return session.open_imported_mesh(stl_path)
    except Exception as exc:
        raise SdkConversionError(f"SolidWorks STL import failed: {exc}") from exc


def imported_mesh_envelope_limits(occupancy: CellSize) -> tuple[float, float]:
    """Return Size-aware (max_axis_m, max_center_offset_m) limits.

    Qualified 1×1×1 limits stay 6.0 m / 2.0 m. Multi-cell limits follow
    the longest occupancy axis plus one cell of protrusion so official
    model origin is preserved and legs/antennas are not recentered.
    """
    size = require_cell_size(occupancy)
    if size == _UNIT_CELL:
        return _UNIT_MAX_AXIS_M, _UNIT_MAX_CENTER_OFFSET_M
    pitch_m = LARGE_GRID_CELL_PITCH_MM / MILLIMETRES_PER_METRE
    max_logical_m = max(size.x, size.y, size.z) * pitch_m
    protrusion_m = _PROTRUSION_CELLS * pitch_m
    return max_logical_m + protrusion_m, (max_logical_m / 2.0) + protrusion_m


def assert_imported_mesh_envelope(
    observed: PartValidation,
    occupancy: CellSize | None = None,
) -> None:
    """Require a spatially plausible imported Large Grid mesh.

    The mesh must be millimetre-scaled. It does not have to fill the
    occupancy box. Sub-centimetre envelopes fail closed as a
    forgotten-scale defect. Legitimate multi-cell extent is allowed.
    """
    cell = _UNIT_CELL if occupancy is None else occupancy
    max_axis_m, max_center_m = imported_mesh_envelope_limits(cell)
    size = tuple(
        observed.bounding_box_max_m[i] - observed.bounding_box_min_m[i]
        for i in range(3)
    )
    if any(axis < _MIN_AXIS_M or axis > max_axis_m for axis in size):
        raise CanonicalPartValidationError(
            "imported SDK mesh envelope is not a coherent Large Grid cell: "
            f"size_m={size}"
        )
    center = tuple(
        (observed.bounding_box_min_m[i] + observed.bounding_box_max_m[i]) / 2.0
        for i in range(3)
    )
    if any(abs(value) > max_center_m for value in center):
        raise CanonicalPartValidationError(
            "imported SDK mesh is not local to the official model origin: "
            f"center_m={center}"
        )
    if (
        observed.solid_body_count == 0
        and observed.sheet_body_count == 0
        and observed.volume_m3 <= 0.0
    ):
        raise CanonicalPartValidationError(
            "imported SDK mesh produced no usable SolidWorks body"
        )


def read_imported_part_validation(
    session: SolidWorksSession,
    model: Any,
) -> PartValidation:
    """Read validation, allowing mesh-only imports if the envelope is usable."""
    try:
        return read_part_validation(session, model)
    except (CanonicalPartValidationError, Exception):
        box = _part_box(model)
        return PartValidation(
            solid_body_count=0,
            sheet_body_count=0,
            bounding_box_min_m=(box[0], box[1], box[2]),
            bounding_box_max_m=(box[3], box[4], box[5]),
            volume_m3=0.0,
            center_of_mass_m=(
                (box[0] + box[3]) / 2.0,
                (box[1] + box[4]) / 2.0,
                (box[2] + box[5]) / 2.0,
            ),
            face_count=None,
        )


def _part_box(model: Any) -> tuple[float, ...]:
    raw = com_get(model, "GetPartBox", True)
    if raw is None:
        raise CanonicalPartValidationError("GetPartBox returned None")
    values = tuple(float(v) for v in raw)
    if len(values) != 6:
        raise CanonicalPartValidationError(
            f"GetPartBox returned {len(values)} values, expected 6"
        )
    return values


def _generated_root_from_work(work: Path) -> Path:
    if work.parent.name != _WORK_DIR_NAME:
        raise SdkConversionError(
            f"SDK work path {work} is not under {_WORK_DIR_NAME}"
        )
    return work.parent.parent


def _blender_captured_text(stdout: str | None, stderr: str | None) -> str:
    text = "\n".join(part for part in (stderr, stdout) if part)
    text = text.strip()
    if len(text) <= _BLENDER_OUTPUT_LIMIT:
        return text
    return text[:_BLENDER_OUTPUT_LIMIT] + "\n...[truncated]"


def _blender_script_failure_text(captured: str, report_path: Path) -> str:
    error_path = Path(str(report_path) + ".error.txt")
    if error_path.is_file():
        try:
            return error_path.read_text(encoding="utf-8").strip()
        except OSError:
            return f"Blender wrote {error_path.name} but it is unreadable"
    for marker in _BLENDER_FAILURE_MARKERS:
        if marker in captured:
            return captured
    return ""


_MAX_WORK_FILE_ATTEMPTS = 32


def _exclusive_work_file(work_dir: Path, stem: str, suffix: str) -> Path:
    """Return a work path Blender can write, skipping leftover locked files."""
    if suffix and not suffix.startswith("."):
        raise SdkConversionError("work file suffix must start with '.'")
    work = work_dir.resolve()
    for index in range(_MAX_WORK_FILE_ATTEMPTS):
        name = f"{stem}{suffix}" if index == 0 else f"{stem}.{index + 1}{suffix}"
        path = (work / name).resolve()
        try:
            path.relative_to(work)
        except ValueError:
            raise SdkConversionError(
                f"work file {path} escapes conversion directory {work_dir}"
            ) from None
        if path.exists():
            try:
                path.unlink()
            except OSError:
                continue
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except OSError:
            continue
        os.close(fd)
        try:
            path.unlink()
        except OSError:
            continue
        return path
    raise SdkConversionError(
        f"could not allocate a writable work file for {stem}{suffix}"
    )


def _ignore_locked_cleanup(_func: Any, _path: str, _exc: Any) -> None:
    """Leave a locked leftover in place rather than failing generation."""
    return


def cleanup_work_dir(work_dir: Path, generated_root: Path) -> None:
    """Remove a contained conversion directory. Ignore if already gone."""
    root = resolve_generated_root(generated_root)
    resolved = work_dir.expanduser().resolve()
    try:
        resolved.relative_to(root / _WORK_DIR_NAME)
    except ValueError:
        raise SdkConversionError(
            f"refusing to delete unmanaged path {resolved}"
        ) from None
    if resolved.exists():
        try:
            shutil.rmtree(resolved, onexc=_ignore_locked_cleanup)
        except TypeError:
            shutil.rmtree(resolved, onerror=_ignore_locked_cleanup)
        except OSError:
            pass
    parent = resolved.parent
    if parent.is_dir() and not any(parent.iterdir()):
        try:
            parent.rmdir()
        except OSError:
            pass
