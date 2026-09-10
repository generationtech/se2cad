"""Bounded official ASCII FBX 7.x parse and binary normalization.

This is a syntactic node-tree transcoder for mesh-bearing FBX 7.1–7.4
ASCII files. It does not implement animation, skins, or materials, and
it does not modify the official SDK source.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from se2cad.solidworks.errors import SdkSourceError
from se2cad.solidworks.sdk_fbx_format import FBX_BINARY_MAGIC_FULL

MAX_ASCII_NODES = 200_000
MAX_ASCII_DEPTH = 40
MAX_ARRAY_VALUES = 2_000_000
MAX_NODE_PROPS = 50_000
_INT32_MIN = -2147483648
_INT32_MAX = 2147483647
_KEEP_ROOTS = frozenset(
    {
        "FBXHeaderExtension",
        "GlobalSettings",
        "Documents",
        "Objects",
        "Connections",
    }
)
_KEEP_OBJECTS = frozenset({"Geometry", "Model", "NodeAttribute", "Document"})
_ID_CONNECTION_NAMES = frozenset({"C"})
_MESH_OBJECT_NAMES = frozenset({"Geometry", "Model"})
_NAMED_OBJECT_NODES = frozenset(
    {
        "Geometry",
        "Model",
        "NodeAttribute",
        "Document",
        "SceneInfo",
        "Material",
        "Texture",
        "Video",
        "Deformer",
        "CollectionExclusive",
        "AnimationStack",
        "AnimationLayer",
        "AnimationCurve",
        "AnimationCurveNode",
        "Pose",
    }
)
_P_DOUBLE_TYPES = frozenset(
    {
        "double",
        "Number",
        "float",
        "Float",
        "Real",
        "Vector",
        "Vector3D",
        "Color",
        "ColorRGB",
        "Lcl Translation",
        "Lcl Rotation",
        "Lcl Scaling",
        "Visibility",
        "FieldOfView",
        "FieldOfViewX",
        "FieldOfViewY",
        "OpticalCenterX",
        "OpticalCenterY",
        "Roll",
        "FilmWidth",
        "FilmHeight",
        "FilmAspectRatio",
        "FocalLength",
        "Time",
    }
)
_P_INT_TYPES = frozenset(
    {
        "int",
        "Integer",
        "enum",
        "bool",
        "Bool",
        "Visibility Inheritance",
        "default",
    }
)
_P_LONG_TYPES = frozenset({"ULongLong"})


@dataclass(frozen=True)
class FbxValue:
    type_code: str
    value: Any


@dataclass(frozen=True)
class FbxNode:
    name: str
    props: tuple[FbxValue, ...]
    children: tuple["FbxNode", ...]


@dataclass(frozen=True)
class AsciiFbxDocument:
    version: int
    nodes: tuple[FbxNode, ...]
    geometry_count: int
    model_count: int
    vertex_values: int
    polygon_index_values: int


@dataclass(frozen=True)
class AsciiNormalizationReport:
    source_path: Path
    source_sha256: str
    normalized_path: Path
    version: int
    geometry_count: int
    model_count: int
    vertex_values: int
    polygon_index_values: int


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.size = len(text)
        self.index = 0
        self.nodes_seen = 0

    def parse_document(self) -> tuple[FbxNode, ...]:
        nodes: list[FbxNode] = []
        self._skip_trivia()
        while self.index < self.size:
            nodes.append(self._parse_node(depth=0))
            self._skip_trivia()
        if not nodes:
            raise SdkSourceError("ASCII FBX contains no nodes")
        return tuple(nodes)

    def _parse_node(self, *, depth: int) -> FbxNode:
        if depth > MAX_ASCII_DEPTH:
            raise SdkSourceError("ASCII FBX nesting exceeds the conversion limit")
        self.nodes_seen += 1
        if self.nodes_seen > MAX_ASCII_NODES:
            raise SdkSourceError("ASCII FBX node count exceeds the conversion limit")
        self._skip_trivia()
        name = self._read_name()
        self._skip_spaces()
        if self._peek() != ":":
            raise SdkSourceError(f"ASCII FBX node {name!r} is missing ':'")
        self.index += 1
        props, array_length = self._parse_property_list()
        self._skip_trivia()
        if self._peek() == "{":
            self.index += 1
            children = self._parse_children(depth=depth + 1)
            if array_length is not None:
                return self._collapse_array_node(name, props, children, array_length)
            return FbxNode(name=name, props=props, children=children)
        if array_length is not None:
            raise SdkSourceError(f"ASCII FBX array node {name!r} is truncated")
        return FbxNode(name=name, props=props, children=())

    def _parse_children(self, *, depth: int) -> tuple[FbxNode, ...]:
        children: list[FbxNode] = []
        while True:
            self._skip_trivia()
            if self.index >= self.size:
                raise SdkSourceError("ASCII FBX block is truncated")
            if self._peek() == "}":
                self.index += 1
                return tuple(children)
            children.append(self._parse_node(depth=depth))

    def _parse_property_list(self) -> tuple[tuple[FbxValue, ...], int | None]:
        values: list[FbxValue] = []
        while True:
            self._skip_spaces()
            ch = self._peek()
            if ch == "" or ch in "{};\n\r":
                return tuple(values), None
            if ch == "*":
                self.index += 1
                count = self._read_int_token()
                if count < 0 or count > MAX_ARRAY_VALUES:
                    raise SdkSourceError("ASCII FBX array length is not convertible")
                return tuple(values), count
            if len(values) >= MAX_NODE_PROPS:
                raise SdkSourceError("ASCII FBX property count exceeds the conversion limit")
            values.append(self._parse_value())
            self._skip_spaces()
            if self._peek() == ",":
                self.index += 1
                self._skip_spaces()
                if self._peek() in "\n\r":
                    self._skip_trivia()
                continue
            return tuple(values), None

    def _parse_value(self) -> FbxValue:
        self._skip_spaces()
        ch = self._peek()
        if ch == '"':
            return FbxValue("S", self._read_string())
        if ch == "" or ch in "{},;":
            raise SdkSourceError("ASCII FBX property value is truncated")
        if ch.isalpha() or ch == "_":
            return FbxValue("S", self._read_name())
        token = self._read_number_token()
        if _is_float_token(token):
            try:
                return FbxValue("D", float(token))
            except ValueError as exc:
                raise SdkSourceError(f"ASCII FBX float is invalid: {token!r}") from exc
        try:
            number = int(token, 10)
        except ValueError as exc:
            raise SdkSourceError(f"ASCII FBX integer is invalid: {token!r}") from exc
        if _INT32_MIN <= number <= _INT32_MAX:
            return FbxValue("I", number)
        return FbxValue("L", number)

    def _collapse_array_node(
        self,
        name: str,
        props: tuple[FbxValue, ...],
        children: tuple[FbxNode, ...],
        array_length: int,
    ) -> FbxNode:
        if props:
            raise SdkSourceError(f"ASCII FBX array node {name!r} has mixed properties")
        if len(children) != 1 or children[0].name != "a":
            raise SdkSourceError(f"ASCII FBX array node {name!r} is not a single 'a' block")
        raw = children[0].props
        if len(raw) != array_length:
            raise SdkSourceError(
                f"ASCII FBX array node {name!r} length {len(raw)} != {array_length}"
            )
        if any(item.type_code == "S" for item in raw):
            raise SdkSourceError(f"ASCII FBX array node {name!r} contains strings")
        if any(item.type_code == "D" for item in raw):
            values = tuple(
                float(item.value) if item.type_code == "D" else float(item.value)
                for item in raw
            )
            array = FbxValue("d", values)
        else:
            array = FbxValue("i", tuple(int(item.value) for item in raw))
        return FbxNode(name=name, props=(array,), children=())

    def _read_name(self) -> str:
        start = self.index
        while self.index < self.size and (
            self.text[self.index].isalnum() or self.text[self.index] == "_"
        ):
            self.index += 1
        if start == self.index:
            raise SdkSourceError("ASCII FBX node name is missing")
        return self.text[start : self.index]

    def _read_string(self) -> str:
        if self._peek() != '"':
            raise SdkSourceError("ASCII FBX string is truncated")
        self.index += 1
        chars: list[str] = []
        while self.index < self.size:
            ch = self.text[self.index]
            self.index += 1
            if ch == "\\":
                if self.index >= self.size:
                    raise SdkSourceError("ASCII FBX string escape is truncated")
                escaped = self.text[self.index]
                self.index += 1
                chars.append(escaped)
                continue
            if ch == '"':
                return "".join(chars)
            chars.append(ch)
        raise SdkSourceError("ASCII FBX string is truncated")

    def _read_number_token(self) -> str:
        start = self.index
        if self._peek() in "+-":
            self.index += 1
        saw_digit = False
        while self.index < self.size and self.text[self.index].isdigit():
            saw_digit = True
            self.index += 1
        if self._peek() == ".":
            self.index += 1
            while self.index < self.size and self.text[self.index].isdigit():
                saw_digit = True
                self.index += 1
        if self._peek() in "eE":
            self.index += 1
            if self._peek() in "+-":
                self.index += 1
            exp_digits = 0
            while self.index < self.size and self.text[self.index].isdigit():
                exp_digits += 1
                self.index += 1
            if exp_digits == 0:
                raise SdkSourceError("ASCII FBX exponent is truncated")
        if not saw_digit or start == self.index:
            raise SdkSourceError("ASCII FBX number is missing")
        return self.text[start : self.index]

    def _read_int_token(self) -> int:
        self._skip_spaces()
        token = self._read_number_token()
        if _is_float_token(token):
            raise SdkSourceError(f"ASCII FBX array length is not an integer: {token!r}")
        return int(token, 10)

    def _skip_trivia(self) -> None:
        while self.index < self.size:
            ch = self.text[self.index]
            if ch in " \t\n\r":
                self.index += 1
                continue
            if ch == ";":
                while self.index < self.size and self.text[self.index] not in "\n\r":
                    self.index += 1
                continue
            return

    def _skip_spaces(self) -> None:
        while self.index < self.size and self.text[self.index] in " \t":
            self.index += 1

    def _peek(self) -> str:
        if self.index >= self.size:
            return ""
        return self.text[self.index]


def parse_ascii_fbx(text: str) -> AsciiFbxDocument:
    """Parse ASCII FBX text into a bounded node tree."""
    if text.startswith("\ufeff"):
        text = text[1:]
    parser = _Parser(text)
    nodes = tuple(
        _encode_object_names(_retype_properties70(node))
        for node in parser.parse_document()
    )
    version = _header_version(nodes)
    geometry_count, model_count, vertex_values, polygon_values = _mesh_stats(nodes)
    return AsciiFbxDocument(
        version=version,
        nodes=nodes,
        geometry_count=geometry_count,
        model_count=model_count,
        vertex_values=vertex_values,
        polygon_index_values=polygon_values,
    )


def validate_ascii_fbx(text: str) -> int:
    """Parse and require a mesh-bearing official ASCII FBX. Return version."""
    document = parse_ascii_fbx(text)
    if document.geometry_count < 1:
        raise SdkSourceError("ASCII FBX has no Geometry mesh objects")
    if document.model_count < 1:
        raise SdkSourceError("ASCII FBX has no Model objects")
    if document.vertex_values < 3 or document.polygon_index_values < 3:
        raise SdkSourceError("ASCII FBX Geometry does not contain usable mesh arrays")
    return document.version


def normalize_ascii_fbx_to_binary(
    source: Path,
    destination: Path,
    *,
    generated_root: Path,
) -> AsciiNormalizationReport:
    """Write a mesh-preserving binary FBX under the generated root."""
    resolved_source = source.expanduser().resolve()
    resolved_dest = destination.expanduser().resolve()
    resolved_root = generated_root.expanduser().resolve()
    try:
        resolved_dest.relative_to(resolved_root)
    except ValueError as exc:
        raise SdkSourceError(
            f"normalized FBX {resolved_dest} escapes generated root {resolved_root}"
        ) from exc
    if resolved_dest == resolved_source:
        raise SdkSourceError("refusing to overwrite the official SDK FBX")
    try:
        payload = resolved_source.read_bytes()
    except OSError as exc:
        raise SdkSourceError(f"authorized SDK source is unreadable: {resolved_source}: {exc}") from exc
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SdkSourceError(f"ASCII FBX is not valid UTF-8: {exc}") from exc
    document = parse_ascii_fbx(text)
    validate_ascii_fbx(text)
    filtered = filter_mesh_document(document.nodes)
    resolved_dest.parent.mkdir(parents=True, exist_ok=True)
    if resolved_dest.exists():
        resolved_dest.unlink()
    write_binary_fbx(filtered, resolved_dest, version=document.version)
    if not resolved_dest.is_file() or resolved_dest.stat().st_size < len(FBX_BINARY_MAGIC_FULL) + 4:
        raise SdkSourceError(f"ASCII FBX normalization did not write {resolved_dest}")
    written = resolved_dest.read_bytes()[: len(FBX_BINARY_MAGIC_FULL)]
    if written != FBX_BINARY_MAGIC_FULL:
        raise SdkSourceError("ASCII FBX normalization did not produce a binary FBX")
    report = AsciiNormalizationReport(
        source_path=resolved_source,
        source_sha256=hashlib.sha256(payload).hexdigest(),
        normalized_path=resolved_dest,
        version=document.version,
        geometry_count=document.geometry_count,
        model_count=document.model_count,
        vertex_values=document.vertex_values,
        polygon_index_values=document.polygon_index_values,
    )
    sidecar = resolved_dest.with_suffix(".normalize.json")
    sidecar.write_text(
        json.dumps(
            {
                "source_path": str(report.source_path),
                "source_sha256": report.source_sha256,
                "normalized_path": str(report.normalized_path),
                "version": report.version,
                "geometry_count": report.geometry_count,
                "model_count": report.model_count,
                "vertex_values": report.vertex_values,
                "polygon_index_values": report.polygon_index_values,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def filter_mesh_document(nodes: tuple[FbxNode, ...]) -> tuple[FbxNode, ...]:
    """Keep header, settings, mesh objects, and connections to those objects."""
    kept_ids: set[int] = {0}
    filtered: list[FbxNode] = []
    for node in nodes:
        if node.name not in _KEEP_ROOTS:
            continue
        if node.name == "Objects":
            objects = []
            for child in node.children:
                if child.name not in _KEEP_OBJECTS:
                    continue
                ident = _node_id(child)
                if ident is not None:
                    kept_ids.add(ident)
                objects.append(_promote_id_props(child))
            filtered.append(FbxNode(name=node.name, props=node.props, children=tuple(objects)))
            continue
        if node.name == "Connections":
            connections = []
            for child in node.children:
                if child.name != "C":
                    continue
                idents = [int(item.value) for item in child.props if item.type_code in {"I", "L"}]
                if idents and all(ident in kept_ids for ident in idents):
                    connections.append(_promote_connection(child))
            filtered.append(
                FbxNode(name=node.name, props=node.props, children=tuple(connections))
            )
            continue
        if node.name == "Documents":
            documents = []
            for child in node.children:
                ident = _node_id(child)
                if ident is not None:
                    kept_ids.add(ident)
                documents.append(_promote_id_props(child))
            filtered.append(FbxNode(name=node.name, props=node.props, children=tuple(documents)))
            continue
        filtered.append(node)
    if not any(node.name == "Objects" for node in filtered):
        raise SdkSourceError("ASCII FBX mesh filter removed all Objects")
    return tuple(filtered)


def write_binary_fbx(nodes: tuple[FbxNode, ...], destination: Path, *, version: int) -> None:
    """Write FBX 7.x binary records Blender's importer can read."""
    if version >= 7500:
        raise SdkSourceError(f"refusing to write incompatible FBX version {version}")
    buffer = bytearray()
    buffer.extend(FBX_BINARY_MAGIC_FULL)
    buffer.extend(struct.pack("<I", version))
    for index, node in enumerate(nodes):
        _write_node(buffer, node, is_last=(index == len(nodes) - 1))
    buffer.extend(b"\x00" * 13)
    destination.write_bytes(bytes(buffer))


