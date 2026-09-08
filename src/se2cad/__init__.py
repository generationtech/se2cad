"""SE2CAD library surface.

S2C-1.2.1 exposes the blueprint parser. S2C-2.1.1 exposes the definition
catalog. IR, transforms, and CAD backends are later units.
"""

from se2cad.catalog import (
    LARGE_GRID_CELL_PITCH_MM,
    CatalogEntry,
    CatalogError,
    CatalogValidationError,
    CellSize,
    DefinitionCatalog,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
    UnknownSubtypeError,
    load_default_catalog,
)
from se2cad.parser import (
    BlueprintParseError,
    Direction,
    GridCoordinate,
    GridSize,
    InvalidFieldError,
    MalformedXmlError,
    MissingRequiredFieldError,
    ParsedBlock,
    ParsedBlueprint,
    ParsedGrid,
    UnsupportedBlueprintError,
    parse_blueprint,
    parse_blueprint_xml,
)

__all__ = [
    "LARGE_GRID_CELL_PITCH_MM",
    "BlueprintParseError",
    "CatalogEntry",
    "CatalogError",
    "CatalogValidationError",
    "CellSize",
    "DefinitionCatalog",
    "Direction",
    "GridCoordinate",
    "GridSize",
    "InvalidFieldError",
    "MalformedXmlError",
    "MissingRequiredFieldError",
    "ObservedDefinition",
    "ParsedBlock",
    "ParsedBlueprint",
    "ParsedGrid",
    "RecipeKind",
    "SupportStatus",
    "UnknownSubtypeError",
    "UnsupportedBlueprintError",
    "load_default_catalog",
    "parse_blueprint",
    "parse_blueprint_xml",
]
