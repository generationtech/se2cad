"""Durable leftover and expansion-honesty workflow (S2C-11.5.1).

Library-build metadata. Runtime lookup still uses the packaged catalog.
Failed generation, unclassified identities, and unsupported recipe kinds
cannot be reported as successful supported conversion. Residual
automatable topologies stay listed. Coverage is not universal.
This module does not invent M12 preflight or scan an install.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any

from se2cad.catalog.authorized import is_authorized_sdk_mesh_entry
from se2cad.catalog.errors import CatalogValidationError, UnknownSubtypeError
from se2cad.catalog.loader import checked_geometry_id, load_default_catalog
from se2cad.catalog.model import (
    CatalogEntry,
    DefinitionCatalog,
    ObservedIdentity,
    RecipeKind,
    SupportStatus,
)
from se2cad.catalog.selection import (
    ExceptionReason,
    GeometryClass,
    classify_observed,
    query_exception_records,
)
from se2cad.library.errors import UnknownGeometryError
from se2cad.library.lookup import lookup_recipe
from se2cad.library.model import NativeSolidRecipe, SdkMeshRecipe
from se2cad.library.recipes import (
    AUTOMATABLE_CUBE_TOPOLOGIES,
    recipe_for_topology,
)

LEFTOVER_SCHEMA_VERSION = 1
COVERAGE_CLAIM_NOT_UNIVERSAL = "not_universal_vanilla"
_PACKAGED_LEFTOVER_NAME = "leftover_set.json"
_REQUIRED_TOP_LEVEL = frozenset(
    {"schema_version", "coverage_claim", "completed_automatable", "leftovers"}
)
_REQUIRED_COMPLETED = frozenset({"subtype_id", "geometry_id", "cube_topology"})
_REQUIRED_LEFTOVER = frozenset(
    {
        "kind",
        "subtype_id",
        "geometry_id",
        "cube_topology",
        "detail",
        "reported_as_supported",
    }
)
_SMUGGLED_ASSET_MARKERS = (".mwm", ".fbx", ".dds", ".hkt")

# Evidenced residual automatable CubeTopology. Not a vanilla inventory.
EVIDENCED_RESIDUAL_TOPOLOGIES: frozenset[str] = frozenset({"Slope2Base"})


class LeftoverKind(str, Enum):
    """Why an identity or topology remains outside supported conversion."""

    LONG_TAIL = "long_tail"
    UNSUPPORTED_RECIPE_KIND = "unsupported_recipe_kind"
    UNCLASSIFIED = "unclassified"
    MISSING_CONSTRUCTION = "missing_construction"
    FAILED_GENERATION = "failed_generation"
    RESIDUAL_AUTOMATABLE = "residual_automatable"


@dataclass(frozen=True)
class GenerationOutcome:
    """One generation attempt. Failure cannot become supported conversion."""

    geometry_id: str
    succeeded: bool
    detail: str = ""


@dataclass(frozen=True)
class CompletedAutomatable:
    """Catalogued automatable identity that has a native construction."""

    subtype_id: str
    geometry_id: str
    cube_topology: str


@dataclass(frozen=True)
class LeftoverRecord:
    """Durable leftover. Must not be reported as supported conversion."""

    kind: LeftoverKind
    subtype_id: str
    geometry_id: str
    cube_topology: str
    detail: str
    reported_as_supported: bool
    exception_reason: ExceptionReason | None = None


@dataclass(frozen=True)
class LeftoverSet:
    """Repository leftover inventory plus the completed automatable remainder."""

    coverage_claim: str
    completed_automatable: tuple[CompletedAutomatable, ...]
    leftovers: tuple[LeftoverRecord, ...]


def default_leftover_path() -> Path:
    """Filesystem path of the packaged leftover set, when one exists."""
    return Path(str(files("se2cad.catalog").joinpath(_PACKAGED_LEFTOVER_NAME)))


def load_default_leftover_set() -> LeftoverSet:
    """Load the repository leftover set shipped with this package."""
    resource = files("se2cad.catalog").joinpath(_PACKAGED_LEFTOVER_NAME)
    try:
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise CatalogValidationError(
            f"packaged leftover set {_PACKAGED_LEFTOVER_NAME!r} is missing"
        ) from exc
    return load_leftover_text(text, source=_PACKAGED_LEFTOVER_NAME)


def load_leftover_text(text: str, *, source: str = "<string>") -> LeftoverSet:
    """Parse and validate leftover-set JSON text."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CatalogValidationError(
            f"{source}: leftover JSON is malformed: {exc}"
        ) from exc
    return _leftover_set_from_data(data, source=source)


