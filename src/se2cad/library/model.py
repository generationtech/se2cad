"""Immutable block-library domain types.

Observed Space Engineers topology tokens stay distinct from SE2CAD
construction recipes. This module does not emit CAD documents or read
game assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

from se2cad.catalog.model import RecipeKind
from se2cad.library.frame import AxisAlignedBoxMm, CanonicalLocalFrame


class SolidKind(str, Enum):
    """SE2CAD constructive-solid vocabulary for native armor recipes."""

    AXIS_ALIGNED_BOX = "axis_aligned_box"
    RIGHT_TRIANGULAR_PRISM = "right_triangular_prism"
    TETRAHEDRON = "tetrahedron"
    BOX_MINUS_TETRAHEDRON = "box_minus_tetrahedron"


@dataclass(frozen=True)
class BoxConstruction:
    """Axis-aligned box from inclusive min to inclusive max, millimetres."""

    min_mm: tuple[int, int, int]
    max_mm: tuple[int, int, int]


@dataclass(frozen=True)
class PrismConstruction:
    """Right triangular prism: YZ triangle extruded along local +X."""

    profile_plane: str
    profile_yz_mm: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]
    extrusion_axis: str
    extrusion_min_mm: int
    extrusion_max_mm: int


@dataclass(frozen=True)
class TetrahedronConstruction:
    """Tetrahedron given by four vertices in the canonical local frame."""

    vertices_mm: tuple[
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
    ]


@dataclass(frozen=True)
class BoxMinusTetrahedronConstruction:
    """Cell box minus the Corner tetrahedron (InvCorner)."""

    box: BoxConstruction
    cut: TetrahedronConstruction


Construction = Union[
    BoxConstruction,
    PrismConstruction,
    TetrahedronConstruction,
    BoxMinusTetrahedronConstruction,
]


@dataclass(frozen=True)
class ValidationProperties:
    """Deterministic integer properties of the authored solid."""

    vertex_count: int
    face_count: int
    volume_times_6_mm3: int
    bounding_box: AxisAlignedBoxMm


@dataclass(frozen=True)
class TopologyOrientation:
    """Identity-orientation convention that distinguishes the four solids.

    These are Space Engineers topology facts, expressed in the canonical
    local frame. They are not SolidWorks insertion rules.
    """

    observed_cube_topology: str
    full_faces: tuple[str, ...]
    cut_description: str
    distinguishing_cube_corner_signs: tuple[int, int, int]


@dataclass(frozen=True)
class PlacementSemantics:
    """How a later backend inserts the canonical solid.

    No extra offset: the S2C-3.1.1 instance transform is the placement.
    Authoritative records leave the part locator unbound. A backend may
    bind a logical identity only after generate, validate, save, and reopen.
    """

    insert_at_cell_center: bool
    additional_offset_mm: tuple[int, int, int]
    part_locator: Optional[str]


@dataclass(frozen=True)
class NativeSolidRecipe:
    """Exact native-procedural solid for one geometry identity."""

    geometry_id: str
    recipe_kind: RecipeKind
    solid_kind: SolidKind
    vertices_mm: tuple[tuple[int, int, int], ...]
    faces: tuple[tuple[int, ...], ...]
    construction: Construction
    orientation: TopologyOrientation
    validation: ValidationProperties


@dataclass(frozen=True)
class LibraryRecord:
    """Canonical library record for one supported geometry identity.

    ``chamfer_capable`` is an explicit CAD/library decision. It is not
    catalog ``support_status``, recipe kind, or SE subtype identity.
    Future imported or hand-authored geometry must set this false until
    chamfer support is established for that construction.
    """

    geometry_id: str
    grid_size: str
    recipe_kind: RecipeKind
    observed_cube_topology: str
    frame: CanonicalLocalFrame
    placement: PlacementSemantics
    recipe: NativeSolidRecipe
    chamfer_capable: bool
