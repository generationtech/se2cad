"""Survey-only document intake for ShipBlueprint and official Prefab XML.

This module does not change the production parser. A single-grid Large
Grid prefab may be wrapped into ShipBlueprint XML so existing parse,
statistics, and preflight paths can run. Multi-grid and Small Grid
content is recorded, not discarded.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from xml.sax.saxutils import escape as _xml_escape
from xml.sax.saxutils import quoteattr as _xml_quoteattr

from se2cad.parser import parse_blueprint, parse_blueprint_xml
from se2cad.parser.errors import BlueprintParseError
from se2cad.parser.model import ParsedBlueprint
from se2cad.survey.model import (
    ExtractedSurveyBlock,
    SourceDocumentKind,
    StructuralGrid,
    StructuralSurvey,
)

_XSI = "http://www.w3.org/2001/XMLSchema-instance"
_XSD = "http://www.w3.org/2001/XMLSchema"
_REJECTED_XML_MARKERS = (
    "<!doctype",
    "<!entity",
    "xinclude",
    "xi:include",
)
_SHIP_BLUEPRINT_TYPE = "MyObjectBuilder_ShipBlueprintDefinition"


def _local_name(el: ET.Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return str(tag)


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if _local_name(child) == name]


def _text_of(el: ET.Element) -> Optional[str]:
    if el.text is None:
        return None
    text = el.text.strip()
    return text if text else None


def _reject_disallowed(xml_text: str, source: str) -> None:
    lowered = xml_text.lower()
    for marker in _REJECTED_XML_MARKERS:
        if marker in lowered:
            raise BlueprintParseError(
                f"XML construct {marker!r} is not accepted in {source}"
            )


def inspect_document_structure(path: str | Path) -> StructuralSurvey:
    """Read document-level facts without granting conversion support."""
    blueprint_path = Path(path)
    if not blueprint_path.is_file():
        raise BlueprintParseError(f"blueprint path is not a file: {blueprint_path}")
    raw = blueprint_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BlueprintParseError(
            f"blueprint is not UTF-8 text: {blueprint_path}"
        ) from exc
    _reject_disallowed(text, str(blueprint_path))
    root = ET.fromstring(text)
    if _local_name(root) != "Definitions":
        return StructuralSurvey(
            source_path=str(blueprint_path),
            sha256=digest,
            byte_count=len(raw),
            kind=SourceDocumentKind.UNSUPPORTED,
            identity=None,
            display_name=None,
            grid_count=0,
            grids=(),
            total_blocks=0,
            unique_subtype_count=0,
            has_non_large_grid=False,
            has_multiple_grids=False,
            parser_error=f"root element must be Definitions, got {_local_name(root)!r}",
            wrapped_for_parser=False,
        )
    if _children(root, "ShipBlueprints"):
        kind = SourceDocumentKind.SHIP_BLUEPRINT
        hosts = _children(_children(root, "ShipBlueprints")[0], "ShipBlueprint")
        host = hosts[0] if hosts else None
    elif _children(root, "Prefabs"):
        kind = SourceDocumentKind.PREFAB
        hosts = _children(_children(root, "Prefabs")[0], "Prefab")
        host = hosts[0] if hosts else None
    else:
        return StructuralSurvey(
            source_path=str(blueprint_path),
            sha256=digest,
            byte_count=len(raw),
            kind=SourceDocumentKind.UNSUPPORTED,
            identity=None,
            display_name=None,
            grid_count=0,
            grids=(),
            total_blocks=0,
            unique_subtype_count=0,
            has_non_large_grid=False,
            has_multiple_grids=False,
            parser_error="document is neither ShipBlueprints nor Prefabs",
            wrapped_for_parser=False,
        )

    identity = None
    display_name = None
    if host is not None:
        ids = _children(host, "Id")
        if ids:
            identity = ids[0].get("Subtype")
        names = _children(host, "DisplayName")
        if names:
            display_name = _text_of(names[0])

    grids: list[StructuralGrid] = []
    subtypes: set[str] = set()
    if host is not None:
        for grid in (el for el in host.iter() if _local_name(el) == "CubeGrid"):
            size_nodes = _children(grid, "GridSizeEnum")
            size = _text_of(size_nodes[0]) if size_nodes else None
            names = _children(grid, "DisplayName")
            grid_name = _text_of(names[0]) if names else None
            block_subtypes: list[str] = []
            cubes = _children(grid, "CubeBlocks")
            if cubes:
                for block in list(cubes[0]):
                    if _local_name(block) != "MyObjectBuilder_CubeBlock":
                        continue
                    subtype_nodes = _children(block, "SubtypeName")
                    subtype = _text_of(subtype_nodes[0]) if subtype_nodes else ""
                    block_subtypes.append(subtype)
                    subtypes.add(subtype)
            grids.append(
                StructuralGrid(
                    display_name=grid_name,
                    grid_size=size,
                    block_count=len(block_subtypes),
                    unique_subtype_count=len(set(block_subtypes)),
                    mechanical_groups=len(_children(grid, "MechanicalGroups")),
                )
            )

    return StructuralSurvey(
        source_path=str(blueprint_path),
        sha256=digest,
        byte_count=len(raw),
        kind=kind,
        identity=identity,
        display_name=display_name,
        grid_count=len(grids),
        grids=tuple(grids),
        total_blocks=sum(grid.block_count for grid in grids),
        unique_subtype_count=len(subtypes),
        has_non_large_grid=any(grid.grid_size != "Large" for grid in grids),
        has_multiple_grids=len(grids) > 1,
        parser_error=None,
        wrapped_for_parser=False,
    )


def wrap_prefab_as_ship_blueprint(xml_text: str, *, source: str) -> str:
    """Return ShipBlueprint XML for a single-grid Large Grid prefab."""
    _reject_disallowed(xml_text, source)
    root = ET.fromstring(xml_text)
    prefabs = _children(root, "Prefabs")
    if len(prefabs) != 1:
        raise BlueprintParseError(f"{source}: prefab wrap requires one Prefabs element")
    prefab_nodes = _children(prefabs[0], "Prefab")
    if len(prefab_nodes) != 1:
        raise BlueprintParseError(f"{source}: prefab wrap requires one Prefab")
    prefab = prefab_nodes[0]
    grids = [el for el in prefab.iter() if _local_name(el) == "CubeGrid"]
    if len(grids) != 1:
        raise BlueprintParseError(
            f"{source}: prefab wrap requires exactly one CubeGrid, got {len(grids)}"
        )
    grid = grids[0]
    size_nodes = _children(grid, "GridSizeEnum")
    size = _text_of(size_nodes[0]) if size_nodes else None
    if size != "Large":
        raise BlueprintParseError(
            f"{source}: prefab wrap requires Large Grid, got {size!r}"
        )
    identity = "survey-prefab"
    ids = _children(prefab, "Id")
    if ids and ids[0].get("Subtype"):
        identity = ids[0].get("Subtype") or identity
    display = _children(prefab, "DisplayName")
    display_name = _text_of(display[0]) if display else identity

    ET.register_namespace("xsi", _XSI)
    ET.register_namespace("xsd", _XSD)
    grid_xml = ET.tostring(grid, encoding="unicode")
    return (
        '<?xml version="1.0"?>'
        f'<Definitions xmlns:xsd="{_XSD}" xmlns:xsi="{_XSI}">'
        "<ShipBlueprints>"
        f'<ShipBlueprint xsi:type="{_SHIP_BLUEPRINT_TYPE}">'
        f"<Id Type={_xml_quoteattr(_SHIP_BLUEPRINT_TYPE)} "
        f"Subtype={_xml_quoteattr(identity)} />"
        f"<DisplayName>{_xml_escape(display_name)}</DisplayName>"
        "<CubeGrids>"
        f"{grid_xml}"
        "</CubeGrids>"
        "</ShipBlueprint>"
        "</ShipBlueprints>"
        "</Definitions>"
    )


def extract_survey_blocks(path: str | Path) -> tuple[ExtractedSurveyBlock, ...]:
    """Read CubeBlocks items without requiring a successful production parse."""
    structural = inspect_document_structure(path)
    text = Path(path).read_text(encoding="utf-8")
    _reject_disallowed(text, str(path))
    root = ET.fromstring(text)
    hosts: list[ET.Element] = []
    if _children(root, "ShipBlueprints"):
        hosts = _children(_children(root, "ShipBlueprints")[0], "ShipBlueprint")
    elif _children(root, "Prefabs"):
        hosts = _children(_children(root, "Prefabs")[0], "Prefab")
    if not hosts:
        return ()
    host = hosts[0]
    if structural.has_multiple_grids:
        grids = [el for el in host.iter() if _local_name(el) == "CubeGrid"]
        large = [
            grid
            for grid in grids
            if _children(grid, "GridSizeEnum")
            and _text_of(_children(grid, "GridSizeEnum")[0]) == "Large"
        ]
        target = large[0] if len(large) == 1 else (grids[0] if grids else None)
    else:
        grids = [el for el in host.iter() if _local_name(el) == "CubeGrid"]
        target = grids[0] if grids else None
    if target is None:
        return ()
    cubes = _children(target, "CubeBlocks")
    if not cubes:
        return ()
    extracted: list[ExtractedSurveyBlock] = []
    for index, child in enumerate(list(cubes[0])):
        if _local_name(child) != "MyObjectBuilder_CubeBlock":
            continue
        declared = child.get("{http://www.w3.org/2001/XMLSchema-instance}type")
        builder = declared or "MyObjectBuilder_CubeBlock"
        subtype_nodes = _children(child, "SubtypeName")
        subtype = _text_of(subtype_nodes[0]) if subtype_nodes else ""
        if subtype is None:
            subtype = ""
        mins = _children(child, "Min")
        min_x = min_y = min_z = None
        if mins:
            try:
                min_x = int(mins[0].attrib["x"], 10)
                min_y = int(mins[0].attrib["y"], 10)
                min_z = int(mins[0].attrib["z"], 10)
            except (KeyError, ValueError):
                min_x = min_y = min_z = None
        extracted.append(
            ExtractedSurveyBlock(
                source_index=index,
                subtype_id=subtype,
                object_builder_type=builder,
                min_x=min_x,
                min_y=min_y,
                min_z=min_z,
            )
        )
    return tuple(extracted)


def load_survey_blueprint(path: str | Path) -> tuple[StructuralSurvey, ParsedBlueprint | None]:
    """Inspect a document and parse it when the current parser can."""
    structural = inspect_document_structure(path)
    if structural.kind is SourceDocumentKind.SHIP_BLUEPRINT:
        try:
            parsed = parse_blueprint(path)
        except BlueprintParseError as exc:
            return (
                StructuralSurvey(
                    source_path=structural.source_path,
                    sha256=structural.sha256,
                    byte_count=structural.byte_count,
                    kind=structural.kind,
                    identity=structural.identity,
                    display_name=structural.display_name,
                    grid_count=structural.grid_count,
                    grids=structural.grids,
                    total_blocks=structural.total_blocks,
                    unique_subtype_count=structural.unique_subtype_count,
                    has_non_large_grid=structural.has_non_large_grid,
                    has_multiple_grids=structural.has_multiple_grids,
                    parser_error=str(exc),
                    wrapped_for_parser=False,
                ),
                None,
            )
        return structural, parsed

    if (
        structural.kind is SourceDocumentKind.PREFAB
        and structural.grid_count == 1
        and not structural.has_non_large_grid
        and not structural.has_multiple_grids
    ):
        text = Path(path).read_text(encoding="utf-8")
        try:
            wrapped = wrap_prefab_as_ship_blueprint(text, source=str(path))
            parsed = parse_blueprint_xml(wrapped, source=f"{path}#survey-wrap")
        except BlueprintParseError as exc:
            return (
                StructuralSurvey(
                    source_path=structural.source_path,
                    sha256=structural.sha256,
                    byte_count=structural.byte_count,
                    kind=structural.kind,
                    identity=structural.identity,
                    display_name=structural.display_name,
                    grid_count=structural.grid_count,
                    grids=structural.grids,
                    total_blocks=structural.total_blocks,
                    unique_subtype_count=structural.unique_subtype_count,
                    has_non_large_grid=structural.has_non_large_grid,
                    has_multiple_grids=structural.has_multiple_grids,
                    parser_error=str(exc),
                    wrapped_for_parser=True,
                ),
                None,
            )
        wrapped_structural = StructuralSurvey(
            source_path=structural.source_path,
            sha256=structural.sha256,
            byte_count=structural.byte_count,
            kind=structural.kind,
            identity=structural.identity,
            display_name=structural.display_name,
            grid_count=structural.grid_count,
            grids=structural.grids,
            total_blocks=structural.total_blocks,
            unique_subtype_count=structural.unique_subtype_count,
            has_non_large_grid=structural.has_non_large_grid,
            has_multiple_grids=structural.has_multiple_grids,
            parser_error=None,
            wrapped_for_parser=True,
        )
        return wrapped_structural, parsed

    return structural, None
