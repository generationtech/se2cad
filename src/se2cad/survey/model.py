"""CAD-neutral compatibility-survey values (S2C-11.12.1).

These types classify current resolver/preflight outcomes. They do not
grant support, mutate the packaged catalog, or convert a blueprint.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from se2cad.catalog.model import CellSize
from se2cad.parser.model import GridSize
from se2cad.statistics.model import NamedCount
from se2cad.transform.placement import ModelOffset


class CompatibilityOutcome(str, Enum):
    """Exactly one practical outcome per unique identity."""

    SUPPORTED_PACKAGED = "SUPPORTED_PACKAGED"
    SUPPORTED_RUNTIME_VANILLA = "SUPPORTED_RUNTIME_VANILLA"
    UNSUPPORTED_KNOWN = "UNSUPPORTED_KNOWN"
    UNKNOWN_UNRESOLVED = "UNKNOWN_UNRESOLVED"


class RootCause(str, Enum):
    """Evidenced reason an identity remains unresolved or unsupported."""

    SMALL_GRID_NOT_ACTIVATED = "SMALL_GRID_NOT_ACTIVATED"
    CUBETOPOLOGY_NOT_SUPPORTED = "CUBETOPOLOGY_NOT_SUPPORTED"
    NON_TRIANGLE_MESH_TOPOLOGY = "NON_TRIANGLE_MESH_TOPOLOGY"
    DEFINITION_SUBPARTS_PRESENT = "DEFINITION_SUBPARTS_PRESENT"
    MULTIPLE_OR_AMBIGUOUS_PRIMARY_MODEL = "MULTIPLE_OR_AMBIGUOUS_PRIMARY_MODEL"
    NO_PRIMARY_MODEL = "NO_PRIMARY_MODEL"
    MODEL_PATH_NOT_CONTAINED = "MODEL_PATH_NOT_CONTAINED"
    SDK_FBX_MISSING = "SDK_FBX_MISSING"
    SDK_FBX_AMBIGUOUS = "SDK_FBX_AMBIGUOUS"
    FBX_FORMAT_UNSUPPORTED = "FBX_FORMAT_UNSUPPORTED"
    DEFINITION_PARSE_UNSUPPORTED = "DEFINITION_PARSE_UNSUPPORTED"
    INVALID_OR_PATHOLOGICAL_SIZE = "INVALID_OR_PATHOLOGICAL_SIZE"
    MODDED_OR_NONVANILLA = "MODDED_OR_NONVANILLA"
    MWM_ONLY = "MWM_ONLY"
    BUILDER_UNAVAILABLE = "BUILDER_UNAVAILABLE"
    EXISTING_POLICY_UNSUPPORTED = "EXISTING_POLICY_UNSUPPORTED"
    EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT = "EMPTY_SUBTYPE_OBJECT_BUILDER_DEFAULT"
    OTHER_EVIDENCED_CAUSE = "OTHER_EVIDENCED_CAUSE"


class Solvability(str, Enum):
    """Hypothetical next-step class. Not a support grant."""

    LIKELY_EXISTING_ARCHITECTURE_EXTENSION = (
        "LIKELY_EXISTING_ARCHITECTURE_EXTENSION"
    )
    REQUIRES_NEW_ARCHITECTURE = "REQUIRES_NEW_ARCHITECTURE"
    POLICY_DECISION = "POLICY_DECISION"
    LOW_VALUE_OR_EDGE_CASE = "LOW_VALUE_OR_EDGE_CASE"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


class BlockerKind(str, Enum):
    SOURCE_RESOLUTION = "source_resolution"
    GEOMETRY_BUILD = "geometry_build"
    PLACEMENT = "placement"
    ASSEMBLY_SEMANTICS = "assembly_semantics"
    PRODUCT_POLICY = "product_policy"


class SourceDocumentKind(str, Enum):
    SHIP_BLUEPRINT = "ship_blueprint"
    PREFAB = "prefab"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ExtractedSurveyBlock:
    """One CubeBlocks item read for survey classification only."""

    source_index: int
    subtype_id: str
    object_builder_type: str
    min_x: Optional[int]
    min_y: Optional[int]
    min_z: Optional[int]


@dataclass(frozen=True)
class StructuralGrid:
    """One observed CubeGrid. Survey intake only."""

    display_name: Optional[str]
    grid_size: Optional[str]
    block_count: int
    unique_subtype_count: int
    mechanical_groups: int


@dataclass(frozen=True)
class StructuralSurvey:
    """Document-level facts recorded before or without conversion."""

    source_path: str
    sha256: str
    byte_count: int
    kind: SourceDocumentKind
    identity: Optional[str]
    display_name: Optional[str]
    grid_count: int
    grids: tuple[StructuralGrid, ...]
    total_blocks: int
    unique_subtype_count: int
    has_non_large_grid: bool
    has_multiple_grids: bool
    parser_error: Optional[str]
    wrapped_for_parser: bool


@dataclass(frozen=True)
class IdentityEvidence:
    """Read-only definition/source facts for one SubtypeId."""

    subtype_id: str
    instance_count: int
    exact_vanilla_definition: bool
    cube_size: Optional[str]
    size: Optional[CellSize]
    block_topology: Optional[str]
    cube_topology: Optional[str]
    primary_model: Optional[str]
    model_count: int
    subparts_present: bool
    subpart_count: int
    model_offset: Optional[ModelOffset]
    definition_source_relative: Optional[str]
    unusable_reason: Optional[str]
    game_mwm_exists: Optional[bool]
    sdk_fbx_exists: Optional[bool]
    sdk_fbx_relative: Optional[str]
    sdk_fbx_format: Optional[str]
    sdk_fbx_probe_reason: Optional[str]
    eligibility_reason: Optional[str]
    placement_size_supported: bool
    materializer_theoretically_handles: bool
    blocker_kind: Optional[BlockerKind]


@dataclass(frozen=True)
class IdentityClassification:
    """One unique SubtypeId's practical outcome and cause."""

    subtype_id: str
    instance_count: int
    outcome: CompatibilityOutcome
    geometry_id: Optional[str]
    root_cause: Optional[RootCause]
    unresolved_reason: Optional[str]
    evidence: IdentityEvidence


@dataclass(frozen=True)
class CauseImpact:
    """Instance and unique-identity impact of one root cause."""

    cause: RootCause
    instance_count: int
    unique_identity_count: int
    percent_of_all_blocks: float
    percent_of_unresolved_instances: float


@dataclass(frozen=True)
class CumulativeCoverage:
    """Hypothetical coverage if top causes were solved. Not implemented."""

    current_supported_percent: float
    after_top_1_percent: float
    after_top_2_percent: float
    after_top_3_percent: float
    top_causes: tuple[RootCause, ...]


@dataclass(frozen=True)
class CompatibilitySurvey:
    """Deterministic survey of one operator-selected document."""

    structural: StructuralSurvey
    parsed_grid_size: Optional[GridSize]
    block_count: int
    unique_identity_count: int
    supported_instance_count: int
    supported_unique_count: int
    packaged_instance_count: int
    packaged_unique_count: int
    runtime_instance_count: int
    runtime_unique_count: int
    unsupported_known_instance_count: int
    unsupported_known_unique_count: int
    unknown_unresolved_instance_count: int
    unknown_unresolved_unique_count: int
    identities: tuple[IdentityClassification, ...]
    cause_impacts: tuple[CauseImpact, ...]
    cumulative: CumulativeCoverage
    subtype_counts: tuple[NamedCount, ...]
    cell_extents: Optional[str]
    millimetre_size: Optional[str]
    parser_warnings: tuple[str, ...]
