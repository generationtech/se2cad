"""Native-procedural Large Grid armor solids.

Vertex signs come from Keen ``MyCubeGridDefinitions`` topology edge tables
for ``Box``, ``Slope``, ``Corner``, and ``InvCorner``. Those signs are
cell-local ±1 corners about the cell center. SE2CAD scales them by the
catalog half-extent so the authored solid sits in the qualified canonical
local frame.

This module does not import Keen meshes or read a game install.
"""

from __future__ import annotations

from se2cad.catalog.model import RecipeKind
from se2cad.library.errors import UnknownGeometryError, UnsupportedTopologyError
from se2cad.library.frame import (
    CANONICAL_CELL_ENVELOPE,
    CANONICAL_LOCAL_FRAME,
    AxisAlignedBoxMm,
    cell_half_extent_mm,
)
from se2cad.library.model import (
    BoxConstruction,
    BoxMinusTetrahedronConstruction,
    LibraryRecord,
    NativeSolidRecipe,
    PlacementSemantics,
    PrismConstruction,
    SolidKind,
    TetrahedronConstruction,
    TopologyOrientation,
    ValidationProperties,
)

# Keen topology-table cube-corner signs. +X Right, +Y Up, +Z Backward.
_CUBE_CORNER_SIGNS: tuple[tuple[int, int, int], ...] = (
    (-1, -1, -1),
    (1, -1, -1),
    (-1, 1, -1),
    (1, 1, -1),
    (-1, -1, 1),
    (1, -1, 1),
    (-1, 1, 1),
    (1, 1, 1),
)

# Right-angle vertex of identity Corner / the cube corner InvCorner removes.
_RIGHT_DOWN_FORWARD_SIGNS = (1, -1, -1)

_CUBE_FACES: tuple[tuple[int, ...], ...] = (
    (1, 3, 7, 5),  # +X Right
    (4, 6, 2, 0),  # -X Left
    (2, 6, 7, 3),  # +Y Up
    (0, 1, 5, 4),  # -Y Down
    (5, 7, 6, 4),  # +Z Backward
    (0, 2, 3, 1),  # -Z Forward
)

_SLOPE_SIGNS: tuple[tuple[int, int, int], ...] = (
    (-1, 1, -1),
    (1, 1, -1),
    (-1, -1, -1),
    (1, -1, -1),
    (-1, -1, 1),
    (1, -1, 1),
)

_SLOPE_FACES: tuple[tuple[int, ...], ...] = (
    (2, 0, 1, 3),  # Forward
    (2, 3, 5, 4),  # Down
    (0, 1, 5, 4),  # slope (Y + Z = 0)
    (0, 2, 4),  # Left
    (1, 5, 3),  # Right
)

_CORNER_SIGNS: tuple[tuple[int, int, int], ...] = (
    (1, 1, -1),
    (1, -1, -1),
    (-1, -1, -1),
    (1, -1, 1),
)

_CORNER_FACES: tuple[tuple[int, ...], ...] = (
    (0, 1, 2),  # Forward
    (0, 3, 1),  # Right
    (1, 3, 2),  # Down
    (0, 2, 3),  # hypotenuse
)

