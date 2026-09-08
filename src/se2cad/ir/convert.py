"""Build canonical IR from a parsed blueprint and a resolved catalog."""

from __future__ import annotations

from se2cad.catalog.model import DefinitionCatalog
from se2cad.ir.model import CanonicalBlock, CanonicalBlueprint, CanonicalGrid
from se2cad.parser.model import ParsedBlueprint
from se2cad.transform.rotation import rotation_from_forward_up
from se2cad.transform.translation import cell_center_mm


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
            CanonicalBlock(
                subtype_id=parsed_block.subtype_id,
                geometry_id=entry.geometry_id,
                recipe_kind=entry.recipe_kind,
                support_status=entry.support_status,
                grid_min=parsed_block.min,
                min_serialized=parsed_block.min_serialized,
                forward=parsed_block.forward,
                up=parsed_block.up,
                orientation_serialized=parsed_block.orientation_serialized,
                position_mm=cell_center_mm(parsed_block.min, pitch_mm),
                rotation=rotation_from_forward_up(
                    parsed_block.forward, parsed_block.up
                ),
                source_index=parsed_block.source_index,
                source=parsed_block.source,
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