def _write_node(buffer: bytearray, node: FbxNode, *, is_last: bool) -> None:
    start = len(buffer)
    buffer.extend(b"\x00" * 12)
    name = node.name.encode("ascii")
    if len(name) > 255:
        raise SdkSourceError(f"ASCII FBX node name is too long: {node.name!r}")
    buffer.append(len(name))
    buffer.extend(name)
    prop_start = len(buffer)
    for prop in node.props:
        _write_prop(buffer, prop)
    prop_len = len(buffer) - prop_start
    for index, child in enumerate(node.children):
        _write_node(buffer, child, is_last=(index == len(node.children) - 1))
    if node.children or (not node.props and not is_last):
        buffer.extend(b"\x00" * 13)
    end = len(buffer)
    struct.pack_into("<III", buffer, start, end, len(node.props), prop_len)


def _write_prop(buffer: bytearray, prop: FbxValue) -> None:
    code = prop.type_code
    buffer.append(ord(code))
    if code == "I":
        buffer.extend(struct.pack("<i", int(prop.value)))
        return
    if code == "L":
        buffer.extend(struct.pack("<q", int(prop.value)))
        return
    if code == "D":
        buffer.extend(struct.pack("<d", float(prop.value)))
        return
    if code == "S":
        encoded = str(prop.value).encode("utf-8")
        buffer.extend(struct.pack("<I", len(encoded)))
        buffer.extend(encoded)
        return
    if code == "i":
        raw = struct.pack(f"<{len(prop.value)}i", *[int(v) for v in prop.value])
        buffer.extend(struct.pack("<III", len(prop.value), 0, len(raw)))
        buffer.extend(raw)
        return
    if code == "d":
        raw = struct.pack(f"<{len(prop.value)}d", *[float(v) for v in prop.value])
        buffer.extend(struct.pack("<III", len(prop.value), 0, len(raw)))
        buffer.extend(raw)
        return
    raise SdkSourceError(f"unsupported FBX property type {code!r}")


