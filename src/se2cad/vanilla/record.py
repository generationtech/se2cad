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
from se2cad.library.frame import CANONICAL_LOCAL_FRAME
from se2cad.library.model import LibraryRecord, PlacementSemantics, SdkMeshRecipe
from se2cad.vanilla.lookup import TargetedDefinition


@dataclass(frozen=True)
class RuntimeVanillaRecord:
    """Immutable runtime bind for one demand-resolved vanilla identity."""

    library_record: LibraryRecord
    catalog_entry: CatalogEntry
    definition_source_relative: str
    sdk_source_relative: str

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
    )
