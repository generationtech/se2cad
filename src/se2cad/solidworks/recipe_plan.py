"""CAD-neutral construction plans consumed from qualified recipes.

The backend does not invent geometry. Each plan is the recipe construction
with millimetres converted to metres. No second coordinate frame.
"""

from __future__ import annotations

from dataclasses import dataclass

from se2cad.library import (
    BoxConstruction,
    BoxMinusTetrahedronConstruction,
    NativeSolidRecipe,
    PrismConstruction,
    SolidKind,
    TETRAHEDRON_CUT_FACES,
    TetrahedronConstruction,
    lookup_recipe,
    signed_volume_times_6,
)
from se2cad.solidworks.artifacts import canonical_geometry_ids
from se2cad.solidworks.units import (
    mm_to_metres,
    point_mm_to_metres,
    recipe_volume_m3,
)


@dataclass(frozen=True)
class BoxPlan:
    min_m: tuple[float, float, float]
    max_m: tuple[float, float, float]
    center_m: tuple[float, float, float]
    size_m: tuple[float, float, float]


@dataclass(frozen=True)
class PrismPlan:
    """YZ right triangle extruded along X, in metres."""

    profile_yz_m: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    extrusion_min_m: float
    extrusion_max_m: float
    midplane_depth_m: float


@dataclass(frozen=True)
class TetrahedronPlan:
    vertices_m: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    faces: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class BoxMinusTetrahedronPlan:
    box: BoxPlan
    cut: TetrahedronPlan


@dataclass(frozen=True)
class ExpectedSolid:
    bounding_box_min_m: tuple[float, float, float]
    bounding_box_max_m: tuple[float, float, float]
    volume_m3: float
    center_of_mass_m: tuple[float, float, float]


@dataclass(frozen=True)
class ConstructionPlan:
    geometry_id: str
    solid_kind: SolidKind
    vertices_m: tuple[tuple[float, float, float], ...]
    faces: tuple[tuple[int, ...], ...]
    box: BoxPlan | None
    prism: PrismPlan | None
    tetrahedron: TetrahedronPlan | None
    box_minus_tetrahedron: BoxMinusTetrahedronPlan | None
    expected: ExpectedSolid


def _box_volume_times_6(construction: BoxConstruction) -> int:
    dx = construction.max_mm[0] - construction.min_mm[0]
    dy = construction.max_mm[1] - construction.min_mm[1]
    dz = construction.max_mm[2] - construction.min_mm[2]
    return 6 * dx * dy * dz


def _box_plan(construction: BoxConstruction) -> BoxPlan:
    min_m = point_mm_to_metres(construction.min_mm)
    max_m = point_mm_to_metres(construction.max_mm)
    return BoxPlan(
        min_m=min_m,
        max_m=max_m,
        center_m=(
            (min_m[0] + max_m[0]) / 2.0,
            (min_m[1] + max_m[1]) / 2.0,
            (min_m[2] + max_m[2]) / 2.0,
        ),
        size_m=(
            max_m[0] - min_m[0],
            max_m[1] - min_m[1],
            max_m[2] - min_m[2],
        ),
    )


def _prism_plan(construction: PrismConstruction) -> PrismPlan:
    if construction.profile_plane != "YZ" or construction.extrusion_axis != "X":
        raise ValueError(
            "backend consumes the qualified YZ-along-X prism; "
            f"got plane={construction.profile_plane!r} "
            f"axis={construction.extrusion_axis!r}"
        )
    profile = tuple(
        (mm_to_metres(y), mm_to_metres(z)) for y, z in construction.profile_yz_mm
    )
    return PrismPlan(
        profile_yz_m=(profile[0], profile[1], profile[2]),
        extrusion_min_m=mm_to_metres(construction.extrusion_min_mm),
        extrusion_max_m=mm_to_metres(construction.extrusion_max_mm),
        midplane_depth_m=mm_to_metres(
            construction.extrusion_max_mm - construction.extrusion_min_mm
        ),
    )


def _tetra_plan(
    construction: TetrahedronConstruction,
    faces: tuple[tuple[int, ...], ...],
) -> TetrahedronPlan:
    verts = tuple(point_mm_to_metres(v) for v in construction.vertices_mm)
    return TetrahedronPlan(
        vertices_m=(verts[0], verts[1], verts[2], verts[3]),
        faces=faces,
    )


