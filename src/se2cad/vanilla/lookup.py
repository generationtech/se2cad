"""Targeted exact-subtype CubeBlocks lookup.

Walks operator-local CubeBlocks ``.sbc`` files once per game-content
root. Sibling definitions that cannot be interpreted are skipped.
A malformed *target* definition is recorded as unusable, not as
absence. Duplicate exact SubtypeId hits fail closed.

S2C-11.15.1 also indexes empty-SubtypeId definitions by TypeId so a
blueprint empty ``SubtypeName`` can resolve only when that TypeId and
grid class identify exactly one vanilla definition.
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
    type_id: str = ""
    cube_size: Optional[str] = None


@dataclass(frozen=True)
class CubeBlockIndex:
    """In-memory exact-subtype index. Indexing does not imply support."""

    game_root: Path
    hits_by_subtype: dict[str, tuple[TargetedHit, ...]]
    hits_by_empty_type: dict[str, tuple[TargetedHit, ...]]
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


def lookup_unique_empty_subtype(
    type_id: str,
    *,
    cube_size: str,
    game_root: Path,
) -> TargetedHit | None:
    """Return the unique empty-SubtypeId hit for one TypeId and grid class.

    Missing identities return None. Two or more empty-SubtypeId hits for
    the same TypeId and CubeSize fail closed. Non-empty SubtypeId
    variants of the same TypeId do not participate. Small and Large
    definitions are never collapsed.
    """
    if not isinstance(type_id, str) or type_id == "":
        raise VanillaLookupError("type_id must be a non-empty string")
    if not isinstance(cube_size, str) or cube_size == "":
        raise VanillaLookupError("cube_size must be a non-empty string")
    normalized = _normalize_type_id(type_id)
    index = cube_block_index(game_root)
    hits = index.hits_by_empty_type.get(normalized, ())
    matching = [hit for hit in hits if hit.cube_size == cube_size]
    if not matching:
        unknown_size = [hit for hit in hits if hit.cube_size is None]
        if unknown_size:
            sources = ", ".join(hit.source_relative for hit in unknown_size)
            raise VanillaLookupError(
                f"unusable empty-SubtypeId {normalized!r} in {sources}"
            )
        return None
    if len(matching) > 1:
        sources = ", ".join(hit.source_relative for hit in matching)
        raise VanillaLookupError(
            f"duplicate empty-SubtypeId {normalized!r} CubeSize {cube_size!r} "
            f"in {sources}"
        )
    return matching[0]


def type_id_from_object_builder(object_builder_type: str) -> str:
    """Normalize a blueprint ``MyObjectBuilder_*`` token to a TypeId."""
    if not isinstance(object_builder_type, str) or object_builder_type == "":
        raise VanillaLookupError("object_builder_type must be a non-empty string")
    if not object_builder_type.startswith(_MY_OBJECT_BUILDER_PREFIX):
        raise VanillaLookupError(
            f"object_builder_type {object_builder_type!r} is not a "
            "MyObjectBuilder token"
        )
    normalized = _normalize_type_id(object_builder_type)
    if normalized == "":
        raise VanillaLookupError(
            f"object_builder_type {object_builder_type!r} has an empty TypeId"
        )
    return normalized


def _build_index(game_root: Path) -> CubeBlockIndex:
    directories = _definition_directories(game_root)
    by_subtype: dict[str, list[TargetedHit]] = {}
    by_empty_type: dict[str, list[TargetedHit]] = {}
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
                if hit.subtype_id == "":
                    key = hit.type_id or ""
                    if key == "":
                        continue
                    by_empty_type.setdefault(key, []).append(hit)
                    continue
                by_subtype.setdefault(hit.subtype_id, []).append(hit)
    frozen = {
        subtype: tuple(hits) for subtype, hits in by_subtype.items()
    }
    frozen_empty = {
        type_id: tuple(hits) for type_id, hits in by_empty_type.items()
    }
    return CubeBlockIndex(
        game_root=game_root,
        hits_by_subtype=frozen,
        hits_by_empty_type=frozen_empty,
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
        identity = _try_definition_identity(child)
        if identity is None:
            continue
        type_id, subtype = identity
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
                    type_id=type_id,
                    cube_size=_safe_cube_size(child),
                )
            )
            continue
        hits.append(
            TargetedHit(
                subtype_id=subtype,
                source_relative=source_relative,
                definition=definition,
                unusable_reason=None,
                type_id=definition.type_id,
                cube_size=definition.cube_size,
            )
        )
    return tuple(hits)


def _safe_cube_size(el: ET.Element) -> Optional[str]:
    nodes = _children(el, "CubeSize")
    if len(nodes) != 1:
        return None
    text = _text_of(nodes[0])
    return text if text else None


def _try_definition_identity(el: ET.Element) -> Optional[tuple[str, str]]:
    try:
        type_id, subtype_id = _parse_id(el, source="sibling")
    except VanillaLookupError:
        return None
    return type_id, subtype_id


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
    block_topology = coalesce_identical_scalar_texts(
        _children(el, "BlockTopology"),
        name="BlockTopology",
        source=loc,
    )
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
    subtype_nodes = _children(ident, "SubtypeId")
    subtype_id: Optional[str]
    if subtype_nodes:
        if len(subtype_nodes) > 1:
            raise VanillaLookupError(f"{source}: multiple SubtypeId elements")
        text = _text_of(subtype_nodes[0])
        subtype_id = "" if text is None else text
    else:
        subtype_id = ident.get("Subtype")
    if type_id is None:
        type_id = ident.get("Type")
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
    values = _read_xyz_strings(nodes[0], source=source, label="ModelOffset")
    if values is None:
        return ModelOffset.zero()
    try:
        return ModelOffset.from_metres(values["x"], values["y"], values["z"])
    except InvalidModelOffsetError as exc:
        raise VanillaLookupError(f"{source}: {exc}") from exc


def _parse_size(parent: ET.Element, source: str) -> CellSize:
    nodes = _children(parent, "Size")
    if len(nodes) != 1:
        raise VanillaLookupError(f"{source}: Definition must contain exactly one Size")
    values = _read_xyz_strings(nodes[0], source=source, label="Size")
    if values is None:
        raise VanillaLookupError(
            f"{source}: Size missing attribute(s): x, y, z"
        )
    return CellSize(
        x=_positive_int(values["x"], f"{source}: Size @x"),
        y=_positive_int(values["y"], f"{source}: Size @y"),
        z=_positive_int(values["z"], f"{source}: Size @z"),
    )


def _read_xyz_strings(
    el: ET.Element,
    *,
    source: str,
    label: str,
) -> dict[str, str] | None:
    """Read one Size/ModelOffset as attributes or child X/Y/Z.

    This is not a general child-collection vector parser. Mix, missing
    axes, duplicate axes, unexpected names, and empty values fail closed.
    """
    attrib_names = {name.lower() for name in el.attrib}
    axis_children = [child for child in list(el) if _local_name(child)]
    if attrib_names and axis_children:
        raise VanillaLookupError(
            f"{source}: {label} must not mix attributes and children"
        )
    if attrib_names:
        by_name = {name.lower(): value for name, value in el.attrib.items()}
        missing = [name for name in ("x", "y", "z") if name not in by_name]
        extra = sorted(set(by_name) - _REQUIRED_SIZE)
        if missing:
            raise VanillaLookupError(
                f"{source}: {label} missing attribute(s): {', '.join(missing)}"
            )
        if extra:
            raise VanillaLookupError(
                f"{source}: {label} has unexpected attribute(s): "
                f"{', '.join(extra)}"
            )
        return {
            "x": by_name["x"],
            "y": by_name["y"],
            "z": by_name["z"],
        }
    if not axis_children:
        return None
    values: dict[str, str] = {}
    for child in axis_children:
        name = _local_name(child).lower()
        if name not in {"x", "y", "z"}:
            raise VanillaLookupError(
                f"{source}: {label} has unexpected child {name!r}"
            )
        if name in values:
            raise VanillaLookupError(
                f"{source}: {label} has duplicate {name!r}"
            )
        text = _text_of(child)
        if text is None or text == "":
            raise VanillaLookupError(f"{source}: {label}.{name} is empty")
        values[name] = text
    missing = [name for name in ("x", "y", "z") if name not in values]
    if missing:
        raise VanillaLookupError(
            f"{source}: {label} missing child(ren): {', '.join(missing)}"
        )
    return values


def coalesce_identical_scalar_texts(
    nodes: list[ET.Element],
    *,
    name: str,
    source: str,
) -> str:
    """Coalesce identical scalar duplicates. Conflicting values fail closed.

    One or more occurrences are accepted only when every normalized text
    is non-empty and equal. Empty plus non-empty is a conflict.
    """
    if not nodes:
        raise VanillaLookupError(
            f"{source}: Definition must contain exactly one {name}"
        )
    values: list[str] = []
    for node in nodes:
        text = _text_of(node)
        if text is None or text == "":
            raise VanillaLookupError(f"{source}: {name} is empty")
        values.append(text)
    unique = set(values)
    if len(unique) != 1:
        raise VanillaLookupError(
            f"{source}: conflicting {name} values {sorted(unique)}"
        )
    return values[0]


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
