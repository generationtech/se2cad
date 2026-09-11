"""Map current resolver/preflight outcomes to survey classes.

Classification consumes existing reason strings and definition facts.
It does not change eligibility or grant support.
"""

from __future__ import annotations

from se2cad.catalog.model import SupportStatus
from se2cad.survey.model import (
    BlockerKind,
    CompatibilityOutcome,
    IdentityEvidence,
    RootCause,
    Solvability,
)
from se2cad.vanilla.resolve import VanillaResolveKind, VanillaResolveResult


def outcome_from_resolve(
    resolved: VanillaResolveResult,
) -> CompatibilityOutcome:
    """Return the practical outcome for one resolver result."""
    if resolved.kind is VanillaResolveKind.PACKAGED:
        assert resolved.catalog_entry is not None
        if resolved.catalog_entry.support_status is SupportStatus.SUPPORTED:
            return CompatibilityOutcome.SUPPORTED_PACKAGED
        return CompatibilityOutcome.UNSUPPORTED_KNOWN
    if resolved.kind is VanillaResolveKind.RUNTIME_VANILLA:
        return CompatibilityOutcome.SUPPORTED_RUNTIME_VANILLA
    return CompatibilityOutcome.UNKNOWN_UNRESOLVED


def classify_root_cause(
    *,
    outcome: CompatibilityOutcome,
    unresolved_reason: str | None,
    evidence: IdentityEvidence,
) -> RootCause | None:
    """Return the evidenced cause, or None when the identity is supported."""
    if outcome is CompatibilityOutcome.SUPPORTED_PACKAGED:
        return None
    if outcome is CompatibilityOutcome.SUPPORTED_RUNTIME_VANILLA:
        return None
    if outcome is CompatibilityOutcome.UNSUPPORTED_KNOWN:
        return RootCause.EXISTING_POLICY_UNSUPPORTED

    reason = unresolved_reason or ""
    lowered = reason.lower()

    if "cubesize" in lowered and "is not large" in lowered:
        return RootCause.SMALL_GRID_NOT_ACTIVATED
    if "exceeds supported occupancy bound" in lowered:
        return RootCause.INVALID_OR_PATHOLOGICAL_SIZE
    if "is not a positive cell triple" in lowered:
        return RootCause.INVALID_OR_PATHOLOGICAL_SIZE
    if reason == "CubeTopology identities are not eligible for this resolver":
        return RootCause.CUBETOPOLOGY_NOT_SUPPORTED
    if "blocktopology" in lowered and "is not trianglemesh" in lowered:
        if evidence.block_topology == "Cube" or evidence.cube_topology is not None:
            return RootCause.CUBETOPOLOGY_NOT_SUPPORTED
        return RootCause.NON_TRIANGLE_MESH_TOPOLOGY
    if reason == "definition requires subpart or composite handling":
        return RootCause.DEFINITION_SUBPARTS_PRESENT
    if reason == "primary Model is missing":
        return RootCause.NO_PRIMARY_MODEL
    if reason == "primary Model is ambiguous":
        return RootCause.MULTIPLE_OR_AMBIGUOUS_PRIMARY_MODEL
    if reason.startswith("empty SubtypeName uses object-builder default"):
        return RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT
    if reason.startswith("empty SubtypeName is missing an object-builder type"):
        return RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT
    if reason.startswith("empty SubtypeName has no unique vanilla definition"):
        return RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT
    if "duplicate empty-subtypeid" in lowered:
        return RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT
    if "object_builder_type" in lowered and "myobjectbuilder" in lowered:
        return RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT
    if "vanilla definition not found" in lowered:
        return RootCause.MODDED_OR_NONVANILLA
    if evidence.cube_topology is not None and (
        "blocktopology" in lowered
        or "must contain exactly one blocktopology" in lowered
        or evidence.block_topology in {None, ""}
    ):
        return RootCause.CUBETOPOLOGY_NOT_SUPPORTED
    if "vanilla definition is unusable" in lowered or evidence.unusable_reason:
        if "unusable" in lowered or evidence.unusable_reason:
            if "vanilla definition not found" not in lowered:
                return RootCause.DEFINITION_PARSE_UNSUPPORTED
    if any(
        token in lowered
        for token in (
            "escapes configured",
            "must not be absolute",
            "must not contain a drive",
            "must stay inside",
            "must stay under",
            "must use the official game mesh suffix",
            "must not name lod",
        )
    ):
        return RootCause.MODEL_PATH_NOT_CONTAINED
    if "ambiguous sdk path" in lowered:
        return RootCause.SDK_FBX_AMBIGUOUS
    if any(
        token in lowered
        for token in (
            "not a binary fbx",
            "not a valid ascii fbx",
            "not a usable binary or ascii fbx",
            "ascii fbx conversion is not available",
            "ascii fbx",
        )
    ):
        return RootCause.FBX_FORMAT_UNSUPPORTED
    if "is not a file" in lowered or "sdk source is not a file" in lowered:
        if evidence.game_mwm_exists is True and evidence.sdk_fbx_exists is not True:
            return RootCause.MWM_ONLY
        return RootCause.SDK_FBX_MISSING
    if evidence.game_mwm_exists is True and evidence.sdk_fbx_exists is False:
        return RootCause.MWM_ONLY
    return RootCause.OTHER_EVIDENCED_CAUSE