def evaluate_leftover_set(
    catalog: DefinitionCatalog,
    *,
    observed_identities: tuple[ObservedIdentity, ...] | list[ObservedIdentity] = (),
    generation_outcomes: tuple[GenerationOutcome, ...] | list[GenerationOutcome] = (),
    residual_topologies: frozenset[str] | None = None,
) -> LeftoverSet:
    """Build leftover records from catalog, optional observations, and outcomes.

    Residual automatable topologies stay listed. Support is never granted.
    """
    leftovers: list[LeftoverRecord] = []
    completed: list[CompletedAutomatable] = []
    catalogued = {entry.subtype_id for entry in catalog.entries}
    failed_geometry = {
        outcome.geometry_id
        for outcome in generation_outcomes
        if not outcome.succeeded
    }
    failed_detail = {
        outcome.geometry_id: outcome.detail
        for outcome in generation_outcomes
        if not outcome.succeeded
    }

    for identity in observed_identities:
        if identity.subtype_id not in catalogued:
            leftovers.append(
                _record(
                    LeftoverKind.UNCLASSIFIED,
                    subtype_id=identity.subtype_id,
                    cube_topology=identity.observed.cube_topology or "",
                    detail="observed identity is not catalogued",
                )
            )

    for entry in catalog.entries:
        leftovers.extend(_leftovers_for_entry(entry, failed_geometry, failed_detail))
        if _is_completed_automatable(entry, failed_geometry):
            completed.append(
                CompletedAutomatable(
                    subtype_id=entry.subtype_id,
                    geometry_id=entry.geometry_id,
                    cube_topology=entry.observed.cube_topology or "",
                )
            )

    listed_topologies = {record.cube_topology for record in leftovers}
    residual = (
        EVIDENCED_RESIDUAL_TOPOLOGIES
        if residual_topologies is None
        else residual_topologies
    )
    for topology in sorted(residual):
        if topology in AUTOMATABLE_CUBE_TOPOLOGIES:
            continue
        if topology in listed_topologies:
            continue
        leftovers.append(
            _record(
                LeftoverKind.MISSING_CONSTRUCTION,
                cube_topology=topology,
                detail=(
                    "CubeTopology is automatable-class but has no native "
                    "construction"
                ),
            )
        )

    leftovers.extend(_generation_leftovers(catalog, failed_geometry, failed_detail))
    return LeftoverSet(
        coverage_claim=COVERAGE_CLAIM_NOT_UNIVERSAL,
        completed_automatable=tuple(completed),
        leftovers=_sorted_leftovers(leftovers),
    )


def stamp_automatable_remainder(
    catalog: DefinitionCatalog,
) -> tuple[NativeSolidRecipe, ...]:
    """Stamp native recipes for catalogued remainder identities.

    Only topologies with a construction are stamped. Residual topologies
    stay leftover. Support is not granted.
    """
    stamped = []
    for entry in catalog.entries:
        classification = classify_observed(entry.observed)
        if classification.geometry_class is not GeometryClass.AUTOMATABLE:
            continue
        topology = entry.observed.cube_topology
        if topology not in AUTOMATABLE_CUBE_TOPOLOGIES:
            continue
        try:
            lookup_recipe(entry.geometry_id)
        except UnknownGeometryError:
            stamped.append(recipe_for_topology(entry.geometry_id, topology))
    return tuple(stamped)


