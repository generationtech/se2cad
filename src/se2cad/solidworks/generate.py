"""Generate the four canonical parts in a Windows-local SolidWorks session."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.library import lookup_recipe
from se2cad.solidworks.artifacts import (
    artifact_path_for,
    assert_overwrite_is_canonical,
    canonical_geometry_ids,
)
from se2cad.solidworks.com_construct import construct_plan
from se2cad.solidworks.com_session import SolidWorksSession
from se2cad.solidworks.com_validate import PartValidation, validate_model
from se2cad.solidworks.config import SolidWorksBackendConfig, load_solidworks_backend_config
from se2cad.solidworks.locator import BoundPartLocator, LogicalPartIdentity
from se2cad.solidworks.recipe_plan import ConstructionPlan, plan_from_recipe


@dataclass(frozen=True)
class GeneratedCanonicalPart:
    locator: BoundPartLocator
    plan: ConstructionPlan
    after_save: PartValidation
    after_reopen: PartValidation


def _prepare_destination(config: SolidWorksBackendConfig, geometry_id: str) -> Path:
    destination = artifact_path_for(config.generated_root, geometry_id)
    assert_overwrite_is_canonical(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def generate_one_canonical_part(
    session: SolidWorksSession,
    geometry_id: str,
    config: SolidWorksBackendConfig,
) -> GeneratedCanonicalPart:
    recipe = lookup_recipe(geometry_id)
    plan = plan_from_recipe(recipe)
    destination = _prepare_destination(config, geometry_id)
    model = session.new_part()
    try:
        construct_plan(session, model, plan)
        after_save = validate_model(session, model, plan)
        session.save_as(model, destination)
    finally:
        session.close_doc(model)

    reopened = session.open_part(destination)
    try:
        after_reopen = validate_model(session, reopened, plan)
    finally:
        session.close_doc(reopened)

    locator = BoundPartLocator(
        identity=LogicalPartIdentity.from_geometry_id(geometry_id),
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
    )


def generate_canonical_parts(
    config: SolidWorksBackendConfig | None = None,
) -> tuple[GeneratedCanonicalPart, ...]:
    """Materialize all four qualified armor recipes as reusable SLDPRT files."""
    resolved = config if config is not None else load_solidworks_backend_config()
    results: list[GeneratedCanonicalPart] = []
    with SolidWorksSession(resolved) as session:
        for geometry_id in canonical_geometry_ids():
            results.append(
                generate_one_canonical_part(session, geometry_id, resolved)
            )
    return tuple(results)