def _encode_object_names(node: FbxNode) -> FbxNode:
    """Translate ASCII ``Class::Name`` strings into binary ``Name\\x00\\x01Class``."""
    children = tuple(_encode_object_names(child) for child in node.children)
    if node.name not in _NAMED_OBJECT_NODES:
        return FbxNode(name=node.name, props=node.props, children=children)
    props = list(node.props)
    for index, item in enumerate(props):
        if item.type_code != "S" or "::" not in item.value:
            continue
        class_name, local_name = item.value.split("::", 1)
        props[index] = FbxValue("S", f"{local_name}\x00\x01{class_name}")
        break
    return FbxNode(name=node.name, props=tuple(props), children=children)


def _retype_properties70(node: FbxNode) -> FbxNode:
    """Coerce Properties70 P values to the types Blender's importer asserts."""
    children = tuple(_retype_properties70(child) for child in node.children)
    if node.name != "P" or len(node.props) < 5:
        return FbxNode(name=node.name, props=node.props, children=children)
    type_name = node.props[1].value if node.props[1].type_code == "S" else ""
    coerced: list[FbxValue] = list(node.props[:4])
    for item in node.props[4:]:
        if type_name in _P_DOUBLE_TYPES:
            coerced.append(FbxValue("D", float(item.value)))
        elif type_name in _P_LONG_TYPES:
            coerced.append(FbxValue("L", int(float(item.value))))
        elif type_name in _P_INT_TYPES:
            coerced.append(FbxValue("I", int(float(item.value))))
        else:
            coerced.append(item)
    return FbxNode(name=node.name, props=tuple(coerced), children=children)


