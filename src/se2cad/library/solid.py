"""CAD-neutral closed solid meshes.

This module has no geometry-identity allowlist and does not emit CAD
documents. Vertices are millimetres in whatever frame the caller used.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from se2cad.library.errors import InvalidSolidError
from se2cad.library.model import NativeSolidRecipe

_EPS = 1e-6
_KEY_DIGITS = 7


Vec3 = tuple[float, float, float]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _length(a: Vec3) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: Vec3, *, what: str) -> Vec3:
    length = _length(a)
    if length < _EPS:
        raise InvalidSolidError(f"degenerate {what}")
    return (a[0] / length, a[1] / length, a[2] / length)


def _as_vec3(point: tuple[float, float, float] | tuple[int, int, int]) -> Vec3:
    return (float(point[0]), float(point[1]), float(point[2]))


def _quantize(point: Vec3) -> Vec3:
    return (
        round(point[0], _KEY_DIGITS),
        round(point[1], _KEY_DIGITS),
        round(point[2], _KEY_DIGITS),
    )


class _VertexTable:
    def __init__(self) -> None:
        self._xyz: list[Vec3] = []
        self._index: dict[Vec3, int] = {}

    def add(self, point: Vec3) -> int:
        key = _quantize(point)
        existing = self._index.get(key)
        if existing is not None:
            return existing
        index = len(self._xyz)
        self._xyz.append(key)
        self._index[key] = index
        return index

    def vertices(self) -> tuple[Vec3, ...]:
        return tuple(self._xyz)


@dataclass(frozen=True)
class BoundsMm:
    """Axis-aligned millimetre bounds. Coordinates may be non-integer."""

    min_mm: Vec3
    max_mm: Vec3

    def contains(self, point: Vec3, *, eps: float = _EPS) -> bool:
        return all(
            self.min_mm[i] - eps <= point[i] <= self.max_mm[i] + eps
            for i in range(3)
        )

    def contains_bounds(self, other: BoundsMm, *, eps: float = _EPS) -> bool:
        return self.contains(other.min_mm, eps=eps) and self.contains(
            other.max_mm, eps=eps
        )


@dataclass(frozen=True)
class MeshEdge:
    """One manifold edge of a closed solid, with its two incident faces."""

    start: int
    end: int
    face_a: int
    face_b: int
    length_mm: float
    convex: bool


@dataclass(frozen=True)
class SolidMesh:
    """Closed oriented polyhedron. Faces are outward-wound."""

    vertices: tuple[Vec3, ...]
    faces: tuple[tuple[int, ...], ...]


def solid_from_vertices_faces(
    vertices: tuple[tuple[float, float, float] | tuple[int, int, int], ...],
    faces: tuple[tuple[int, ...], ...],
) -> SolidMesh:
    """Build a solid from explicit vertices and outward-wound faces."""
    table = _VertexTable()
    mapped: list[int] = []
    for vertex in vertices:
        mapped.append(table.add(_as_vec3(vertex)))
    remapped_faces: list[tuple[int, ...]] = []
    for face in faces:
        remapped_faces.append(tuple(mapped[index] for index in face))
    solid = SolidMesh(vertices=table.vertices(), faces=tuple(remapped_faces))
    validate_solid(solid)
    return solid


def solid_from_recipe(recipe: NativeSolidRecipe) -> SolidMesh:
    """Copy a native recipe's mesh. The result does not carry geometry_id."""
    return solid_from_vertices_faces(recipe.vertices_mm, recipe.faces)


def volume_times_6(solid: SolidMesh) -> float:
    """Six times the enclosed volume of a closed outward-wound mesh."""
    total = 0.0
    vertices = solid.vertices
    for face in solid.faces:
        origin = vertices[face[0]]
        for i in range(1, len(face) - 1):
            a = vertices[face[i]]
            b = vertices[face[i + 1]]
            total += _dot(origin, _cross(a, b))
    return total


def bounding_box(solid: SolidMesh) -> BoundsMm:
    xs = [vertex[0] for vertex in solid.vertices]
    ys = [vertex[1] for vertex in solid.vertices]
    zs = [vertex[2] for vertex in solid.vertices]
    return BoundsMm(
        min_mm=(min(xs), min(ys), min(zs)),
        max_mm=(max(xs), max(ys), max(zs)),
    )


def face_normal(solid: SolidMesh, face_index: int) -> Vec3:
    face = solid.faces[face_index]
    points = [solid.vertices[index] for index in face]
    nx = ny = nz = 0.0
    count = len(points)
    for i, point in enumerate(points):
        nxt = points[(i + 1) % count]
        nx += (point[1] - nxt[1]) * (point[2] + nxt[2])
        ny += (point[2] - nxt[2]) * (point[0] + nxt[0])
        nz += (point[0] - nxt[0]) * (point[1] + nxt[1])
    return _unit((nx, ny, nz), what="face normal")