def conversion_may_report_supported(
    entry: CatalogEntry,
    leftover_set: LeftoverSet,
) -> bool:
    """Return True only when conversion may report this entry as supported.

    Failed generation, unclassified identities, long-tail records, missing
    constructions, and unsupported recipe kinds are exceptions.
    """
    if entry.support_status is not SupportStatus.SUPPORTED:
        return False
    if entry.recipe_kind is RecipeKind.UNSUPPORTED:
        return False
    if is_authorized_sdk_mesh_entry(entry):
        try:
            recipe = lookup_recipe(entry.geometry_id)
        except UnknownGeometryError:
            return False
        if not isinstance(recipe, SdkMeshRecipe):
            return False
        return not any(
            _matches_entry(entry, record) for record in leftover_set.leftovers
        )
    classification = classify_observed(entry.observed)
    if classification.geometry_class is GeometryClass.LONG_TAIL:
        return False
    topology = entry.observed.cube_topology
    if topology not in AUTOMATABLE_CUBE_TOPOLOGIES:
        return False
    try:
        lookup_recipe(entry.geometry_id)
    except UnknownGeometryError:
        return False
    return not any(_matches_entry(entry, record) for record in leftover_set.leftovers)


def assert_leftover_honesty(
    leftover_set: LeftoverSet,
    catalog: DefinitionCatalog,
) -> None:
    """Fail closed if a leftover can be reported as supported conversion."""
    if leftover_set.coverage_claim != COVERAGE_CLAIM_NOT_UNIVERSAL:
        raise CatalogValidationError(
            "leftover set must not claim universal vanilla coverage"
        )
    for record in leftover_set.leftovers:
        if record.reported_as_supported:
            raise CatalogValidationError(
                f"{_leftover_loc(record)}: leftover must not be reported "
                "as supported"
            )
        if record.kind is LeftoverKind.UNCLASSIFIED and record.subtype_id:
            try:
                catalog.lookup(record.subtype_id)
            except UnknownSubtypeError:
                continue
            raise CatalogValidationError(
                f"{record.subtype_id}: unclassified leftover is catalogued"
            )
        if not record.subtype_id:
            continue
        try:
            entry = catalog.lookup(record.subtype_id)
        except UnknownSubtypeError:
            continue
        if conversion_may_report_supported(entry, leftover_set):
            raise CatalogValidationError(
                f"{entry.subtype_id}: leftover cannot appear as supported "
                "conversion"
            )
        if entry.support_status is SupportStatus.SUPPORTED and record.kind in {
            LeftoverKind.LONG_TAIL,
            LeftoverKind.UNSUPPORTED_RECIPE_KIND,
            LeftoverKind.UNCLASSIFIED,
            LeftoverKind.FAILED_GENERATION,
        }:
            raise CatalogValidationError(
                f"{entry.subtype_id}: {record.kind.value} leftover must "
                "not be catalogued as supported"
            )


def assert_packaged_leftover_matches_catalog() -> LeftoverSet:
    """Require packaged leftover metadata to match live catalog evaluation."""
    catalog = load_default_catalog()
    packaged = load_default_leftover_set()
    evaluated = evaluate_leftover_set(catalog)
    if packaged != evaluated:
        raise CatalogValidationError(
            "packaged leftover set does not match catalog evaluation"
        )
    assert_leftover_honesty(packaged, catalog)
    for entry in catalog.entries:
        if entry.support_status is SupportStatus.SUPPORTED:
            if not conversion_may_report_supported(entry, packaged):
                raise CatalogValidationError(
                    f"{entry.subtype_id}: supported catalog entry cannot "
                    "report supported conversion"
                )
    for exception in query_exception_records(catalog):
        if exception.reported_as_supported:
            raise CatalogValidationError(
                f"{exception.subtype_id}: long-tail exception reported "
                "as supported"
            )
    return packaged


