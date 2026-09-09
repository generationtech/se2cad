"""Backend-independent assembly placements from a qualified canonical IR.

Each IR block becomes exactly one placement. Geometry identity, multiplicity,
rotation, and millimetre translation are taken from the IR without
reinterpretation. SolidWorks COM types are not used here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.ir.model import CanonicalBlock, CanonicalBlueprint
from se2cad.ir.naming import component_name_from_block, component_names_from_blocks
from se2cad.library import (
    EDGE_TREATMENT_OFF,
    EdgeTreatmentKind,
    EdgeTreatmentRequest,
    UnknownGeometryError,
    geometry_supports_chamfer,
    lookup_recipe,
)
from se2cad.parser.model import AppearanceSupport, ColorMaskHSV
from se2cad.solidworks.appearance import color_mask_hsv_to_rgb
from se2cad.solidworks.artifacts import (
    canonical_geometry_ids,
    is_treated_artifact_filename,
    logical_assembly_part_filename,
    logical_part_filename,
    part_artifact_path,
)
from se2cad.solidworks.errors import MissingCanonicalPartError, UnknownCanonicalPartError
from se2cad.transform.rotation import RotationMatrix

CHAMFER_UNAVAILABLE_REASON = "geometry is not chamfer-capable"


@dataclass(frozen=True)
class ChamferFallback:
    """One blueprint instance that could not receive requested chamfer."""

    source_index: int
    subtype_id: str
    geometry_id: str
    requested_setback_mm: float
    reason: str


@dataclass(frozen=True)
class AssemblyTreatmentReport:
    """Assembly-level treatment outcome. Not a claim of full treatment."""

    requested_kind: str
    requested_setback_mm: float | None
    treated_component_count: int
    untreated_fallback_component_count: int
    fallbacks: tuple[ChamferFallback, ...]


@dataclass(frozen=True)
class ComponentPlacement:
    """One IR instance ready for CAD insertion."""

    source_index: int
    subtype_id: str
    geometry_id: str
    part_filename: str
    component_name: str
    grid_min: tuple[int, int, int]
    position_mm: tuple[int, int, int]
    rotation: RotationMatrix
    orientation_serialized: bool
    color_mask_hsv: ColorMaskHSV
    appearance_support: AppearanceSupport
    appearance_rgb: tuple[float, float, float]


def resolved_assembly_part_filename(
    geometry_id: str,
    request: EdgeTreatmentRequest,
) -> str:
    """Assembly filename for one geometry under a treatment request.

    Chamfer-capable geometries use the size-specific treated sibling.
    Non-capable geometries keep the untreated canonical name. This is
    not catalog support and does not change ``geometry_id``.
    """
    if not request.enabled:
        return logical_part_filename(geometry_id)
    if geometry_supports_chamfer(geometry_id):
        return logical_assembly_part_filename(geometry_id, request)
    return logical_part_filename(geometry_id)


def treatment_report_from_ir(
    ir: CanonicalBlueprint,
    treatment: EdgeTreatmentRequest | None = None,
) -> AssemblyTreatmentReport:
    """Structured fallback report for the requested assembly treatment."""
    chosen = EDGE_TREATMENT_OFF if treatment is None else treatment
    if not chosen.enabled:
        return AssemblyTreatmentReport(
            requested_kind=EdgeTreatmentKind.OFF.value,
            requested_setback_mm=None,
            treated_component_count=0,
            untreated_fallback_component_count=0,
            fallbacks=(),
        )
    fallbacks: list[ChamferFallback] = []
    treated = 0
    for block in ir.grid.blocks:
        if geometry_supports_chamfer(block.geometry_id):
            treated += 1
            continue
        fallbacks.append(
            ChamferFallback(
                source_index=block.source_index,
                subtype_id=block.subtype_id,
                geometry_id=block.geometry_id,
                requested_setback_mm=chosen.setback_mm,
                reason=CHAMFER_UNAVAILABLE_REASON,
            )
        )
    return AssemblyTreatmentReport(
        requested_kind="chamfer",
        requested_setback_mm=chosen.setback_mm,
        treated_component_count=treated,
        untreated_fallback_component_count=len(fallbacks),
        fallbacks=tuple(fallbacks),
    )


def demanded_treated_geometry_ids(
    ir: CanonicalBlueprint,
    treatment: EdgeTreatmentRequest | None = None,
) -> tuple[str, ...]:
    """Unique chamfer-capable geometry IDs required by this blueprint."""
    chosen = EDGE_TREATMENT_OFF if treatment is None else treatment
    if not chosen.enabled:
        return ()
    seen: list[str] = []
    for block in ir.grid.blocks:
        if block.geometry_id in seen:
            continue
        if geometry_supports_chamfer(block.geometry_id):
            seen.append(block.geometry_id)
    return tuple(seen)


def missing_treated_geometry_ids(
    root: Path,
    geometry_ids: tuple[str, ...],
    treatment: EdgeTreatmentRequest,
) -> tuple[str, ...]:
    """Return demanded IDs whose exact size-specific treated file is absent."""
    if not treatment.enabled:
        return ()
    missing: list[str] = []
    for geometry_id in geometry_ids:
        path = part_artifact_path(root, geometry_id, treatment)
        if not path.is_file():
            missing.append(geometry_id)
    return tuple(missing)


def placements_from_ir(
    ir: CanonicalBlueprint,
    treatment: EdgeTreatmentRequest | None = None,
) -> tuple[ComponentPlacement, ...]:
    """Preserve IR document order and exact block multiplicity.

    Default and ``EDGE_TREATMENT_OFF`` name untreated canonical parts.
    An explicit chamfer request names size-specific treated siblings for
    chamfer-capable geometry and untreated parts for the rest. Geometry
    identity, component names, transforms, and appearance stay on the IR
    block.
    """
    component_names_from_blocks(ir.grid.blocks)
    chosen = EDGE_TREATMENT_OFF if treatment is None else treatment
    placements: list[ComponentPlacement] = []
    for block in ir.grid.blocks:
        placements.append(_placement_from_block(block, chosen))
    return tuple(placements)


def _placement_from_block(
    block: CanonicalBlock,
    treatment: EdgeTreatmentRequest,
) -> ComponentPlacement:
    try:
        lookup_recipe(block.geometry_id)
    except UnknownGeometryError as exc:
        raise UnknownCanonicalPartError(
            f"no canonical assembly part for geometry_id {block.geometry_id!r}"
        ) from exc
    return ComponentPlacement(
        source_index=block.source_index,
        subtype_id=block.subtype_id,
        geometry_id=block.geometry_id,
        part_filename=resolved_assembly_part_filename(block.geometry_id, treatment),
        component_name=component_name_from_block(block),
        grid_min=(block.grid_min.x, block.grid_min.y, block.grid_min.z),
        position_mm=block.position_mm.as_tuple(),
        rotation=block.rotation,
        orientation_serialized=block.orientation_serialized,
        color_mask_hsv=block.color_mask_hsv,
        appearance_support=block.appearance_support,
        appearance_rgb=color_mask_hsv_to_rgb(block.color_mask_hsv),
    )


def require_canonical_part_files(
    root: Path,
    treatment: EdgeTreatmentRequest | None = None,
    geometry_ids: tuple[str, ...] | None = None,
) -> dict[str, Path]:
    """Fail closed when a required generated SLDPRT is missing.

    Default looks up untreated ``{geometry_id}.SLDPRT``. An explicit
    chamfer request looks up the exact size-specific treated sibling for
    chamfer-capable geometry and the untreated file only for geometries
    that are not chamfer-capable. Capable geometry never silently uses
    untreated parts or the historical generic ``*_chamfer.SLDPRT`` name.
    ``geometry_ids`` defaults to the four initial-program identities.
    """
    chosen = EDGE_TREATMENT_OFF if treatment is None else treatment
    requested = canonical_geometry_ids() if geometry_ids is None else geometry_ids
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for geometry_id in requested:
        filename = resolved_assembly_part_filename(geometry_id, chosen)
        capable = geometry_supports_chamfer(geometry_id)
        if chosen.enabled and capable:
            expected = logical_assembly_part_filename(geometry_id, chosen)
            if filename != expected or not is_treated_artifact_filename(filename):
                raise MissingCanonicalPartError(
                    "treated assembly refused to resolve an untreated or "
                    f"generic chamfer artifact for geometry_id {geometry_id!r}"
                )
            path = part_artifact_path(root, geometry_id, chosen)
            if path.name != expected:
                raise MissingCanonicalPartError(
                    "treated destination does not match the requested "
                    f"size-specific artifact for geometry_id {geometry_id!r}"
                )
        else:
            path = part_artifact_path(root, geometry_id, EDGE_TREATMENT_OFF)
            if path.name != logical_part_filename(geometry_id):
                raise MissingCanonicalPartError(
                    "untreated assembly refused a non-canonical part "
                    f"for geometry_id {geometry_id!r}"
                )
        if not path.is_file():
            missing.append(path.name)
        else:
            resolved[geometry_id] = path
    if missing:
        if chosen.enabled and any(is_treated_artifact_filename(name) for name in missing):
            raise MissingCanonicalPartError(
                "treated part artifacts are missing from the generated root: "
                + ", ".join(missing)
                + "; assemble with --edge-treatment chamfer generates only "
                "the demanded size-specific siblings"
            )
        raise MissingCanonicalPartError(
            "canonical part artifacts are missing from the generated root: "
            + ", ".join(Path(name).stem for name in missing)
        )
    return resolved
