"""Windows-local SolidWorks backend.

CAD-neutral surfaces import without pywin32. COM modules are loaded only
when a SolidWorks session is requested.
"""

from se2cad.solidworks.artifacts import (
    artifact_path_for,
    canonical_geometry_ids,
    contained_destination,
    logical_part_filename,
)
from se2cad.solidworks.availability import (
    solidworks_backend_available,
    solidworks_backend_status,
)
from se2cad.solidworks.config import (
    GENERATED_ROOT_ENV,
    SolidWorksBackendConfig,
    load_solidworks_backend_config,
)
from se2cad.solidworks.errors import (
    CanonicalPartValidationError,
    GeneratedRootError,
    SolidWorksBackendError,
    SolidWorksBackendUnavailableError,
    SolidWorksComError,
    SolidWorksConfigError,
    UnknownCanonicalPartError,
)
from se2cad.solidworks.locator import BoundPartLocator, LogicalPartIdentity
from se2cad.solidworks.pipeline import (
    BlueprintRecipeResolution,
    resolve_recipes_from_blueprint,
)
from se2cad.solidworks.recipe_plan import ConstructionPlan, plan_from_recipe
from se2cad.solidworks.units import mm_to_metres, metres_to_mm, point_mm_to_metres


def generate_canonical_parts(config: SolidWorksBackendConfig | None = None):
    """Generate the four canonical parts. Requires Windows + pywin32 + SolidWorks."""
    from se2cad.solidworks.generate import generate_canonical_parts as impl

    return impl(config)


__all__ = [
    "GENERATED_ROOT_ENV",
    "BoundPartLocator",
    "BlueprintRecipeResolution",
    "CanonicalPartValidationError",
    "ConstructionPlan",
    "GeneratedRootError",
    "LogicalPartIdentity",
    "SolidWorksBackendConfig",
    "SolidWorksBackendError",
    "SolidWorksBackendUnavailableError",
    "SolidWorksComError",
    "SolidWorksConfigError",
    "UnknownCanonicalPartError",
    "artifact_path_for",
    "canonical_geometry_ids",
    "contained_destination",
    "generate_canonical_parts",
    "load_solidworks_backend_config",
    "logical_part_filename",
    "metres_to_mm",
    "mm_to_metres",
    "plan_from_recipe",
    "point_mm_to_metres",
    "resolve_recipes_from_blueprint",
    "solidworks_backend_available",
    "solidworks_backend_status",
]