def _leftovers_for_entry(
    entry: CatalogEntry,
    failed_geometry: set[str],
    failed_detail: dict[str, str],
) -> list[LeftoverRecord]:
    topology = entry.observed.cube_topology or ""
    if is_authorized_sdk_mesh_entry(entry):
        try:
            recipe = lookup_recipe(entry.geometry_id)
        except UnknownGeometryError:
            return [
                _record(
                    LeftoverKind.UNSUPPORTED_RECIPE_KIND,
                    subtype_id=entry.subtype_id,
                    geometry_id=entry.geometry_id,
                    cube_topology=topology,
                    detail="authorized SDK-mesh identity has no library recipe",
                )
            ]
        if not isinstance(recipe, SdkMeshRecipe):
            return [
                _record(
                    LeftoverKind.UNSUPPORTED_RECIPE_KIND,
                    subtype_id=entry.subtype_id,
                    geometry_id=entry.geometry_id,
                    cube_topology=topology,
                    detail="authorized SDK-mesh identity is not an SDK recipe",
                )
            ]
        if entry.geometry_id in failed_geometry:
            return [
                _record(
                    LeftoverKind.FAILED_GENERATION,
                    subtype_id=entry.subtype_id,
                    geometry_id=entry.geometry_id,
                    cube_topology=topology,
                    detail=failed_detail.get(entry.geometry_id) or "generation failed",
                )
            ]
        return []
    classification = classify_observed(entry.observed)
    if classification.geometry_class is GeometryClass.LONG_TAIL:
        return [
            _record(
                LeftoverKind.LONG_TAIL,
                subtype_id=entry.subtype_id,
                geometry_id=entry.geometry_id,
                cube_topology=topology,
                detail=classification.decision_note,
                exception_reason=classification.exception_reason,
            )
        ]
    if entry.recipe_kind is RecipeKind.UNSUPPORTED:
        return [
            _record(
                LeftoverKind.UNSUPPORTED_RECIPE_KIND,
                subtype_id=entry.subtype_id,
                geometry_id=entry.geometry_id,
                cube_topology=topology,
                detail="recipe_kind unsupported cannot be supported conversion",
            )
        ]
    if topology not in AUTOMATABLE_CUBE_TOPOLOGIES:
        return [
            _record(
                LeftoverKind.MISSING_CONSTRUCTION,
                subtype_id=entry.subtype_id,
                geometry_id=entry.geometry_id,
                cube_topology=topology,
                detail=(
                    "CubeTopology is automatable-class but has no native "
                    "construction"
                ),
            )
        ]
    try:
        lookup_recipe(entry.geometry_id)
    except UnknownGeometryError:
        return [
            _record(
                LeftoverKind.RESIDUAL_AUTOMATABLE,
                subtype_id=entry.subtype_id,
                geometry_id=entry.geometry_id,
                cube_topology=topology,
                detail="automatable identity has no library recipe",
            )
        ]
    if entry.geometry_id in failed_geometry:
        return [
            _record(
                LeftoverKind.FAILED_GENERATION,
                subtype_id=entry.subtype_id,
                geometry_id=entry.geometry_id,
                cube_topology=topology,
                detail=failed_detail.get(entry.geometry_id) or "generation failed",
            )
        ]
    return []


def _generation_leftovers(
    catalog: DefinitionCatalog,
    failed_geometry: set[str],
    failed_detail: dict[str, str],
) -> list[LeftoverRecord]:
    catalogued_geometry = {entry.geometry_id for entry in catalog.entries}
    leftovers: list[LeftoverRecord] = []
    for geometry_id in sorted(failed_geometry):
        if geometry_id in catalogued_geometry:
            continue
        leftovers.append(
            _record(
                LeftoverKind.FAILED_GENERATION,
                geometry_id=geometry_id,
                detail=failed_detail.get(geometry_id) or "generation failed",
            )
        )
    return leftovers


