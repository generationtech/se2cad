"""Build canonical IR from a parsed blueprint and a resolved catalog."""

from __future__ import annotations

from se2cad.catalog.model import DefinitionCatalog, RecipeKind, SupportStatus
from se2cad.ir.model import CanonicalBlock, CanonicalBlueprint, CanonicalGrid
from se2cad.parser.model import ParsedBlock, ParsedBlueprint
from se2cad.transform.rotation import rotation_from_forward_up
from se2cad.transform.translation import cell_center_mm


def canonical_block_from_parsed(
    parsed_block: ParsedBlock,
    *,
    geometry_id: str,
    recipe_kind: RecipeKind,
    support_status: SupportStatus,
    pitch_mm: int,
) -> CanonicalBlock:
    """Place one parsed block. Pose uses Min, Forward, and Up only."""
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
        position_mm=cell_center_mm(parsed_block.min, pitch_mm),
        rotation=rotation_from_forward_up(parsed_block.forward, parsed_block.up),
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
