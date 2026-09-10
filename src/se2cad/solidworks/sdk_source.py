"""Resolve an official SDK mesh from a recipe stem. No install scan.

Operator root comes from ``SE2CAD_SDK_ROOT`` or uncommitted
``se2cad.local.json`` ``sdk_root``. The recipe carries a relative stem;
this module appends the official mesh suffix and refuses escape,
LOD/construction siblings, and game MWM files.
"""

from __future__ import annotations

import os
from pathlib import Path

from se2cad.library.model import SdkMeshRecipe
from se2cad.local_config import (
    DEFAULT_LOCAL_CONFIG_NAME,
    LocalConfigError,
    discover_local_config,
    read_local_config,
)
from se2cad.solidworks.errors import SdkSourceError
from se2cad.solidworks.sdk_fbx_format import require_usable_sdk_fbx

SDK_ROOT_ENV = "SE2CAD_SDK_ROOT"
SDK_MESH_SUFFIX = ".fbx"
AUTHORIZED_SDK_SOURCE_FILENAME = "HydrogenThrusterSmall.fbx"
_FORBIDDEN_NAME_PARTS = ("lod", "construction")


def load_sdk_root() -> Path:
    """Return the configured SDK content root. Fail closed when absent."""
    env = os.environ.get(SDK_ROOT_ENV)
    if env:
        return _require_existing_dir(Path(env), source=SDK_ROOT_ENV)
    try:
        local_path = discover_local_config()
        local = read_local_config(local_path) if local_path is not None else {}
    except LocalConfigError as exc:
        raise SdkSourceError(str(exc)) from exc
    if "sdk_root" not in local:
        raise SdkSourceError(
            "SDK root is required: set "
            f"{SDK_ROOT_ENV} or {DEFAULT_LOCAL_CONFIG_NAME} "
            '{"sdk_root": "..."}'
        )
    value = local["sdk_root"]
    if not isinstance(value, str) or not value.strip():
        raise SdkSourceError("sdk_root must be a non-empty string")
    source = str(local_path) if local_path is not None else DEFAULT_LOCAL_CONFIG_NAME
    return _require_existing_dir(Path(value), source=source)


def resolve_sdk_mesh_file(
    recipe: SdkMeshRecipe,
    *,
    sdk_root: Path | None = None,
) -> Path:
    """Resolve a recipe-relative stem to a contained official SDK file."""
    if not isinstance(recipe, SdkMeshRecipe):
        raise SdkSourceError("SDK mesh resolution requires an SDK-mesh recipe")
    root = load_sdk_root() if sdk_root is None else _require_existing_dir(sdk_root, source="sdk_root")
    relative = _relative_source_file(recipe.relative_source_stem)
    expected_name = Path(relative).name
    resolved = _unique_casefold_file(root, Path(relative).parts)
    contained = contained_sdk_file(root, resolved, expected_name=expected_name)
    require_usable_sdk_fbx(contained)
    return contained


def contained_sdk_file(
    root: Path,
    candidate: Path,
    *,
    expected_name: str | None = None,
) -> Path:
    """Resolve ``candidate`` and reject any path that escapes ``root``."""
    resolved_root = root.expanduser().resolve()
    resolved = candidate.expanduser().resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        raise SdkSourceError(
            f"path {resolved} escapes configured SDK root {resolved_root}"
        ) from None
    if expected_name is not None and resolved.name.lower() != expected_name.lower():
        raise SdkSourceError(
            f"refusing non-authorized SDK filename {resolved.name!r}"
        )
    lowered_parts = [part.lower() for part in resolved.parts]
    if any(
        any(token in part for token in _FORBIDDEN_NAME_PARTS)
        for part in lowered_parts
    ):
        raise SdkSourceError(
            f"refusing LOD or construction SDK sibling {resolved}"
        )
    if resolved.suffix.lower() == ".mwm":
        raise SdkSourceError("game MWM files are not an authorized source")
    if resolved.suffix.lower() != SDK_MESH_SUFFIX:
        raise SdkSourceError(
            f"authorized SDK source must use {SDK_MESH_SUFFIX}, got {resolved.suffix!r}"
        )
    if not resolved.is_file():
        raise SdkSourceError(f"authorized SDK source is not a file: {resolved}")
    return resolved


def _require_binary_fbx(path: Path) -> None:
    """Refuse unusable SDK FBX. Valid ASCII is accepted only with conversion."""
    require_usable_sdk_fbx(path)


def _relative_source_file(stem: str) -> str:
    if not isinstance(stem, str) or stem.strip() == "":
        raise SdkSourceError("relative SDK source stem is missing")
    if stem.lower().endswith(SDK_MESH_SUFFIX):
        raise SdkSourceError("relative SDK source stem must not include a suffix")
    normalized = stem.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("\\"):
        raise SdkSourceError("relative SDK source must not be absolute")
    if ":" in normalized:
        raise SdkSourceError("relative SDK source must not contain a drive")
    parts = Path(normalized).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise SdkSourceError("relative SDK source must stay inside the SDK root")
    if any(any(token in part.lower() for token in _FORBIDDEN_NAME_PARTS) for part in parts):
        raise SdkSourceError("relative SDK source must not name LOD or construction files")
    return "/".join(parts) + SDK_MESH_SUFFIX


def _unique_casefold_file(root: Path, parts: tuple[str, ...]) -> Path:
    resolved_root = root.expanduser().resolve()
    current = resolved_root
    relative = "/".join(parts)
    for index, part in enumerate(parts):
        try:
            current.relative_to(resolved_root)
        except ValueError:
            raise SdkSourceError(
                f"path {current} escapes configured SDK root {resolved_root}"
            ) from None
        if not current.is_dir():
            raise SdkSourceError(f"authorized SDK source is not a file: {resolved_root / relative}")
        is_last = index == len(parts) - 1
        matches = [
            child
            for child in current.iterdir()
            if child.name.lower() == part.lower()
            and ((is_last and child.is_file()) or (not is_last and child.is_dir()))
        ]
        if not matches:
            raise SdkSourceError(
                f"authorized SDK source is not a file: {resolved_root / relative}"
            )
        if len(matches) > 1:
            names = ", ".join(sorted(child.name for child in matches))
            raise SdkSourceError(
                f"ambiguous SDK path {part!r} under {current}: {names}"
            )
        current = matches[0].resolve()
    return current


def _require_existing_dir(path: Path, *, source: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise SdkSourceError(f"{source} does not exist: {resolved}")
    if not resolved.is_dir():
        raise SdkSourceError(f"{source} is not a directory: {resolved}")
    return resolved
