"""Native SolidWorks construction from qualified recipe plans.

COM argument lists are taken from official 2026 method-page existence plus
live late-bound SolidWorks 2026 CDispatch evidence. Live typelib constants
are preferred when gencache is available.
"""

from __future__ import annotations

from typing import Any, Sequence

from se2cad.library import SolidKind
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.errors import SolidWorksComError
from se2cad.solidworks.recipe_plan import (
    BoxPlan,
    ConstructionPlan,
    TetrahedronPlan,
)


def _com_fail(exc: BaseException, message: str) -> SolidWorksComError:
    return SolidWorksComError(f"{message}: {exc}")


def _const(session: Any, name: str, fallback: int) -> int:
    try:
        return int(getattr(session.constants, name))
    except Exception:
        return fallback


def _clear_selection(model: Any) -> None:
    try:
        model.ClearSelection2(True)
    except Exception as exc:
        raise _com_fail(exc, "ClearSelection2 failed") from exc


def _first_ref_plane(model: Any) -> Any:
    try:
        feat = com_get(model, "FirstFeature")
        while feat is not None:
            type_name = str(com_get(feat, "GetTypeName2"))
            if type_name == "RefPlane":
                return feat
            feat = com_get(feat, "GetNextFeature")
    except Exception as exc:
        raise _com_fail(exc, "walking reference planes failed") from exc
    raise SolidWorksComError("part template has no RefPlane feature")


def _select_feature(feature: Any) -> None:
    try:
        ok = feature.Select2(False, 0)
    except Exception as exc:
        raise _com_fail(exc, "Select2 failed") from exc
    if not ok:
        raise SolidWorksComError("Select2 returned false")


def _feature_extrusion_midplane(model: Any, session: Any, depth_m: float) -> Any:
    """IFeatureManager.FeatureExtrusion2 mid-plane, depths in metres.

    Live SolidWorks 2026 CDispatch requires 23 arguments. The first 20 match
    published FeatureExtrusion2 samples; the last three are the
    FeatureExtrusion3 assembly-scope flags (confirmed 2026-09-08: 20–22 args
    raise DISP_E_PARAMNOTOPTIONAL, 23 args succeed):

    Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2,
    OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2,
    Merge, UseFeatScope, UseAutoSelect, AssemblyFeatureScope,
    AutoSelectComponents, PropagateFeatureToParts.
    """
    midplane = _const(session, "swEndCondMidPlane", 6)
    try:
        feature = model.FeatureManager.FeatureExtrusion2(
            True,
            False,
            False,
            midplane,
            0,
            float(depth_m),
            0.0,
            False,
            False,
            False,
            False,
            0.0,
            0.0,
            False,
            False,
            False,
            False,
            True,
            True,
            True,
            True,
            True,
            False,
        )
    except Exception as exc:
        raise _com_fail(exc, "FeatureExtrusion2 failed") from exc
    if feature is None:
        raise SolidWorksComError("FeatureExtrusion2 returned None")
    return feature


def _construct_box(session: Any, model: Any, box: BoxPlan) -> None:
    """Cell-envelope box: Front-plane rectangle, mid-plane extrude along Z."""
    _clear_selection(model)
    _select_feature(_first_ref_plane(model))
    sketch = model.SketchManager
    try:
        sketch.InsertSketch(True)
        sketch.CreateCornerRectangle(
            box.min_m[0],
            box.min_m[1],
            0.0,
            box.max_m[0],
            box.max_m[1],
            0.0,
        )
        sketch.InsertSketch(True)
    except Exception as exc:
        raise _com_fail(exc, "box sketch failed") from exc
    _feature_extrusion_midplane(session=session, model=model, depth_m=box.size_m[2])


def _yz_profile_to_right_plane_sketch(
    y: float, z: float
) -> tuple[float, float, float]:
    """Map qualified YZ profile coordinates onto the Right Plane sketch.

    Live SolidWorks 2026: sketch +X → model −Z, sketch +Y → model +Y.
    """
    return (-z, y, 0.0)


def _nth_ref_plane(model: Any, index: int) -> Any:
    """Return the Nth RefPlane. Standard templates: 0 Front, 1 Top, 2 Right."""
    seen = 0
    feat = com_get(model, "FirstFeature")
    while feat is not None:
        if str(com_get(feat, "GetTypeName2")) == "RefPlane":
            if seen == index:
                return feat
            seen += 1
        feat = com_get(feat, "GetNextFeature")
    raise SolidWorksComError(f"part template has no RefPlane at index {index}")


