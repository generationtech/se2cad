"""Optional printable block-edge treatment.

Equal-setback chamfer on convex manifold edges of a closed solid. Default
conversion does not apply it. The operation is identity-free: it consumes
a mesh, not a geometry_id allowlist, and it does not create a new subtype.

The CAD-neutral realization clips the solid by each convex edge's chamfer
half-space. That coincides with a local edge chamfer on the native
recipes and on convex solids. A later backend may use a local CAD chamfer
feature; it must still satisfy this module's measurable contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from se2cad.library.errors import TreatmentError
from se2cad.library.solid import (
    BoundsMm,
    SolidMesh,
    bounding_box,
    chamfer_plane,
    clip_solid_by_plane,
    mesh_edges,
    validate_solid,
    volume_times_6,
)

# Face setback, millimetres. Independent of grid pitch and of geometry_id.
EDGE_TREATMENT_SETBACK_MM = 50

# Treated volume must stay above this fraction of the untreated volume.
EDGE_TREATMENT_MIN_VOLUME_RATIO = 0.85


class EdgeTreatmentKind(str, Enum):
    """Authorized treatment kinds. Unknown values cannot be constructed."""

    OFF = "off"
    CHAMFER_EQUAL_SETBACK = "chamfer_equal_setback"


@dataclass(frozen=True)
class EdgeTreatmentRequest:
    """Explicit on/off request. Omission is not a request; default is off."""

    kind: EdgeTreatmentKind

    @property
    def enabled(self) -> bool:
        return self.kind is not EdgeTreatmentKind.OFF


EDGE_TREATMENT_OFF = EdgeTreatmentRequest(kind=EdgeTreatmentKind.OFF)
EDGE_TREATMENT_CHAMFER = EdgeTreatmentRequest(
    kind=EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK
)


@dataclass(frozen=True)
class EdgeTreatmentResult:
    """Measurable outcome of applying or declining the treatment."""

    solid: SolidMesh
    request: EdgeTreatmentRequest
    applied: bool
    convex_edge_count: int
    treated_edge_count: int
    volume_times_6: float
    bounding_box: BoundsMm


def apply_edge_treatment(
    solid: SolidMesh,
    request: EdgeTreatmentRequest | None = None,
) -> EdgeTreatmentResult:
    """Apply the optional treatment, or return the untreated solid.

    ``request=None`` and ``EDGE_TREATMENT_OFF`` are the default conversion
    path: the mesh is validated and returned unchanged.
    """
    chosen = EDGE_TREATMENT_OFF if request is None else request
    validate_solid(solid)
    edges = mesh_edges(solid)
    convex = tuple(edge for edge in edges if edge.convex)
    untreated_volume = volume_times_6(solid)
    untreated_bounds = bounding_box(solid)

    if not chosen.enabled:
        return EdgeTreatmentResult(
            solid=solid,
            request=chosen,
            applied=False,
            convex_edge_count=len(convex),
            treated_edge_count=0,
            volume_times_6=untreated_volume,
            bounding_box=untreated_bounds,
        )

    if chosen.kind is not EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK:
        raise TreatmentError(f"unsupported edge treatment {chosen.kind.value!r}")
    if not convex:
        raise TreatmentError("edge treatment requested but no convex edge exists")

    setback = EDGE_TREATMENT_SETBACK_MM
    shortest = min(edge.length_mm for edge in convex)
    if setback * 2 >= shortest:
        raise TreatmentError(
            "edge treatment setback consumes a convex edge; "
            f"setback_mm={setback} shortest_convex_mm={shortest}"
        )

    treated = solid
    for edge in convex:
        normal, origin = chamfer_plane(solid, edge, setback)
        treated = clip_solid_by_plane(treated, normal, origin)

    treated_volume = volume_times_6(treated)
    if treated_volume <= 0.0:
        raise TreatmentError("edge treatment destroyed the solid")
    if treated_volume >= untreated_volume:
        raise TreatmentError("edge treatment requested but volume did not decrease")
    ratio = treated_volume / untreated_volume
    if ratio < EDGE_TREATMENT_MIN_VOLUME_RATIO:
        raise TreatmentError(
            "edge treatment exceeds the volume-change bound; "
            f"ratio={ratio} min={EDGE_TREATMENT_MIN_VOLUME_RATIO}"
        )

    treated_bounds = bounding_box(treated)
    if not untreated_bounds.contains_bounds(treated_bounds):
        raise TreatmentError("treated solid left the untreated envelope")

    return EdgeTreatmentResult(
        solid=treated,
        request=chosen,
        applied=True,
        convex_edge_count=len(convex),
        treated_edge_count=len(convex),
        volume_times_6=treated_volume,
        bounding_box=treated_bounds,
    )