def _mean_points(
    points: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    n = float(len(points))
    return (
        sum(p[0] for p in points) / n,
        sum(p[1] for p in points) / n,
        sum(p[2] for p in points) / n,
    )


def _expected_com_m(recipe: NativeSolidRecipe) -> tuple[float, float, float]:
    """Center of mass from the qualified construction, in metres.

    Box: cell center. Prism: mid-X and YZ triangle centroid. Tetrahedron:
    mean of the four vertices. InvCorner: volume-weighted complement.
    """
    if isinstance(recipe.construction, BoxConstruction):
        return _box_plan(recipe.construction).center_m
    if isinstance(recipe.construction, PrismConstruction):
        prism = _prism_plan(recipe.construction)
        ys = [p[0] for p in prism.profile_yz_m]
        zs = [p[1] for p in prism.profile_yz_m]
        return (0.0, sum(ys) / 3.0, sum(zs) / 3.0)
    if isinstance(recipe.construction, TetrahedronConstruction):
        verts = tuple(point_mm_to_metres(v) for v in recipe.construction.vertices_mm)
        return _mean_points(verts)
    if isinstance(recipe.construction, BoxMinusTetrahedronConstruction):
        box = recipe.construction.box
        box_vol = recipe_volume_m3(_box_volume_times_6(box))
        tet_vol = recipe_volume_m3(
            signed_volume_times_6(
                recipe.construction.cut.vertices_mm, TETRAHEDRON_CUT_FACES
            )
        )
        tet_com = _mean_points(
            tuple(point_mm_to_metres(v) for v in recipe.construction.cut.vertices_mm)
        )
        inv_vol = box_vol - tet_vol
        return (
            (box_vol * 0.0 - tet_vol * tet_com[0]) / inv_vol,
            (box_vol * 0.0 - tet_vol * tet_com[1]) / inv_vol,
            (box_vol * 0.0 - tet_vol * tet_com[2]) / inv_vol,
        )
    raise TypeError(f"unsupported construction {type(recipe.construction)!r}")


def plan_from_recipe(recipe: NativeSolidRecipe) -> ConstructionPlan:
    """Build a metre-space plan from one qualified native recipe."""
    vertices_m = tuple(point_mm_to_metres(v) for v in recipe.vertices_mm)
    box = (
        _box_plan(recipe.construction)
        if isinstance(recipe.construction, BoxConstruction)
        else None
    )
    prism = (
        _prism_plan(recipe.construction)
        if isinstance(recipe.construction, PrismConstruction)
        else None
    )
    tetra = None
    box_minus = None
    if isinstance(recipe.construction, TetrahedronConstruction):
        tetra = _tetra_plan(recipe.construction, recipe.faces)
    elif isinstance(recipe.construction, BoxMinusTetrahedronConstruction):
        box_minus = BoxMinusTetrahedronPlan(
            box=_box_plan(recipe.construction.box),
            cut=_tetra_plan(recipe.construction.cut, TETRAHEDRON_CUT_FACES),
        )

    expected_box = recipe.validation.bounding_box
    return ConstructionPlan(
        geometry_id=recipe.geometry_id,
        solid_kind=recipe.solid_kind,
        vertices_m=vertices_m,
        faces=recipe.faces,
        box=box,
        prism=prism,
        tetrahedron=tetra,
        box_minus_tetrahedron=box_minus,
        expected=ExpectedSolid(
            bounding_box_min_m=point_mm_to_metres(expected_box.min_mm),
            bounding_box_max_m=point_mm_to_metres(expected_box.max_mm),
            volume_m3=recipe_volume_m3(recipe.validation.volume_times_6_mm3),
            center_of_mass_m=_expected_com_m(recipe),
        ),
    )


def plan_for_geometry_id(geometry_id: str) -> ConstructionPlan:
    return plan_from_recipe(lookup_recipe(geometry_id))


def all_canonical_plans() -> tuple[ConstructionPlan, ...]:
    return tuple(plan_for_geometry_id(gid) for gid in canonical_geometry_ids())
