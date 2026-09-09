"""Resolve operator-local Space Engineers / ModSDK roots.

Reuses the established environment and uncommitted ``se2cad.local.json``
pattern. Discovery is a library-build tool; conversion does not call this.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from se2cad.discovery.errors import DiscoveryConfigError, DiscoveryPathError
from se2cad.local_config import (
    DEFAULT_LOCAL_CONFIG_NAME,
    LocalConfigError,
    discover_local_config,
    read_local_config,
)

GAME_ROOT_ENV = "SE2CAD_GAME_ROOT"
SDK_ROOT_ENV = "SE2CAD_SDK_ROOT"


@dataclass(frozen=True)
class DiscoveryConfig:
    """Resolved install roots. Paths are absolute existing directories."""

    game_root: Optional[Path]
    sdk_root: Optional[Path]
    source: str


def load_discovery_config(
    *,
    game_root: Optional[Path] = None,
    sdk_root: Optional[Path] = None,
) -> DiscoveryConfig:
    """Load game and/or SDK roots. Explicit arguments win over env and file."""
    try:
        local_path = discover_local_config()
        local = read_local_config(local_path) if local_path is not None else {}
    except LocalConfigError as exc:
        raise DiscoveryConfigError(str(exc)) from exc
    local_source = str(local_path) if local_path is not None else "defaults"

    env_game = os.environ.get(GAME_ROOT_ENV)
    env_sdk = os.environ.get(SDK_ROOT_ENV)

    game_value, game_source = _resolve_root(
        explicit=game_root,
        env_value=env_game,
        env_name=GAME_ROOT_ENV,
        local=local,
        local_field="game_root",
        local_source=local_source,
    )
    sdk_value, sdk_source = _resolve_root(
        explicit=sdk_root,
        env_value=env_sdk,
        env_name=SDK_ROOT_ENV,
        local=local,
        local_field="sdk_root",
        local_source=local_source,
    )
    if game_value is None and sdk_value is None:
        raise DiscoveryConfigError(
            "a game or SDK root is required: set "
            f"{GAME_ROOT_ENV}, {SDK_ROOT_ENV}, or {DEFAULT_LOCAL_CONFIG_NAME} "
            '{"game_root": "..."} / {"sdk_root": "..."}'
        )
    sources = [item for item in (game_source, sdk_source) if item is not None]
    source = ",".join(sources)
    return DiscoveryConfig(
        game_root=_require_existing_dir(game_value, field="game_root")
        if game_value is not None
        else None,
        sdk_root=_require_existing_dir(sdk_value, field="sdk_root")
        if sdk_value is not None
        else None,
        source=source,
    )


def _resolve_root(
    *,
    explicit: Optional[Path],
    env_value: Optional[str],
    env_name: str,
    local: dict[str, object],
    local_field: str,
    local_source: str,
) -> tuple[Optional[Path], Optional[str]]:
    if explicit is not None:
        return Path(explicit), "caller"
    if env_value:
        return Path(env_value), env_name
    if local_field in local:
        value = local[local_field]
        if not isinstance(value, str) or not value.strip():
            raise DiscoveryConfigError(
                f"{local_field} in {local_source} must be a non-empty string"
            )
        return Path(value).expanduser(), local_source
    return None, None


def _require_existing_dir(path: Path, *, field: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise DiscoveryPathError(f"{field} does not exist: {resolved}")
    if not resolved.is_dir():
        raise DiscoveryPathError(f"{field} is not a directory: {resolved}")
    return resolved


def contained_file(root: Path, candidate: Path) -> Path:
    """Resolve ``candidate`` and reject any path that escapes ``root``."""
    resolved_root = root.expanduser().resolve()
    resolved = candidate.expanduser().resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        raise DiscoveryPathError(
            f"path {resolved} escapes configured root {resolved_root}"
        ) from None
    if not resolved.is_file():
        raise DiscoveryPathError(f"definition path is not a file: {resolved}")
    return resolved
