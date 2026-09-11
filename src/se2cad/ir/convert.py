"""Build canonical IR from a parsed blueprint and a resolved catalog."""

from __future__ import annotations

import threading

from se2cad.catalog.errors import UnknownSubtypeError
from se2cad.catalog.model import CatalogEntry, DefinitionCatalog, RecipeKind, SupportStatus
from se2cad.ir.model import CanonicalBlock, CanonicalBlueprint, CanonicalGrid
from se2cad.parser.model import ParsedBlock, ParsedBlueprint
from se2cad.transform.placement import (
    QUALIFIED_ONE_BY_ONE_PLACEMENT,
    BlockPlacementDefinition,
    placement_from_cell_size,
    placement_translation_mm,
)
from se2cad.transform.rotation import rotation_from_forward_up

_PLACEMENT_LOCK = threading.Lock()
_RUNTIME_PLACEMENTS: dict[str, BlockPlacementDefinition] = {}


def register_runtime_placement(
    subtype_id: str,
    placement: BlockPlacementDefinition,
) -> None:
    """Remember resolved Size/ModelOffset for one runtime subtype."""
    if not isinstance(subtype_id, str) or subtype_id == "":
        raise ValueError("subtype_id must be a non-empty string")
    if not isinstance(placement, BlockPlacementDefinition):
        raise ValueError("placement must be a BlockPlacementDefinition")
    with _PLACEMENT_LOCK:
        existing = _RUNTIME_PLACEMENTS.get(subtype_id)
        if existing is not None and existing != placement:
            raise ValueError(
                f"runtime subtype {subtype_id!r} is already bound to a "
                "different placement"
            )
        _RUNTIME_PLACEMENTS[subtype_id] = placement


def lookup_runtime_placement(subtype_id: str) -> BlockPlacementDefinition | None:
    """Return the transient placement for a runtime-supported subtype."""
    with _PLACEMENT_LOCK:
        return _RUNTIME_PLACEMENTS.get(subtype_id)


def clear_runtime_placements() -> None:
    """Drop transient placement overlays. Tests use this for isolation."""
    with _PLACEMENT_LOCK:
        _RUNTIME_PLACEMENTS.clear()


def placement_for_resolved_block(
    subtype_id: str,
    catalog: DefinitionCatalog,
    *,
    catalog_supported: bool,
    runtime_placement: BlockPlacementDefinition | None = None,
) -> BlockPlacementDefinition:
    """Choose placement metadata without granting new support.

    Packaged catalog hits use observed Size and the established zero
    ModelOffset. Runtime-supported vanilla identities use the transient
    resolved Size and ModelOffset overlay. Unresolved blocks receive the
    designated 1×1×1 filler placement contract, not a guessed Size.
    """
    if catalog_supported:
        try:
            return placement_from_catalog_entry(catalog.lookup(subtype_id))
        except UnknownSubtypeError:
            found = (
                runtime_placement
                if runtime_placement is not None
                else lookup_runtime_placement(subtype_id)
            )
            if found is None:
                raise ValueError(
                    f"runtime-supported subtype {subtype_id!r} has no "
                    "placement metadata"
                )
            return found
    return QUALIFIED_ONE_BY_ONE_PLACEMENT


def placement_from_catalog_entry(entry: CatalogEntry) -> BlockPlacementDefinition:
    """Use packaged observed Size and the established zero ModelOffset.

    Packaged identities have no ModelOffset field. The qualified
    library/catalog contract for those identities is zero offset.
    """
    return placement_from_cell_size(entry.observed.size)


def canonical_block_from_parsed(
    parsed_block: ParsedBlock,
    *,
    geometry_id: str,
    recipe_kind: RecipeKind,
    support_status: SupportStatus,
    pitch_mm: int,
    placement: BlockPlacementDefinition,
) -> CanonicalBlock:
    """Place one parsed block from blueprint facts plus placement metadata.

    ``ParsedBlock`` stays blueprint-only. Size and ModelOffset come from
    ``placement``. Definition Center is not an IR or translation input.
    CanonicalBlock retains the resulting ``(R, t)`` only.
    """
    rotation = rotation_from_forward_up(parsed_block.forward, parsed_block.up)
    return CanonicalBlock(
        subtype_id=parsed_block.subtype_id,
        geometry_id=geometry_id,
        recipe_kind=recipe_kind,
        support_status=support_status,
        grid_min=parsed_block.min,
        min_serialized=parsed_block.min_serialized,
        forward=parsed_block.forward,
        up=parsed_block.up,
        orientation_serialized=parsed_block.orientation_serialized,
        color_mask_hsv=parsed_block.color_mask_hsv,
        color_serialized=parsed_block.color_serialized,
        appearance_support=parsed_block.appearance_support,
        position_mm=placement_translation_mm(
            parsed_block.min, placement, rotation, pitch_mm
        ),
        rotation=rotation,
        source_index=parsed_block.source_index,
        source=parsed_block.source,
    )


def build_canonical_blueprint(
    parsed: ParsedBlueprint,
    catalog: DefinitionCatalog,
) -> CanonicalBlueprint:
    """Resolve every parsed block and compute its exact placement."""
    pitch_mm = catalog.large_grid_cell_pitch_mm
    blocks = []
    for parsed_block in parsed.grid.blocks:
        entry = catalog.lookup(parsed_block.subtype_id)
        blocks.append(
            canonical_block_from_parsed(
                parsed_block,
                geometry_id=entry.geometry_id,
                recipe_kind=entry.recipe_kind,
                support_status=entry.support_status,
                pitch_mm=pitch_mm,
                placement=placement_from_catalog_entry(entry),
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
