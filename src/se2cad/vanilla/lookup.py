"""Targeted exact-subtype CubeBlocks lookup.

Walks operator-local CubeBlocks ``.sbc`` files once per game-content
root. Sibling definitions that cannot be interpreted are skipped.
A malformed *target* definition is recorded as unusable, not as
absence. Duplicate exact SubtypeId hits fail closed.
"""

from __future__ import annotations

import threading
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from se2cad.catalog.model import CellSize
from se2cad.transform.errors import InvalidModelOffsetError
from se2cad.transform.placement import ModelOffset
from se2cad.vanilla.errors import VanillaLookupError

_REJECTED_XML_MARKERS = (
    "<!doctype",
    "<!entity",
    "xinclude",
    "xi:include",
)
_MY_OBJECT_BUILDER_PREFIX = "MyObjectBuilder_"
_DEFINITION_RELATIVE_DIRS = (
    Path("Content") / "Data" / "CubeBlocks",
    Path("Data") / "CubeBlocks",
)
_REQUIRED_SIZE = frozenset({"x", "y", "z"})


@dataclass(frozen=True)
class TargetedDefinition:
    """Facts extracted for one exact SubtypeId. Not a support grant."""

    subtype_id: str
    type_id: str
    cube_size: str
    size: CellSize
    block_topology: str
    cube_topology: Optional[str]
    primary_model: str
    has_subparts: bool
    model_count: int
    source_relative: str
    model_offset: ModelOffset = field(default_factory=ModelOffset.zero)


@dataclass(frozen=True)
class TargetedHit:
    """One exact-subtype match, usable or not."""

    subtype_id: str
    source_relative: str
    definition: Optional[TargetedDefinition]
    unusable_reason: Optional[str]


@dataclass(frozen=True)
class CubeBlockIndex:
    """In-memory exact-subtype index. Indexing does not imply support."""

    game_root: Path
    hits_by_subtype: dict[str, tuple[TargetedHit, ...]]
    files_read: tuple[str, ...]
    skipped_files: tuple[str, ...]


_INDEX_LOCK = threading.Lock()
_INDEX_CACHE: dict[Path, CubeBlockIndex] = {}


def clear_vanilla_definition_index() -> None:
    """Drop cached indexes. Tests use this for isolation."""
    with _INDEX_LOCK:
        _INDEX_CACHE.clear()


def cube_block_index(game_root: Path) -> CubeBlockIndex:
    """Return the CubeBlocks index for ``game_root``, building it once."""
    resolved = game_root.expanduser().resolve()
    with _INDEX_LOCK:
        cached = _INDEX_CACHE.get(resolved)
        if cached is not None:
            return cached
        built = _build_index(resolved)
        _INDEX_CACHE[resolved] = built
        return built


def lookup_exact_subtype(
    subtype_id: str,
    game_root: Path,
) -> TargetedHit | None:
    """Return the unique exact-subtype hit, or None when absent.

    Duplicate exact matches raise. A present but unusable target is a
    hit with ``definition is None``.
    """
    if not isinstance(subtype_id, str) or subtype_id == "":
        raise VanillaLookupError("subtype_id must be a non-empty string")
    index = cube_block_index(game_root)
    hits = index.hits_by_subtype.get(subtype_id, ())
    if not hits:
        return None
    if len(hits) > 1:
        sources = ", ".join(hit.source_relative for hit in hits)
        raise VanillaLookupError(
            f"duplicate SubtypeId {subtype_id!r} in {sources}"
        )
    return hits[0]


def _build_index(game_root: Path) -> CubeBlockIndex:
    directories = _definition_directories(game_root)
    by_subtype: dict[str, list[TargetedHit]] = {}
    files_read: list[str] = []
    skipped: list[str] = []
    for directory in directories:
        for candidate in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if not candidate.is_file() or candidate.suffix.lower() != ".sbc":
                continue
            contained = _contained_file(game_root, candidate)
            relative = contained.relative_to(game_root).as_posix()
            try:
                xml_text = contained.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                skipped.append(f"{relative}: {exc}")
                continue
            try:
                hits = _extract_hits(xml_text, source_relative=relative)
            except VanillaLookupError as exc:
                skipped.append(f"{relative}: {exc}")
                continue
            files_read.append(relative)
            for hit in hits:
                by_subtype.setdefault(hit.subtype_id, []).append(hit)
    frozen = {
        subtype: tuple(hits) for subtype, hits in by_subtype.items()
    }
    return CubeBlockIndex(
        game_root=game_root,
        hits_by_subtype=frozen,
        files_read=tuple(sorted(files_read)),
        skipped_files=tuple(skipped),
    )


def _definition_directories(root: Path) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for relative in _DEFINITION_RELATIVE_DIRS:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError as exc:
            raise VanillaLookupError(
                f"definition directory {candidate} escapes root {root}"
            ) from exc
        if not candidate.is_dir() or candidate in seen:
            continue
        seen.add(candidate)
        found.append(candidate)
    return found


