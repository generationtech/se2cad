"""Generate canonical parts in a Windows-local SolidWorks session."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.library import (
    EDGE_TREATMENT_OFF,
    EdgeTreatmentKind,
    EdgeTreatmentRequest,
    lookup_recipe,
    representative_automatable_geometry_ids,
)
from se2cad.solidworks.artifacts import (
    assert_overwrite_is_canonical,
    canonical_geometry_ids,
    is_canonical_artifact_filename,
    logical_part_filename,
    part_artifact_path,
)
from se2cad.solidworks.com_construct import construct_plan
from se2cad.solidworks.com_session import SolidWorksSession
from se2cad.solidworks.com_treat import apply_equal_setback_chamfer
from se2cad.solidworks.com_validate import (
    PartValidation,
    assert_matches_treatment_contract,
    read_part_validation,
    validate_model,
)
from se2cad.solidworks.config import SolidWorksBackendConfig, load_solidworks_backend_config
from se2cad.solidworks.errors import GeneratedRootError, SolidWorksComError
from se2cad.solidworks.locator import BoundPartLocator, LogicalPartIdentity
from se2cad.solidworks.recipe_plan import ConstructionPlan, plan_from_recipe


@dataclass(frozen=True)
class GeneratedCanonicalPart:
    locator: BoundPartLocator
    plan: ConstructionPlan
    after_save: PartValidation
    after_reopen: PartValidation
    treatment: EdgeTreatmentRequest = EDGE_TREATMENT_OFF
    treatment_applied: bool = False
    untreated_after_construct: PartValidation | None = None


def _prepare_destination(
    config: SolidWorksBackendConfig,
    geometry_id: str,
    request: EdgeTreatmentRequest,
) -> Path:
    destination = part_artifact_path(config.generated_root, geometry_id, request)
    if request.enabled and is_canonical_artifact_filename(destination.name):
        raise GeneratedRootError(
            "treated generation refused to write an untreated canonical filename"
        )
    if not request.enabled and destination.name != logical_part_filename(geometry_id):
        raise GeneratedRootError(
            "untreated generation must write the qualified canonical filename"
        )
    assert_overwrite_is_canonical(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _logical_identity(
    geometry_id: str,
    destination: Path,
    request: EdgeTreatmentRequest,
) -> LogicalPartIdentity:
    if not request.enabled:
        return LogicalPartIdentity.from_geometry_id(geometry_id)
    if destination.name == logical_part_filename(geometry_id):
        raise GeneratedRootError(
            "treated locator must not use the untreated canonical filename"
        )
    return LogicalPartIdentity(geometry_id=geometry_id, filename=destination.name)


def _validate_treated(
    untreated: PartValidation,
    treated: PartValidation,
    plan: ConstructionPlan,
) -> None:
    assert_matches_treatment_contract(
        untreated,
        treated,
        envelope_min_m=plan.expected.bounding_box_min_m,
        envelope_max_m=plan.expected.bounding_box_max_m,
    )


def generate_one_canonical_part(
    session: SolidWorksSession,
    geometry_id: str,
    config: SolidWorksBackendConfig,
    treatment: EdgeTreatmentRequest | None = None,
) -> GeneratedCanonicalPart:
    request = EDGE_TREATMENT_OFF if treatment is None else treatment
    if request.enabled and request.kind is not EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK:
        raise SolidWorksComError(
            f"unsupported edge treatment {request.kind.value!r}"
        )
    recipe = lookup_recipe(geometry_id)
    plan = plan_from_recipe(recipe)
    destination = _prepare_destination(config, geometry_id, request)
    model = session.new_part()
    untreated_obs: PartValidation | None = None
    try:
        construct_plan(session, model, plan)
        if request.enabled:
            untreated_obs = validate_model(session, model, plan)
            apply_equal_setback_chamfer(session, model, recipe)
            after_save = read_part_validation(session, model)
            _validate_treated(untreated_obs, after_save, plan)
        else:
            after_save = validate_model(session, model, plan)
        session.save_as(model, destination)
    finally:
        session.close_doc(model)

    reopened = session.open_part(destination)
    try:
        if request.enabled:
            if untreated_obs is None:
                raise SolidWorksComError("missing pre-treatment validation")
            after_reopen = read_part_validation(session, reopened)
            _validate_treated(untreated_obs, after_reopen, plan)
        else:
            after_reopen = validate_model(session, reopened, plan)
    finally:
        session.close_doc(reopened)

    locator = BoundPartLocator(
        identity=_logical_identity(geometry_id, destination, request),
        path=destination,
        generated=True,
        validated=True,
        saved=True,
        reopened=True,
    )
    return GeneratedCanonicalPart(
        locator=locator,
        plan=plan,
        after_save=after_save,
        after_reopen=after_reopen,
        treatment=request,
        treatment_applied=request.enabled,
        untreated_after_construct=untreated_obs,
    )


def generate_canonical_parts(
    config: SolidWorksBackendConfig | None = None,
    treatment: EdgeTreatmentRequest | None = None,
    geometry_ids: tuple[str, ...] | None = None,
) -> tuple[GeneratedCanonicalPart, ...]:
    """Materialize native recipes as reusable SLDPRT files.

    Default ``geometry_ids`` remains the four initial-program identities.
    ``treatment=None`` and ``EDGE_TREATMENT_OFF`` remain the default
    untreated conversion. Treated siblings are written only when requested.
    """
    resolved = config if config is not None else load_solidworks_backend_config()
    request = EDGE_TREATMENT_OFF if treatment is None else treatment
    requested = canonical_geometry_ids() if geometry_ids is None else geometry_ids
    if not requested:
        raise GeneratedRootError("generation requires at least one geometry_id")
    if len(requested) != len(set(requested)):
        raise GeneratedRootError("duplicate geometry_id in generation request")
    results: list[GeneratedCanonicalPart] = []
    with SolidWorksSession(resolved) as session:
        for geometry_id in requested:
            results.append(
                generate_one_canonical_part(
                    session, geometry_id, resolved, treatment=request
                )
            )
    return tuple(results)


def generate_representative_automatable_parts(
    config: SolidWorksBackendConfig | None = None,
    treatment: EdgeTreatmentRequest | None = None,
) -> tuple[GeneratedCanonicalPart, ...]:
    """Generate the S2C-11.4.1 representative automatable subset."""
    return generate_canonical_parts(
        config,
        treatment=treatment,
        geometry_ids=representative_automatable_geometry_ids(),
    )
