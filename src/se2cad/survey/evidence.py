"""Read-only definition and source evidence for survey classification.

This module does not grant runtime support and does not persist records.
It prefers existing targeted lookup plus contained path probes.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from se2cad.catalog.model import CellSize
from se2cad.survey.classify import blocker_kind_for
from se2cad.survey.model import BlockerKind, IdentityEvidence, RootCause
from se2cad.transform.placement import ModelOffset
from se2cad.vanilla.errors import VanillaLookupError
from se2cad.vanilla.lookup import TargetedDefinition, TargetedHit, lookup_exact_subtype
from se2cad.vanilla.mapping import contained_game_model_path, sdk_stem_from_vanilla_model
from se2cad.vanilla.resolve import eligibility_reason

_MAX_OCCUPANCY_AXIS = 32


def _local_name(el: ET.Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return str(tag)


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if _local_name(child) == name]


def collect_identity_evidence(
    subtype_id: str,
    instance_count: int,
    *,
    game_root: Path | None,
    sdk_root: Path | None,
    eligibility: Optional[str],
    cause: RootCause | None,
) -> IdentityEvidence:
    """Collect definition/source facts for one SubtypeId."""
    hit: TargetedHit | None = None
    if game_root is not None:
        try:
            hit = lookup_exact_subtype(subtype_id, game_root)
        except VanillaLookupError as exc:
            return _empty_evidence(
                subtype_id,
                instance_count,
                eligibility=eligibility or str(exc),
                cause=cause,
                unusable_reason=str(exc),
            )

    definition = hit.definition if hit is not None else None
    extra = _extra_definition_facts(hit, game_root) if hit is not None else None
    observed_cube_topology = (
        definition.cube_topology if definition is not None else None
    )
    observed_block_topology = (
        definition.block_topology if definition is not None else None
    )
    if extra is not None:
        if observed_cube_topology is None:
            observed_cube_topology = extra[2]
        if observed_block_topology is None:
            observed_block_topology = extra[3]
    mwm_exists: Optional[bool] = None
    sdk_exists: Optional[bool] = None
    sdk_relative: Optional[str] = None
    sdk_format: Optional[str] = None
    sdk_reason: Optional[str] = None
    primary = definition.primary_model if definition is not None else None
    if game_root is not None and definition is not None and primary:
        try:
            mwm_path = contained_game_model_path(game_root, primary)
            mwm_exists = mwm_path.is_file()
        except VanillaLookupError:
            mwm_exists = False
        sdk_exists, sdk_relative, sdk_format, sdk_reason = _probe_sdk_fbx(
            primary, sdk_root=sdk_root
        )

    size = definition.size if definition is not None else None
    placement_ok = _placement_size_supported(size)
    materializer_ok = (
        cause is None
        and definition is not None
        and eligibility is None
        and sdk_exists is True
        and sdk_format in {"binary", "ascii"}
    )
    return IdentityEvidence(
        subtype_id=subtype_id,
        instance_count=instance_count,
        exact_vanilla_definition=definition is not None,
        cube_size=definition.cube_size if definition is not None else None,
        size=size,
        block_topology=observed_block_topology,
        cube_topology=observed_cube_topology,
        primary_model=primary,
        model_count=(
            extra[0]
            if extra is not None
            else (definition.model_count if definition is not None else 0)
        ),
        subparts_present=(
            extra[1] > 0
            if extra is not None
            else bool(definition.has_subparts) if definition is not None else False
        ),
        subpart_count=extra[1] if extra is not None else 0,
        model_offset=definition.model_offset if definition is not None else None,
        definition_source_relative=(
            hit.source_relative if hit is not None else None
        ),
        unusable_reason=hit.unusable_reason if hit is not None else None,
        game_mwm_exists=mwm_exists,
        sdk_fbx_exists=sdk_exists,
        sdk_fbx_relative=sdk_relative,
        sdk_fbx_format=sdk_format,
        sdk_fbx_probe_reason=sdk_reason,
        eligibility_reason=(
            eligibility
            if eligibility is not None
            else (eligibility_reason(definition) if definition is not None else None)
        ),
        placement_size_supported=placement_ok,
        materializer_theoretically_handles=materializer_ok,
        blocker_kind=blocker_kind_for(cause),
    )


def evidence_from_definition(
    definition: TargetedDefinition,
    *,
    instance_count: int,
    source_relative: str,
    eligibility: Optional[str],
) -> IdentityEvidence:
    """Build evidence from an already-loaded targeted definition."""
    return IdentityEvidence(
        subtype_id=definition.subtype_id,
        instance_count=instance_count,
        exact_vanilla_definition=True,
        cube_size=definition.cube_size,
        size=definition.size,
        block_topology=definition.block_topology,
        cube_topology=definition.cube_topology,
        primary_model=definition.primary_model or None,
        model_count=definition.model_count,
        subparts_present=definition.has_subparts,
        subpart_count=0,
        model_offset=definition.model_offset,
        definition_source_relative=source_relative,
        unusable_reason=None,
        game_mwm_exists=None,
        sdk_fbx_exists=None,
        sdk_fbx_relative=None,
        sdk_fbx_format=None,
        sdk_fbx_probe_reason=None,
        eligibility_reason=eligibility,
        placement_size_supported=_placement_size_supported(definition.size),
        materializer_theoretically_handles=eligibility is None,
        blocker_kind=None,
    )


def empty_identity_evidence(
    subtype_id: str,
    instance_count: int,
    *,
    eligibility: Optional[str],
    cause: RootCause | None,
) -> IdentityEvidence:
    return _empty_evidence(
        subtype_id,
        instance_count,
        eligibility=eligibility,
        cause=cause,
        unusable_reason=None,
    )


def _empty_evidence(
    subtype_id: str,
    instance_count: int,
    *,
    eligibility: Optional[str],
    cause: RootCause | None,
    unusable_reason: Optional[str],
) -> IdentityEvidence:
    return IdentityEvidence(
        subtype_id=subtype_id,
        instance_count=instance_count,
        exact_vanilla_definition=False,
        cube_size=None,
        size=None,
        block_topology=None,
        cube_topology=None,
        primary_model=None,
        model_count=0,
        subparts_present=False,
        subpart_count=0,
        model_offset=None,
        definition_source_relative=None,
        unusable_reason=unusable_reason,
        game_mwm_exists=None,
        sdk_fbx_exists=None,
        sdk_fbx_relative=None,
        sdk_fbx_format=None,
        sdk_fbx_probe_reason=None,
        eligibility_reason=eligibility,
        placement_size_supported=False,
        materializer_theoretically_handles=False,
        blocker_kind=blocker_kind_for(cause),
    )


def _placement_size_supported(size: CellSize | None) -> bool:
    if size is None:
        return False
    axes = (size.x, size.y, size.z)
    return all(1 <= axis <= _MAX_OCCUPANCY_AXIS for axis in axes)


def _extra_definition_facts(
    hit: TargetedHit,
    game_root: Path,
) -> tuple[int, int, str | None, str | None] | None:
    """Return model_count, subpart_count, CubeTopology, BlockTopology."""
    source = game_root / Path(*hit.source_relative.split("/"))
    try:
        contained = source.expanduser().resolve()
        contained.relative_to(game_root.expanduser().resolve())
        text = contained.read_text(encoding="utf-8")
        root = ET.fromstring(text)
    except (OSError, ValueError, ET.ParseError):
        return None
    for cube_blocks in root.iter():
        if _local_name(cube_blocks) != "CubeBlocks":
            continue
        for definition in list(cube_blocks):
            if _local_name(definition) != "Definition":
                continue
            ids = _children(definition, "Id")
            if not ids:
                continue
            subtype = ids[0].findtext("SubtypeId")
            if subtype is None:
                subtype = ids[0].get("Subtype")
            if subtype != hit.subtype_id:
                continue
            models = _children(definition, "Model")
            subpart_count = 0
            for subparts in _children(definition, "Subparts"):
                subpart_count += sum(1 for _child in list(subparts))
            cube_topology = None
            cube_defs = _children(definition, "CubeDefinition")
            if cube_defs:
                tokens = _children(cube_defs[0], "CubeTopology")
                if tokens:
                    cube_topology = (tokens[0].text or "").strip() or None
            topologies = _children(definition, "BlockTopology")
            block_topology = None
            if topologies:
                block_topology = (topologies[0].text or "").strip() or None
            return len(models), subpart_count, cube_topology, block_topology
    return None


def _probe_sdk_fbx(
    primary_model: str,
    *,
    sdk_root: Path | None,
) -> tuple[Optional[bool], Optional[str], Optional[str], Optional[str]]:
    if sdk_root is None:
        return None, None, None, "SDK root is not configured"
    try:
        stem = sdk_stem_from_vanilla_model(primary_model)
    except VanillaLookupError as exc:
        return False, None, None, str(exc)
    parts = tuple(Path(stem + ".fbx").parts)
    try:
        found = _unique_casefold_file(sdk_root, parts)
    except VanillaLookupError as exc:
        message = str(exc)
        if "ambiguous" in message.lower():
            return False, None, None, message
        return False, "/".join(parts), None, message
    relative = found.relative_to(sdk_root.expanduser().resolve()).as_posix()
    try:
        from se2cad.solidworks.sdk_fbx_format import classify_sdk_fbx

        classified = classify_sdk_fbx(found)
        return True, relative, classified.kind.value, classified.reason
    except Exception as exc:  # noqa: BLE001 — survey probe must stay fail-soft
        return True, relative, None, str(exc)


def _unique_casefold_file(root: Path, parts: tuple[str, ...]) -> Path:
    resolved_root = root.expanduser().resolve()
    current = resolved_root
    relative = "/".join(parts)
    for index, part in enumerate(parts):
        try:
            current.relative_to(resolved_root)
        except ValueError as exc:
            raise VanillaLookupError(
                f"path {current} escapes configured SDK root {resolved_root}"
            ) from exc
        if not current.is_dir():
            raise VanillaLookupError(
                f"authorized SDK source is not a file: {resolved_root / relative}"
            )
        is_last = index == len(parts) - 1
        matches = [
            child
            for child in current.iterdir()
            if child.name.lower() == part.lower()
            and ((is_last and child.is_file()) or (not is_last and child.is_dir()))
        ]
        if not matches:
            raise VanillaLookupError(
                f"authorized SDK source is not a file: {resolved_root / relative}"
            )
        if len(matches) > 1:
            names = ", ".join(sorted(child.name for child in matches))
            raise VanillaLookupError(
                f"ambiguous SDK path {part!r} under {current}: {names}"
            )
        current = matches[0].resolve()
    return current
