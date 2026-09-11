"""Canonical CAD-neutral intermediate representation (S2C-3.1.1)."""

from se2cad.ir.convert import (
    build_canonical_blueprint,
    canonical_block_from_parsed,
    clear_runtime_placements,
    lookup_runtime_placement,
    placement_for_resolved_block,
    placement_from_catalog_entry,
    register_runtime_placement,
)
from se2cad.ir.errors import ComponentNameError, IrError
from se2cad.ir.model import CanonicalBlock, CanonicalBlueprint, CanonicalGrid
from se2cad.ir.naming import (
    COMPONENT_NAME_MAX_LENGTH,
    component_name,
    component_name_from_block,
    component_names_from_blocks,
)

__all__ = [
    "COMPONENT_NAME_MAX_LENGTH",
    "CanonicalBlock",
    "CanonicalBlueprint",
    "CanonicalGrid",
    "ComponentNameError",
    "IrError",
    "build_canonical_blueprint",
    "canonical_block_from_parsed",
    "clear_runtime_placements",
    "lookup_runtime_placement",
    "placement_for_resolved_block",
    "placement_from_catalog_entry",
    "register_runtime_placement",
    "component_name",
    "component_name_from_block",
    "component_names_from_blocks",
]
