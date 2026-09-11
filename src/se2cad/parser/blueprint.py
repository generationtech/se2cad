"""Parse a supported single-grid Large Grid Space Engineers blueprint.

S2C-1.2.1 support set:

- one ``Definitions`` / ``ShipBlueprints`` / ``ShipBlueprint`` document
- exactly one ``CubeGrid``
- ``GridSizeEnum`` = Large
- ``CubeBlocks`` items serialized as ``MyObjectBuilder_CubeBlock`` elements
- per-block subtype identity, Min, and BlockOrientation

S2C-9.1.1 adds per-block ``ColorMaskHSV`` as CAD-neutral appearance.

S2C-12.3.1 accepts ordinary vanilla cube-block-derived object builders.
Keen serializes ``CubeBlocks`` as a list of ``MyObjectBuilder_CubeBlock``
elements whose ``xsi:type`` is the runtime builder, a
``MyObjectBuilder_*`` identifier. Parser acceptance is that structural
shape plus the existing field contract. It is not a catalog allowlist
and is not a geometry-support decision.

Omitted-field defaults are Space Engineers XML serialization defaults, not
SE2CAD inventions. See ``_DEFAULT_MIN``, ``_DEFAULT_ORIENTATION``, and
``DEFAULT_COLOR_MASK_HSV``.

S2C-11.15.1 accepts an empty ``SubtypeName`` only when a specific
``MyObjectBuilder_*`` ``xsi:type`` other than ``MyObjectBuilder_CubeBlock``
is present. The empty subtype is stored as ``""``; it is not rewritten
into a synthetic SubtypeId. Unidentified empty subtypes still fail closed.

This module does not resolve catalogs, compute CAD transforms, or execute
blueprint content.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from se2cad.parser.errors import (
    BlueprintParseError,
    InvalidFieldError,
    MalformedXmlError,
    MissingRequiredFieldError,
    UnsupportedBlueprintError,
)
from se2cad.parser.model import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    ColorMaskHSV,
    Direction,
    GridCoordinate,
    GridSize,
    ParsedBlock,
    ParsedBlueprint,
    ParsedGrid,
)

# XmlSerializer omits Min when it equals SerializableVector3I(0, 0, 0).
# Evidence: Keen MyObjectBuilder_CubeBlock.ShouldSerializeMin and field
# initializer; current local VRage.Game.dll still exports ShouldSerializeMin.
_DEFAULT_MIN = GridCoordinate(0, 0, 0)

# XmlSerializer omits BlockOrientation when it equals Identity (Forward, Up).
# Evidence: ShouldSerializeBlockOrientation; SerializableBlockOrientation.Identity
# = (Forward, Up); local VRage.Game.dll still exports ShouldSerializeBlockOrientation.
_DEFAULT_ORIENTATION = (Direction.FORWARD, Direction.UP)

# XmlSerializer omits ColorMaskHSV when it equals SerializableVector3(0, -1, 0).
# Evidence: Keen MyObjectBuilder_CubeBlock field initializer and
# ShouldSerializeColorMaskHSV(); current ModAPI still lists both;
# qualified acceptance fixture serializes no ColorMaskHSV.
_DEFAULT_COLOR_MASK_HSV = DEFAULT_COLOR_MASK_HSV

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"
_SHIP_BLUEPRINT_TYPE = "MyObjectBuilder_ShipBlueprintDefinition"
_CUBE_BLOCK_TYPE = "MyObjectBuilder_CubeBlock"
# Keen object-builder type names. Not an allowlist of supported geometry.
_OBJECT_BUILDER_TYPE_RE = re.compile(r"^MyObjectBuilder_[A-Za-z][A-Za-z0-9_]*$")
_SUPPORTED_DIRECTIONS = {item.value: item for item in Direction}
_DIRECTION_AXIS = {
    Direction.FORWARD: "forward_backward",
    Direction.BACKWARD: "forward_backward",
    Direction.LEFT: "left_right",
    Direction.RIGHT: "left_right",
    Direction.UP: "up_down",
    Direction.DOWN: "up_down",
}

# Cheap rejection of XML constructs Space Engineers blueprints do not need.
_REJECTED_XML_MARKERS = (
    "<!doctype",
    "<!entity",
    "xinclude",
    "xi:include",
)

_UNSUPPORTED_GRID_CHILDREN = frozenset(
    {
        "MechanicalGroups",
        "CubeGrids",
    }
)
_UNSUPPORTED_BLOCK_CHILDREN = frozenset(
    {
        "SubBlocks",
        "MultiBlockId",
        "MultiBlockDefinition",
    }
)


def parse_blueprint(path: str | Path) -> ParsedBlueprint:
    """Parse a blueprint from an operator-selected filesystem path."""
    blueprint_path = Path(path)
    if not blueprint_path.is_file():
        raise BlueprintParseError(f"blueprint path is not a file: {blueprint_path}")
    try:
        xml_text = blueprint_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise MalformedXmlError(
            f"blueprint is not UTF-8 text: {blueprint_path}"
        ) from exc
    return parse_blueprint_xml(xml_text, source=str(blueprint_path))


def parse_blueprint_xml(xml_text: str, *, source: str = "<xml>") -> ParsedBlueprint:
    """Parse an already-loaded blueprint XML document."""
    _reject_disallowed_xml_constructs(xml_text, source)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise MalformedXmlError(f"malformed XML in {source}: {exc}") from exc
    return _parse_document(root, source)


def _reject_disallowed_xml_constructs(xml_text: str, source: str) -> None:
    lowered = xml_text.lower()
    for marker in _REJECTED_XML_MARKERS:
        if marker in lowered:
            raise MalformedXmlError(
                f"XML construct {marker!r} is not accepted in {source}"
            )


def _parse_document(root: ET.Element, source: str) -> ParsedBlueprint:
    if _local_name(root) != "Definitions":
        raise UnsupportedBlueprintError(
            f"{source}: root element must be Definitions, got {_local_name(root)!r}"
        )

    unexpected_root_children = [
        _local_name(child)
        for child in list(root)
        if _local_name(child) != "ShipBlueprints"
    ]
    if unexpected_root_children:
        raise UnsupportedBlueprintError(
            f"{source}: unsupported Definitions children: "
            f"{', '.join(sorted(set(unexpected_root_children)))}"
        )

    ship_blueprints_nodes = _children(root, "ShipBlueprints")
    if len(ship_blueprints_nodes) != 1:
        raise UnsupportedBlueprintError(
            f"{source}: document must contain exactly one ShipBlueprints element"
        )

    ship_nodes = _children(ship_blueprints_nodes[0], "ShipBlueprint")
    if len(ship_nodes) != 1:
        raise UnsupportedBlueprintError(
            f"{source}: document must contain exactly one ShipBlueprint"
        )
    ship = ship_nodes[0]
    ship_type = _xsi_type(ship)
    if ship_type is not None and ship_type != _SHIP_BLUEPRINT_TYPE:
        raise UnsupportedBlueprintError(
            f"{source}: unsupported ShipBlueprint type {ship_type!r}"
        )

    identity = _optional_id_subtype(ship, source)
    display_name = _optional_text_child(ship, "DisplayName")
    grid = _parse_single_grid(ship, source)
    return ParsedBlueprint(
        identity_subtype=identity,
        display_name=display_name,
        grid=grid,
    )


def _parse_single_grid(ship: ET.Element, source: str) -> ParsedGrid:
    cube_grids_nodes = _children(ship, "CubeGrids")
    if len(cube_grids_nodes) != 1:
        raise UnsupportedBlueprintError(
            f"{source}: ShipBlueprint must contain exactly one CubeGrids element"
        )

    all_grids = [el for el in ship.iter() if _local_name(el) == "CubeGrid"]
    if len(all_grids) == 0:
        raise UnsupportedBlueprintError(f"{source}: blueprint contains zero CubeGrid elements")
    if len(all_grids) > 1:
        raise UnsupportedBlueprintError(
            f"{source}: multiple CubeGrid elements are not supported"
        )

    grid = all_grids[0]
    if grid not in list(cube_grids_nodes[0]):
        raise UnsupportedBlueprintError(
            f"{source}: CubeGrid must be a direct child of CubeGrids"
        )

    for child in list(grid):
        name = _local_name(child)
        if name in _UNSUPPORTED_GRID_CHILDREN:
            raise UnsupportedBlueprintError(
                f"{source}: CubeGrid child {name!r} is not supported"
            )
        if name == "CubeGrid":
            raise UnsupportedBlueprintError(f"{source}: nested CubeGrid is not supported")

    grid_size_text = _required_text_child(grid, "GridSizeEnum", source, "CubeGrid")
    if grid_size_text != GridSize.LARGE.value:
        raise UnsupportedBlueprintError(
            f"{source}: only Large Grid is supported, got GridSizeEnum={grid_size_text!r}"
        )

    cube_blocks_nodes = _children(grid, "CubeBlocks")
    if len(cube_blocks_nodes) != 1:
        raise UnsupportedBlueprintError(
            f"{source}: CubeGrid must contain exactly one CubeBlocks element"
        )

    blocks = _parse_cube_blocks(cube_blocks_nodes[0], source)
    return ParsedGrid(
        display_name=_optional_text_child(grid, "DisplayName"),
        grid_size=GridSize.LARGE,
        blocks=tuple(blocks),
    )


def _parse_cube_blocks(cube_blocks: ET.Element, source: str) -> list[ParsedBlock]:
    parsed: list[ParsedBlock] = []
    for index, child in enumerate(list(cube_blocks)):
        name = _local_name(child)
        if name != _CUBE_BLOCK_TYPE:
            raise UnsupportedBlueprintError(
                f"{source}: CubeBlocks[{index}] has unsupported element {name!r}"
            )
        declared_type = _xsi_type(child)
        object_builder_type = _accepted_object_builder_type(declared_type)
        if object_builder_type is None:
            raise UnsupportedBlueprintError(
                f"{source}: CubeBlocks[{index}] has unsupported xsi:type "
                f"{declared_type!r}"
            )
        parsed.append(
            _parse_cube_block(child, index, source, object_builder_type)
        )
    return parsed


def _accepted_object_builder_type(token: Optional[str]) -> Optional[str]:
    """Return a representable cube-block object-builder type, or None.

    Omitted ``xsi:type`` is the XmlSerializer default for a ``CubeBlocks``
    item: ``MyObjectBuilder_CubeBlock``. A present token must be a Keen
    ``MyObjectBuilder_*`` identifier. Acceptance here is structural, not
    catalog support.
    """
    if token is None:
        return _CUBE_BLOCK_TYPE
    if _OBJECT_BUILDER_TYPE_RE.fullmatch(token):
        return token
    return None


def _parse_cube_block(
    block: ET.Element,
    index: int,
    source: str,
    object_builder_type: str,
) -> ParsedBlock:
    context = f"{source}: CubeBlocks[{index}]"
    subtype_nodes = _children(block, "SubtypeName")
    if len(subtype_nodes) != 1:
        raise MissingRequiredFieldError(
            f"{context}: exactly one SubtypeName is required"
        )
    subtype_id = _text_of(subtype_nodes[0])
    if subtype_id is None:
        subtype_id = ""
    if subtype_id == "":
        if (
            object_builder_type == _CUBE_BLOCK_TYPE
            or not object_builder_type.startswith("MyObjectBuilder_")
            or object_builder_type == ""
        ):
            raise MissingRequiredFieldError(
                f"{context}: empty SubtypeName is unidentified without a "
                "specific object-builder type"
            )

    min_nodes = _children(block, "Min")
    if len(min_nodes) > 1:
        raise InvalidFieldError(f"{context}: multiple Min elements")
    if min_nodes:
        coordinate = _parse_min(min_nodes[0], context)
        min_serialized = True
    else:
        coordinate = _DEFAULT_MIN
        min_serialized = False

    orientation_nodes = _children(block, "BlockOrientation")
    if len(orientation_nodes) > 1:
        raise InvalidFieldError(f"{context}: multiple BlockOrientation elements")
    if orientation_nodes:
        forward, up = _parse_orientation(orientation_nodes[0], context)
        orientation_serialized = True
    else:
        forward, up = _DEFAULT_ORIENTATION
        orientation_serialized = False

    color_nodes = _children(block, "ColorMaskHSV")
    if len(color_nodes) > 1:
        raise InvalidFieldError(f"{context}: multiple ColorMaskHSV elements")
    if color_nodes:
        color_mask_hsv = _parse_color_mask_hsv(color_nodes[0], context)
        color_serialized = True
        appearance_support = AppearanceSupport.EXPLICIT
    else:
        color_mask_hsv = _DEFAULT_COLOR_MASK_HSV
        color_serialized = False
        appearance_support = AppearanceSupport.DEFAULT

    unsupported = sorted(
        {
            _local_name(child)
            for child in list(block)
            if _local_name(child) in _UNSUPPORTED_BLOCK_CHILDREN
        }
    )
    if unsupported:
        raise UnsupportedBlueprintError(
            f"{context}: unsupported cube-block child {', '.join(unsupported)}"
        )

    return ParsedBlock(
        subtype_id=subtype_id,
        object_builder_type=object_builder_type,
        min=coordinate,
        min_serialized=min_serialized,
        forward=forward,
        up=up,
        orientation_serialized=orientation_serialized,
        color_mask_hsv=color_mask_hsv,
        color_serialized=color_serialized,
        appearance_support=appearance_support,
        source_index=index,
        source=source,
    )


def _parse_min(min_el: ET.Element, context: str) -> GridCoordinate:
    if _is_nil(min_el):
        raise InvalidFieldError(f"{context}: Min is nil")
    if list(min_el):
        raise InvalidFieldError(f"{context}: Min must use x/y/z attributes")
    allowed = {"x", "y", "z"}
    extras = set(min_el.attrib) - allowed - {_XSI_TYPE, "type"}
    if extras:
        raise InvalidFieldError(
            f"{context}: Min has unsupported attributes {sorted(extras)}"
        )
    missing = [axis for axis in ("x", "y", "z") if axis not in min_el.attrib]
    if missing:
        raise MissingRequiredFieldError(
            f"{context}: Min is missing attribute(s) {', '.join(missing)}"
        )
    return GridCoordinate(
        x=_parse_int_attr(min_el, "x", context),
        y=_parse_int_attr(min_el, "y", context),
        z=_parse_int_attr(min_el, "z", context),
    )


def _parse_orientation(el: ET.Element, context: str) -> tuple[Direction, Direction]:
    if _is_nil(el):
        raise InvalidFieldError(f"{context}: BlockOrientation is nil")
    if list(el):
        raise InvalidFieldError(
            f"{context}: BlockOrientation must use Forward/Up attributes"
        )
    allowed = {"Forward", "Up"}
    extras = set(el.attrib) - allowed - {_XSI_TYPE, "type"}
    if extras:
        raise InvalidFieldError(
            f"{context}: BlockOrientation has unsupported attributes {sorted(extras)}"
        )
    if "Forward" not in el.attrib or "Up" not in el.attrib:
        raise MissingRequiredFieldError(
            f"{context}: BlockOrientation requires Forward and Up"
        )
    forward = _parse_direction(el.attrib["Forward"], "Forward", context)
    up = _parse_direction(el.attrib["Up"], "Up", context)
    if _DIRECTION_AXIS[forward] == _DIRECTION_AXIS[up]:
        raise InvalidFieldError(
            f"{context}: BlockOrientation Forward={forward.value!r} "
            f"Up={up.value!r} are not orthogonal"
        )
    return forward, up


def _parse_color_mask_hsv(el: ET.Element, context: str) -> ColorMaskHSV:
    if _is_nil(el):
        raise InvalidFieldError(f"{context}: ColorMaskHSV is nil")
    if list(el):
        raise InvalidFieldError(
            f"{context}: ColorMaskHSV must use x/y/z attributes"
        )
    allowed = {"x", "y", "z"}
    extras = set(el.attrib) - allowed - {_XSI_TYPE, "type"}
    if extras:
        raise InvalidFieldError(
            f"{context}: ColorMaskHSV has unsupported attributes {sorted(extras)}"
        )
    missing = [axis for axis in ("x", "y", "z") if axis not in el.attrib]
    if missing:
        raise MissingRequiredFieldError(
            f"{context}: ColorMaskHSV is missing attribute(s) {', '.join(missing)}"
        )
    return ColorMaskHSV(
        h=_parse_float_attr(el, "x", context, "ColorMaskHSV"),
        s=_parse_float_attr(el, "y", context, "ColorMaskHSV"),
        v=_parse_float_attr(el, "z", context, "ColorMaskHSV"),
    )


def _parse_direction(token: str, field: str, context: str) -> Direction:
    try:
        return _SUPPORTED_DIRECTIONS[token]
    except KeyError:
        raise InvalidFieldError(
            f"{context}: invalid {field} direction token {token!r}"
        ) from None


def _parse_int_attr(el: ET.Element, name: str, context: str) -> int:
    raw = el.attrib[name]
    if raw.strip() != raw or raw == "" or raw[0] == "+" or " " in raw:
        raise InvalidFieldError(f"{context}: Min @{name} is not an integer: {raw!r}")
    try:
        value = int(raw, 10)
    except ValueError:
        raise InvalidFieldError(
            f"{context}: Min @{name} is not an integer: {raw!r}"
        ) from None
    if str(value) != raw:
        raise InvalidFieldError(f"{context}: Min @{name} is not an integer: {raw!r}")
    return value


_REJECTED_FLOAT_TOKENS = frozenset(
    {
        "nan",
        "inf",
        "+inf",
        "-inf",
        "infinity",
        "+infinity",
        "-infinity",
    }
)


def _parse_float_attr(
    el: ET.Element, name: str, context: str, field: str
) -> float:
    raw = el.attrib[name]
    if (
        raw.strip() != raw
        or raw == ""
        or raw[0] == "+"
        or " " in raw
        or "_" in raw
        or len(raw) > 32
    ):
        raise InvalidFieldError(
            f"{context}: {field} @{name} is not a finite float: {raw!r}"
        )
    if raw.lower() in _REJECTED_FLOAT_TOKENS:
        raise InvalidFieldError(
            f"{context}: {field} @{name} is not a finite float: {raw!r}"
        )
    try:
        value = float(raw)
    except ValueError:
        raise InvalidFieldError(
            f"{context}: {field} @{name} is not a finite float: {raw!r}"
        ) from None
    if not math.isfinite(value):
        raise InvalidFieldError(
            f"{context}: {field} @{name} is not a finite float: {raw!r}"
        )
    return value


def _optional_id_subtype(ship: ET.Element, source: str) -> Optional[str]:
    id_nodes = _children(ship, "Id")
    if len(id_nodes) == 0:
        return None
    if len(id_nodes) > 1:
        raise InvalidFieldError(f"{source}: multiple ShipBlueprint Id elements")
    subtype = id_nodes[0].get("Subtype")
    if subtype is None:
        return None
    if subtype == "":
        raise InvalidFieldError(f"{source}: ShipBlueprint Id Subtype is empty")
    return subtype


def _required_text_child(
    parent: ET.Element, name: str, source: str, parent_name: str
) -> str:
    nodes = _children(parent, name)
    if len(nodes) != 1:
        raise MissingRequiredFieldError(
            f"{source}: {parent_name} must contain exactly one {name}"
        )
    text = _text_of(nodes[0])
    if text is None or text == "":
        raise MissingRequiredFieldError(f"{source}: {parent_name}/{name} is empty")
    return text


def _optional_text_child(parent: ET.Element, name: str) -> Optional[str]:
    nodes = _children(parent, name)
    if not nodes:
        return None
    return _text_of(nodes[0])


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if _local_name(child) == name]


def _local_name(el: ET.Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return str(tag)


def _xsi_type(el: ET.Element) -> Optional[str]:
    if _XSI_TYPE in el.attrib:
        return el.attrib[_XSI_TYPE]
    if "type" in el.attrib:
        return el.attrib["type"]
    return None


def _is_nil(el: ET.Element) -> bool:
    value = el.get("{http://www.w3.org/2001/XMLSchema-instance}nil") or el.get("nil")
    return value in {"true", "1"}


def _text_of(el: ET.Element) -> Optional[str]:
    if el.text is None:
        return None
    return el.text
