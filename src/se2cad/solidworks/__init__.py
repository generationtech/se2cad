"""Windows-local SolidWorks backend.

CAD-neutral surfaces import without pywin32. COM modules are loaded only
when a SolidWorks session is requested.
"""

from se2cad.solidworks.appearance import (
    APPEARANCE_RGB_TOLERANCE,
    SATURATION_DELTA,
    VALUE_DELTA,
    color_mask_hsv_to_rgb,
    hsv_offset_to_hsv,
    hsv_to_rgb,
    material_property_values,
    quantize_rgb_8bit,
)
from se2cad.solidworks.artifacts import (
    assembly_path_for,
    artifact_path_for,
    canonical_geometry_ids,
    contained_destination,
    logical_assembly_filename,
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
    AssemblyIdentityError,
    AssemblyValidationError,
    CanonicalPartValidationError,
    GeneratedRootError,
    MissingCanonicalPartError,
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
from se2cad.solidworks.placement import (
    ComponentPlacement,
    placements_from_ir,
    require_canonical_part_files,
)
from se2cad.solidworks.recipe_plan import ConstructionPlan, plan_from_recipe
from se2cad.solidworks.transform_pack import solidworks_arraydata
from se2cad.solidworks.units import mm_to_metres, metres_to_mm, point_mm_to_metres


def generate_canonical_parts(config: SolidWorksBackendConfig | None = None):
    """Generate the four canonical parts. Requires Windows + pywin32 + SolidWorks."""
    from se2cad.solidworks.generate import generate_canonical_parts as impl

    return impl(config)


def generate_assembly(blueprint_path, config: SolidWorksBackendConfig | None = None):
    """Generate a transform-placed SLDASM. Requires Windows + pywin32 + SolidWorks."""
    from se2cad.solidworks.assemble import generate_assembly as impl

    return impl(blueprint_path, config)


__all__ = [
    "APPEARANCE_RGB_TOLERANCE",
    "GENERATED_ROOT_ENV",
    "SATURATION_DELTA",
    "VALUE_DELTA",
    "AssemblyIdentityError",
    "AssemblyValidationError",
    "BoundPartLocator",
    "BlueprintRecipeResolution",
    "CanonicalPartValidationError",
    "ComponentPlacement",
    "ConstructionPlan",
    "GeneratedRootError",
    "LogicalPartIdentity",
    "MissingCanonicalPartError",
    "SolidWorksBackendConfig",
    "SolidWorksBackendError",
    "SolidWorksBackendUnavailableError",
    "SolidWorksComError",
    "SolidWorksConfigError",
    "UnknownCanonicalPartError",
    "assembly_path_for",
    "artifact_path_for",
    "canonical_geometry_ids",
    "color_mask_hsv_to_rgb",
    "hsv_offset_to_hsv",
    "hsv_to_rgb",
    "material_property_values",
    "quantize_rgb_8bit",
    "contained_destination",
    "generate_assembly",
    "generate_canonical_parts",
    "load_solidworks_backend_config",
    "logical_assembly_filename",
    "logical_part_filename",
    "metres_to_mm",
    "mm_to_metres",
    "placements_from_ir",
    "plan_from_recipe",
    "point_mm_to_metres",
    "require_canonical_part_files",
    "resolve_recipes_from_blueprint",
    "solidworks_arraydata",
    "solidworks_backend_available",
    "solidworks_backend_status",
]
