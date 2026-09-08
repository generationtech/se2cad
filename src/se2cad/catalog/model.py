"""Immutable definition-catalog domain types.

Observed Space Engineers definition facts are kept distinct from SE2CAD
mapping decisions. This module does not parse XML or compute CAD transforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from se2cad.catalog.constants import LARGE_GRID_CELL_PITCH_MM
from se2cad.catalog.errors import UnknownSubtypeError


class RecipeKind(str, Enum):
    """Architectural geometry-strategy vocabulary. Not an implementation list."""

    NATIVE_PROCEDURAL = "native_procedural"
    SDK_MESH_DIRECT = "sdk_mesh_direct"
    SDK_MESH_MANIFOLD = "sdk_mesh_manifold"
    HAND_AUTHORED = "hand_authored"
    UNSUPPORTED = "unsupported"


class SupportStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CellSize:
    """Block occupancy in grid cells, from Keen ``Size``."""

    x: int
    y: int
    z: int


@dataclass(frozen=True)
class ObservedDefinition:
    """Facts taken from installed Space Engineers cube-block definitions."""

    type_id: str
    cube_size: str
    size: CellSize
    block_topology: str
    cube_topology: str


@dataclass(frozen=True)
class CatalogEntry:
    """One subtype identity plus its observed facts and SE2CAD mapping."""

    subtype_id: str
    observed: ObservedDefinition
    geometry_id: str
    recipe_kind: RecipeKind
    support_status: SupportStatus


@dataclass(frozen=True)
class DefinitionCatalog:
    """Exact, case-sensitive catalog of supported subtype identities."""

    entries: tuple[CatalogEntry, ...]

    @property
    def large_grid_cell_pitch_mm(self) -> int:
        return LARGE_GRID_CELL_PITCH_MM

    def lookup(self, subtype_id: str) -> CatalogEntry:
        """Resolve an exact parser subtype string. No case folding or aliases."""
        for entry in self.entries:
            if entry.subtype_id == subtype_id:
                return entry
        raise UnknownSubtypeError(f"unknown cube-block subtype {subtype_id!r}")