_INV_CORNER_SIGNS: tuple[tuple[int, int, int], ...] = (
    (-1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (1, -1, 1),
    (-1, -1, 1),
    (-1, 1, 1),
    (1, 1, 1),
)

_INV_CORNER_FACES: tuple[tuple[int, ...], ...] = (
    (2, 5, 6, 1),  # Up
    (4, 5, 2, 0),  # Left
    (3, 6, 5, 4),  # Backward
    (0, 2, 1),  # Forward triangle
    (1, 6, 3),  # Right triangle
    (0, 3, 4),  # Down triangle
    (1, 3, 0),  # hypotenuse (opposite Corner winding)
)

_IDENTITY_PLACEMENT = PlacementSemantics(
    insert_at_cell_center=True,
    additional_offset_mm=(0, 0, 0),
    part_locator=None,
)


def _scale(signs: tuple[tuple[int, int, int], ...]) -> tuple[tuple[int, int, int], ...]:
    half = cell_half_extent_mm()
    return tuple((sx * half, sy * half, sz * half) for sx, sy, sz in signs)


def _cross(
    a: tuple[int, int, int], b: tuple[int, int, int]
) -> tuple[int, int, int]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _sub(
    a: tuple[int, int, int], b: tuple[int, int, int]
) -> tuple[int, int, int]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def signed_volume_times_6(
    vertices: tuple[tuple[int, int, int], ...],
    faces: tuple[tuple[int, ...], ...],
) -> int:
    """Six times the enclosed volume of a closed mesh.

    Faces are wound counter-clockwise when viewed from outside the solid
    so this value is positive.
    """
    total = 0
    for face in faces:
        origin = vertices[face[0]]
        for i in range(1, len(face) - 1):
            a = vertices[face[i]]
            b = vertices[face[i + 1]]
            total += _dot(origin, _cross(a, b))
    return total


def _bounding_box(
    vertices: tuple[tuple[int, int, int], ...],
) -> AxisAlignedBoxMm:
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    return AxisAlignedBoxMm(
        min_mm=(min(xs), min(ys), min(zs)),
        max_mm=(max(xs), max(ys), max(zs)),
    )


def _validation(
    vertices: tuple[tuple[int, int, int], ...],
    faces: tuple[tuple[int, ...], ...],
) -> ValidationProperties:
    return ValidationProperties(
        vertex_count=len(vertices),
        face_count=len(faces),
        volume_times_6_mm3=signed_volume_times_6(vertices, faces),
        bounding_box=_bounding_box(vertices),
    )


# Face winding of the Corner tetrahedron, in construction-vertex order.
TETRAHEDRON_CUT_FACES: tuple[tuple[int, ...], ...] = _CORNER_FACES

# CubeTopology tokens that have a native construction. Other automatable-class
# tokens (for example Slope2Base) fail closed until a later construction exists.
AUTOMATABLE_CUBE_TOPOLOGIES: frozenset[str] = frozenset(
    {"Box", "Slope", "Corner", "InvCorner"}
)

# Initial-program identities. Default part generation still uses this set.
ORIGINAL_LIBRARY_BINDINGS: tuple[tuple[str, str], ...] = (
    ("large_armor_block", "Box"),
    ("large_armor_slope", "Slope"),
    ("large_armor_corner", "Corner"),
    ("large_armor_corner_inv", "InvCorner"),
)

# S2C-11.4.1 representative automatable subset beyond the original four.
REPRESENTATIVE_AUTOMATABLE_BINDINGS: tuple[tuple[str, str], ...] = (
    ("large_heavy_block_armor_block", "Box"),
    ("large_heavy_block_armor_slope", "Slope"),
    ("large_heavy_block_armor_corner", "Corner"),
    ("large_heavy_block_armor_corner_inv", "InvCorner"),
)

_GEOMETRY_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")


def _box_construction() -> BoxConstruction:
    env = CANONICAL_CELL_ENVELOPE
    return BoxConstruction(min_mm=env.min_mm, max_mm=env.max_mm)


def _corner_construction() -> TetrahedronConstruction:
    verts = _scale(_CORNER_SIGNS)
    return TetrahedronConstruction(
        vertices_mm=(verts[0], verts[1], verts[2], verts[3]),
    )


def _checked_geometry_id(geometry_id: str) -> str:
    if geometry_id == "" or geometry_id[0] < "a" or geometry_id[0] > "z":
        raise UnknownGeometryError(
            f"geometry_id {geometry_id!r} is not a valid SE2CAD identity"
        )
    if any(ch not in _GEOMETRY_ID_CHARS for ch in geometry_id):
        raise UnknownGeometryError(
            f"geometry_id {geometry_id!r} is not a valid SE2CAD identity"
        )
    return geometry_id


def _block_recipe(geometry_id: str) -> NativeSolidRecipe:
    vertices = _scale(_CUBE_CORNER_SIGNS)
    faces = _CUBE_FACES
    return NativeSolidRecipe(
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
        solid_kind=SolidKind.AXIS_ALIGNED_BOX,
        vertices_mm=vertices,
        faces=faces,
        construction=_box_construction(),
        orientation=TopologyOrientation(
            observed_cube_topology="Box",
            full_faces=("Right", "Left", "Up", "Down", "Backward", "Forward"),
            cut_description="none; occupies the entire 1×1×1 cell",
            distinguishing_cube_corner_signs=_RIGHT_DOWN_FORWARD_SIGNS,
        ),
        validation=_validation(vertices, faces),
    )


def _slope_recipe(geometry_id: str) -> NativeSolidRecipe:
    vertices = _scale(_SLOPE_SIGNS)
    faces = _SLOPE_FACES
    half = cell_half_extent_mm()
    return NativeSolidRecipe(
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
        solid_kind=SolidKind.RIGHT_TRIANGULAR_PRISM,
        vertices_mm=vertices,
        faces=faces,
        construction=PrismConstruction(
            profile_plane="YZ",
            profile_yz_mm=((half, -half), (-half, -half), (-half, half)),
            extrusion_axis="X",
            extrusion_min_mm=-half,
            extrusion_max_mm=half,
        ),
        orientation=TopologyOrientation(
            observed_cube_topology="Slope",
            full_faces=("Forward", "Down"),
            cut_description=(
                "identity solid is the half-cell Y+Z <= 0; full faces on "
                "Forward and Down; sloped quad from the Forward-Up edge to "
                "the Backward-Down edge"
            ),
            distinguishing_cube_corner_signs=_RIGHT_DOWN_FORWARD_SIGNS,
        ),
        validation=_validation(vertices, faces),
    )


def _corner_recipe(geometry_id: str) -> NativeSolidRecipe:
    vertices = _scale(_CORNER_SIGNS)
    faces = _CORNER_FACES
    return NativeSolidRecipe(
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
        solid_kind=SolidKind.TETRAHEDRON,
        vertices_mm=vertices,
        faces=faces,
        construction=_corner_construction(),
        orientation=TopologyOrientation(
            observed_cube_topology="Corner",
            full_faces=(),
            cut_description=(
                "identity tetrahedron occupies the Right-Down-Forward cube "
                "corner; orthogonal triangular faces on Right, Down, and "
                "Forward; hypotenuse through the other three vertices"
            ),
            distinguishing_cube_corner_signs=_RIGHT_DOWN_FORWARD_SIGNS,
        ),
        validation=_validation(vertices, faces),
    )


def _inv_corner_recipe(geometry_id: str) -> NativeSolidRecipe:
    vertices = _scale(_INV_CORNER_SIGNS)
    faces = _INV_CORNER_FACES
    return NativeSolidRecipe(
        geometry_id=geometry_id,
        recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
        solid_kind=SolidKind.BOX_MINUS_TETRAHEDRON,
        vertices_mm=vertices,
        faces=faces,
        construction=BoxMinusTetrahedronConstruction(
            box=_box_construction(),
            cut=_corner_construction(),
        ),
        orientation=TopologyOrientation(
            observed_cube_topology="InvCorner",
            full_faces=("Up", "Left", "Backward"),
            cut_description=(
                "identity solid is the cell box minus the Corner "
                "tetrahedron; the missing cube corner is Right-Down-Forward"
            ),
            distinguishing_cube_corner_signs=_RIGHT_DOWN_FORWARD_SIGNS,
        ),
        validation=_validation(vertices, faces),
    )


_TOPOLOGY_BUILDERS = {
    "Box": _block_recipe,
    "Slope": _slope_recipe,
    "Corner": _corner_recipe,
    "InvCorner": _inv_corner_recipe,
}


def recipe_for_topology(geometry_id: str, cube_topology: str) -> NativeSolidRecipe:
    """Stamp a native recipe for one automatable CubeTopology.

    Box, Slope, Corner, and InvCorner reuse the qualified constructions.
    Other topologies fail closed; they are not forced through one technique.
    """
    checked = _checked_geometry_id(geometry_id)
    builder = _TOPOLOGY_BUILDERS.get(cube_topology)
    if builder is None:
        raise UnsupportedTopologyError(
            f"cube_topology {cube_topology!r} has no native construction"
        )
    return builder(checked)


def _record(recipe: NativeSolidRecipe) -> LibraryRecord:
    return LibraryRecord(
        geometry_id=recipe.geometry_id,
        grid_size="Large",
        recipe_kind=recipe.recipe_kind,
        observed_cube_topology=recipe.orientation.observed_cube_topology,
        frame=CANONICAL_LOCAL_FRAME,
        placement=_IDENTITY_PLACEMENT,
        recipe=recipe,
    )


LIBRARY_RECORDS: tuple[LibraryRecord, ...] = tuple(
    _record(recipe_for_topology(geometry_id, cube_topology))
    for geometry_id, cube_topology in (
        ORIGINAL_LIBRARY_BINDINGS + REPRESENTATIVE_AUTOMATABLE_BINDINGS
    )
)
