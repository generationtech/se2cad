"""Definition catalog: exact subtype lookup to SE2CAD geometry identity.

S2C-2.1.1 / S2C-11.2.1 / S2C-11.3.1 / S2C-11.4.1. Independent of blueprint XML
parsing, CAD transforms, and SolidWorks. The packaged catalog is the
runtime source; game-install scanning is not required.
"""

from se2cad.catalog.constants import (
    CATALOG_CUBE_SIZE_LARGE,
    CATALOG_SCHEMA_VERSION,
    LARGE_GRID_CELL_PITCH_MM,
)
from se2cad.catalog.errors import (
    CatalogError,
    CatalogValidationError,
    UnknownSubtypeError,
)
from se2cad.catalog.expand import (
    catalog_to_data,
    expand_catalog_identities,
    geometry_id_for_subtype,
)
from se2cad.catalog.loader import (
    checked_geometry_id,
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
    ObservedIdentity,
    RecipeKind,
    SupportStatus,
)
from se2cad.catalog.selection import (
    Classification,
    ExceptionReason,
    ExceptionRecord,
    GeometryClass,
    ProvenanceRecord,
    SelectionReport,
    classify_observed,
    provenance_records,
    query_exception_records,
    select_catalog_recipes,
)

__all__ = [
    "CATALOG_CUBE_SIZE_LARGE",
    "CATALOG_SCHEMA_VERSION",
    "LARGE_GRID_CELL_PITCH_MM",
    "CatalogEntry",
    "CatalogError",
    "CatalogValidationError",
    "CellSize",
    "Classification",
    "DefinitionCatalog",
    "ExceptionReason",
    "ExceptionRecord",
    "GeometryClass",
    "ObservedDefinition",
    "ObservedIdentity",
    "ProvenanceRecord",
    "RecipeKind",
    "SelectionReport",
    "SupportStatus",
    "UnknownSubtypeError",
    "catalog_to_data",
    "checked_geometry_id",
    "classify_observed",
    "default_catalog_path",
    "expand_catalog_identities",
    "geometry_id_for_subtype",
    "load_catalog_file",
    "load_catalog_text",
    "load_default_catalog",
    "provenance_records",
    "query_exception_records",
    "select_catalog_recipes",
]