def _is_completed_automatable(
    entry: CatalogEntry,
    failed_geometry: set[str],
) -> bool:
    if entry.geometry_id in failed_geometry:
        return False
    if entry.support_status is not SupportStatus.SUPPORTED:
        return False
    if entry.recipe_kind is RecipeKind.UNSUPPORTED:
        return False
    classification = classify_observed(entry.observed)
    if classification.geometry_class is not GeometryClass.AUTOMATABLE:
        return False
    topology = entry.observed.cube_topology
    if topology not in AUTOMATABLE_CUBE_TOPOLOGIES:
        return False
    try:
        lookup_recipe(entry.geometry_id)
    except UnknownGeometryError:
        return False
    return True


def _record(
    kind: LeftoverKind,
    *,
    subtype_id: str = "",
    geometry_id: str = "",
    cube_topology: str = "",
    detail: str,
    exception_reason: ExceptionReason | None = None,
) -> LeftoverRecord:
    if subtype_id:
        _reject_smuggled(subtype_id, "leftover.subtype_id")
    if geometry_id:
        checked_geometry_id(geometry_id, "leftover.geometry_id")
    if cube_topology:
        _reject_smuggled(cube_topology, "leftover.cube_topology")
    _reject_smuggled(detail, "leftover.detail")
    return LeftoverRecord(
        kind=kind,
        subtype_id=subtype_id,
        geometry_id=geometry_id,
        cube_topology=cube_topology,
        detail=detail,
        reported_as_supported=False,
        exception_reason=exception_reason,
    )


def _sorted_leftovers(records: list[LeftoverRecord]) -> tuple[LeftoverRecord, ...]:
    unique: dict[tuple[str, str, str, str], LeftoverRecord] = {}
    for record in records:
        key = (
            record.kind.value,
            record.subtype_id,
            record.geometry_id,
            record.cube_topology,
        )
        unique[key] = record
    return tuple(
        sorted(
            unique.values(),
            key=lambda record: (
                record.kind.value,
                record.subtype_id,
                record.geometry_id,
                record.cube_topology,
            ),
        )
    )


def _matches_entry(entry: CatalogEntry, record: LeftoverRecord) -> bool:
    if record.subtype_id and record.subtype_id == entry.subtype_id:
        return True
    if record.geometry_id and record.geometry_id == entry.geometry_id:
        return True
    return False


def _leftover_loc(record: LeftoverRecord) -> str:
    if record.subtype_id:
        return record.subtype_id
    if record.geometry_id:
        return record.geometry_id
    if record.cube_topology:
        return record.cube_topology
    return record.kind.value


def _leftover_set_from_data(data: Any, *, source: str) -> LeftoverSet:
    if not isinstance(data, dict):
        raise CatalogValidationError(f"{source}: leftover root must be an object")
    _require_keys(data, _REQUIRED_TOP_LEVEL, where=f"{source} root")
    version = data["schema_version"]
    if version != LEFTOVER_SCHEMA_VERSION:
        raise CatalogValidationError(
            f"{source}: unsupported schema_version {version!r}"
        )
    coverage = data["coverage_claim"]
    if coverage != COVERAGE_CLAIM_NOT_UNIVERSAL:
        raise CatalogValidationError(
            f"{source}: coverage_claim must be {COVERAGE_CLAIM_NOT_UNIVERSAL!r}"
        )
    raw_completed = data["completed_automatable"]
    raw_leftovers = data["leftovers"]
    if not isinstance(raw_completed, list):
        raise CatalogValidationError(
            f"{source}: completed_automatable must be an array"
        )
    if not isinstance(raw_leftovers, list):
        raise CatalogValidationError(f"{source}: leftovers must be an array")
    completed = tuple(
        _completed_from_data(raw, f"{source} completed_automatable[{index}]")
        for index, raw in enumerate(raw_completed)
    )
    leftovers = tuple(
        _leftover_from_data(raw, f"{source} leftovers[{index}]")
        for index, raw in enumerate(raw_leftovers)
    )
    leftover_set = LeftoverSet(
        coverage_claim=coverage,
        completed_automatable=completed,
        leftovers=leftovers,
    )
    for record in leftover_set.leftovers:
        if record.reported_as_supported:
            raise CatalogValidationError(
                f"{source}: leftover must not be reported as supported"
            )
    return leftover_set


