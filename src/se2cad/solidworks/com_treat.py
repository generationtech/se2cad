"""Apply the S2C-10.1.1 treatment as a local SolidWorks chamfer feature.

The backend does not invent a second frame. Convex edges are taken from
the CAD-neutral mesh and matched to live body edges. Concave edges are
not selected.
"""

from __future__ import annotations

import math
from typing import Any

from se2cad.library import (
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_SETBACK_MM,
    NativeSolidRecipe,
    apply_edge_treatment,
    mesh_edges,
    solid_from_recipe,
)
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.errors import SolidWorksComError
from se2cad.solidworks.units import mm_to_metres

# Looser than length-compare: matching recipe midpoints to live edges.
_EDGE_MATCH_TOLERANCE_M = 1e-4


def _com_fail(exc: BaseException, message: str) -> SolidWorksComError:
    return SolidWorksComError(f"{message}: {exc}")


def _const(session: Any, name: str, fallback: int) -> int:
    try:
        return int(getattr(session.constants, name))
    except Exception:
        return fallback


def _as_point3(raw: Any) -> tuple[float, float, float]:
    if raw is None:
        raise SolidWorksComError("edge vertex GetPoint returned None")
    values = tuple(float(v) for v in raw)
    if len(values) != 3:
        raise SolidWorksComError(
            f"edge vertex GetPoint returned {len(values)} values, expected 3"
        )
    return values[0], values[1], values[2]


def _edge_midpoint_m(edge: Any) -> tuple[float, float, float]:
    try:
        start = com_get(edge, "GetStartVertex")
        end = com_get(edge, "GetEndVertex")
        start_xyz = _as_point3(com_get(start, "GetPoint"))
        end_xyz = _as_point3(com_get(end, "GetPoint"))
    except SolidWorksComError:
        raise
    except Exception as exc:
        raise _com_fail(exc, "reading live edge endpoints failed") from exc
    return (
        (start_xyz[0] + end_xyz[0]) / 2.0,
        (start_xyz[1] + end_xyz[1]) / 2.0,
        (start_xyz[2] + end_xyz[2]) / 2.0,
    )