def _header_version(nodes: tuple[FbxNode, ...]) -> int:
    for node in nodes:
        if node.name != "FBXHeaderExtension":
            continue
        for child in node.children:
            if child.name == "FBXVersion" and child.props:
                value = child.props[0]
                if value.type_code in {"I", "L"}:
                    return int(value.value)
        raise SdkSourceError("ASCII FBX header is missing FBXVersion")
    raise SdkSourceError("ASCII FBX is missing FBXHeaderExtension")


def _mesh_stats(nodes: tuple[FbxNode, ...]) -> tuple[int, int, int, int]:
    geometries = 0
    models = 0
    vertices = 0
    polygons = 0
    stack = list(nodes)
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.name == "Geometry":
            geometries += 1
        elif node.name == "Model":
            models += 1
        elif node.name == "Vertices" and node.props and node.props[0].type_code in {"d", "i"}:
            vertices = max(vertices, len(node.props[0].value))
        elif (
            node.name == "PolygonVertexIndex"
            and node.props
            and node.props[0].type_code in {"i", "d"}
        ):
            polygons = max(polygons, len(node.props[0].value))
    return geometries, models, vertices, polygons


def _node_id(node: FbxNode) -> int | None:
    if not node.props:
        return None
    first = node.props[0]
    if first.type_code in {"I", "L"}:
        return int(first.value)
    return None


def _promote_id_props(node: FbxNode) -> FbxNode:
    if not node.props:
        return node
    first = node.props[0]
    if first.type_code == "I" and node.name in _MESH_OBJECT_NAMES | _KEEP_OBJECTS:
        promoted = (FbxValue("L", int(first.value)),) + node.props[1:]
        return FbxNode(
            name=node.name,
            props=promoted,
            children=tuple(_promote_id_props(child) for child in node.children),
        )
    return FbxNode(
        name=node.name,
        props=node.props,
        children=tuple(_promote_id_props(child) for child in node.children),
    )


def _promote_connection(node: FbxNode) -> FbxNode:
    promoted: list[FbxValue] = []
    for item in node.props:
        if item.type_code == "I" and node.name in _ID_CONNECTION_NAMES:
            promoted.append(FbxValue("L", int(item.value)))
        else:
            promoted.append(item)
    return FbxNode(name=node.name, props=tuple(promoted), children=node.children)


def _is_float_token(token: str) -> bool:
    return "." in token or "e" in token or "E" in token