def _completed_from_data(raw: Any, loc: str) -> CompletedAutomatable:
    if not isinstance(raw, dict):
        raise CatalogValidationError(f"{loc}: must be an object")
    _require_keys(raw, _REQUIRED_COMPLETED, where=loc)
    topology = _token(raw["cube_topology"], f"{loc}.cube_topology")
    return CompletedAutomatable(
        subtype_id=_token(raw["subtype_id"], f"{loc}.subtype_id"),
        geometry_id=checked_geometry_id(
            raw["geometry_id"], f"{loc}.geometry_id"
        ),
        cube_topology=topology,
    )


def _leftover_from_data(raw: Any, loc: str) -> LeftoverRecord:
    if not isinstance(raw, dict):
        raise CatalogValidationError(f"{loc}: must be an object")
    _require_keys(raw, _REQUIRED_LEFTOVER, where=loc)
    kind = _leftover_kind(raw["kind"], f"{loc}.kind")
    reported = raw["reported_as_supported"]
    if reported is not False:
        raise CatalogValidationError(
            f"{loc}.reported_as_supported: leftover must be false"
        )
    geometry_raw = raw["geometry_id"]
    geometry_id = ""
    if geometry_raw != "":
        geometry_id = checked_geometry_id(geometry_raw, f"{loc}.geometry_id")
    return LeftoverRecord(
        kind=kind,
        subtype_id=_optional_token(raw["subtype_id"], f"{loc}.subtype_id"),
        geometry_id=geometry_id,
        cube_topology=_optional_token(
            raw["cube_topology"], f"{loc}.cube_topology"
        ),
        detail=_token(raw["detail"], f"{loc}.detail"),
        reported_as_supported=False,
    )


def _leftover_kind(value: Any, loc: str) -> LeftoverKind:
    if not isinstance(value, str):
        raise CatalogValidationError(f"{loc}: kind must be a string")
    try:
        return LeftoverKind(value)
    except ValueError:
        raise CatalogValidationError(f"{loc}: unknown leftover kind {value!r}") from None


def _token(value: Any, loc: str) -> str:
    if not isinstance(value, str) or value == "":
        raise CatalogValidationError(f"{loc}: must be a non-empty string")
    _reject_smuggled(value, loc)
    return value


def _optional_token(value: Any, loc: str) -> str:
    if not isinstance(value, str):
        raise CatalogValidationError(f"{loc}: must be a string")
    if value == "":
        return ""
    _reject_smuggled(value, loc)
    return value


def _reject_smuggled(value: str, loc: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in _SMUGGLED_ASSET_MARKERS):
        raise CatalogValidationError(
            f"{loc}: proprietary asset reference is not allowed"
        )
    if "/" in value or "\\" in value or ":" in value:
        raise CatalogValidationError(f"{loc}: filesystem path is not allowed")


def _require_keys(
    raw: dict[str, Any],
    required: frozenset[str],
    *,
    where: str,
) -> None:
    missing = sorted(required.difference(raw))
    if missing:
        raise CatalogValidationError(
            f"{where}: missing required field(s): {', '.join(missing)}"
        )
    unexpected = sorted(set(raw).difference(required))
    if unexpected:
        raise CatalogValidationError(
            f"{where}: unexpected field(s): {', '.join(unexpected)}"
        )
