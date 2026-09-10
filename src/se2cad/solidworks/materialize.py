"""Demand-driven materialization of already-qualified canonical parts.

Assembly asks this module whether a library-bound geometry_id has a
qualified untreated builder and whether the exact
``{geometry_id}.SLDPRT`` already exists. It generates only missing
qualified identities. It does not stamp remainder recipes, scan a
game/SDK install, or expand catalog support.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.catalog.constants import FILLER_GEOMETRY_ID
from se2cad.catalog.model import RecipeKind
from se2cad.ir.model import CanonicalBlueprint
from se2cad.library import (
    EDGE_TREATMENT_OFF,
    EdgeTreatmentRequest,
    UnknownGeometryError,
    lookup_record,
)
from se2cad.solidworks.artifacts import (
    artifact_path_for,
    logical_part_filename,
    part_artifact_path,
)
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.errors import MissingCanonicalPartError
from se2cad.solidworks.placement import (
    demanded_treated_geometry_ids,
    missing_treated_geometry_ids,
)
from se2cad.solidworks.recipe_plan import plan_from_recipe


@dataclass(frozen=True)
class ArtifactMaterialization:
    """Reuse versus one-time generation for one artifact class."""

    reused: tuple[str, ...]
    generated: tuple[str, ...]


@dataclass(frozen=True)
class AssemblyMaterializationReport:
    """Narrow assembly materialization outcome.

    This is not catalog support, not a claim of universal vanilla
    coverage, and not a substitute for conversion-policy reporting.
    """

    untreated: ArtifactMaterialization
    treated: ArtifactMaterialization
    substituted_geometry_ids: tuple[str, ...]


def unique_geometry_ids(geometry_ids: tuple[str, ...]) -> tuple[str, ...]:
    """Preserve first-seen order and drop later duplicates."""
    return tuple(dict.fromkeys(geometry_ids))


def demanded_untreated_geometry_ids(ir: CanonicalBlueprint) -> tuple[str, ...]:
    """Unique library-bound geometry IDs whose untreated parts assembly needs."""
    return unique_geometry_ids(tuple(block.geometry_id for block in ir.grid.blocks))


def missing_untreated_geometry_ids(
    root: Path,
    geometry_ids: tuple[str, ...],
) -> tuple[str, ...]:
    """Return demanded IDs whose exact untreated ``{geometry_id}.SLDPRT`` is absent."""
    missing: list[str] = []
    for geometry_id in unique_geometry_ids(geometry_ids):
        path = artifact_path_for(root, geometry_id)
        if path.name != logical_part_filename(geometry_id):
            raise MissingCanonicalPartError(
                "untreated destination does not match the canonical "
                f"filename for geometry_id {geometry_id!r}"
            )
        if not path.is_file():
            missing.append(geometry_id)
    return tuple(missing)


def has_qualified_untreated_builder(geometry_id: str) -> bool:
    """True only for an existing library record with a constructible recipe.

    This is not catalog ``support_status``. Unknown identities, hidden
    round-armor aliases, and topologies without a library binding are
    false. The function does not stamp a new recipe.
    """
    try:
        record = lookup_record(geometry_id)
    except UnknownGeometryError:
        return False
    if record.recipe.recipe_kind is not RecipeKind.NATIVE_PROCEDURAL:
        return False
    try:
        plan_from_recipe(record.recipe)
    except TypeError:
        return False
    return True


def substituted_geometry_ids_from_ir(ir: CanonicalBlueprint) -> tuple[str, ...]:
    """Unique filler identities already assigned by conversion policy."""
    found = [
        block.geometry_id
        for block in ir.grid.blocks
        if block.geometry_id == FILLER_GEOMETRY_ID
    ]
    return unique_geometry_ids(tuple(found))


def _assert_usable_untreated_part(root: Path, geometry_id: str) -> Path:
    path = artifact_path_for(root, geometry_id)
    expected = logical_part_filename(geometry_id)
    if path.name != expected:
        raise MissingCanonicalPartError(
            "qualified untreated builder wrote a non-canonical path "
            f"for geometry_id {geometry_id!r}"
        )
    if not path.is_file():
        raise MissingCanonicalPartError(
            f"qualified untreated builder for geometry_id {geometry_id!r} "
            "produced no usable canonical part"
        )
    return path


def ensure_untreated_canonical_parts(
    config: SolidWorksBackendConfig,
    geometry_ids: tuple[str, ...],
) -> ArtifactMaterialization:
    """Reuse or generate exact untreated ``{geometry_id}.SLDPRT`` files.

    Generates only missing identities that already have a qualified
    builder. Existing files are not regenerated. Missing identities
    without a qualified builder fail closed; they are not replaced by
    the filler.
    """
    demanded = unique_geometry_ids(geometry_ids)
    reused: list[str] = []
    to_generate: list[str] = []
    for geometry_id in demanded:
        if not has_qualified_untreated_builder(geometry_id):
            raise MissingCanonicalPartError(
                f"geometry_id {geometry_id!r} has no qualified untreated "
                "builder; refusing to improvise a construction"
            )
        path = artifact_path_for(config.generated_root, geometry_id)
        if path.is_file():
            reused.append(geometry_id)
            continue
        to_generate.append(geometry_id)
    if to_generate:
        from se2cad.solidworks.generate import generate_canonical_parts

        generate_canonical_parts(
            config,
            treatment=EDGE_TREATMENT_OFF,
            geometry_ids=tuple(to_generate),
        )
        for geometry_id in to_generate:
            _assert_usable_untreated_part(config.generated_root, geometry_id)
    return ArtifactMaterialization(
        reused=tuple(reused),
        generated=tuple(to_generate),
    )


def ensure_treated_canonical_parts(
    config: SolidWorksBackendConfig,
    geometry_ids: tuple[str, ...],
    treatment: EdgeTreatmentRequest,
) -> ArtifactMaterialization:
    """Reuse or generate exact size-specific treated siblings.

    Does not regenerate untreated bases. Untreated assembly callers
    must not invoke this.
    """
    if not treatment.enabled:
        return ArtifactMaterialization(reused=(), generated=())
    demanded = unique_geometry_ids(geometry_ids)
    missing = missing_treated_geometry_ids(
        config.generated_root, demanded, treatment
    )
    reused = tuple(gid for gid in demanded if gid not in set(missing))
    if missing:
        from se2cad.solidworks.generate import generate_canonical_parts

        generate_canonical_parts(
            config, treatment=treatment, geometry_ids=missing
        )
        for geometry_id in missing:
            path = part_artifact_path(
                config.generated_root, geometry_id, treatment
            )
            if not path.is_file():
                raise MissingCanonicalPartError(
                    "qualified treated builder for geometry_id "
                    f"{geometry_id!r} produced no usable treated part"
                )
    return ArtifactMaterialization(reused=reused, generated=missing)


def materialize_required_parts(
    ir: CanonicalBlueprint,
    config: SolidWorksBackendConfig,
    treatment: EdgeTreatmentRequest,
) -> AssemblyMaterializationReport:
    """Ensure demanded untreated bases, then demanded treated siblings.

    Untreated assembly never generates chamfer siblings. Chamfer
    assembly does not regenerate an existing untreated base.
    """
    untreated = ensure_untreated_canonical_parts(
        config, demanded_untreated_geometry_ids(ir)
    )
    treated = ArtifactMaterialization(reused=(), generated=())
    if treatment.enabled:
        treated = ensure_treated_canonical_parts(
            config,
            demanded_treated_geometry_ids(ir, treatment),
            treatment,
        )
    return AssemblyMaterializationReport(
        untreated=untreated,
        treated=treated,
        substituted_geometry_ids=substituted_geometry_ids_from_ir(ir),
    )