def _contained_file(root: Path, candidate: Path) -> Path:
    resolved_root = root.expanduser().resolve()
    resolved = candidate.expanduser().resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise VanillaLookupError(
            f"path {resolved} escapes configured root {resolved_root}"
        ) from exc
    if not resolved.is_file():
        raise VanillaLookupError(f"definition path is not a file: {resolved}")
    return resolved


def _extract_hits(xml_text: str, *, source_relative: str) -> tuple[TargetedHit, ...]:
    _reject_disallowed_xml_constructs(xml_text, source_relative)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise VanillaLookupError(
            f"malformed XML in {source_relative}: {exc}"
        ) from exc
    if _local_name(root) != "Definitions":
        raise VanillaLookupError(
            f"{source_relative}: root element must be Definitions"
        )
    cube_nodes = _children(root, "CubeBlocks")
    if not cube_nodes:
        return ()
    if len(cube_nodes) != 1:
        raise VanillaLookupError(
            f"{source_relative}: document must contain exactly one CubeBlocks element"
        )
    hits: list[TargetedHit] = []
    for index, child in enumerate(list(cube_nodes[0])):
        if _local_name(child) != "Definition":
            continue
        loc = f"{source_relative}: CubeBlocks[{index}]"
        subtype = _try_subtype_id(child)
        if subtype is None:
            continue
        try:
            definition = _parse_usable_definition(
                child, subtype_id=subtype, source_relative=source_relative, loc=loc
            )
        except VanillaLookupError as exc:
            hits.append(
                TargetedHit(
                    subtype_id=subtype,
                    source_relative=source_relative,
                    definition=None,
                    unusable_reason=str(exc),
                )
            )
            continue
        hits.append(
            TargetedHit(
                subtype_id=subtype,
                source_relative=source_relative,
                definition=definition,
                unusable_reason=None,
            )
        )
    return tuple(hits)


def _try_subtype_id(el: ET.Element) -> Optional[str]:
    try:
        _type_id, subtype_id = _parse_id(el, source="sibling")
    except VanillaLookupError:
        return None
    if subtype_id == "":
        return None
    return subtype_id


def _parse_usable_definition(
    el: ET.Element,
    *,
    subtype_id: str,
    source_relative: str,
    loc: str,
) -> TargetedDefinition:
    type_id, parsed_subtype = _parse_id(el, loc)
    if parsed_subtype != subtype_id:
        raise VanillaLookupError(f"{loc}: SubtypeId mismatch")
    cube_size = _required_text_child(el, "CubeSize", loc)
    size = _parse_size(el, loc)
    model_offset = _parse_model_offset(el, loc)
    block_topology = _required_text_child(el, "BlockTopology", loc)
    cube_topology = _optional_cube_topology(el, loc)
    models = _direct_model_texts(el)
    subparts = _children(el, "Subparts")
    has_subparts = any(len(list(node)) > 0 for node in subparts)
    if len(models) == 1:
        primary = models[0]
    elif not models:
        primary = ""
    else:
        primary = models[0]
    return TargetedDefinition(
        subtype_id=parsed_subtype,
        type_id=type_id,
        cube_size=cube_size,
        size=size,
        block_topology=block_topology,
        cube_topology=cube_topology,
        primary_model=primary,
        has_subparts=has_subparts,
        model_count=len(models),
        source_relative=source_relative,
        model_offset=model_offset,
    )


def _direct_model_texts(el: ET.Element) -> tuple[str, ...]:
    texts: list[str] = []
    for child in _children(el, "Model"):
        text = _text_of(child)
        if text is None or text == "":
            texts.append("")
        else:
            texts.append(text)
    return tuple(texts)


def _parse_id(el: ET.Element, source: str) -> tuple[str, str]:
    id_nodes = _children(el, "Id")
    if len(id_nodes) != 1:
        raise VanillaLookupError(f"{source}: Definition must contain exactly one Id")
    ident = id_nodes[0]
    type_id = _optional_text_child(ident, "TypeId", source)
    subtype_id = _optional_text_child(ident, "SubtypeId", source)
    if type_id is None:
        type_id = ident.get("Type")
    if subtype_id is None:
        subtype_id = ident.get("Subtype")
    if type_id is None or type_id == "":
        raise VanillaLookupError(f"{source}: Id TypeId is missing")
    if subtype_id is None:
        raise VanillaLookupError(f"{source}: Id SubtypeId is missing")
    return _normalize_type_id(type_id), subtype_id


def _normalize_type_id(type_id: str) -> str:
    if type_id.startswith(_MY_OBJECT_BUILDER_PREFIX):
        return type_id[len(_MY_OBJECT_BUILDER_PREFIX) :]
    return type_id