def blocker_kind_for(cause: RootCause | None) -> BlockerKind | None:
    """Classify where the blocker sits in the current pipeline."""
    if cause is None:
        return None
    if cause is RootCause.EXISTING_POLICY_UNSUPPORTED:
        return BlockerKind.PRODUCT_POLICY
    if cause is RootCause.SMALL_GRID_NOT_ACTIVATED:
        return BlockerKind.PRODUCT_POLICY
    if cause is RootCause.CUBETOPOLOGY_NOT_SUPPORTED:
        return BlockerKind.GEOMETRY_BUILD
    if cause is RootCause.DEFINITION_SUBPARTS_PRESENT:
        return BlockerKind.ASSEMBLY_SEMANTICS
    if cause is RootCause.INVALID_OR_PATHOLOGICAL_SIZE:
        return BlockerKind.PLACEMENT
    if cause in {
        RootCause.MULTIPLE_OR_AMBIGUOUS_PRIMARY_MODEL,
        RootCause.NO_PRIMARY_MODEL,
        RootCause.MODEL_PATH_NOT_CONTAINED,
        RootCause.SDK_FBX_MISSING,
        RootCause.SDK_FBX_AMBIGUOUS,
        RootCause.FBX_FORMAT_UNSUPPORTED,
        RootCause.MWM_ONLY,
        RootCause.MODDED_OR_NONVANILLA,
        RootCause.DEFINITION_PARSE_UNSUPPORTED,
        RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT,
        RootCause.NON_TRIANGLE_MESH_TOPOLOGY,
    }:
        return BlockerKind.SOURCE_RESOLUTION
    if cause is RootCause.BUILDER_UNAVAILABLE:
        return BlockerKind.GEOMETRY_BUILD
    return BlockerKind.SOURCE_RESOLUTION