def _distance(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> float:
    return math.sqrt(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
    )


def _bodies(part: Any, body_type: int) -> list[Any]:
    try:
        raw = com_get(part, "GetBodies2", body_type, False)
    except Exception as exc:
        raise _com_fail(exc, "GetBodies2 failed") from exc
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [body for body in raw if body is not None]
    return [raw]


def _live_solid_edges(session: Any, model: Any) -> list[Any]:
    try:
        solid_type = session.constants.swSolidBody
    except Exception:
        solid_type = 0
    solids = _bodies(model, solid_type)
    if len(solids) != 1:
        raise SolidWorksComError(
            f"edge treatment requires one solid body, found {len(solids)}"
        )
    try:
        raw = com_get(solids[0], "GetEdges")
    except Exception as exc:
        raise _com_fail(exc, "GetEdges failed") from exc
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [edge for edge in raw if edge is not None]
    return [raw]


def _select_edge(edge: Any, *, append: bool) -> None:
    try:
        ok = edge.Select2(append, 0)
    except Exception as exc:
        raise _com_fail(exc, "Select2 of a live edge failed") from exc
    if not ok:
        raise SolidWorksComError("Select2 returned false for a convex edge")


def _match_convex_edges(
    recipe: NativeSolidRecipe,
    live_edges: list[Any],
) -> list[Any]:
    solid = solid_from_recipe(recipe)
    convex = tuple(edge for edge in mesh_edges(solid) if edge.convex)
    if not convex:
        raise SolidWorksComError("edge treatment requested but no convex edge exists")
    needed: list[tuple[tuple[float, float, float], int]] = []
    for index, edge in enumerate(convex):
        start = solid.vertices[edge.start]
        end = solid.vertices[edge.end]
        midpoint = (
            mm_to_metres((start[0] + end[0]) / 2.0),
            mm_to_metres((start[1] + end[1]) / 2.0),
            mm_to_metres((start[2] + end[2]) / 2.0),
        )
        needed.append((midpoint, index))

    pool = [(_edge_midpoint_m(edge), edge) for edge in live_edges]
    selected: list[Any] = []
    used: set[int] = set()
    for midpoint, _index in needed:
        matches = [
            (pool_index, edge)
            for pool_index, (live_mid, edge) in enumerate(pool)
            if pool_index not in used
            and _distance(live_mid, midpoint) <= _EDGE_MATCH_TOLERANCE_M
        ]
        if len(matches) != 1:
            raise SolidWorksComError(
                "could not uniquely match a convex recipe edge at "
                f"{midpoint} m (matches={len(matches)})"
            )
        pool_index, edge = matches[0]
        used.add(pool_index)
        selected.append(edge)
    if len(selected) != len(convex):
        raise SolidWorksComError(
            f"matched {len(selected)} live edges, expected {len(convex)}"
        )
    return selected


def _clear_selection(model: Any) -> None:
    try:
        model.ClearSelection2(True)
    except Exception as exc:
        raise _com_fail(exc, "ClearSelection2 failed") from exc


def _select_edges(edges: list[Any]) -> None:
    if not edges:
        raise SolidWorksComError("no edges selected for chamfer")
    for index, edge in enumerate(edges):
        _select_edge(edge, append=index > 0)


def _rebuild(model: Any) -> None:
    try:
        rebuilt = model.ForceRebuild3(False)
    except Exception as exc:
        raise _com_fail(exc, "ForceRebuild3 after chamfer failed") from exc
    if rebuilt is False:
        raise SolidWorksComError("ForceRebuild3 returned false after chamfer")


def _insert_equal_setback_chamfer(
    session: Any,
    model: Any,
    setback_m: float,
) -> Any:
    """IFeatureManager.InsertFeatureChamfer, 8 published arguments.

    Options, ChamferType, Width, Angle, OtherDist, VertexChamDist1–3.

    Live SolidWorks 2026 ``RevisionNumber`` 34.3.2: published
    ``swChamferEqualDistance`` (16) inserts a Chamfer feature that does
    not change volume even after ``ForceRebuild3``. Equal face setback
    is ``swChamferDistanceDistance`` (2) with Width and OtherDist both
    set to the named setback. Returns None when the selection includes
    a live-concave edge (InvCorner notch).
    """
    options = 0
    chamfer_type = _const(session, "swChamferDistanceDistance", 2)
    distance = float(setback_m)
    try:
        feature = model.FeatureManager.InsertFeatureChamfer(
            options,
            chamfer_type,
            distance,
            0.0,
            distance,
            0.0,
            0.0,
            0.0,
        )
    except Exception as exc:
        raise _com_fail(exc, "InsertFeatureChamfer failed") from exc
    if feature is None:
        return None
    _rebuild(model)
    return feature


def _face_normal(face: Any) -> tuple[float, float, float]:
    try:
        raw = com_get(face, "Normal")
    except Exception as exc:
        raise _com_fail(exc, "reading a face Normal failed") from exc
    if raw is None:
        raise SolidWorksComError("face Normal returned None")
    values = tuple(float(v) for v in raw)
    if len(values) != 3:
        raise SolidWorksComError(
            f"face Normal returned {len(values)} values, expected 3"
        )
    return values[0], values[1], values[2]


def _has_oblique_face(edge: Any) -> bool:
    """True when an incident face is not axis-aligned.

    Live InvCorner notch edges sit on the hypotenuse cut plane. A local
    chamfer of those concave edges returns None. Axis-aligned box,
    slope, and corner never reach this filter because the full convex
    set succeeds.
    """
    try:
        faces = com_get(edge, "GetTwoAdjacentFaces2")
    except Exception as exc:
        raise _com_fail(exc, "GetTwoAdjacentFaces2 failed") from exc
    if faces is None:
        return False
    if not isinstance(faces, (list, tuple)):
        faces = (faces,)
    for face in faces:
        if face is None:
            continue
        normal = _face_normal(face)
        significant = sum(1 for component in normal if abs(component) > 0.2)
        if significant >= 2:
            return True
    return False


def apply_equal_setback_chamfer(
    session: Any,
    model: Any,
    recipe: NativeSolidRecipe,
) -> int:
    """Chamfer live-convex recipe edges. Return the chamfered edge count.

    Concave live edges (the InvCorner notch) are skipped: a local CAD
    chamfer refuses them, which matches the S2C-10.1.1 concave rule.
    """
    preview = apply_edge_treatment(solid_from_recipe(recipe), EDGE_TREATMENT_CHAMFER)
    if not preview.applied:
        raise SolidWorksComError("CAD-neutral treatment was not applied")
    setback_m = mm_to_metres(EDGE_TREATMENT_SETBACK_MM)
    live_edges = _live_solid_edges(session, model)
    selected = _match_convex_edges(recipe, live_edges)
    _clear_selection(model)
    _select_edges(selected)
    feature = _insert_equal_setback_chamfer(session, model, setback_m)
    if feature is not None:
        return len(selected)

    filtered = [edge for edge in selected if not _has_oblique_face(edge)]
    if not filtered:
        raise SolidWorksComError(
            "InsertFeatureChamfer refused the convex set and no "
            "axis-aligned-face subset remains"
        )
    _clear_selection(model)
    _select_edges(filtered)
    feature = _insert_equal_setback_chamfer(session, model, setback_m)
    if feature is None:
        raise SolidWorksComError(
            "InsertFeatureChamfer returned None after excluding "
            "oblique-face (live-concave) edges"
        )
    return len(filtered)
