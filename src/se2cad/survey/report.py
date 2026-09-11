"""Render a human-readable compatibility survey. Not a support grant."""

from __future__ import annotations

from se2cad.survey.classify import solvability_for
from se2cad.survey.model import (
    CompatibilityOutcome,
    CompatibilitySurvey,
    IdentityClassification,
)


def format_survey_markdown(survey: CompatibilitySurvey) -> str:
    """Return a durable markdown report for one survey result."""
    structural = survey.structural
    lines = [
        "# Real Blueprint Compatibility Survey",
        "",
        "S2C-11.12.1. Classification only. No compatibility category was newly activated.",
        "",
        "## 1. Survey scope",
        "",
        f"- Source path: `{structural.source_path}`",
        f"- Document kind: `{structural.kind.value}`",
        f"- Wrapped for parser: `{str(structural.wrapped_for_parser).lower()}`",
        f"- SHA-256: `{structural.sha256}`",
        f"- Bytes: {structural.byte_count}",
        "",
        "## 2. Blueprint inventory",
        "",
        f"- Identity: `{structural.identity or ''}`",
        f"- Display name: {structural.display_name or ''}",
        f"- Total grids: {structural.grid_count}",
        f"- Has multiple grids: `{str(structural.has_multiple_grids).lower()}`",
        f"- Has non-Large Grid: `{str(structural.has_non_large_grid).lower()}`",
        f"- Total blocks (structural): {structural.total_blocks}",
        f"- Unique SubtypeIds (structural): {structural.unique_subtype_count}",
        f"- Parsed grid size: {survey.parsed_grid_size.value if survey.parsed_grid_size else ''}",
        f"- Cell extents: {survey.cell_extents or ''}",
        f"- Dimensions mm: {survey.millimetre_size or ''}",
    ]
    if survey.parser_warnings:
        lines.append("- Parser / intake notes:")
        for warning in survey.parser_warnings:
            lines.append(f"  - {warning}")
    for index, grid in enumerate(structural.grids):
        lines.append(
            f"- Grid {index}: size={grid.grid_size or '?'} "
            f"blocks={grid.block_count} unique={grid.unique_subtype_count} "
            f"mechanical_groups={grid.mechanical_groups} "
            f"name={grid.display_name or ''}"
        )
    lines.extend(
        [
            "",
            "## 3. Current support coverage",
            "",
            f"- Parsed blocks: {survey.block_count}",
            f"- Unique identities: {survey.unique_identity_count}",
            f"- Supported instances: {survey.supported_instance_count} "
            f"({survey.cumulative.current_supported_percent}%)",
            f"- Supported unique identities: {survey.supported_unique_count}",
            f"- Packaged instances / unique: "
            f"{survey.packaged_instance_count} / {survey.packaged_unique_count} "
            f"(`SUPPORTED_PACKAGED`)",
            f"- Runtime vanilla instances / unique: "
            f"{survey.runtime_instance_count} / {survey.runtime_unique_count} "
            f"(`SUPPORTED_RUNTIME_VANILLA`)",
            f"- Unsupported known instances / unique: "
            f"{survey.unsupported_known_instance_count} / "
            f"{survey.unsupported_known_unique_count}",
            f"- Unknown unresolved instances / unique: "
            f"{survey.unknown_unresolved_instance_count} / "
            f"{survey.unknown_unresolved_unique_count}",
            "",
            "## 4. Unresolved/unsupported identities",
            "",
        ]
    )
    unresolved = [
        item
        for item in survey.identities
        if item.outcome
        in {
            CompatibilityOutcome.UNSUPPORTED_KNOWN,
            CompatibilityOutcome.UNKNOWN_UNRESOLVED,
        }
    ]
    if not unresolved:
        lines.append("None.")
    else:
        lines.extend(_identity_table(unresolved))
    lines.extend(
        [
            "",
            "## 5. Root-cause classification",
            "",
        ]
    )
    if not survey.cause_impacts:
        lines.append("No unresolved/unsupported root causes.")
    else:
        lines.append(
            "| Cause | Instances | Unique identities | % of blocks | % of unresolved |"
        )
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for impact in survey.cause_impacts:
            lines.append(
                f"| `{impact.cause.value}` | {impact.instance_count} | "
                f"{impact.unique_identity_count} | "
                f"{impact.percent_of_all_blocks:.2f} | "
                f"{impact.percent_of_unresolved_instances:.2f} |"
            )
    lines.extend(
        [
            "",
            "## 6. Ranked impact",
            "",
            "By unresolved/unsupported instance count:",
        ]
    )
    by_instances = sorted(
        unresolved, key=lambda item: (-item.instance_count, item.subtype_id)
    )
    for item in by_instances[:25]:
        cause = item.root_cause.value if item.root_cause else ""
        lines.append(
            f"- `{item.subtype_id}` ×{item.instance_count} `{cause}`"
        )
    lines.append("")
    lines.append("By unique identity, root causes ranked by unique count:")
    unique_ranked = sorted(
        survey.cause_impacts,
        key=lambda item: (-item.unique_identity_count, item.cause.value),
    )
    for impact in unique_ranked:
        lines.append(
            f"- `{impact.cause.value}` unique={impact.unique_identity_count} "
            f"instances={impact.instance_count}"
        )
    lines.extend(
        [
            "",
            "## 7. Representative evidence",
            "",
        ]
    )
    for cause_impact in survey.cause_impacts:
        sample = next(
            (
                item
                for item in unresolved
                if item.root_cause is cause_impact.cause
            ),
            None,
        )
        if sample is None:
            continue
        lines.extend(_evidence_block(sample))
        lines.append("")
    lines.extend(
        [
            "## 8. Generic-solvability assessment",
            "",
        ]
    )
    seen: set[str] = set()
    for impact in survey.cause_impacts:
        if impact.cause.value in seen:
            continue
        seen.add(impact.cause.value)
        label, rationale = solvability_for(impact.cause)
        lines.append(f"### `{impact.cause.value}`")
        lines.append("")
        lines.append(f"- Solvability: `{label.value}`")
        lines.append(f"- Evidence: {rationale}")
        lines.append("")
    lines.extend(
        [
            "## 9. Architecture implications",
            "",
            "See the durable S2C-11.12.1 report. This generated section does "
            "not authorize a later implementation unit.",
            "",
            "## 10. Recommended next decision",
            "",
            _recommendation(survey),
            "",
            "## 11. Residual unknowns",
            "",
            "- Hypothetical coverage figures assume every instance of a cause "
            "would become supported. That is classification math only.",
            "- Official Prefab wrap is survey intake, not production Prefab parse.",
            "- Modded identities, if any, must not dominate vanilla conclusions.",
            "",
            "### Cumulative hypothetical coverage",
            "",
            f"- Current supported: {survey.cumulative.current_supported_percent:.2f}%",
            f"- After top 1: {survey.cumulative.after_top_1_percent:.2f}%",
            f"- After top 2: {survey.cumulative.after_top_2_percent:.2f}%",
            f"- After top 3: {survey.cumulative.after_top_3_percent:.2f}%",
            f"- Top causes: {', '.join(cause.value for cause in survey.cumulative.top_causes) or '(none)'}",
        ]
    )
    return "\n".join(lines) + "\n"


