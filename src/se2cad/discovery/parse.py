"""Parse untrusted cube-block definition XML into observed catalog fields.

Does not copy Model, Icon, FBX, MWM, or texture references into the result.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from se2cad.catalog.model import CellSize
from se2cad.discovery.errors import DiscoveryParseError
from se2cad.discovery.model import DiscoveredDefinition

_REJECTED_XML_MARKERS = (
    "<!doctype",
    "<!entity",
    "xinclude",
    "xi:include",
)
_MY_OBJECT_BUILDER_PREFIX = "MyObjectBuilder_"
_REQUIRED_SIZE = frozenset({"x", "y", "z"})


def parse_cube_block_definitions_xml(
    xml_text: str,
    *,
    source: str,
    source_kind: str,
    source_relative: str,
) -> tuple[DiscoveredDefinition, ...]:
    """Parse one Definitions/CubeBlocks document into observed facts."""
    _reject_disallowed_xml_constructs(xml_text, source)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise DiscoveryParseError(f"malformed XML in {source}: {exc}") from exc
    if _local_name(root) != "Definitions":
        raise DiscoveryParseError(
            f"{source}: root element must be Definitions, got {_local_name(root)!r}"
        )
    cube_blocks_nodes = _children(root, "CubeBlocks")
    if len(cube_blocks_nodes) != 1:
        raise DiscoveryParseError(
            f"{source}: document must contain exactly one CubeBlocks element"
        )
    discovered: list[DiscoveredDefinition] = []
    seen: set[str] = set()
    for index, child in enumerate(list(cube_blocks_nodes[0])):
        if _local_name(child) != "Definition":
            raise DiscoveryParseError(
                f"{source}: CubeBlocks[{index}] has unsupported element "
                f"{_local_name(child)!r}"
            )
        item = _parse_definition(
            child,
            source=f"{source}: CubeBlocks[{index}]",
            source_kind=source_kind,
            source_relative=source_relative,
        )
        if item.subtype_id in seen:
            raise DiscoveryParseError(
                f"{source}: duplicate SubtypeId {item.subtype_id!r}"
            )
        seen.add(item.subtype_id)
        discovered.append(item)
    return tuple(discovered)


def parse_cube_block_definitions_file(
    path: Path,
    *,
    source_kind: str,
    source_relative: str,
) -> tuple[DiscoveredDefinition, ...]:
    """Read one operator-local ``.sbc`` definition file as UTF-8 text."""
    try:
        xml_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DiscoveryParseError(
            f"definition is not UTF-8 text: {source_relative}"
        ) from exc
    except OSError as exc:
        raise DiscoveryParseError(
            f"cannot read definition {source_relative}: {exc}"
        ) from exc
    return parse_cube_block_definitions_xml(
        xml_text,
        source=source_relative,
        source_kind=source_kind,
        source_relative=source_relative,
    )


def _parse_definition(
    el: ET.Element,
    *,
    source: str,
    source_kind: str,
    source_relative: str,
) -> DiscoveredDefinition:
    type_id, subtype_id = _parse_id(el, source)
    cube_size = _required_text_child(el, "CubeSize", source)
    size = _parse_size(el, source)
    block_topology = _required_text_child(el, "BlockTopology", source)
    cube_topology = _optional_cube_topology(el, source)
    return DiscoveredDefinition(
        subtype_id=subtype_id,
        type_id=type_id,
        cube_size=cube_size,
        size=size,
        block_topology=block_topology,
        cube_topology=cube_topology,
        source_kind=source_kind,
        source_relative=source_relative,
    )


def _parse_id(el: ET.Element, source: str) -> tuple[str, str]:
    id_nodes = _children(el, "Id")
    if len(id_nodes) != 1:
        raise DiscoveryParseError(f"{source}: Definition must contain exactly one Id")
    ident = id_nodes[0]
    type_id = _optional_text_child(ident, "TypeId", source)
    subtype_id = _optional_text_child(ident, "SubtypeId", source)
    if type_id is None:
        type_id = ident.get("Type")
    if subtype_id is None:
        subtype_id = ident.get("Subtype")
    if type_id is None or type_id == "":
        raise DiscoveryParseError(f"{source}: Id TypeId is missing")
    if subtype_id is None or subtype_id == "":
        raise DiscoveryParseError(f"{source}: Id SubtypeId is missing")
    return _normalize_type_id(type_id), subtype_id


def _normalize_type_id(type_id: str) -> str:
    if type_id.startswith(_MY_OBJECT_BUILDER_PREFIX):
        return type_id[len(_MY_OBJECT_BUILDER_PREFIX) :]
    return type_id


def _parse_size(parent: ET.Element, source: str) -> CellSize:
    nodes = _children(parent, "Size")
    if len(nodes) != 1:
        raise DiscoveryParseError(f"{source}: Definition must contain exactly one Size")
    el = nodes[0]
    missing = [name for name in ("x", "y", "z") if name not in el.attrib]
    if missing:
        raise DiscoveryParseError(
            f"{source}: Size missing attribute(s): {', '.join(missing)}"
        )
    extra = sorted(set(el.attrib) - _REQUIRED_SIZE)
    if extra:
        raise DiscoveryParseError(
            f"{source}: Size has unexpected attribute(s): {', '.join(extra)}"
        )
    return CellSize(
        x=_positive_int(el.attrib["x"], f"{source}: Size @x"),
        y=_positive_int(el.attrib["y"], f"{source}: Size @y"),
        z=_positive_int(el.attrib["z"], f"{source}: Size @z"),
    )


def _optional_cube_topology(parent: ET.Element, source: str) -> Optional[str]:
    cube_defs = _children(parent, "CubeDefinition")
    if not cube_defs:
        return None
    if len(cube_defs) > 1:
        raise DiscoveryParseError(
            f"{source}: Definition has multiple CubeDefinition elements"
        )
    tokens = _children(cube_defs[0], "CubeTopology")
    if not tokens:
        return None
    if len(tokens) > 1:
        raise DiscoveryParseError(
            f"{source}: CubeDefinition has multiple CubeTopology elements"
        )
    text = _text_of(tokens[0])
    if text is None or text == "":
        raise DiscoveryParseError(f"{source}: CubeTopology is empty")
    return text


def _required_text_child(parent: ET.Element, name: str, source: str) -> str:
    nodes = _children(parent, name)
    if len(nodes) != 1:
        raise DiscoveryParseError(
            f"{source}: Definition must contain exactly one {name}"
        )
    text = _text_of(nodes[0])
    if text is None or text == "":
        raise DiscoveryParseError(f"{source}: {name} is empty")
    return text


def _optional_text_child(
    parent: ET.Element, name: str, source: str | None = None
) -> Optional[str]:
    nodes = _children(parent, name)
    if not nodes:
        return None
    if len(nodes) > 1:
        where = f"{source}: " if source else ""
        raise DiscoveryParseError(f"{where}multiple {name} elements")
    return _text_of(nodes[0])


def _reject_disallowed_xml_constructs(xml_text: str, source: str) -> None:
    lowered = xml_text.lower()
    for marker in _REJECTED_XML_MARKERS:
        if marker in lowered:
            raise DiscoveryParseError(
                f"XML construct {marker!r} is not accepted in {source}"
            )


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if _local_name(child) == name]


def _local_name(el: ET.Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return str(tag)


def _text_of(el: ET.Element) -> Optional[str]:
    if el.text is None:
        return None
    return el.text.strip()


def _positive_int(raw: str, loc: str) -> int:
    if raw.strip() != raw or raw == "" or raw[0] == "+" or " " in raw:
        raise DiscoveryParseError(f"{loc} is not an integer: {raw!r}")
    try:
        value = int(raw, 10)
    except ValueError:
        raise DiscoveryParseError(f"{loc} is not an integer: {raw!r}") from None
    if str(value) != raw:
        raise DiscoveryParseError(f"{loc} is not an integer: {raw!r}")
    if value < 1:
        raise DiscoveryParseError(f"{loc} must be >= 1")
    return value