def _construct_prism(session: Any, model: Any, plan: ConstructionPlan) -> None:
    """YZ triangular prism: 2D sketch on Right plane, mid-plane extrude on X.

    Live SolidWorks 2026 mapping on Right Plane (confirmed 2026-09-08):
    sketch +X → model −Z, sketch +Y → model +Y, mid-plane extrude along X.
    3D-sketch FeatureExtrusion2 returns None on this host.
    """
    prism = plan.prism
    if prism is None:
        raise SolidWorksComError("prism plan missing")
    _clear_selection(model)
    _select_feature(_nth_ref_plane(model, 2))
    sketch = model.SketchManager
    try:
        sketch.InsertSketch(True)
        yz = prism.profile_yz_m
        points = tuple(_yz_profile_to_right_plane_sketch(y, z) for y, z in yz)
        for i in range(3):
            a = points[i]
            b = points[(i + 1) % 3]
            sketch.CreateLine(a[0], a[1], a[2], b[0], b[1], b[2])
        sketch.InsertSketch(True)
    except Exception as exc:
        raise _com_fail(exc, "slope Right-plane sketch failed") from exc
    _feature_extrusion_midplane(
        session=session, model=model, depth_m=prism.midplane_depth_m
    )


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _sub(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _features_of_type(model: Any, type_name: str) -> list[Any]:
    found: list[Any] = []
    feat = com_get(model, "FirstFeature")
    while feat is not None:
        if str(com_get(feat, "GetTypeName2")) == type_name:
            found.append(feat)
        feat = com_get(feat, "GetNextFeature")
    return found


def _hypotenuse_and_apex(
    tetra: TetrahedronPlan,
) -> tuple[tuple[int, ...], int]:
    """Qualified recipes list the hypotenuse as the last tetrahedron face."""
    if not tetra.faces:
        raise SolidWorksComError("tetrahedron faces missing")
    hypotenuse = tetra.faces[-1]
    if len(hypotenuse) != 3:
        raise SolidWorksComError("tetrahedron hypotenuse must be a triangle")
    remaining = [
        index
        for index in range(len(tetra.vertices_m))
        if index not in set(hypotenuse)
    ]
    if len(remaining) != 1:
        raise SolidWorksComError("tetrahedron must have one vertex off the hypotenuse")
    return hypotenuse, remaining[0]


def _feature_cut_dir_keeps_point(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    keep: tuple[float, float, float],
) -> bool:
    """Return FeatureCut4 Dir that keeps ``keep`` after a through-all cut.

    Live SolidWorks 2026: with Flip=False, Dir=False keeps the +normal
    half-space of (p1−p0)×(p2−p0). Confirmed 2026-09-08 against the
    qualified Corner / InvCorner volumes and centers of mass.
    """
    normal = _cross(_sub(p1, p0), _sub(p2, p0))
    return _dot(normal, _sub(keep, p0)) < 0.0


def _box_from_vertices(
    vertices: Sequence[tuple[float, float, float]],
) -> BoxPlan:
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    min_m = (min(xs), min(ys), min(zs))
    max_m = (max(xs), max(ys), max(zs))
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


def _feature_cut_through_all(model: Any, session: Any, *, direction: bool) -> Any:
    """IFeatureManager.FeatureCut4 through-all, 27 arguments.

    Live SolidWorks 2026 CDispatch: the published FeatureCut4 list is 27
    arguments and succeeds. Flip=True returns None on this host; only Dir
    is used to choose the kept half-space.

    Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2,
    OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2,
    NormalCut, UseFeatScope, UseAutoSelect, AssemblyFeatureScope,
    AutoSelectComponents, PropagateFeatureToParts, T0, StartOffset,
    FlipStartOffset, OptimizeGeometry.
    """
    through_all = _const(session, "swEndCondThroughAll", 1)
    start_plane = _const(session, "swStartSketchPlane", 0)
    try:
        feature = model.FeatureManager.FeatureCut4(
            True,
            False,
            bool(direction),
            through_all,
            0,
            0.01,
            0.01,
            False,
            False,
            False,
            False,
            1.0,
            1.0,
            False,
            False,
            False,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            start_plane,
            0.0,
            False,
            False,
        )
    except Exception as exc:
        raise _com_fail(exc, "FeatureCut4 failed") from exc
    if feature is None:
        raise SolidWorksComError("FeatureCut4 returned None")
    return feature


def _insert_plane_through_recipe_points(
    session: Any,
    model: Any,
    points: Sequence[tuple[float, float, float]],
) -> Any:
    """3D-sketch points at recipe vertices, then InsertRefPlane coincident×3.

    Live 2026: Select2 marks 0,1,2 plus constraint 4 (Coincident) on each
    reference creates the plane. SelectByID2 Callout type-mismatches.
    IModeler.CreatePlanarSurface2 raises RPC_E_SERVERFAULT.
    """
    if len(points) != 3:
        raise SolidWorksComError("a cutting plane needs three recipe vertices")
    sketch = model.SketchManager
    try:
        sketch.Insert3DSketch(True)
        created = [sketch.CreatePoint(p[0], p[1], p[2]) for p in points]
        sketch.Insert3DSketch(True)
    except Exception as exc:
        raise _com_fail(exc, "hypotenuse 3D-sketch points failed") from exc
    if any(point is None for point in created):
        raise SolidWorksComError("CreatePoint returned None")
    _clear_selection(model)
    for index, point in enumerate(created):
        try:
            ok = point.Select2(index > 0, index)
        except Exception as exc:
            raise _com_fail(exc, "Select2 of recipe sketch point failed") from exc
        if not ok:
            raise SolidWorksComError("Select2 returned false for recipe sketch point")
    coincident = _const(session, "swRefPlaneReferenceConstraint_Coincident", 4)
    try:
        plane = model.FeatureManager.InsertRefPlane(
            coincident, 0.0, coincident, 0.0, coincident, 0.0
        )
    except Exception as exc:
        raise _com_fail(exc, "InsertRefPlane failed") from exc
    if plane is None:
        raise SolidWorksComError("InsertRefPlane returned None")
    return plane


def _cut_box_by_tetra_hypotenuse(
    session: Any,
    model: Any,
    box: BoxPlan,
    tetra: TetrahedronPlan,
    *,
    keep_apex: bool,
) -> None:
    """Cell box plus one through-all cut on the recipe hypotenuse.

    The cube split by the hypotenuse plane is exactly the qualified
    tetrahedron and its complement. FeatureManager-native; no IModeler.
    """
    hypotenuse, apex_index = _hypotenuse_and_apex(tetra)
    plane_points = tuple(tetra.vertices_m[index] for index in hypotenuse)
    apex = tetra.vertices_m[apex_index]
    direction = _feature_cut_dir_keeps_point(*plane_points, apex)
    if not keep_apex:
        direction = not direction

    _construct_box(session, model, box)
    plane = _insert_plane_through_recipe_points(session, model, plane_points)
    _clear_selection(model)
    _select_feature(plane)
    cover = max(box.size_m) * 4.0
    sketch = model.SketchManager
    try:
        sketch.InsertSketch(True)
        sketch.CreateCornerRectangle(-cover, -cover, 0.0, cover, cover, 0.0)
        sketch.InsertSketch(True)
    except Exception as exc:
        raise _com_fail(exc, "hypotenuse-plane cut sketch failed") from exc
    profiles = _features_of_type(model, "ProfileFeature")
    if not profiles:
        raise SolidWorksComError("hypotenuse-plane cut sketch missing")
    _select_feature(profiles[-1])
    _feature_cut_through_all(model, session, direction=direction)


def _construct_tetrahedron(
    session: Any,
    model: Any,
    tetra: TetrahedronPlan,
) -> None:
    """Qualified tetrahedron: cell box cut, keeping the apex half-space."""
    _cut_box_by_tetra_hypotenuse(
        session,
        model,
        _box_from_vertices(tetra.vertices_m),
        tetra,
        keep_apex=True,
    )


def _construct_box_minus_tetra(
    session: Any, model: Any, plan: ConstructionPlan
) -> None:
    spec = plan.box_minus_tetrahedron
    if spec is None:
        raise SolidWorksComError("missing box-minus-tetrahedron plan")
    _cut_box_by_tetra_hypotenuse(
        session, model, spec.box, spec.cut, keep_apex=False
    )


def construct_plan(session: Any, model: Any, plan: ConstructionPlan) -> None:
    """Materialize one qualified plan with native SolidWorks solids."""
    if plan.solid_kind is SolidKind.AXIS_ALIGNED_BOX:
        if plan.box is None:
            raise SolidWorksComError("box plan missing")
        _construct_box(session, model, plan.box)
        return
    if plan.solid_kind is SolidKind.RIGHT_TRIANGULAR_PRISM:
        if plan.prism is None:
            raise SolidWorksComError("prism plan missing")
        _construct_prism(session, model, plan)
        return
    if plan.solid_kind is SolidKind.TETRAHEDRON:
        if plan.tetrahedron is None:
            raise SolidWorksComError("tetrahedron plan missing")
        _construct_tetrahedron(session, model, plan.tetrahedron)
        return
    if plan.solid_kind is SolidKind.BOX_MINUS_TETRAHEDRON:
        _construct_box_minus_tetra(session, model, plan)
        return
    raise SolidWorksComError(f"unsupported solid kind {plan.solid_kind!r}")
