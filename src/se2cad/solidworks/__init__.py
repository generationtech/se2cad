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
    TREATED_PART_STEM_SUFFIX,
    assembly_path_for,
    artifact_path_for,
    canonical_geometry_ids,
    contained_destination,
    is_treated_artifact_filename,
    logical_assembly_filename,
    logical_assembly_part_filename,
    logical_part_filename,
    logical_treated_part_filename,
    part_artifact_path,
    treated_artifact_key,
    treated_artifact_path_for,
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
    SdkConversionError,
    SdkSourceError,
    SolidWorksConfigError,
    UnknownCanonicalPartError,
)
from se2cad.solidworks.locator import BoundPartLocator, LogicalPartIdentity
from se2cad.solidworks.pipeline import (
    BlueprintRecipeResolution,
    resolve_recipes_from_blueprint,
)
from se2cad.solidworks.materialize import (
    ArtifactMaterialization,
    AssemblyMaterializationReport,
    demanded_untreated_geometry_ids,
    ensure_untreated_canonical_parts,
    has_qualified_untreated_builder,
    materialize_required_parts,
    missing_untreated_geometry_ids,
)
from se2cad.solidworks.placement import (
    AssemblyTreatmentReport,
    ChamferFallback,
    ComponentPlacement,
    demanded_treated_geometry_ids,
    missing_treated_geometry_ids,
    placements_from_ir,
    require_canonical_part_files,
    resolved_assembly_part_filename,
    treatment_report_from_ir,
)
from se2cad.solidworks.recipe_plan import ConstructionPlan, plan_from_recipe
from se2cad.solidworks.transform_pack import solidworks_arraydata
from se2cad.solidworks.units import mm_to_metres, metres_to_mm, point_mm_to_metres


def generate_canonical_parts(
    config: SolidWorksBackendConfig | None = None,
    treatment=None,
    geometry_ids=None,
):
    """Generate canonical parts. Requires Windows + pywin32 + SolidWorks.

    Default ``geometry_ids`` remains the four initial-program identities.
    Untreated ``{geometry_id}.SLDPRT`` remain the default. Pass
    ``EDGE_TREATMENT_CHAMFER`` to write size-specific treated siblings
    for the requested identities only.
    """
    from se2cad.solidworks.generate import generate_canonical_parts as impl

    return impl(config, treatment=treatment, geometry_ids=geometry_ids)


def generate_representative_automatable_parts(
    config: SolidWorksBackendConfig | None = None,
    treatment=None,
):
    """Generate the S2C-11.4.1 representative automatable subset."""
    from se2cad.solidworks.generate import (
        generate_representative_automatable_parts as impl,
    )

    return impl(config, treatment=treatment)


def generate_assembly(
    blueprint_path,
    config: SolidWorksBackendConfig | None = None,
    treatment=None,
    policy=None,
):
    """Generate a transform-placed SLDASM. Requires Windows + pywin32 + SolidWorks.

    Default inserts untreated ``{geometry_id}.SLDPRT``, generating
    missing qualified untreated bases on demand. Pass
    ``EDGE_TREATMENT_CHAMFER`` to insert size-specific treated siblings
    after those bases exist. Default policy is strict.
    """
    from se2cad.policy import ConversionPolicy
    from se2cad.solidworks.assemble import generate_assembly as impl

    chosen = ConversionPolicy.STRICT if policy is None else policy
    return impl(blueprint_path, config, treatment=treatment, policy=chosen)


__all__ = [
    "APPEARANCE_RGB_TOLERANCE",
    "GENERATED_ROOT_ENV",
    "SATURATION_DELTA",
    "TREATED_PART_STEM_SUFFIX",
    "VALUE_DELTA",
    "ArtifactMaterialization",
    "AssemblyMaterializationReport",
    "AssemblyTreatmentReport",
    "ChamferFallback",
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
    "SdkConversionError",
    "SdkSourceError",
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
    "demanded_treated_geometry_ids",
    "demanded_untreated_geometry_ids",
    "ensure_untreated_canonical_parts",
    "generate_assembly",
    "generate_canonical_parts",
    "generate_representative_automatable_parts",
    "has_qualified_untreated_builder",
    "is_treated_artifact_filename",
    "load_solidworks_backend_config",
    "logical_assembly_filename",
    "logical_assembly_part_filename",
    "logical_part_filename",
    "logical_treated_part_filename",
    "materialize_required_parts",
    "missing_treated_geometry_ids",
    "missing_untreated_geometry_ids",
    "part_artifact_path",
    "resolved_assembly_part_filename",
    "treated_artifact_key",
    "treated_artifact_path_for",
    "treatment_report_from_ir",
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
