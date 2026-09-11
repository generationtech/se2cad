"""Demand-driven vanilla TriangleMesh resolution.

Packaged catalog hits are returned unchanged. Catalog-unknown identities
may receive a transient runtime bind only when every eligibility rule
passes. This module does not write the packaged catalog.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from se2cad.catalog.constants import CATALOG_CUBE_SIZE_LARGE
from se2cad.catalog.errors import UnknownSubtypeError
from se2cad.catalog.model import CatalogEntry, DefinitionCatalog
from se2cad.vanilla.errors import VanillaLookupError, VanillaRootError
from se2cad.vanilla.identity import (
    empty_subtype_placement_key,
    vanilla_runtime_geometry_id,
    vanilla_runtime_geometry_id_for_empty_type,
)
from se2cad.vanilla.lookup import (
    TargetedDefinition,
    lookup_exact_subtype,
    lookup_unique_empty_subtype,
    type_id_from_object_builder,
)
from se2cad.vanilla.mapping import contained_game_model_path, sdk_stem_from_vanilla_model
from se2cad.vanilla.record import (
    RuntimeVanillaRecord,
    register_runtime_vanilla_record,
    runtime_sdk_mesh_record,
)
from se2cad.vanilla.roots import try_load_game_content_root, try_load_sdk_root

_TRIANGLE_MESH = "TriangleMesh"
_MAX_OCCUPANCY_AXIS = 32


class VanillaResolveKind(str, Enum):
    PACKAGED = "packaged"
    RUNTIME_VANILLA = "runtime_vanilla"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class VanillaResolveResult:
    """Outcome of one subtype resolution. Indexing is not a support grant."""

    kind: VanillaResolveKind
    subtype_id: str
    catalog_entry: CatalogEntry | None
    runtime: RuntimeVanillaRecord | None
    unresolved_reason: Optional[str]


_RESULT_LOCK = threading.Lock()
_RESULT_CACHE: dict[tuple[str, str, str, str], VanillaResolveResult] = {}


def clear_vanilla_resolution_cache() -> None:
    """Drop per-conversion resolve results. Tests use this for isolation."""
    with _RESULT_LOCK:
        _RESULT_CACHE.clear()


def resolve_vanilla_geometry(
    subtype_id: str,
    catalog: DefinitionCatalog,
    *,
    object_builder_type: str | None = None,
    game_root: Path | None = None,
    sdk_root: Path | None = None,
) -> VanillaResolveResult:
    """Resolve a packaged record, a transient vanilla record, or unresolved.

    Duplicate exact SubtypeId definitions and unsafe SDK mapping fail
    closed. Missing configuration, missing definitions, and ineligible
    identities remain unresolved.

    An empty ``subtype_id`` resolves only when ``object_builder_type``
    and the Large Grid context identify exactly one empty-SubtypeId
    vanilla definition. That is not a general empty-subtype grant.
    """
    if not isinstance(subtype_id, str):
        raise VanillaLookupError("subtype_id must be a string")
    if subtype_id != "":
        try:
            entry = catalog.lookup(subtype_id)
        except UnknownSubtypeError:
            entry = None
        else:
            return VanillaResolveResult(
                kind=VanillaResolveKind.PACKAGED,
                subtype_id=subtype_id,
                catalog_entry=entry,
                runtime=None,
                unresolved_reason=None,
            )
    elif object_builder_type is None or object_builder_type == "":
        return _unresolved(
            subtype_id,
            "empty SubtypeName is missing an object-builder type",
        )

    resolved_game = _optional_resolved_root(game_root)
    if resolved_game is None:
        resolved_game = try_load_game_content_root()
    if resolved_game is None:
        return _unresolved(subtype_id, "game-content root is not configured")

    resolved_sdk = _optional_resolved_root(sdk_root)
    cache_key = _cache_key(
        subtype_id, object_builder_type, resolved_game, resolved_sdk
    )
    with _RESULT_LOCK:
        cached = _RESULT_CACHE.get(cache_key)
        if cached is not None:
            if cached.kind is VanillaResolveKind.RUNTIME_VANILLA:
                assert cached.runtime is not None
                register_runtime_vanilla_record(cached.runtime)
            return cached

    if subtype_id == "":
        result = _resolve_empty_subtype(
            object_builder_type=object_builder_type,
            game_root=resolved_game,
            sdk_root=resolved_sdk,
        )
    else:
        result = _resolve_unknown(
            subtype_id,
            game_root=resolved_game,
            sdk_root=resolved_sdk,
        )
    with _RESULT_LOCK:
        _RESULT_CACHE[cache_key] = result
    return result


def _cache_key(
    subtype_id: str,
    object_builder_type: str | None,
    game_root: Path,
    sdk_root: Path | None,
) -> tuple[str, str, str, str]:
    return (
        subtype_id,
        object_builder_type or "",
        str(game_root),
        str(sdk_root) if sdk_root is not None else "",
    )


def eligibility_reason(definition: TargetedDefinition) -> Optional[str]:
    """Return why a targeted definition is ineligible, or None if eligible."""
    if definition.cube_size != CATALOG_CUBE_SIZE_LARGE:
        return f"CubeSize {definition.cube_size!r} is not Large"
    if (
        definition.size.x < 1
        or definition.size.y < 1
        or definition.size.z < 1
    ):
        return (
            "block size "
            f"{definition.size.x}x{definition.size.y}x{definition.size.z} "
            "is not a positive cell triple"
        )
    if (
        definition.size.x > _MAX_OCCUPANCY_AXIS
        or definition.size.y > _MAX_OCCUPANCY_AXIS
        or definition.size.z > _MAX_OCCUPANCY_AXIS
    ):
        return (
            "block size "
            f"{definition.size.x}x{definition.size.y}x{definition.size.z} "
            "exceeds supported occupancy bound"
        )
    if definition.block_topology != _TRIANGLE_MESH:
        return f"BlockTopology {definition.block_topology!r} is not TriangleMesh"
    if definition.cube_topology is not None:
        return "CubeTopology identities are not eligible for this resolver"
    if definition.has_subparts:
        return "definition requires subpart or composite handling"
    if definition.model_count == 0 or definition.primary_model == "":
        return "primary Model is missing"
    if definition.model_count != 1:
        return "primary Model is ambiguous"
    return None


def _resolve_unknown(
    subtype_id: str,
    *,
    game_root: Path,
    sdk_root: Path | None,
) -> VanillaResolveResult:
    hit = lookup_exact_subtype(subtype_id, game_root)
    if hit is None:
        return _unresolved(subtype_id, "vanilla definition not found")
    if hit.definition is None:
        return _unresolved(
            subtype_id,
            hit.unusable_reason or "vanilla definition is unusable",
        )
    return _bind_eligible_hit(
        subtype_id,
        hit.definition,
        hit.source_relative,
        game_root=game_root,
        sdk_root=sdk_root,
    )


def _resolve_empty_subtype(
    *,
    object_builder_type: str,
    game_root: Path,
    sdk_root: Path | None,
) -> VanillaResolveResult:
    try:
        type_id = type_id_from_object_builder(object_builder_type)
    except VanillaLookupError as exc:
        return _unresolved("", str(exc))
    try:
        hit = lookup_unique_empty_subtype(
            type_id,
            cube_size=CATALOG_CUBE_SIZE_LARGE,
            game_root=game_root,
        )
    except VanillaLookupError as exc:
        return _unresolved("", str(exc))
    if hit is None:
        return _unresolved(
            "",
            "empty SubtypeName has no unique vanilla definition for "
            f"{object_builder_type}",
        )
    if hit.definition is None:
        return _unresolved(
            "",
            hit.unusable_reason or "vanilla definition is unusable",
        )
    return _bind_eligible_hit(
        "",
        hit.definition,
        hit.source_relative,
        game_root=game_root,
        sdk_root=sdk_root,
        type_id=type_id,
    )


def _bind_eligible_hit(
    subtype_id: str,
    definition: TargetedDefinition,
    source_relative: str,
    *,
    game_root: Path,
    sdk_root: Path | None,
    type_id: str | None = None,
) -> VanillaResolveResult:
    reason = eligibility_reason(definition)
    if reason is not None:
        return _unresolved(subtype_id, reason)
    try:
        stem = sdk_stem_from_vanilla_model(definition.primary_model)
        contained_game_model_path(game_root, definition.primary_model)
    except VanillaLookupError as exc:
        return _unresolved(subtype_id, str(exc))

    resolved_sdk = sdk_root if sdk_root is not None else try_load_sdk_root()
    if resolved_sdk is None:
        raise VanillaRootError(
            "SDK root is required for vanilla SDK-mesh resolution: "
            "set SE2CAD_SDK_ROOT or se2cad.local.json "
            '{"sdk_root": "..."}'
        )

    if subtype_id == "":
        assert type_id is not None
        try:
            geometry_id = vanilla_runtime_geometry_id_for_empty_type(
                type_id, definition.size
            )
        except ValueError as exc:
            return _unresolved(subtype_id, str(exc))
        placement_key = empty_subtype_placement_key(type_id)
    else:
        geometry_id = vanilla_runtime_geometry_id(subtype_id, definition.size)
        placement_key = subtype_id
    provisional = runtime_sdk_mesh_record(
        subtype_id=subtype_id,
        geometry_id=geometry_id,
        relative_source_stem=stem,
        definition=definition,
        definition_source_relative=source_relative,
        sdk_source_relative=f"{stem}.fbx",
    )
    from se2cad.solidworks.errors import SdkSourceError
    from se2cad.solidworks.sdk_source import resolve_sdk_mesh_file

    try:
        source = resolve_sdk_mesh_file(
            provisional.library_record.recipe, sdk_root=resolved_sdk
        )
    except SdkSourceError as exc:
        message = str(exc)
        if _is_missing_sdk_file(message):
            return _unresolved(subtype_id, message)
        raise VanillaLookupError(message) from exc

    relative_used = source.relative_to(resolved_sdk.expanduser().resolve()).as_posix()
    runtime = runtime_sdk_mesh_record(
        subtype_id=subtype_id,
        geometry_id=geometry_id,
        relative_source_stem=stem,
        definition=definition,
        definition_source_relative=source_relative,
        sdk_source_relative=relative_used,
    )
    register_runtime_vanilla_record(runtime, placement_key=placement_key)
    return VanillaResolveResult(
        kind=VanillaResolveKind.RUNTIME_VANILLA,
        subtype_id=subtype_id,
        catalog_entry=runtime.catalog_entry,
        runtime=runtime,
        unresolved_reason=None,
    )


def _is_missing_sdk_file(message: str) -> bool:
    lowered = message.lower()
    return (
        "is not a file" in lowered
        or "sdk source is not a file" in lowered
        or "not a binary fbx" in lowered
        or "not a valid ascii fbx" in lowered
        or "not a usable binary or ascii fbx" in lowered
        or "ascii fbx conversion is not available" in lowered
        or "ascii fbx " in lowered
        or "ascii fbx" in lowered
        or "ambiguous sdk path" in lowered
    )


def _unresolved(subtype_id: str, reason: str) -> VanillaResolveResult:
    return VanillaResolveResult(
        kind=VanillaResolveKind.UNRESOLVED,
        subtype_id=subtype_id,
        catalog_entry=None,
        runtime=None,
        unresolved_reason=reason,
    )


def _optional_resolved_root(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path.expanduser().resolve()