def face_centroid(solid: SolidMesh, face_index: int) -> Vec3:
    face = solid.faces[face_index]
    points = [solid.vertices[index] for index in face]
    scale = 1.0 / len(points)
    return (
        sum(point[0] for point in points) * scale,
        sum(point[1] for point in points) * scale,
        sum(point[2] for point in points) * scale,
    )


def _edge_map(solid: SolidMesh) -> dict[frozenset[int], list[int]]:
    edges: dict[frozenset[int], list[int]] = defaultdict(list)
    for face_index, face in enumerate(solid.faces):
        count = len(face)
        if count < 3:
            raise InvalidSolidError("face has fewer than three vertices")
        if len(set(face)) != count:
            raise InvalidSolidError("face repeats a vertex")
        for i, start in enumerate(face):
            end = face[(i + 1) % count]
            if start == end:
                raise InvalidSolidError("degenerate face edge")
            edges[frozenset((start, end))].append(face_index)
    return edges


def validate_solid(solid: SolidMesh) -> None:
    """Require a closed manifold with positive volume."""
    if len(solid.vertices) < 4:
        raise InvalidSolidError("solid needs at least four vertices")
    if not solid.faces:
        raise InvalidSolidError("solid has no faces")
    count = len(solid.vertices)
    for face_index, face in enumerate(solid.faces):
        if any(index < 0 or index >= count for index in face):
            raise InvalidSolidError("face index is out of range")
        face_normal(solid, face_index)
    edges = _edge_map(solid)
    for pair, faces in edges.items():
        if len(faces) != 2:
            raise InvalidSolidError(
                f"non-manifold edge {tuple(pair)} is used by {len(faces)} faces"
            )
    if volume_times_6(solid) <= _EPS:
        raise InvalidSolidError("solid volume is not positive")


def mesh_edges(solid: SolidMesh) -> tuple[MeshEdge, ...]:
    """Return every manifold edge and whether its dihedral is convex."""
    validate_solid(solid)
    centroid = _vertex_centroid(solid)
    collected: list[MeshEdge] = []
    for pair, faces in _edge_map(solid).items():
        start, end = tuple(pair)
        length = _length(_sub(solid.vertices[end], solid.vertices[start]))
        collected.append(
            MeshEdge(
                start=start,
                end=end,
                face_a=faces[0],
                face_b=faces[1],
                length_mm=length,
                convex=_edge_is_convex(
                    solid, start, end, faces[0], faces[1], centroid
                ),
            )
        )
    return tuple(collected)


def _vertex_centroid(solid: SolidMesh) -> Vec3:
    count = float(len(solid.vertices))
    return (
        sum(vertex[0] for vertex in solid.vertices) / count,
        sum(vertex[1] for vertex in solid.vertices) / count,
        sum(vertex[2] for vertex in solid.vertices) / count,
    )


def _outward_normal(solid: SolidMesh, face_index: int, centroid: Vec3) -> Vec3:
    """Newell normal flipped so it points away from the vertex centroid."""
    normal = face_normal(solid, face_index)
    face_center = face_centroid(solid, face_index)
    if _dot(normal, _sub(face_center, centroid)) < 0.0:
        return _scale(normal, -1.0)
    return normal


def _edge_is_convex(
    solid: SolidMesh,
    start: int,
    end: int,
    face_a: int,
    face_b: int,
    centroid: Vec3,
) -> bool:
    normal_a = _outward_normal(solid, face_a, centroid)
    origin = solid.vertices[start]
    for index in solid.faces[face_b]:
        if index in (start, end):
            continue
        side = _dot(normal_a, _sub(solid.vertices[index], origin))
        if abs(side) < _EPS:
            continue
        return side < 0.0
    return False


def _inward_on_face(
    solid: SolidMesh,
    face_index: int,
    edge_start: Vec3,
    edge_end: Vec3,
    normal: Vec3,
) -> Vec3:
    direction = _unit(_sub(edge_end, edge_start), what="edge")
    option_a = _cross(direction, normal)
    option_b = _cross(normal, direction)
    midpoint = _scale(_add(edge_start, edge_end), 0.5)
    toward = _sub(face_centroid(solid, face_index), midpoint)
    chosen = option_a if _dot(option_a, toward) >= _dot(option_b, toward) else option_b
    return _unit(chosen, what="in-face inward")


