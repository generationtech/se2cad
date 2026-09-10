"""One authorized SDK-mesh library bind. No game-asset I/O.

The relative source stem is operator-root-relative and has no file
extension. The SolidWorks backend appends the SDK mesh suffix.
"""

from __future__ import annotations

from se2cad.catalog.authorized import (
    AUTHORIZED_SDK_MESH_GEOMETRY_ID,
    AUTHORIZED_SDK_MESH_RECIPE_KIND,
    AUTHORIZED_SDK_MESH_SUBTYPE_ID,
)
from se2cad.catalog.constants import CATALOG_CUBE_SIZE_LARGE
from se2cad.library.frame import CANONICAL_LOCAL_FRAME
from se2cad.library.model import LibraryRecord, PlacementSemantics, SdkMeshRecipe

# Official ModSDK OriginalContent stem. Extension is resolved outside library.
_AUTHORIZED_SOURCE_STEM = "Models/Cubes/Large/HydrogenThrusterSmall"

# Blender FBX import already applies Keen RescaleFactor 0.01 on the parent
# object, yielding metres. Recipe-owned Rx +90 deg maps imported +Y (nozzle)
# onto SE2CAD +Z (Backward). SolidWorks STL import treats numbers as
# millimetres, so additional_scale 1000 exports millimetre units.
LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECIPE = SdkMeshRecipe(
    geometry_id=AUTHORIZED_SDK_MESH_GEOMETRY_ID,
    recipe_kind=AUTHORIZED_SDK_MESH_RECIPE_KIND,
    subtype_id=AUTHORIZED_SDK_MESH_SUBTYPE_ID,
    relative_source_stem=_AUTHORIZED_SOURCE_STEM,
    source_type="official_modsdk",
    apply_imported_object_transforms=True,
    additional_scale=1000.0,
    rotation_xyz_deg=(90.0, 0.0, 0.0),
    translation_mm=(0.0, 0.0, 0.0),
)

LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECORD = LibraryRecord(
    geometry_id=AUTHORIZED_SDK_MESH_GEOMETRY_ID,
    grid_size=CATALOG_CUBE_SIZE_LARGE,
    recipe_kind=AUTHORIZED_SDK_MESH_RECIPE_KIND,
    observed_cube_topology=None,
    frame=CANONICAL_LOCAL_FRAME,
    placement=PlacementSemantics(
        insert_at_cell_center=True,
        additional_offset_mm=(0, 0, 0),
        part_locator=None,
    ),
    recipe=LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECIPE,
    chamfer_capable=False,
)