def _parse_model_offset(parent: ET.Element, source: str) -> ModelOffset:
    """Read optional ModelOffset. Omitted or explicit zero is zero.

    Keen serializes either attributes (``x y z``) or ``X/Y/Z`` children.
    Definition Center is intentionally not read.
    """
    nodes = _children(parent, "ModelOffset")
    if not nodes:
        return ModelOffset.zero()
    if len(nodes) > 1:
        raise VanillaLookupError(
            f"{source}: Definition must contain at most one ModelOffset"
        )
    el = nodes[0]
    attrib_names = {name.lower() for name in el.attrib}
    children = [child for child in list(el) if _local_name(child)]
    if attrib_names and children:
        raise VanillaLookupError(
            f"{source}: ModelOffset must not mix attributes and children"
        )
    try:
        if attrib_names:
            by_name = {name.lower(): value for name, value in el.attrib.items()}
            missing = [name for name in ("x", "y", "z") if name not in by_name]
            extra = sorted(set(by_name) - _REQUIRED_SIZE)
            if missing:
                raise VanillaLookupError(
                    f"{source}: ModelOffset missing attribute(s): "
                    f"{', '.join(missing)}"
                )
            if extra:
                raise VanillaLookupError(
                    f"{source}: ModelOffset has unexpected attribute(s): "
                    f"{', '.join(extra)}"
                )
            return ModelOffset.from_metres(by_name["x"], by_name["y"], by_name["z"])
        if not children:
            return ModelOffset.zero()
        values: dict[str, str] = {}
        for child in children:
            name = _local_name(child).lower()
            if name not in {"x", "y", "z"}:
                raise VanillaLookupError(
                    f"{source}: ModelOffset has unexpected child {name!r}"
                )
            if name in values:
                raise VanillaLookupError(
                    f"{source}: ModelOffset has duplicate {name!r}"
                )
            text = _text_of(child)
            if text is None or text == "":
                raise VanillaLookupError(f"{source}: ModelOffset.{name} is empty")
            values[name] = text
        missing = [name for name in ("x", "y", "z") if name not in values]
        if missing:
            raise VanillaLookupError(
                f"{source}: ModelOffset missing child(ren): {', '.join(missing)}"
            )
        return ModelOffset.from_metres(values["x"], values["y"], values["z"])
    except InvalidModelOffsetError as exc:
        raise VanillaLookupError(f"{source}: {exc}") from exc


def _parse_size(parent: ET.Element, source: str) -> CellSize:
    nodes = _children(parent, "Size")
    if len(nodes) != 1:
        raise VanillaLookupError(f"{source}: Definition must contain exactly one Size")
    el = nodes[0]
    missing = [name for name in ("x", "y", "z") if name not in el.attrib]
    if missing:
        raise VanillaLookupError(
            f"{source}: Size missing attribute(s): {', '.join(missing)}"
        )
    extra = sorted(set(el.attrib) - _REQUIRED_SIZE)
    if extra:
        raise VanillaLookupError(
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
        raise VanillaLookupError(
            f"{source}: Definition has multiple CubeDefinition elements"
        )
    tokens = _children(cube_defs[0], "CubeTopology")
    if not tokens:
        return None
    if len(tokens) > 1:
        raise VanillaLookupError(
            f"{source}: CubeDefinition has multiple CubeTopology elements"
        )
    text = _text_of(tokens[0])
    if text is None or text == "":
        raise VanillaLookupError(f"{source}: CubeTopology is empty")
    return text


def _required_text_child(parent: ET.Element, name: str, source: str) -> str:
    nodes = _children(parent, name)
    if len(nodes) != 1:
        raise VanillaLookupError(
            f"{source}: Definition must contain exactly one {name}"
        )
    text = _text_of(nodes[0])
    if text is None or text == "":
        raise VanillaLookupError(f"{source}: {name} is empty")
    return text


def _optional_text_child(
    parent: ET.Element, name: str, source: str | None = None
) -> Optional[str]:
    nodes = _children(parent, name)
    if not nodes:
        return None
    if len(nodes) > 1:
        where = f"{source}: " if source else ""
        raise VanillaLookupError(f"{where}multiple {name} elements")
    return _text_of(nodes[0])


def _reject_disallowed_xml_constructs(xml_text: str, source: str) -> None:
    lowered = xml_text.lower()
    for marker in _REJECTED_XML_MARKERS:
        if marker in lowered:
            raise VanillaLookupError(
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
        raise VanillaLookupError(f"{loc} is not an integer: {raw!r}")
    try:
        value = int(raw, 10)
    except ValueError:
        raise VanillaLookupError(f"{loc} is not an integer: {raw!r}") from None
    if str(value) != raw:
        raise VanillaLookupError(f"{loc} is not an integer: {raw!r}")
    if value < 1:
        raise VanillaLookupError(f"{loc} must be >= 1")
    return value
