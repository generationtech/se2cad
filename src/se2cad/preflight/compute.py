"""Compute CAD-neutral conversion preflight from a parsed blueprint."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional

from se2cad.catalog import DefinitionCatalog, UnknownSubtypeError, load_default_catalog
from se2cad.catalog.model import SupportStatus
from se2cad.parser import parse_blueprint, parse_blueprint_xml
from se2cad.parser.model import ParsedBlueprint
from se2cad.preflight.model import (
    BlockPreflight,
    CatalogOutcome,
    ConversionPreflight,
)
from se2cad.statistics.model import NamedCount


def compute_conversion_preflight(
    parsed: ParsedBlueprint,
    catalog: DefinitionCatalog,
) -> ConversionPreflight:
    """Diagnose every parsed block. Do not drop blocks or convert."""
    blocks: list[BlockPreflight] = []
    supported_count = 0
    unsupported_count = 0
    unknown_count = 0
    unknown_counter: Counter[str] = Counter()
    unsupported_counter: Counter[str] = Counter()

    for parsed_block in parsed.grid.blocks:
        try:
            entry = catalog.lookup(parsed_block.subtype_id)
        except UnknownSubtypeError:
            unknown_count += 1
            unknown_counter[parsed_block.subtype_id] += 1
            blocks.append(
                BlockPreflight(
                    source_index=parsed_block.source_index,
                    subtype_id=parsed_block.subtype_id,
                    grid_min=parsed_block.min,
                    catalog_outcome=CatalogOutcome.UNKNOWN,
                    geometry_id=None,
                    geometry_support=None,
                    appearance_support=parsed_block.appearance_support,
                )
            )
            continue

        if entry.support_status is SupportStatus.SUPPORTED:
            outcome = CatalogOutcome.SUPPORTED
            supported_count += 1
        else:
            outcome = CatalogOutcome.UNSUPPORTED
            unsupported_count += 1
            unsupported_counter[parsed_block.subtype_id] += 1

        blocks.append(
            BlockPreflight(
                source_index=parsed_block.source_index,
                subtype_id=parsed_block.subtype_id,
                grid_min=parsed_block.min,
                catalog_outcome=outcome,
                geometry_id=entry.geometry_id,
                geometry_support=entry.support_status,
                appearance_support=parsed_block.appearance_support,
            )
        )

    block_count = len(parsed.grid.blocks)
    return ConversionPreflight(
        identity_subtype=parsed.identity_subtype,
        display_name=parsed.display_name,
        grid_display_name=parsed.grid.display_name,
        grid_size=parsed.grid.grid_size,
        block_count=block_count,
        blocks=tuple(blocks),
        supported_count=supported_count,
        unsupported_count=unsupported_count,
        unknown_count=unknown_count,
        unknown_subtype_counts=_named_counts(unknown_counter),
        unsupported_subtype_counts=_named_counts(unsupported_counter),
        all_supported=unsupported_count == 0 and unknown_count == 0,
    )


def compute_conversion_preflight_from_path(
    path: str | Path,
    catalog: Optional[DefinitionCatalog] = None,
) -> ConversionPreflight:
    """Parse an operator-selected blueprint and compute preflight."""
    parsed = parse_blueprint(path)
    return compute_conversion_preflight(parsed, catalog or load_default_catalog())


def compute_conversion_preflight_from_xml(
    xml_text: str,
    catalog: Optional[DefinitionCatalog] = None,
    *,
    source: str = "<xml>",
) -> ConversionPreflight:
    """Parse already-loaded XML and compute preflight."""
    parsed = parse_blueprint_xml(xml_text, source=source)
    return compute_conversion_preflight(parsed, catalog or load_default_catalog())


def _named_counts(counter: Counter[str]) -> tuple[NamedCount, ...]:
    return tuple(
        NamedCount(name=name, count=counter[name]) for name in sorted(counter)
    )