def _identity_table(items: list[IdentityClassification]) -> list[str]:
    lines = [
        "| SubtypeId | N | Outcome | Cause | Grid | Size | Topology | Subparts | Model | Eligibility |",
        "| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for item in items:
        evidence = item.evidence
        size = ""
        if evidence.size is not None:
            size = f"{evidence.size.x}×{evidence.size.y}×{evidence.size.z}"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item.subtype_id}`",
                    str(item.instance_count),
                    item.outcome.value,
                    item.root_cause.value if item.root_cause else "",
                    evidence.cube_size or "",
                    size,
                    evidence.block_topology or "",
                    str(evidence.subpart_count),
                    (evidence.primary_model or "").replace("|", "/"),
                    (item.unresolved_reason or "").replace("|", "/"),
                ]
            )
            + " |"
        )
    return lines


def _evidence_block(item: IdentityClassification) -> list[str]:
    evidence = item.evidence
    size = ""
    if evidence.size is not None:
        size = f"{evidence.size.x}×{evidence.size.y}×{evidence.size.z}"
    offset = ""
    if evidence.model_offset is not None:
        offset = (
            f"{evidence.model_offset.x},{evidence.model_offset.y},"
            f"{evidence.model_offset.z}"
        )
    return [
        f"### `{item.subtype_id}`",
        "",
        f"- Instances: {item.instance_count}",
        f"- Outcome: `{item.outcome.value}`",
        f"- Cause: `{item.root_cause.value if item.root_cause else ''}`",
        f"- CubeSize: {evidence.cube_size or ''}",
        f"- Size: {size}",
        f"- BlockTopology: {evidence.block_topology or ''}",
        f"- CubeTopology: {evidence.cube_topology or ''}",
        f"- Model: {evidence.primary_model or ''}",
        f"- Model count: {evidence.model_count}",
        f"- Subparts: {evidence.subparts_present} / {evidence.subpart_count}",
        f"- ModelOffset m: {offset}",
        f"- Definition source: {evidence.definition_source_relative or ''}",
        f"- Exact vanilla definition: `{str(evidence.exact_vanilla_definition).lower()}`",
        f"- Game MWM exists: {evidence.game_mwm_exists}",
        f"- SDK FBX exists: {evidence.sdk_fbx_exists}",
        f"- SDK FBX: {evidence.sdk_fbx_relative or ''}",
        f"- SDK FBX format: {evidence.sdk_fbx_format or ''}",
        f"- Eligibility: {item.unresolved_reason or evidence.eligibility_reason or ''}",
        f"- Placement Size already supported: "
        f"`{str(evidence.placement_size_supported).lower()}`",
        f"- Materializer theoretically handles source: "
        f"`{str(evidence.materializer_theoretically_handles).lower()}`",
        f"- Blocker kind: {evidence.blocker_kind.value if evidence.blocker_kind else ''}",
    ]


def _recommendation(survey: CompatibilitySurvey) -> str:
    if not survey.cause_impacts:
        return (
            "No unresolved/unsupported cause remains in this document. "
            "Do not invent a next implementation unit from this survey alone."
        )
    top = survey.cause_impacts[0]
    share = top.percent_of_unresolved_instances
    label, _rationale = solvability_for(top.cause)
    if share < 40.0:
        return (
            f"No single cause dominates (top `{top.cause.value}` is "
            f"{share:.2f}% of unresolved instances). Do not force a next "
            "implementation unit from this survey."
        )
    return (
        f"If a later human-authorized unit is chosen, evidence points first "
        f"at `{top.cause.value}` ({top.instance_count} instances, "
        f"{top.unique_identity_count} identities, {share:.2f}% of unresolved "
        f"instances; solvability `{label.value}`). This survey does not "
        "create or start that unit."
    )
