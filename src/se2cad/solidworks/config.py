"""Smallest Windows-local backend configuration boundary.

Generated parts live under a caller-configured root. Machine-specific
paths are not stored in the catalog. The general CLI is not defined here.

Resolution order:

1. ``SE2CAD_GENERATED_ROOT``
2. ``generated_root`` in an uncommitted local JSON config
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from se2cad.solidworks.artifacts import resolve_generated_root
from se2cad.solidworks.errors import SolidWorksConfigError

GENERATED_ROOT_ENV = "SE2CAD_GENERATED_ROOT"
PART_TEMPLATE_ENV = "SE2CAD_SOLIDWORKS_PART_TEMPLATE"
LOCAL_CONFIG_ENV = "SE2CAD_LOCAL_CONFIG"
VISIBLE_ENV = "SE2CAD_SOLIDWORKS_VISIBLE"
DEFAULT_LOCAL_CONFIG_NAME = "se2cad.local.json"

_ALLOWED_LOCAL_KEYS = frozenset(
    {"generated_root", "part_template", "visible"}
)


@dataclass(frozen=True)
class SolidWorksBackendConfig:
    """Resolved backend configuration. Paths are absolute."""

    generated_root: Path
    part_template: Optional[Path]
    visible: bool
    source: str


def _read_local_config(path: Path) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SolidWorksConfigError(
            f"cannot read local config {path}: {exc}"
        ) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SolidWorksConfigError(
            f"local config {path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise SolidWorksConfigError(
            f"local config {path} must be a JSON object"
        )
    unknown = set(data) - _ALLOWED_LOCAL_KEYS
    if unknown:
        raise SolidWorksConfigError(
            f"local config {path} has unexpected keys: {sorted(unknown)}"
        )
    return data


def _discover_local_config() -> Optional[Path]:
    override = os.environ.get(LOCAL_CONFIG_ENV)
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise SolidWorksConfigError(
                f"{LOCAL_CONFIG_ENV} does not point to a file: {path}"
            )
        return path
    candidate = Path.cwd() / DEFAULT_LOCAL_CONFIG_NAME
    if candidate.is_file():
        return candidate
    return None


def _as_optional_path(value: object, *, field: str, source: str) -> Optional[Path]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise SolidWorksConfigError(
            f"{field} in {source} must be a non-empty string"
        )
    return Path(value).expanduser()


def _as_bool(value: object, *, field: str, source: str) -> bool:
    if isinstance(value, bool):
        return value
    raise SolidWorksConfigError(f"{field} in {source} must be a JSON boolean")


def load_solidworks_backend_config(
    *,
    generated_root: Optional[Path] = None,
    part_template: Optional[Path] = None,
    visible: Optional[bool] = None,
) -> SolidWorksBackendConfig:
    """Load the backend config. Explicit arguments win over env and file."""
    local_path = _discover_local_config()
    local = _read_local_config(local_path) if local_path is not None else {}
    local_source = str(local_path) if local_path is not None else "defaults"

    env_root = os.environ.get(GENERATED_ROOT_ENV)
    env_template = os.environ.get(PART_TEMPLATE_ENV)
    env_visible = os.environ.get(VISIBLE_ENV)

    root_value: Optional[Path]
    source: str
    if generated_root is not None:
        root_value = Path(generated_root)
        source = "caller"
    elif env_root:
        root_value = Path(env_root)
        source = GENERATED_ROOT_ENV
    elif "generated_root" in local:
        root_value = _as_optional_path(
            local["generated_root"], field="generated_root", source=local_source
        )
        source = local_source
    else:
        raise SolidWorksConfigError(
            "generated root is required: set "
            f"{GENERATED_ROOT_ENV} or {DEFAULT_LOCAL_CONFIG_NAME} "
            '{"generated_root": "..."}'
        )
    if root_value is None:
        raise SolidWorksConfigError("generated root is empty")

    template_value: Optional[Path]
    if part_template is not None:
        template_value = Path(part_template)
    elif env_template:
        template_value = Path(env_template)
    elif "part_template" in local:
        template_value = _as_optional_path(
            local["part_template"], field="part_template", source=local_source
        )
    else:
        template_value = None

    if visible is not None:
        visible_value = visible
    elif env_visible is not None:
        visible_value = env_visible.strip().lower() in {"1", "true", "yes"}
    elif "visible" in local:
        visible_value = _as_bool(
            local["visible"], field="visible", source=local_source
        )
    else:
        visible_value = False

    resolved_root = resolve_generated_root(root_value)
    resolved_template = (
        template_value.expanduser().resolve() if template_value is not None else None
    )
    if resolved_template is not None and not resolved_template.is_file():
        raise SolidWorksConfigError(
            f"part template does not exist: {resolved_template}"
        )
    return SolidWorksBackendConfig(
        generated_root=resolved_root,
        part_template=resolved_template,
        visible=visible_value,
        source=source,
    )
