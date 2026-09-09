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

import math
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
# Used when chamfer is requested without an explicit size.
EDGE_TREATMENT_SETBACK_MM = 50

# Inclusive operator-validated range for a requested chamfer size.
CHAMFER_SETBACK_MIN_MM = 5
CHAMFER_SETBACK_MAX_MM = 250

# Treated volume must stay above this fraction of the untreated volume.
EDGE_TREATMENT_MIN_VOLUME_RATIO = 0.85


class EdgeTreatmentKind(str, Enum):
    """Authorized treatment kinds. Unknown values cannot be constructed."""

    OFF = "off"
    CHAMFER_EQUAL_SETBACK = "chamfer_equal_setback"


def validate_chamfer_setback_mm(value: float) -> float:
    """Accept a finite setback in ``[5, 250]`` mm. Do not clamp."""
    try:
        setback = float(value)
    except (TypeError, ValueError) as exc:
        raise TreatmentError("chamfer setback must be a finite number of millimetres") from exc
    if not math.isfinite(setback):
        raise TreatmentError("chamfer setback must be a finite number of millimetres")
    if setback < CHAMFER_SETBACK_MIN_MM or setback > CHAMFER_SETBACK_MAX_MM:
        raise TreatmentError(
            "chamfer setback must be between "
            f"{CHAMFER_SETBACK_MIN_MM} and {CHAMFER_SETBACK_MAX_MM} mm inclusive, "
            f"got {setback}"
        )
    return float(setback)


def parse_chamfer_mm_token(raw: str) -> float:
    """Parse an operator-supplied ``--chamfer-mm`` token. Do not clamp."""
    text = raw.strip()
    if not text:
        raise TreatmentError("chamfer setback must be a finite number of millimetres")
    try:
        value = float(text)
    except ValueError as exc:
        raise TreatmentError("chamfer setback must be a finite number of millimetres") from exc
    return validate_chamfer_setback_mm(value)


def chamfer_size_token(setback_mm: float) -> str:
    """Deterministic size token used in treated artifact names and keys.

    Integer-valued sizes use ``50mm``. Non-integers use a decimal token
    produced from the validated number, never from a raw path string.
    """
    mm = validate_chamfer_setback_mm(setback_mm)
    if mm == int(mm):
        return f"{int(mm)}mm"
    text = format(mm, ".9f").rstrip("0").rstrip(".")
    if not text or any(sep in text for sep in ("/", "\\", ":", "..")):
        raise TreatmentError(f"chamfer size token is not a safe filename fragment: {text!r}")
    return f"{text}mm"


def chamfer_treatment(setback_mm: float | None = None) -> EdgeTreatmentRequest:
    """Equal-setback chamfer request. Omitted size is the default 50 mm."""
    mm = EDGE_TREATMENT_SETBACK_MM if setback_mm is None else setback_mm
    return EdgeTreatmentRequest(
        kind=EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK,
        setback_mm=validate_chamfer_setback_mm(mm),
    )


@dataclass(frozen=True)
class EdgeTreatmentRequest:
    """Explicit on/off request. Omission is not a request; default is off.

    ``setback_mm`` is meaningful only when the kind is chamfer. Invalid
    sizes fail closed; they are not clamped.
    """

    kind: EdgeTreatmentKind
    setback_mm: float = EDGE_TREATMENT_SETBACK_MM

    def __post_init__(self) -> None:
        if self.kind is EdgeTreatmentKind.OFF:
            return
        if self.kind is not EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK:
            raise TreatmentError(f"unsupported edge treatment {self.kind.value!r}")
        object.__setattr__(self, "setback_mm", validate_chamfer_setback_mm(self.setback_mm))

    @property
    def enabled(self) -> bool:
        return self.kind is not EdgeTreatmentKind.OFF


EDGE_TREATMENT_OFF = EdgeTreatmentRequest(kind=EdgeTreatmentKind.OFF)
EDGE_TREATMENT_CHAMFER = chamfer_treatment()


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

    setback = validate_chamfer_setback_mm(chosen.setback_mm)
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
