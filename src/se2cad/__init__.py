"""SE2CAD library surface.

S2C-1.2.1 exposes only the blueprint parser. Catalog, IR, transforms, and CAD
backends are later units.
"""

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
    "BlueprintParseError",
    "Direction",
    "GridCoordinate",
    "GridSize",
    "InvalidFieldError",
    "MalformedXmlError",
    "MissingRequiredFieldError",
    "ParsedBlock",
    "ParsedBlueprint",
    "ParsedGrid",
    "UnsupportedBlueprintError",
    "parse_blueprint",
    "parse_blueprint_xml",
]
