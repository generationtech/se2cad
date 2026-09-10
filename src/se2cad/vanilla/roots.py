"""Operator-local game-content and SDK roots for vanilla resolution.

Reuses ``SE2CAD_GAME_ROOT`` / ``SE2CAD_SDK_ROOT`` and uncommitted
``se2cad.local.json`` keys ``game_root`` / ``sdk_root``. This module
does not walk an install until a caller asks for a root.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from se2cad.local_config import (
    DEFAULT_LOCAL_CONFIG_NAME,
    LocalConfigError,
    discover_local_config,
    read_local_config,
)
from se2cad.vanilla.errors import VanillaRootError

GAME_ROOT_ENV = "SE2CAD_GAME_ROOT"
SDK_ROOT_ENV = "SE2CAD_SDK_ROOT"


def try_load_game_content_root() -> Optional[Path]:
    """Return the configured game-content root, or None when unset."""
    return _try_load_root(
        env_name=GAME_ROOT_ENV,
        local_field="game_root",
        label="game-content root",
    )


def load_game_content_root() -> Path:
    """Return the configured game-content root. Fail closed when absent."""
    root = try_load_game_content_root()
    if root is None:
        raise VanillaRootError(
            "game-content root is required for vanilla definition resolution: "
            f"set {GAME_ROOT_ENV} or {DEFAULT_LOCAL_CONFIG_NAME} "
            '{"game_root": "..."}'
        )
    return root


def try_load_sdk_root() -> Optional[Path]:
    """Return the configured SDK content root, or None when unset."""
    return _try_load_root(
        env_name=SDK_ROOT_ENV,
        local_field="sdk_root",
        label="SDK root",
    )


def load_sdk_root() -> Path:
    """Return the configured SDK content root. Fail closed when absent."""
    root = try_load_sdk_root()
    if root is None:
        raise VanillaRootError(
            "SDK root is required for vanilla SDK-mesh resolution: "
            f"set {SDK_ROOT_ENV} or {DEFAULT_LOCAL_CONFIG_NAME} "
            '{"sdk_root": "..."}'
        )
    return root


def require_existing_dir(path: Path, *, source: str) -> Path:
    """Resolve ``path`` and require an existing directory."""
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise VanillaRootError(f"{source} does not exist: {resolved}")
    if not resolved.is_dir():
        raise VanillaRootError(f"{source} is not a directory: {resolved}")
    return resolved


def _try_load_root(
    *,
    env_name: str,
    local_field: str,
    label: str,
) -> Optional[Path]:
    env = os.environ.get(env_name)
    if env:
        return require_existing_dir(Path(env), source=env_name)
    try:
        local_path = discover_local_config()
        local = read_local_config(local_path) if local_path is not None else {}
    except LocalConfigError as exc:
        raise VanillaRootError(str(exc)) from exc
    if local_field not in local:
        return None
    value = local[local_field]
    if not isinstance(value, str) or not value.strip():
        raise VanillaRootError(f"{local_field} must be a non-empty string")
    source = str(local_path) if local_path is not None else DEFAULT_LOCAL_CONFIG_NAME
    return require_existing_dir(Path(value), source=f"{source} {label}")
