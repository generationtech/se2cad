"""Transient runtime library records for eligible vanilla TriangleMesh.

These records are never written to the packaged catalog. They feed the
existing lazy materializer with the S2C-11.7.1 SDK-mesh contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from se2cad.catalog.constants import CATALOG_CUBE_SIZE_LARGE
from se2cad.catalog.model import (
    CatalogEntry,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
)
from se2cad.ir.convert import (
    clear_runtime_placements,
    lookup_runtime_placement,
    register_runtime_placement,
)
from se2cad.library.frame import CANONICAL_LOCAL_FRAME
from se2cad.library.lookup import register_runtime_library_record
from se2cad.library.model import LibraryRecord, PlacementSemantics, SdkMeshRecipe
from se2cad.transform.placement import BlockPlacementDefinition
from se2cad.vanilla.identity import empty_subtype_placement_key
from se2cad.vanilla.lookup import TargetedDefinition


@dataclass(frozen=True)
class RuntimeVanillaRecord:
    """Immutable runtime bind for one demand-resolved vanilla identity."""

    library_record: LibraryRecord
    catalog_entry: CatalogEntry
    definition_source_relative: str
    sdk_source_relative: str
    placement: BlockPlacementDefinition

    @property
    def geometry_id(self) -> str:
        return self.library_record.geometry_id

    @property
    def subtype_id(self) -> str:
        return self.catalog_entry.subtype_id


def runtime_sdk_mesh_record(
    *,
    subtype_id: str,
    geometry_id: str,
    relative_source_stem: str,
    definition: TargetedDefinition,
    definition_source_relative: str,
    sdk_source_relative: str,
) -> RuntimeVanillaRecord:
    """Build the transient catalog/library pair for one eligible identity."""
    placement = BlockPlacementDefinition(
        size=definition.size,
        model_offset=definition.model_offset,
    )
    recipe = SdkMeshRecipe(
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.SDK_MESH_DIRECT,
        subtype_id=subtype_id,
        relative_source_stem=relative_source_stem,
        source_type="official_modsdk",
        apply_imported_object_transforms=True,
        additional_scale=1000.0,
        rotation_xyz_deg=(90.0, 0.0, 0.0),
        translation_mm=(0.0, 0.0, 0.0),
        occupancy_size=definition.size,
    )
    library_record = LibraryRecord(
        geometry_id=geometry_id,
        grid_size=CATALOG_CUBE_SIZE_LARGE,
        recipe_kind=RecipeKind.SDK_MESH_DIRECT,
        observed_cube_topology=None,
        frame=CANONICAL_LOCAL_FRAME,
        placement=PlacementSemantics(
            insert_at_cell_center=True,
            additional_offset_mm=(0, 0, 0),
            part_locator=None,
        ),
        recipe=recipe,
        chamfer_capable=False,
    )
    catalog_entry = CatalogEntry(
        subtype_id=subtype_id,
        observed=ObservedDefinition(
            type_id=definition.type_id,
            cube_size=definition.cube_size,
            size=definition.size,
            block_topology=definition.block_topology,
            cube_topology=definition.cube_topology,
        ),
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.SDK_MESH_DIRECT,
        support_status=SupportStatus.SUPPORTED,
    )
    return RuntimeVanillaRecord(
        library_record=library_record,
        catalog_entry=catalog_entry,
        definition_source_relative=definition_source_relative,
        sdk_source_relative=sdk_source_relative,
        placement=placement,
    )


def register_runtime_vanilla_record(
    runtime: RuntimeVanillaRecord,
    *,
    placement_key: str | None = None,
) -> None:
    """Register the transient library bind and subtype placement overlay."""
    register_runtime_library_record(runtime.library_record)
    key = placement_key
    if key is None:
        if runtime.subtype_id == "":
            key = empty_subtype_placement_key(runtime.catalog_entry.observed.type_id)
        else:
            key = runtime.subtype_id
    register_runtime_placement(key, runtime.placement)


__all__ = [
    "RuntimeVanillaRecord",
    "clear_runtime_placements",
    "lookup_runtime_placement",
    "register_runtime_placement",
    "register_runtime_vanilla_record",
    "runtime_sdk_mesh_record",
]
