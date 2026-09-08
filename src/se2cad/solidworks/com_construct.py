"""Native SolidWorks construction from qualified recipe plans.

COM argument lists below are taken from official 2026 method pages (titles
and current existence), static/older published signatures, and CodeStack
examples. Live typelib constants are preferred when gencache is available.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from se2cad.library import SolidKind
from se2cad.solidworks.errors import SolidWorksComError
from se2cad.solidworks.recipe_plan import (
    BoxPlan,
    ConstructionPlan,
    PrismPlan,
    TetrahedronPlan,
)

# ISurface.CreateTrimmedSheet5 tolerance from CodeStack multi-extrude example.
_SHEET_TRIM_TOLERANCE_M = 1e-5


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
        feat = model.FirstFeature()
        while feat is not None:
            type_name = str(feat.GetTypeName2())
            if type_name == "RefPlane":
                return feat
            feat = feat.GetNextFeature()
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

    Argument order from the official FeatureExtrusion2 page (still present
    in the 2026 help set) and matching 20-argument VBA samples:

    Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2,
    OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2,
    Merge, UseFeatScope, UseAutoSelect.
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


def _construct_prism(session: Any, model: Any, prism: PrismPlan) -> None:
    """YZ triangle at X=0, mid-plane extrude along X. 3D sketch, metres."""
    yz = prism.profile_yz_m
    points = (
        (0.0, yz[0][0], yz[0][1]),
        (0.0, yz[1][0], yz[1][1]),
        (0.0, yz[2][0], yz[2][1]),
    )
    sketch = model.SketchManager
    try:
        sketch.Insert3DSketch(True)
        for i in range(3):
            a = points[i]
            b = points[(i + 1) % 3]
            sketch.CreateLine(a[0], a[1], a[2], b[0], b[1], b[2])
        sketch.Insert3DSketch(True)
    except Exception as exc:
        raise _com_fail(exc, "slope 3D-sketch failed") from exc
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


def _norm(v: tuple[float, float, float]) -> float:
    return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5


def _create_line(modeler: Any, start: Sequence[float], end: Sequence[float]) -> Any:
    """IModeler.CreateLine(StartPoint, Direction) — direction includes length."""
    direction = (
        float(end[0]) - float(start[0]),
        float(end[1]) - float(start[1]),
        float(end[2]) - float(start[2]),
    )
    try:
        curve = modeler.CreateLine(list(start), list(direction))
    except Exception as exc:
        raise _com_fail(exc, "IModeler.CreateLine failed") from exc
    if curve is None:
        raise SolidWorksComError("IModeler.CreateLine returned None")
    return curve


def _create_planar_sheet(
    modeler: Any, points: Sequence[tuple[float, float, float]]
) -> Any:
    """Planar trimmed sheet from recipe face vertices.

    CreatePlanarSurface2(root, normal, reference) — official 2026 page plus
    CodeStack CreatePlanarSurface2(ArrayData, ArrayData, ArrayData).
    ISurface.CreateTrimmedSheet5(curves, closed, tolerance_m) — CodeStack
    multi-extrude example (tolerance 1e-5 m).
    """
    if len(points) < 3:
        raise SolidWorksComError("a planar face needs at least three vertices")
    p0, p1, p2 = points[0], points[1], points[2]
    normal = _cross(_sub(p1, p0), _sub(p2, p0))
    if _norm(normal) == 0.0:
        raise SolidWorksComError("degenerate recipe face normal")
    reference = _sub(p1, p0)
    try:
        surface = modeler.CreatePlanarSurface2(list(p0), list(normal), list(reference))
    except Exception as exc:
        raise _com_fail(exc, "CreatePlanarSurface2 failed") from exc
    if surface is None:
        raise SolidWorksComError("CreatePlanarSurface2 returned None")

    curves = []
    for i, start in enumerate(points):
        end = points[(i + 1) % len(points)]
        curves.append(_create_line(modeler, start, end))
    try:
        sheet = surface.CreateTrimmedSheet5(curves, True, _SHEET_TRIM_TOLERANCE_M)
    except Exception as exc:
        raise _com_fail(exc, "CreateTrimmedSheet5 failed") from exc
    if sheet is None:
        raise SolidWorksComError("CreateTrimmedSheet5 returned None")
    return sheet


def _faces_from_sheets(sheets: Iterable[Any]) -> list[Any]:
    faces: list[Any] = []
    for sheet in sheets:
        try:
            raw = sheet.GetFaces()
        except Exception as exc:
            raise _com_fail(exc, "sheet GetFaces failed") from exc
        if raw is None:
            raise SolidWorksComError("sheet GetFaces returned None")
        if isinstance(raw, (list, tuple)):
            faces.extend(face for face in raw if face is not None)
        else:
            faces.append(raw)
    return faces


def _knit_solid(session: Any, modeler: Any, faces: list[Any]) -> Any:
    """IModeler.CreateBodyFromFaces2(count, faces, action, bool, bool)."""
    knit = _const(session, "swCreateFacesBodyActionKnit", 1)
    try:
        body = modeler.CreateBodyFromFaces2(len(faces), faces, knit, False, False)
    except Exception as exc:
        raise _com_fail(exc, "CreateBodyFromFaces2 failed") from exc
    if body is None:
        raise SolidWorksComError("CreateBodyFromFaces2 returned None")
    return body


def _persist_body(session: Any, model: Any, body: Any) -> Any:
    """IPartDoc.CreateFeatureFromBody3(body, makeCopy, options)."""
    check = _const(session, "swCreateFeatureBodyCheck", 1)
    simplify = _const(session, "swCreateFeatureBodySimplify", 2)
    try:
        feature = model.CreateFeatureFromBody3(body, False, check + simplify)
    except Exception as exc:
        raise _com_fail(exc, "CreateFeatureFromBody3 failed") from exc
    if feature is None:
        raise SolidWorksComError("CreateFeatureFromBody3 returned None")
    return feature


def _sheet_body_from_face_indices(
    modeler: Any,
    vertices: Sequence[tuple[float, float, float]],
    faces: Sequence[tuple[int, ...]],
) -> list[Any]:
    sheets = []
    for face in faces:
        points = tuple(vertices[index] for index in face)
        sheets.append(_create_planar_sheet(modeler, points))
    return sheets


def _construct_tetrahedron(
    session: Any, model: Any, tetra: TetrahedronPlan
) -> Any:
    modeler = session.get_modeler()
    sheets = _sheet_body_from_face_indices(modeler, tetra.vertices_m, tetra.faces)
    body = _knit_solid(session, modeler, _faces_from_sheets(sheets))
    _persist_body(session, model, body)
    return body


def _create_box_body(modeler: Any, box: BoxPlan) -> Any:
    """IModeler.CreateBodyFromBox3 — 9 doubles: center, +Z axis, size.

    Layout from CodeStack create-box-body and multiple published samples.
    Values are metres.
    """
    data = [
        box.center_m[0],
        box.center_m[1],
        box.center_m[2],
        0.0,
        0.0,
        1.0,
        box.size_m[0],
        box.size_m[1],
        box.size_m[2],
    ]
    try:
        body = modeler.CreateBodyFromBox3(data)
    except Exception as exc:
        raise _com_fail(exc, "CreateBodyFromBox3 failed") from exc
    if body is None:
        raise SolidWorksComError("CreateBodyFromBox3 returned None")
    return body


def _operations_cut(session: Any, target: Any, tool: Any) -> Any:
    """IBody2.Operations2(SWBODYCUT, tool, error)."""
    cut = _const(session, "SWBODYCUT", 1593)
    try:
        result = target.Operations2(cut, tool, 0)
    except TypeError:
        try:
            result = target.Operations2(cut, tool)
        except Exception as exc:
            raise _com_fail(exc, "IBody2.Operations2 cut failed") from exc
    except Exception as exc:
        raise _com_fail(exc, "IBody2.Operations2 cut failed") from exc
    if result is None:
        raise SolidWorksComError("Operations2 returned None")
    if isinstance(result, (list, tuple)):
        bodies = [body for body in result if body is not None]
    else:
        bodies = [result]
    if len(bodies) != 1:
        raise SolidWorksComError(
            f"Operations2 produced {len(bodies)} bodies, expected 1"
        )
    return bodies[0]


def _construct_box_minus_tetra(
    session: Any, model: Any, plan: ConstructionPlan
) -> None:
    spec = plan.box_minus_tetrahedron
    if spec is None:
        raise SolidWorksComError("missing box-minus-tetrahedron plan")
    modeler = session.get_modeler()
    box_body = _create_box_body(modeler, spec.box)
    tet_sheets = _sheet_body_from_face_indices(
        modeler, spec.cut.vertices_m, spec.cut.faces
    )
    tet_body = _knit_solid(session, modeler, _faces_from_sheets(tet_sheets))
    try:
        target = box_body.Copy()
    except Exception as exc:
        raise _com_fail(exc, "IBody2.Copy failed") from exc
    result = _operations_cut(session, target, tet_body)
    _persist_body(session, model, result)


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
        _construct_prism(session, model, plan.prism)
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
