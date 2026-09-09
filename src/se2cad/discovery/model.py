"""Observed cube-block definition facts from an operator-local tree.

These records are library-build evidence. They are not catalog entries
and they do not assign ``geometry_id``, ``recipe_kind``, or support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from se2cad.catalog.model import CellSize


@dataclass(frozen=True)
class DiscoveredDefinition:
    """One vanilla cube-block identity and the catalog-modeled observed fields."""

    subtype_id: str
    type_id: str
    cube_size: str
    size: CellSize
    block_topology: str
    cube_topology: Optional[str]
    source_kind: str
    source_relative: str


@dataclass(frozen=True)
class DiscoveryReport:
    """Deterministic discovery result. Paths in records are root-relative."""

    definitions: tuple[DiscoveredDefinition, ...]
    files_read: tuple[str, ...]
    game_root_configured: bool
    sdk_root_configured: bool