def chamfer_plane(
    solid: SolidMesh,
    edge: MeshEdge,
    setback_mm: float,
) -> tuple[Vec3, Vec3]:
    """Equal-setback chamfer plane for one convex edge.

    The returned normal points toward the original edge (removed material).
    The remaining solid is the half-space ``n · (x - point) <= 0``.
    """
    if setback_mm <= _EPS:
        raise InvalidSolidError("chamfer setback must be positive")
    start = solid.vertices[edge.start]
    end = solid.vertices[edge.end]
    normal_a = face_normal(solid, edge.face_a)
    normal_b = face_normal(solid, edge.face_b)
    inward_a = _inward_on_face(solid, edge.face_a, start, end, normal_a)
    inward_b = _inward_on_face(solid, edge.face_b, start, end, normal_b)
    point_a = _add(start, _scale(inward_a, setback_mm))
    point_b = _add(start, _scale(inward_b, setback_mm))
    edge_dir = _unit(_sub(end, start), what="edge")
    plane_n = _cross(edge_dir, _sub(point_b, point_a))
    plane_n = _unit(plane_n, what="chamfer plane normal")
    if _dot(plane_n, _sub(start, point_a)) < 0.0:
        plane_n = _scale(plane_n, -1.0)
    return plane_n, point_a


def _side_of_plane(point: Vec3, normal: Vec3, origin: Vec3) -> float:
    return _dot(normal, _sub(point, origin))


def _intersect_segment(
    start: Vec3,
    end: Vec3,
    normal: Vec3,
    origin: Vec3,
) -> Vec3:
    direction = _sub(end, start)
    denom = _dot(normal, direction)
    if abs(denom) < _EPS:
        raise InvalidSolidError("segment is parallel to a cutting plane")
    t = _dot(normal, _sub(origin, start)) / denom
    return _add(start, _scale(direction, t))


def _clip_polygon(
    points: list[Vec3],
    normal: Vec3,
    origin: Vec3,
) -> list[Vec3]:
    if len(points) < 3:
        return []
    kept: list[Vec3] = []
    count = len(points)
    for i, current in enumerate(points):
        nxt = points[(i + 1) % count]
        current_in = _side_of_plane(current, normal, origin) <= _EPS
        next_in = _side_of_plane(nxt, normal, origin) <= _EPS
        if current_in:
            kept.append(current)
        if current_in != next_in:
            kept.append(_intersect_segment(current, nxt, normal, origin))
    return kept


def _loops_from_undirected(
    segments: list[tuple[int, int]],
) -> list[list[int]]:
    adj: dict[int, list[int]] = defaultdict(list)
    unused: set[frozenset[int]] = set()
    for start, end in segments:
        if start == end:
            continue
        key = frozenset((start, end))
        if key in unused:
            continue
        unused.add(key)
        adj[start].append(end)
        adj[end].append(start)
    loops: list[list[int]] = []
    while unused:
        start, end = next(iter(unused))
        unused.remove(frozenset((start, end)))
        loop = [start, end]
        while loop[-1] != loop[0]:
            current = loop[-1]
            previous = loop[-2]
            candidates = [
                node
                for node in adj[current]
                if node != previous
                and frozenset((current, node)) in unused
            ]
            if not candidates:
                raise InvalidSolidError("cutting plane did not close a loop")
            nxt = candidates[0]
            unused.remove(frozenset((current, nxt)))
            loop.append(nxt)
            if len(loop) > 64:
                raise InvalidSolidError("cutting-plane loop is not simple")
        loops.append(loop[:-1])
    return loops


def clip_solid_by_plane(solid: SolidMesh, normal: Vec3, origin: Vec3) -> SolidMesh:
    """Keep the half-space ``n · (x - origin) <= 0`` and cap the cut."""
    validate_solid(solid)
    table = _VertexTable()
    new_faces: list[tuple[int, ...]] = []
    cap_segments: list[tuple[int, int]] = []
    for face in solid.faces:
        points = [solid.vertices[index] for index in face]
        clipped = _clip_polygon(points, normal, origin)
        if len(clipped) < 3:
            continue
        indices = [table.add(point) for point in clipped]
        # Drop immediately repeated vertices after quantize.
        compact: list[int] = []
        for index in indices:
            if not compact or compact[-1] != index:
                compact.append(index)
        if len(compact) >= 2 and compact[0] == compact[-1]:
            compact.pop()
        if len(compact) < 3:
            continue
        new_faces.append(tuple(compact))
        verts = table.vertices()
        on_plane_flags = [
            abs(_side_of_plane(verts[index], normal, origin)) <= _EPS * 10
            for index in compact
        ]
        if all(on_plane_flags):
            continue
        count = len(compact)
        for i, index in enumerate(compact):
            nxt = compact[(i + 1) % count]
            if on_plane_flags[i] and on_plane_flags[(i + 1) % count]:
                cap_segments.append((index, nxt))

    vertices_so_far = table.vertices()
    loops = _loops_from_undirected(cap_segments)
    for loop in loops:
        if len(loop) < 3:
            continue
        points = [vertices_so_far[index] for index in loop]
        cap_normal = _unit(
            _cross(_sub(points[1], points[0]), _sub(points[2], points[0])),
            what="cap normal",
        )
        if _dot(cap_normal, normal) < 0.0:
            loop = list(reversed(loop))
        new_faces.append(tuple(loop))

    result = SolidMesh(vertices=table.vertices(), faces=tuple(new_faces))
    validate_solid(result)
    return result
