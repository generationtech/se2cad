"""Demand-driven vanilla Large Grid TriangleMesh resolution.

S2C-11.8.1 / S2C-11.11.1. Runtime binds are transient. The packaged
catalog is not mutated. This is not universal vanilla support.

``resolve`` is imported lazily so CAD-neutral preflight/policy import
does not load the SolidWorks package.
"""

from se2cad.vanilla.errors import (
    VanillaLookupError,
    VanillaResolutionError,
    VanillaRootError,
)
from se2cad.vanilla.identity import (
    VANILLA_RUNTIME_EMPTY_TYPE_INFIX,
    VANILLA_RUNTIME_GEOMETRY_PREFIX,
    VANILLA_RUNTIME_MULTICELL_PREFIX,
    empty_subtype_placement_key,
    runtime_placement_key,
    vanilla_runtime_geometry_id,
    vanilla_runtime_geometry_id_for_empty_type,
)
from se2cad.vanilla.lookup import (
    CubeBlockIndex,
    TargetedDefinition,
    TargetedHit,
    clear_vanilla_definition_index,
    coalesce_identical_scalar_texts,
    cube_block_index,
    lookup_exact_subtype,
    lookup_unique_empty_subtype,
    type_id_from_object_builder,
)
from se2cad.vanilla.roots import (
    GAME_ROOT_ENV,
    SDK_ROOT_ENV,
    load_game_content_root,
    load_sdk_root,
    try_load_game_content_root,
    try_load_sdk_root,
)

__all__ = [
    "GAME_ROOT_ENV",
    "SDK_ROOT_ENV",
    "VANILLA_RUNTIME_EMPTY_TYPE_INFIX",
    "VANILLA_RUNTIME_GEOMETRY_PREFIX",
    "VANILLA_RUNTIME_MULTICELL_PREFIX",
    "CubeBlockIndex",
    "TargetedDefinition",
    "TargetedHit",
    "VanillaLookupError",
    "VanillaResolutionError",
    "VanillaResolveKind",
    "VanillaResolveResult",
    "VanillaRootError",
    "clear_vanilla_definition_index",
    "clear_vanilla_resolution_cache",
    "clear_vanilla_runtime_state",
    "coalesce_identical_scalar_texts",
    "cube_block_index",
    "eligibility_reason",
    "empty_subtype_placement_key",
    "load_game_content_root",
    "load_sdk_root",
    "lookup_exact_subtype",
    "lookup_unique_empty_subtype",
    "resolve_vanilla_geometry",
    "runtime_placement_key",
    "try_load_game_content_root",
    "try_load_sdk_root",
    "type_id_from_object_builder",
    "vanilla_runtime_geometry_id",
    "vanilla_runtime_geometry_id_for_empty_type",
]


def __getattr__(name: str):
    if name in {
        "VanillaResolveKind",
        "VanillaResolveResult",
        "clear_vanilla_resolution_cache",
        "eligibility_reason",
        "resolve_vanilla_geometry",
    }:
        from se2cad.vanilla import resolve as _resolve

        return getattr(_resolve, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def clear_vanilla_runtime_state() -> None:
    """Drop indexes, resolve cache, and runtime library overlays."""
    from se2cad.library.lookup import clear_runtime_library_records
    from se2cad.ir.convert import clear_runtime_placements
    from se2cad.vanilla.resolve import clear_vanilla_resolution_cache

    clear_vanilla_definition_index()
    clear_vanilla_resolution_cache()
    clear_runtime_library_records()
    clear_runtime_placements()
