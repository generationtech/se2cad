"""Definition catalog: exact subtype lookup to SE2CAD geometry identity.

S2C-2.1.1. Independent of blueprint XML parsing, CAD transforms, and
SolidWorks. The packaged catalog is the runtime source; game-install
scanning is not required.
"""

from se2cad.catalog.constants import LARGE_GRID_CELL_PITCH_MM
from se2cad.catalog.errors import (
    CatalogError,
    CatalogValidationError,
    UnknownSubtypeError,
)
from se2cad.catalog.loader import (
    default_catalog_path,
    load_catalog_file,
    load_catalog_text,
    load_default_catalog,
)
from se2cad.catalog.model import (
    CatalogEntry,
    CellSize,
    DefinitionCatalog,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
)

__all__ = [
    "LARGE_GRID_CELL_PITCH_MM",
    "CatalogEntry",
    "CatalogError",
    "CatalogValidationError",
    "CellSize",
    "DefinitionCatalog",
    "ObservedDefinition",
    "RecipeKind",
    "SupportStatus",
    "UnknownSubtypeError",
    "default_catalog_path",
    "load_catalog_file",
    "load_catalog_text",
    "load_default_catalog",
]
