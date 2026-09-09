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
from se2cad.library import EDGE_TREATMENT_OFF, EdgeTreatmentRequest
from se2cad.parser.model import AppearanceSupport, ColorMaskHSV
from se2cad.solidworks.appearance import color_mask_hsv_to_rgb
from se2cad.solidworks.artifacts import (
    canonical_geometry_ids,
    logical_assembly_part_filename,
    part_artifact_path,
)
from se2cad.solidworks.errors import MissingCanonicalPartError, UnknownCanonicalPartError
from se2cad.transform.rotation import RotationMatrix


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


def placements_from_ir(
    ir: CanonicalBlueprint,
    treatment: EdgeTreatmentRequest | None = None,
) -> tuple[ComponentPlacement, ...]:
    """Preserve IR document order and exact block multiplicity.

    Default and ``EDGE_TREATMENT_OFF`` name untreated canonical parts.
    An explicit chamfer request names treated siblings. Geometry identity,
    component names, transforms, and appearance stay on the IR block.
    """
    allowed = set(canonical_geometry_ids())
    component_names_from_blocks(ir.grid.blocks)
    chosen = EDGE_TREATMENT_OFF if treatment is None else treatment
    placements: list[ComponentPlacement] = []
    for block in ir.grid.blocks:
        placements.append(_placement_from_block(block, allowed, chosen))
    return tuple(placements)


def _placement_from_block(
    block: CanonicalBlock,
    allowed: set[str],
    treatment: EdgeTreatmentRequest,
) -> ComponentPlacement:
    if block.geometry_id not in allowed:
        raise UnknownCanonicalPartError(
            f"no canonical assembly part for geometry_id {block.geometry_id!r}"
        )
    return ComponentPlacement(
        source_index=block.source_index,
        subtype_id=block.subtype_id,
        geometry_id=block.geometry_id,
        part_filename=logical_assembly_part_filename(block.geometry_id, treatment),
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
) -> dict[str, Path]:
    """Fail closed when a required generated SLDPRT is missing.

    Default looks up untreated ``{geometry_id}.SLDPRT``. An explicit
    chamfer request looks up ``{geometry_id}_chamfer.SLDPRT`` only and
    does not fall back to the untreated file.
    """
    chosen = EDGE_TREATMENT_OFF if treatment is None else treatment
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for geometry_id in canonical_geometry_ids():
        path = part_artifact_path(root, geometry_id, chosen)
        if chosen.enabled and path.name == logical_assembly_part_filename(
            geometry_id, EDGE_TREATMENT_OFF
        ):
            raise MissingCanonicalPartError(
                "treated assembly refused to resolve an untreated canonical part "
                f"for geometry_id {geometry_id!r}"
            )
        if not path.is_file():
            missing.append(path.name)
        else:
            resolved[geometry_id] = path
    if missing:
        if chosen.enabled:
            raise MissingCanonicalPartError(
                "treated part artifacts are missing from the generated root: "
                + ", ".join(missing)
                + "; generate them with python -m se2cad.solidworks "
                "--edge-treatment chamfer"
            )
        raise MissingCanonicalPartError(
            "canonical part artifacts are missing from the generated root: "
            + ", ".join(Path(name).stem for name in missing)
        )
    return resolved