def solvability_for(cause: RootCause) -> tuple[Solvability, str]:
    """Return a conservative solvability label and the evidence it rests on."""
    if cause is RootCause.CUBETOPOLOGY_NOT_SUPPORTED:
        return (
            Solvability.LIKELY_EXISTING_ARCHITECTURE_EXTENSION,
            "Qualified native constructions already exist for Box, Slope, "
            "Corner, and InvCorner. Other CubeTopology tokens would need "
            "additional primitives; that is still the existing recipe path, "
            "not a new conversion architecture.",
        )
    if cause is RootCause.DEFINITION_SUBPARTS_PRESENT:
        return (
            Solvability.REQUIRES_NEW_ARCHITECTURE,
            "Resolver eligibility already rejects definition-level Subparts. "
            "Visible completeness often depends on a hierarchy the current "
            "one-static-reusable-part model does not represent.",
        )
    if cause is RootCause.MWM_ONLY:
        return (
            Solvability.POLICY_DECISION,
            "Game MWM exists and the same-stem official SDK FBX does not. "
            "That is a source-availability / licensing gap, not a missing "
            "placement or transform primitive. MWM decoding and OBJ export "
            "remain out of scope.",
        )
    if cause is RootCause.SDK_FBX_MISSING:
        return (
            Solvability.POLICY_DECISION,
            "Official SDK FBX was not found at the exact same-stem path. "
            "This is source availability unless a later unit authorizes a "
            "bounded alternate official source rule.",
        )
    if cause is RootCause.SDK_FBX_AMBIGUOUS:
        return (
            Solvability.LOW_VALUE_OR_EDGE_CASE,
            "Case-insensitive duplicate SDK names fail closed. That is an "
            "operator-tree hygiene problem, not a missing architecture.",
        )
    if cause is RootCause.FBX_FORMAT_UNSUPPORTED:
        return (
            Solvability.LIKELY_EXISTING_ARCHITECTURE_EXTENSION,
            "S2C-11.9.1 already consumes official binary and ASCII FBX 7.x. "
            "A new format would be another source-format extension, not a "
            "new resolver architecture.",
        )
    if cause is RootCause.MULTIPLE_OR_AMBIGUOUS_PRIMARY_MODEL:
        return (
            Solvability.NEEDS_MORE_EVIDENCE,
            "Current resolver requires exactly one primary Model. Some "
            "multi-Model documents are construction-stage metadata; others "
            "are real composites. Evidence must distinguish those before "
            "choosing an architecture.",
        )
    if cause is RootCause.NO_PRIMARY_MODEL:
        return (
            Solvability.NEEDS_MORE_EVIDENCE,
            "No primary Model was present. The identity may be CubeTopology, "
            "Sides-driven, or otherwise non-mesh. Inspect the definition "
            "before choosing a builder.",
        )
    if cause is RootCause.SMALL_GRID_NOT_ACTIVATED:
        return (
            Solvability.POLICY_DECISION,
            "Small Grid remains an authorized later milestone and is "
            "explicitly postponed. The resolver already names CubeSize.",
        )
    if cause is RootCause.MODDED_OR_NONVANILLA:
        return (
            Solvability.POLICY_DECISION,
            "Exact vanilla definition was not found. Mod resolution is "
            "outside the current vanilla Large Grid boundary.",
        )
    if cause is RootCause.EXISTING_POLICY_UNSUPPORTED:
        return (
            Solvability.POLICY_DECISION,
            "The packaged catalog already records the identity as "
            "unsupported. That is an existing support-status decision.",
        )
    if cause is RootCause.INVALID_OR_PATHOLOGICAL_SIZE:
        return (
            Solvability.LOW_VALUE_OR_EDGE_CASE,
            "Placement already rejects non-positive Size and occupancy "
            "axes above 32. Those are fail-closed safety bounds.",
        )
    if cause is RootCause.MODEL_PATH_NOT_CONTAINED:
        return (
            Solvability.LOW_VALUE_OR_EDGE_CASE,
            "Model path failed containment or official-suffix rules. "
            "That is a source-mapping safety bound, not missing CAD.",
        )
    if cause is RootCause.EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT:
        return (
            Solvability.LIKELY_EXISTING_ARCHITECTURE_EXTENSION,
            "Keen serializes some vanilla defaults as an empty SubtypeName "
            "plus a concrete MyObjectBuilder_* type. The current parser "
            "fails closed rather than inventing that default identity. A "
            "later bounded parser rule could map that pair to the unique "
            "empty-SubtypeId definition. This survey does not add that rule "
            "and does not grant support.",
        )
    if cause is RootCause.DEFINITION_PARSE_UNSUPPORTED:
        return (
            Solvability.LIKELY_EXISTING_ARCHITECTURE_EXTENSION,
            "A targeted lookup already exists. A newly observed definition "
            "pattern would be a bounded parser/discovery extension if it "
            "blocks classification, not a new conversion architecture.",
        )
    if cause is RootCause.NON_TRIANGLE_MESH_TOPOLOGY:
        return (
            Solvability.NEEDS_MORE_EVIDENCE,
            "BlockTopology is neither TriangleMesh nor Cube. Inspect the "
            "token before choosing a builder family.",
        )
    if cause is RootCause.BUILDER_UNAVAILABLE:
        return (
            Solvability.REQUIRES_NEW_ARCHITECTURE,
            "Source resolution succeeded but no qualified builder exists "
            "for that geometry class.",
        )
    return (
        Solvability.NEEDS_MORE_EVIDENCE,
        "The unresolved reason did not match a more specific evidenced "
        "cause. Inspect the exact resolver string before planning work.",
    )
