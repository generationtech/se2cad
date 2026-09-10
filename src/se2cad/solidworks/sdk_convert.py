"""Demand-driven conversion of the one authorized SDK FBX to a SLDPRT."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from se2cad.library.model import SdkMeshRecipe
from se2cad.solidworks.artifacts import resolve_generated_root
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.com_session import SolidWorksSession
from se2cad.solidworks.com_validate import PartValidation, read_part_validation
from se2cad.solidworks.errors import CanonicalPartValidationError, SdkConversionError
from se2cad.solidworks.sdk_source import resolve_sdk_mesh_file

BLENDER_EXE_ENV = "SE2CAD_BLENDER_EXE"
_BLENDER_SCRIPT = Path(__file__).with_name("blender_fbx_to_stl.py")
_WORK_DIR_NAME = "_se2cad_sdk_work"
# Catch forgotten millimetre scale (the unscaled thruster was ~0.0026 m).
# 1x1x1 placement does not require the mesh to fill the cell.
_MIN_AXIS_M = 0.05
_MAX_AXIS_M = 6.0
_MAX_CENTER_OFFSET_M = 2.0


@dataclass(frozen=True)
class SdkConversionReport:
    source_path: Path
    intermediate_stl: Path
    blender_report: dict[str, object]


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
    work.mkdir(parents=True, exist_ok=True)
    stl = work / f"{recipe.geometry_id}.stl"
    report_path = work / f"{recipe.geometry_id}.convert.json"
    blender = resolve_blender_exe()
    command = [
        str(blender),
        "--background",
        "--python",
        str(_BLENDER_SCRIPT),
        "--",
        "--fbx",
        str(source),
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
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise SdkConversionError(f"Blender could not be started: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise SdkConversionError(
            f"Blender conversion failed with exit {completed.returncode}: {detail}"
        )
    if not stl.is_file():
        detail = (completed.stderr or completed.stdout or "").strip()
        extra = f": {detail}" if detail else ""
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
    return SdkConversionReport(
        source_path=source,
        intermediate_stl=stl,
        blender_report=report,
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


def assert_imported_mesh_envelope(observed: PartValidation) -> None:
    """Require a spatially plausible imported Large Grid mesh.

    The mesh must be millimetre-scaled and cell-local. It does not have
    to fill the 2.5 m cell. Sub-centimetre envelopes fail closed as a
    forgotten-scale defect.
    """
    size = tuple(
        observed.bounding_box_max_m[i] - observed.bounding_box_min_m[i]
        for i in range(3)
    )
    if any(axis < _MIN_AXIS_M or axis > _MAX_AXIS_M for axis in size):
        raise CanonicalPartValidationError(
            "imported SDK mesh envelope is not a coherent Large Grid cell: "
            f"size_m={size}"
        )
    center = tuple(
        (observed.bounding_box_min_m[i] + observed.bounding_box_max_m[i]) / 2.0
        for i in range(3)
    )
    if any(abs(value) > _MAX_CENTER_OFFSET_M for value in center):
        raise CanonicalPartValidationError(
            "imported SDK mesh is not centered on the cell origin: "
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
        shutil.rmtree(resolved)
    parent = resolved.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
