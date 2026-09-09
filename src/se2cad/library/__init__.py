"""Canonical block library: reference frame and native armor recipes.

S2C-4.1.1 / S2C-11.4.1. Independent of SolidWorks, Blender, and
game-install scanning. Lookup is by catalog geometry identity.
Authoritative locators stay unbound. S2C-10.1.1 adds an optional
identity-free edge treatment on closed solids. S2C-11.4.1 stamps
native recipes from known CubeTopology tokens.
"""

from se2cad.library.errors import (
    InvalidSolidError,
    LibraryError,
    TreatmentError,
    UnknownGeometryError,
    UnsupportedTopologyError,
)
from se2cad.library.frame import (
    CANONICAL_CELL_ENVELOPE,
    CANONICAL_LOCAL_FRAME,
    AxisAlignedBoxMm,
    CanonicalLocalFrame,
    cell_half_extent_mm,
)
from se2cad.library.lookup import (
    all_library_records,
    lookup_recipe,
    lookup_record,
    original_library_geometry_ids,
    representative_automatable_geometry_ids,
)
from se2cad.library.model import (
    BoxConstruction,
    BoxMinusTetrahedronConstruction,
    Construction,
    LibraryRecord,
    NativeSolidRecipe,
    PlacementSemantics,
    PrismConstruction,
    SolidKind,
    TetrahedronConstruction,
    TopologyOrientation,
    ValidationProperties,
)
from se2cad.library.recipes import (
    AUTOMATABLE_CUBE_TOPOLOGIES,
    ORIGINAL_LIBRARY_BINDINGS,
    REPRESENTATIVE_AUTOMATABLE_BINDINGS,
    TETRAHEDRON_CUT_FACES,
    recipe_for_topology,
    signed_volume_times_6,
)
from se2cad.library.solid import (
    BoundsMm,
    MeshEdge,
    SolidMesh,
    bounding_box,
    mesh_edges,
    solid_from_recipe,
    solid_from_vertices_faces,
    volume_times_6,
)
from se2cad.library.treatment import (
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_MIN_VOLUME_RATIO,
    EDGE_TREATMENT_OFF,
    EDGE_TREATMENT_SETBACK_MM,
    EdgeTreatmentKind,
    EdgeTreatmentRequest,
    EdgeTreatmentResult,
    apply_edge_treatment,
)

__all__ = [
    "CANONICAL_CELL_ENVELOPE",
    "CANONICAL_LOCAL_FRAME",
    "EDGE_TREATMENT_CHAMFER",
    "EDGE_TREATMENT_MIN_VOLUME_RATIO",
    "EDGE_TREATMENT_OFF",
    "EDGE_TREATMENT_SETBACK_MM",
    "AxisAlignedBoxMm",
    "BoundsMm",
    "BoxConstruction",
    "BoxMinusTetrahedronConstruction",
    "CanonicalLocalFrame",
    "Construction",
    "EdgeTreatmentKind",
    "EdgeTreatmentRequest",
    "EdgeTreatmentResult",
    "InvalidSolidError",
    "LibraryError",
    "LibraryRecord",
    "MeshEdge",
    "NativeSolidRecipe",
    "PlacementSemantics",
    "PrismConstruction",
    "SolidKind",
    "SolidMesh",
    "TetrahedronConstruction",
    "TopologyOrientation",
    "AUTOMATABLE_CUBE_TOPOLOGIES",
    "ORIGINAL_LIBRARY_BINDINGS",
    "REPRESENTATIVE_AUTOMATABLE_BINDINGS",
    "TETRAHEDRON_CUT_FACES",
    "TreatmentError",
    "UnknownGeometryError",
    "UnsupportedTopologyError",
    "ValidationProperties",
    "all_library_records",
    "apply_edge_treatment",
    "bounding_box",
    "cell_half_extent_mm",
    "lookup_recipe",
    "lookup_record",
    "mesh_edges",
    "original_library_geometry_ids",
    "recipe_for_topology",
    "representative_automatable_geometry_ids",
    "signed_volume_times_6",
    "solid_from_recipe",
    "solid_from_vertices_faces",
    "volume_times_6",
]
