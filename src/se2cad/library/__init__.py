"""Canonical block library: reference frame and native armor recipes.

S2C-4.1.1. Independent of SolidWorks, Blender, and game-install scanning.
Lookup is by catalog geometry identity. Part documents are a later unit.
"""

from se2cad.library.errors import LibraryError, UnknownGeometryError
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
from se2cad.library.recipes import signed_volume_times_6

__all__ = [
    "CANONICAL_CELL_ENVELOPE",
    "CANONICAL_LOCAL_FRAME",
    "AxisAlignedBoxMm",
    "BoxConstruction",
    "BoxMinusTetrahedronConstruction",
    "CanonicalLocalFrame",
    "Construction",
    "LibraryError",
    "LibraryRecord",
    "NativeSolidRecipe",
    "PlacementSemantics",
    "PrismConstruction",
    "SolidKind",
    "TetrahedronConstruction",
    "TopologyOrientation",
    "UnknownGeometryError",
    "ValidationProperties",
    "all_library_records",
    "cell_half_extent_mm",
    "lookup_recipe",
    "lookup_record",
    "signed_volume_times_6",
]
