"""Apply strict or permissive conversion policy to a parsed blueprint."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from se2cad.catalog import DefinitionCatalog, load_default_catalog
from se2cad.catalog.constants import FILLER_GEOMETRY_ID
from se2cad.catalog.model import RecipeKind, SupportStatus
from se2cad.ir.convert import build_canonical_blueprint, canonical_block_from_parsed
from se2cad.ir.model import CanonicalBlueprint, CanonicalGrid
from se2cad.parser import parse_blueprint, parse_blueprint_xml
from se2cad.parser.model import ParsedBlueprint
from se2cad.policy.errors import ConversionRefusedError, UnknownConversionPolicyError
from se2cad.policy.model import ConversionPolicy, ConversionResult
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight
from se2cad.preflight.model import ConversionPreflight
from se2cad.statistics.model import NamedCount


def convert_blueprint(
    parsed: ParsedBlueprint,
    catalog: DefinitionCatalog,
    policy: ConversionPolicy = ConversionPolicy.STRICT,
) -> ConversionResult:
    """Convert every parsed block under an explicit policy.

    Strict is the default. Permissive must be requested. Unknown and
    unsupported blocks are never dropped.
    """
    if policy not in {ConversionPolicy.STRICT, ConversionPolicy.PERMISSIVE}:
        raise UnknownConversionPolicyError(
            f"unknown conversion policy {getattr(policy, 'value', policy)!r}"
        )
    preflight = compute_conversion_preflight(parsed, catalog)
    if policy is ConversionPolicy.STRICT:
        if not preflight.all_supported:
            raise ConversionRefusedError(_refusal_message(preflight), preflight)
        ir = build_canonical_blueprint(parsed, catalog)
        return ConversionResult(
            policy=policy,
            preflight=preflight,
            ir=ir,
            filler_count=0,
        )
    ir = _convert_permissive(parsed, catalog, preflight)
    filler_count = sum(
        1 for block in ir.grid.blocks if block.geometry_id == FILLER_GEOMETRY_ID
    )
    return ConversionResult(
        policy=policy,
        preflight=preflight,
        ir=ir,
        filler_count=filler_count,
    )


def convert_blueprint_from_path(
    path: str | Path,
    catalog: Optional[DefinitionCatalog] = None,
    policy: ConversionPolicy = ConversionPolicy.STRICT,
) -> ConversionResult:
    """Parse an operator-selected blueprint and convert under policy."""
    parsed = parse_blueprint(path)
    return convert_blueprint(parsed, catalog or load_default_catalog(), policy)


def convert_blueprint_from_xml(
    xml_text: str,
    catalog: Optional[DefinitionCatalog] = None,
    policy: ConversionPolicy = ConversionPolicy.STRICT,
    *,
    source: str = "<xml>",
) -> ConversionResult:
    """Parse already-loaded XML and convert under policy."""
    parsed = parse_blueprint_xml(xml_text, source=source)
    return convert_blueprint(parsed, catalog or load_default_catalog(), policy)


def _convert_permissive(
    parsed: ParsedBlueprint,
    catalog: DefinitionCatalog,
    preflight: ConversionPreflight,
) -> CanonicalBlueprint:
    pitch_mm = catalog.large_grid_cell_pitch_mm
    blocks = []
    for parsed_block, diagnosis in zip(
        parsed.grid.blocks, preflight.blocks, strict=True
    ):
        if diagnosis.catalog_outcome is CatalogOutcome.SUPPORTED:
            entry = catalog.lookup(parsed_block.subtype_id)
            geometry_id = entry.geometry_id
            recipe_kind = entry.recipe_kind
            support_status = entry.support_status
        else:
            geometry_id = FILLER_GEOMETRY_ID
            recipe_kind = RecipeKind.UNSUPPORTED
            support_status = SupportStatus.UNSUPPORTED
        blocks.append(
            canonical_block_from_parsed(
                parsed_block,
                geometry_id=geometry_id,
                recipe_kind=recipe_kind,
                support_status=support_status,
                pitch_mm=pitch_mm,
            )
        )
    return CanonicalBlueprint(
        identity_subtype=parsed.identity_subtype,
        display_name=parsed.display_name,
        grid=CanonicalGrid(
            display_name=parsed.grid.display_name,
            grid_size=parsed.grid.grid_size,
            blocks=tuple(blocks),
        ),
    )


def _refusal_message(preflight: ConversionPreflight) -> str:
    unknown = _format_named(preflight.unknown_subtype_counts)
    unsupported = _format_named(preflight.unsupported_subtype_counts)
    return (
        "strict conversion refused: "
        f"unknown_count={preflight.unknown_count} "
        f"unsupported_count={preflight.unsupported_count} "
        f"unknown_subtype_counts={unknown} "
        f"unsupported_subtype_counts={unsupported}"
    )


def _format_named(counts: tuple[NamedCount, ...]) -> str:
    if not counts:
        return ""
    return ",".join(f"{item.name}={item.count}" for item in counts)
