"""Geometry provenance and recipe-kind selection (S2C-11.3.1).

Library-build authoring. Runtime lookup still uses the packaged catalog.
This module does not import discovery or scan an install. Keen-mesh
recipe kinds stay forbidden except the one human-authorized S2C-11.7.1
catalog bind.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from se2cad.catalog.authorized import (
    AUTHORIZED_SDK_MESH_GEOMETRY_ID,
    AUTHORIZED_SDK_MESH_RECIPE_KIND,
    AUTHORIZED_SDK_MESH_SUBTYPE_ID,
    is_authorized_sdk_mesh_entry,
)
from se2cad.catalog.constants import CATALOG_CUBE_SIZE_LARGE
from se2cad.catalog.errors import CatalogValidationError
from se2cad.catalog.model import (
    CatalogEntry,
    DefinitionCatalog,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
)

# Observed tokens that identify CubeTopology-class cube blocks.
_CUBE_BLOCK_TOPOLOGY = "Cube"
_TRIANGLE_MESH_TOPOLOGY = "TriangleMesh"
_CUBE_BLOCK_TYPE_ID = "CubeBlock"

# Mesh recipe kinds would require Keen-derived CAD. Do not assign them.
_FORBIDDEN_MESH_RECIPE_KINDS = frozenset(
    {
        RecipeKind.SDK_MESH_DIRECT,
        RecipeKind.SDK_MESH_MANIFOLD,
    }
)


class GeometryClass(str, Enum):
    """Production class. CubeTopology armor vs long-tail exceptions."""

    AUTOMATABLE = "automatable"
    LONG_TAIL = "long_tail"


class ExceptionReason(str, Enum):
    """Why an identity is not in the automatable CubeTopology set."""

    TRIANGLE_MESH = "triangle_mesh"
    MISSING_CUBE_TOPOLOGY = "missing_cube_topology"
    UNUSUAL_BLOCK_TOPOLOGY = "unusual_block_topology"
    UNUSUAL_TYPE_ID = "unusual_type_id"
    SMALL_GRID_NOT_ACTIVATED = "small_grid_not_activated"


@dataclass(frozen=True)
class Classification:
    """Evidence-derived class and suggested recipe. Not a support grant."""

    geometry_class: GeometryClass
    recipe_kind: RecipeKind
    exception_reason: ExceptionReason | None
    observed_note: str
    decision_note: str


@dataclass(frozen=True)
class ProvenanceRecord:
    """What was observed and what SE2CAD decided for one identity."""

    subtype_id: str
    geometry_id: str
    observed: ObservedDefinition
    geometry_class: GeometryClass
    recipe_kind: RecipeKind
    support_status: SupportStatus
    exception_reason: ExceptionReason | None
    observed_note: str
    decision_note: str


@dataclass(frozen=True)
class ExceptionRecord:
    """Durable long-tail record. Must not be reported as supported."""

    subtype_id: str
    geometry_id: str
    reason: ExceptionReason
    detail: str
    reported_as_supported: bool


@dataclass(frozen=True)
class SelectionReport:
    """Selected catalog plus queryable provenance and exceptions."""

    catalog: DefinitionCatalog
    provenance: tuple[ProvenanceRecord, ...]
    exceptions: tuple[ExceptionRecord, ...]


def classify_observed(observed: ObservedDefinition) -> Classification:
    """Classify observed definition facts into automatable vs long-tail.

    CubeTopology-class ``CubeBlock`` armor is the automatable majority
    (``native_procedural``). TriangleMesh and unusual relationships are
    long-tail ``unsupported``. Support is never granted here.
    """
    observed_note = (
        f"type_id={observed.type_id} cube_size={observed.cube_size} "
        f"occupancy={observed.size.x}x{observed.size.y}x{observed.size.z} "
        f"block_topology={observed.block_topology} "
        f"cube_topology={observed.cube_topology!s}"
    )
    if observed.cube_size != CATALOG_CUBE_SIZE_LARGE:
        return _long_tail(
            ExceptionReason.SMALL_GRID_NOT_ACTIVATED,
            observed_note,
            "Small Grid is not activated",
        )
    if observed.block_topology == _TRIANGLE_MESH_TOPOLOGY:
        return _long_tail(
            ExceptionReason.TRIANGLE_MESH,
            observed_note,
            "TriangleMesh is long-tail, not a CubeTopology recipe",
        )
    if observed.block_topology != _CUBE_BLOCK_TOPOLOGY:
        return _long_tail(
            ExceptionReason.UNUSUAL_BLOCK_TOPOLOGY,
            observed_note,
            "block_topology is not CubeTopology-class Cube",
        )
    if observed.cube_topology is None:
        return _long_tail(
            ExceptionReason.MISSING_CUBE_TOPOLOGY,
            observed_note,
            "Cube block without CubeTopology is not automatable",
        )
    if observed.type_id != _CUBE_BLOCK_TYPE_ID:
        return _long_tail(
            ExceptionReason.UNUSUAL_TYPE_ID,
            observed_note,
            "CubeTopology on a non-CubeBlock type is an unusual relationship",
        )
    return Classification(
        geometry_class=GeometryClass.AUTOMATABLE,
        recipe_kind=RecipeKind.NATIVE_PROCEDURAL,
        exception_reason=None,
        observed_note=observed_note,
        decision_note=(
            "CubeTopology-class CubeBlock armor; recipe_kind "
            "native_procedural; support is not implied"
        ),
    )


def select_catalog_recipes(catalog: DefinitionCatalog) -> SelectionReport:
    """Assign recipe kinds from evidence and record provenance.

    Existing ``supported`` status is preserved only when classification
    remains automatable, except the one authorized S2C-11.7.1 SDK-mesh
    bind. New support is never granted. Other mesh recipe kinds are
    rejected.
    """
    selected = tuple(
        _apply_classification(entry, classify_observed(entry.observed))
        for entry in catalog.entries
    )
    return _inspect_catalog(DefinitionCatalog(entries=selected))


def query_exception_records(
    catalog: DefinitionCatalog,
) -> tuple[ExceptionRecord, ...]:
    """Return long-tail exception records for catalogued identities."""
    return _inspect_catalog(catalog).exceptions


def provenance_records(
    catalog: DefinitionCatalog,
) -> tuple[ProvenanceRecord, ...]:
    """Return observed-vs-decided provenance for catalogued identities."""
    return _inspect_catalog(catalog).provenance


def _inspect_catalog(catalog: DefinitionCatalog) -> SelectionReport:
    provenance: list[ProvenanceRecord] = []
    exceptions: list[ExceptionRecord] = []
    for entry in catalog.entries:
        record = _provenance_for(entry, classify_observed(entry.observed))
        provenance.append(record)
        exception = _exception_for(record)
        if exception is not None:
            exceptions.append(exception)
    return SelectionReport(
        catalog=catalog,
        provenance=tuple(provenance),
        exceptions=tuple(exceptions),
    )


def _apply_classification(
    entry: CatalogEntry,
    classification: Classification,
) -> CatalogEntry:
    if is_authorized_sdk_mesh_entry(entry):
        return entry
    if (
        entry.recipe_kind in _FORBIDDEN_MESH_RECIPE_KINDS
        or classification.recipe_kind in _FORBIDDEN_MESH_RECIPE_KINDS
    ):
        raise CatalogValidationError(
            f"{entry.subtype_id}: recipe_kind would require Keen-derived "
            "CAD; stop for ADR-004"
        )
    if (
        entry.support_status is SupportStatus.SUPPORTED
        and classification.geometry_class is GeometryClass.LONG_TAIL
    ):
        raise CatalogValidationError(
            f"{entry.subtype_id}: long-tail identity must not be supported"
        )
    if entry.recipe_kind is RecipeKind.UNSUPPORTED:
        return replace(entry, recipe_kind=classification.recipe_kind)
    if entry.recipe_kind is classification.recipe_kind:
        return entry
    raise CatalogValidationError(
        f"{entry.subtype_id}: recorded recipe_kind "
        f"{entry.recipe_kind.value!r} conflicts with classified "
        f"{classification.recipe_kind.value!r}"
    )


def _provenance_for(
    entry: CatalogEntry,
    classification: Classification,
) -> ProvenanceRecord:
    if is_authorized_sdk_mesh_entry(entry):
        return ProvenanceRecord(
            subtype_id=entry.subtype_id,
            geometry_id=entry.geometry_id,
            observed=entry.observed,
            geometry_class=classification.geometry_class,
            recipe_kind=entry.recipe_kind,
            support_status=entry.support_status,
            exception_reason=classification.exception_reason,
            observed_note=classification.observed_note,
            decision_note=(
                "authorized S2C-11.7.1 single-identity SDK-mesh bind; "
                "not general mesh support"
            ),
        )
    if (
        entry.support_status is SupportStatus.SUPPORTED
        and classification.geometry_class is GeometryClass.LONG_TAIL
    ):
        raise CatalogValidationError(
            f"{entry.subtype_id}: long-tail identity must not be supported"
        )
    return ProvenanceRecord(
        subtype_id=entry.subtype_id,
        geometry_id=entry.geometry_id,
        observed=entry.observed,
        geometry_class=classification.geometry_class,
        recipe_kind=entry.recipe_kind,
        support_status=entry.support_status,
        exception_reason=classification.exception_reason,
        observed_note=classification.observed_note,
        decision_note=classification.decision_note,
    )


def _exception_for(record: ProvenanceRecord) -> ExceptionRecord | None:
    if (
        record.subtype_id == AUTHORIZED_SDK_MESH_SUBTYPE_ID
        and record.geometry_id == AUTHORIZED_SDK_MESH_GEOMETRY_ID
        and record.recipe_kind is AUTHORIZED_SDK_MESH_RECIPE_KIND
        and record.support_status is SupportStatus.SUPPORTED
    ):
        return None
    if record.geometry_class is not GeometryClass.LONG_TAIL:
        return None
    if record.exception_reason is None:
        raise CatalogValidationError(
            f"{record.subtype_id}: long-tail record is missing a reason"
        )
    if record.support_status is SupportStatus.SUPPORTED:
        raise CatalogValidationError(
            f"{record.subtype_id}: long-tail identity must not be supported"
        )
    return ExceptionRecord(
        subtype_id=record.subtype_id,
        geometry_id=record.geometry_id,
        reason=record.exception_reason,
        detail=record.decision_note,
        reported_as_supported=False,
    )


def _long_tail(
    reason: ExceptionReason,
    observed_note: str,
    decision_note: str,
) -> Classification:
    return Classification(
        geometry_class=GeometryClass.LONG_TAIL,
        recipe_kind=RecipeKind.UNSUPPORTED,
        exception_reason=reason,
        observed_note=observed_note,
        decision_note=decision_note,
    )
