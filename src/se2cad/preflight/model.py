"""CAD-neutral conversion-preflight values.

These types diagnose catalog and support outcomes. They do not convert,
insert filler, or claim that a successful report is a successful
conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from se2cad.catalog.model import SupportStatus
from se2cad.parser.model import AppearanceSupport, GridCoordinate, GridSize
from se2cad.statistics.model import NamedCount


class CatalogOutcome(str, Enum):
    """Distinct catalog/conversion-readiness outcomes. Not aliases."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BlockPreflight:
    """One parsed block's preflight diagnosis."""

    source_index: int
    subtype_id: str
    grid_min: GridCoordinate
    catalog_outcome: CatalogOutcome
    geometry_id: Optional[str]
    geometry_support: Optional[SupportStatus]
    appearance_support: AppearanceSupport


@dataclass(frozen=True)
class ConversionPreflight:
    """Deterministic preflight of one parsed single-grid blueprint.

    ``all_supported`` is the strict-versus-permissive decision input.
    It is not conversion success. Producing this report is not a
    conversion.
    """

    identity_subtype: Optional[str]
    display_name: Optional[str]
    grid_display_name: Optional[str]
    grid_size: GridSize
    block_count: int
    blocks: tuple[BlockPreflight, ...]
    supported_count: int
    unsupported_count: int
    unknown_count: int
    unknown_subtype_counts: tuple[NamedCount, ...]
    unsupported_subtype_counts: tuple[NamedCount, ...]
    all_supported: bool
