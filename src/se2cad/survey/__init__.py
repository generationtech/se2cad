"""CAD-neutral real-blueprint compatibility survey (S2C-11.12.1).

Classification and reporting only. This package does not grant runtime
support, persist catalog records, expand CubeTopology, activate Small
Grid, or add OBJ export.
"""

from se2cad.survey.classify import (
    blocker_kind_for,
    classify_root_cause,
    outcome_from_resolve,
    solvability_for,
)
from se2cad.survey.compute import (
    compute_compatibility_survey,
    compute_compatibility_survey_from_path,
)
from se2cad.survey.intake import (
    extract_survey_blocks,
    inspect_document_structure,
    load_survey_blueprint,
    wrap_prefab_as_ship_blueprint,
)
from se2cad.survey.model import (
    BlockerKind,
    CauseImpact,
    CompatibilityOutcome,
    CompatibilitySurvey,
    CumulativeCoverage,
    IdentityClassification,
    ExtractedSurveyBlock,
    IdentityEvidence,
    RootCause,
    Solvability,
    SourceDocumentKind,
    StructuralGrid,
    StructuralSurvey,
)
from se2cad.survey.report import format_survey_markdown

__all__ = [
    "BlockerKind",
    "CauseImpact",
    "CompatibilityOutcome",
    "CompatibilitySurvey",
    "CumulativeCoverage",
    "IdentityClassification",
    "ExtractedSurveyBlock",
    "IdentityEvidence",
    "RootCause",
    "Solvability",
    "SourceDocumentKind",
    "StructuralGrid",
    "StructuralSurvey",
    "blocker_kind_for",
    "classify_root_cause",
    "compute_compatibility_survey",
    "compute_compatibility_survey_from_path",
    "extract_survey_blocks",
    "format_survey_markdown",
    "inspect_document_structure",
    "load_survey_blueprint",
    "outcome_from_resolve",
    "solvability_for",
    "wrap_prefab_as_ship_blueprint",
]
