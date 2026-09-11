"""Compute a CAD-neutral compatibility survey from existing pipeline facts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional

from se2cad.catalog import DefinitionCatalog, load_default_catalog
from se2cad.parser.model import ParsedBlueprint
from se2cad.statistics.compute import compute_blueprint_statistics
from se2cad.survey.classify import classify_root_cause, outcome_from_resolve
from se2cad.survey.evidence import collect_identity_evidence
from se2cad.parser.model import GridSize
from se2cad.survey.intake import extract_survey_blocks, load_survey_blueprint
from se2cad.survey.model import (
    CauseImpact,
    CompatibilityOutcome,
    CompatibilitySurvey,
    CumulativeCoverage,
    ExtractedSurveyBlock,
    IdentityClassification,
    RootCause,
    StructuralSurvey,
)
from se2cad.vanilla.resolve import VanillaResolveKind, resolve_vanilla_geometry
from se2cad.vanilla.roots import try_load_game_content_root, try_load_sdk_root
from se2cad.statistics.model import NamedCount


def compute_compatibility_survey_from_path(
    path: str | Path,
    catalog: Optional[DefinitionCatalog] = None,
) -> CompatibilitySurvey:
    """Inspect one operator-selected document and classify its identities."""
    structural, parsed = load_survey_blueprint(path)
    return compute_compatibility_survey(
        structural,
        parsed,
        catalog or load_default_catalog(),
    )


def compute_compatibility_survey(
    structural: StructuralSurvey,
    parsed: ParsedBlueprint | None,
    catalog: DefinitionCatalog,
) -> CompatibilitySurvey:
    """Classify identities from a parsed blueprint when one exists."""
    game_root = try_load_game_content_root()
    sdk_root = try_load_sdk_root()
    parser_warnings: list[str] = []
    if structural.wrapped_for_parser:
        parser_warnings.append(
            "official Prefab XML was wrapped to ShipBlueprint for the "
            "existing parser; production parse of Prefabs is unchanged"
        )
    if structural.has_multiple_grids:
        parser_warnings.append(
            f"document contains {structural.grid_count} CubeGrid elements"
        )
    if structural.has_non_large_grid:
        parser_warnings.append("document contains non-Large Grid content")
    if structural.parser_error:
        parser_warnings.append(structural.parser_error)

    extracted = extract_survey_blocks(structural.source_path)
    if parsed is None:
        if extracted:
            parser_warnings.append(
                "production parse failed; survey classified extracted "
                "CubeBlocks without granting parser support"
            )
            return _survey_from_extracted(
                structural,
                extracted,
                catalog,
                game_root,
                sdk_root,
                tuple(parser_warnings),
            )
        return _unparsed_survey(structural, parser_warnings)

    counts: Counter[str] = Counter()
    builders: dict[str, str] = {}
    for block in parsed.grid.blocks:
        key = _identity_key(block)
        counts[key] += 1
        builders[key] = block.object_builder_type
    identities = [
        _classified_identity(
            key if not key.startswith("(empty SubtypeName)/") else "",
            counts[key],
            catalog,
            game_root,
            sdk_root,
            object_builder_type=builders[key],
            report_subtype_id=key,
        )
        for key in sorted(counts)
    ]

    stats = compute_blueprint_statistics(parsed, catalog)
    extents = None
    millimetres = None
    if stats.cell_extents is not None and stats.millimetre_size is not None:
        extents = (
            f"x[{stats.cell_extents.x.minimum}..{stats.cell_extents.x.maximum}] "
            f"y[{stats.cell_extents.y.minimum}..{stats.cell_extents.y.maximum}] "
            f"z[{stats.cell_extents.z.minimum}..{stats.cell_extents.z.maximum}]"
        )
        millimetres = (
            f"{stats.millimetre_size.x} x {stats.millimetre_size.y} x "
            f"{stats.millimetre_size.z}"
        )
    return _assemble_survey(
        structural=structural,
        parsed_grid_size=parsed.grid.grid_size,
        block_count=len(parsed.grid.blocks),
        identities=tuple(identities),
        subtype_counts=tuple(
            NamedCount(name=name, count=counts[name]) for name in sorted(counts)
        ),
        cell_extents=extents,
        millimetre_size=millimetres,
        parser_warnings=tuple(parser_warnings),
    )


def _survey_from_extracted(
    structural: StructuralSurvey,
    extracted: tuple[ExtractedSurveyBlock, ...],
    catalog: DefinitionCatalog,
    game_root,
    sdk_root,
    parser_warnings: tuple[str, ...],
) -> CompatibilitySurvey:
    counts: Counter[str] = Counter()
    empty_builders: dict[str, str] = {}
    mins: set[tuple[int, int, int]] = set()
    for block in extracted:
        key = _identity_key(block)
        counts[key] += 1
        if block.subtype_id == "":
            empty_builders[key] = block.object_builder_type
        if (
            block.min_x is not None
            and block.min_y is not None
            and block.min_z is not None
        ):
            mins.add((block.min_x, block.min_y, block.min_z))
    identities = []
    for key in sorted(counts):
        if key in empty_builders:
            identities.append(
                _classified_identity(
                    "",
                    counts[key],
                    catalog,
                    game_root,
                    sdk_root,
                    object_builder_type=empty_builders[key],
                    report_subtype_id=key,
                )
            )
            continue
        identities.append(
            _classified_identity(
                key,
                counts[key],
                catalog,
                game_root,
                sdk_root,
            )
        )
    extents, millimetres = _extents_from_mins(mins, catalog.large_grid_cell_pitch_mm)
    parsed_size = None
    if structural.grids and all(grid.grid_size == "Large" for grid in structural.grids):
        parsed_size = GridSize.LARGE
    return _assemble_survey(
        structural=structural,
        parsed_grid_size=parsed_size,
        block_count=len(extracted),
        identities=tuple(identities),
        subtype_counts=tuple(
            NamedCount(name=name, count=counts[name]) for name in sorted(counts)
        ),
        cell_extents=extents,
        millimetre_size=millimetres,
        parser_warnings=parser_warnings,
    )


def _identity_key(block: ExtractedSurveyBlock | object) -> str:
    subtype_id = getattr(block, "subtype_id", "")
    if subtype_id:
        return subtype_id
    return f"(empty SubtypeName)/{getattr(block, 'object_builder_type')}"


def _classified_identity(
    subtype_id: str,
    instance_count: int,
    catalog: DefinitionCatalog,
    game_root,
    sdk_root,
    object_builder_type: str | None = None,
    report_subtype_id: str | None = None,
) -> IdentityClassification:
    resolved = resolve_vanilla_geometry(
        subtype_id,
        catalog,
        object_builder_type=object_builder_type,
    )
    outcome = outcome_from_resolve(resolved)
    reason = resolved.unresolved_reason
    preliminary = collect_identity_evidence(
        subtype_id,
        instance_count,
        game_root=game_root,
        sdk_root=sdk_root,
        eligibility=reason,
        cause=None,
        object_builder_type=object_builder_type,
    )
    cause = classify_root_cause(
        outcome=outcome,
        unresolved_reason=reason,
        evidence=preliminary,
    )
    evidence = collect_identity_evidence(
        subtype_id,
        instance_count,
        game_root=game_root,
        sdk_root=sdk_root,
        eligibility=reason,
        cause=cause,
        object_builder_type=object_builder_type,
    )
    geometry_id = None
    if resolved.kind is VanillaResolveKind.PACKAGED:
        assert resolved.catalog_entry is not None
        geometry_id = resolved.catalog_entry.geometry_id
    elif resolved.kind is VanillaResolveKind.RUNTIME_VANILLA:
        assert resolved.runtime is not None
        geometry_id = resolved.runtime.geometry_id
    return IdentityClassification(
        subtype_id=report_subtype_id if report_subtype_id is not None else subtype_id,
        instance_count=instance_count,
        outcome=outcome,
        geometry_id=geometry_id,
        root_cause=cause,
        unresolved_reason=reason,
        evidence=evidence,
    )


def _extents_from_mins(
    mins: set[tuple[int, int, int]],
    pitch_mm: int,
) -> tuple[Optional[str], Optional[str]]:
    if not mins:
        return None, None
    xs = [item[0] for item in mins]
    ys = [item[1] for item in mins]
    zs = [item[2] for item in mins]
    extents = (
        f"x[{min(xs)}..{max(xs)}] "
        f"y[{min(ys)}..{max(ys)}] "
        f"z[{min(zs)}..{max(zs)}]"
    )
    millimetres = (
        f"{(max(xs) - min(xs) + 1) * pitch_mm} x "
        f"{(max(ys) - min(ys) + 1) * pitch_mm} x "
        f"{(max(zs) - min(zs) + 1) * pitch_mm}"
    )
    return extents, millimetres


def _unparsed_survey(
    structural: StructuralSurvey,
    parser_warnings: list[str],
) -> CompatibilitySurvey:
    return CompatibilitySurvey(
        structural=structural,
        parsed_grid_size=None,
        block_count=structural.total_blocks,
        unique_identity_count=structural.unique_subtype_count,
        supported_instance_count=0,
        supported_unique_count=0,
        packaged_instance_count=0,
        packaged_unique_count=0,
        runtime_instance_count=0,
        runtime_unique_count=0,
        unsupported_known_instance_count=0,
        unsupported_known_unique_count=0,
        unknown_unresolved_instance_count=structural.total_blocks,
        unknown_unresolved_unique_count=structural.unique_subtype_count,
        identities=(),
        cause_impacts=(),
        cumulative=CumulativeCoverage(
            current_supported_percent=0.0,
            after_top_1_percent=0.0,
            after_top_2_percent=0.0,
            after_top_3_percent=0.0,
            top_causes=(),
        ),
        subtype_counts=(),
        cell_extents=None,
        millimetre_size=None,
        parser_warnings=tuple(parser_warnings),
    )


def _assemble_survey(
    *,
    structural: StructuralSurvey,
    parsed_grid_size: Optional[GridSize],
    block_count: int,
    identities: tuple[IdentityClassification, ...],
    subtype_counts: tuple[NamedCount, ...],
    cell_extents: Optional[str],
    millimetre_size: Optional[str],
    parser_warnings: tuple[str, ...],
) -> CompatibilitySurvey:
    packaged_ids = [
        item
        for item in identities
        if item.outcome is CompatibilityOutcome.SUPPORTED_PACKAGED
    ]
    runtime_ids = [
        item
        for item in identities
        if item.outcome is CompatibilityOutcome.SUPPORTED_RUNTIME_VANILLA
    ]
    unsupported_ids = [
        item
        for item in identities
        if item.outcome is CompatibilityOutcome.UNSUPPORTED_KNOWN
    ]
    unknown_ids = [
        item
        for item in identities
        if item.outcome is CompatibilityOutcome.UNKNOWN_UNRESOLVED
    ]
    packaged_instances = sum(item.instance_count for item in packaged_ids)
    runtime_instances = sum(item.instance_count for item in runtime_ids)
    unsupported_instances = sum(item.instance_count for item in unsupported_ids)
    unknown_instances = sum(item.instance_count for item in unknown_ids)
    supported_instances = packaged_instances + runtime_instances
    unresolved_instances = unsupported_instances + unknown_instances
    cause_counter_instances: Counter[RootCause] = Counter()
    cause_counter_unique: Counter[RootCause] = Counter()
    for item in identities:
        if item.root_cause is None:
            continue
        cause_counter_instances[item.root_cause] += item.instance_count
        cause_counter_unique[item.root_cause] += 1
    impacts = tuple(
        CauseImpact(
            cause=cause,
            instance_count=cause_counter_instances[cause],
            unique_identity_count=cause_counter_unique[cause],
            percent_of_all_blocks=_percent(
                cause_counter_instances[cause], block_count
            ),
            percent_of_unresolved_instances=_percent(
                cause_counter_instances[cause], unresolved_instances
            ),
        )
        for cause in sorted(
            cause_counter_instances,
            key=lambda item: (
                -cause_counter_instances[item],
                -cause_counter_unique[item],
                item.value,
            ),
        )
    )
    top = tuple(impact.cause for impact in impacts[:3])
    current_pct = _percent(supported_instances, block_count)
    after: list[float] = []
    running = supported_instances
    for impact in impacts[:3]:
        running += impact.instance_count
        after.append(_percent(running, block_count))
    while len(after) < 3:
        after.append(current_pct if not impacts else after[-1])
    return CompatibilitySurvey(
        structural=structural,
        parsed_grid_size=parsed_grid_size,
        block_count=block_count,
        unique_identity_count=len(identities),
        supported_instance_count=supported_instances,
        supported_unique_count=len(packaged_ids) + len(runtime_ids),
        packaged_instance_count=packaged_instances,
        packaged_unique_count=len(packaged_ids),
        runtime_instance_count=runtime_instances,
        runtime_unique_count=len(runtime_ids),
        unsupported_known_instance_count=unsupported_instances,
        unsupported_known_unique_count=len(unsupported_ids),
        unknown_unresolved_instance_count=unknown_instances,
        unknown_unresolved_unique_count=len(unknown_ids),
        identities=identities,
        cause_impacts=impacts,
        cumulative=CumulativeCoverage(
            current_supported_percent=current_pct,
            after_top_1_percent=after[0],
            after_top_2_percent=after[1],
            after_top_3_percent=after[2],
            top_causes=top,
        ),
        subtype_counts=subtype_counts,
        cell_extents=cell_extents,
        millimetre_size=millimetre_size,
        parser_warnings=parser_warnings,
    )


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(100.0 * numerator / denominator, 2)
