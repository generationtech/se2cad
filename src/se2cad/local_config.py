"""Shared uncommitted local-config file and environment discovery.

Operator machine paths live in environment variables and/or an
uncommitted ``se2cad.local.json``. This module does not interpret
SolidWorks or game/SDK semantics; callers read the keys they own.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

LOCAL_CONFIG_ENV = "SE2CAD_LOCAL_CONFIG"
DEFAULT_LOCAL_CONFIG_NAME = "se2cad.local.json"

ALLOWED_LOCAL_KEYS = frozenset(
    {
        "generated_root",
        "part_template",
        "visible",
        "game_root",
        "sdk_root",
    }
)


class LocalConfigError(Exception):
    """Local JSON config is missing, unreadable, or has unexpected keys."""


def discover_local_config() -> Optional[Path]:
    """Return the operator local-config path, or None when none is present."""
    override = os.environ.get(LOCAL_CONFIG_ENV)
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise LocalConfigError(
                f"{LOCAL_CONFIG_ENV} does not point to a file: {path}"
            )
        return path
    candidate = Path.cwd() / DEFAULT_LOCAL_CONFIG_NAME
    if candidate.is_file():
        return candidate
    return None


def read_local_config(path: Path) -> dict[str, object]:
    """Read and validate one uncommitted local JSON object."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LocalConfigError(f"cannot read local config {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LocalConfigError(
            f"local config {path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise LocalConfigError(f"local config {path} must be a JSON object")
    unknown = set(data) - ALLOWED_LOCAL_KEYS
    if unknown:
        raise LocalConfigError(
            f"local config {path} has unexpected keys: {sorted(unknown)}"
        )
    return data
