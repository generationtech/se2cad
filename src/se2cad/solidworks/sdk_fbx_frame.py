"""CAD-neutral frame rule for multi-node official SDK FBX imports.

Keen/3ds Max FBX nodes may carry a Geometric translation that applies
only to that node's own mesh. Blender's FBX importer folds Geometric
transforms into the object transform, so mesh children incorrectly
inherit a parent translation that the parent's own vertices already
cancel.

This module decides which descendant world translations to neutralize.
It does not import Blender, does not name block identities, and does
not modify official SDK files.
"""

from __future__ import annotations

from dataclasses import dataclass

# Ignore numerical residue after Blender FBX import.
_TRANSLATION_EPS_M = 1.0e-3
# A root mesh whose world center is this close to the model origin is
# already in the Keen block/model frame.
_ORIGIN_ABS_M = 0.15
_ORIGIN_RATIO = 0.20
# A root mesh whose world center tracks the node translation is using
# ordinary inherited local geometry.
_INHERIT_ABS_M = 0.15
_INHERIT_RATIO = 0.20
# A parentless mesh must be a substantial body before its translation
# may be treated as a baked geometric offset.
_MIN_ROOT_MESH_EXTENT_M = 0.50


class AmbiguousFbxFrameError(ValueError):
    """Imported mesh-node frames cannot be interpreted deterministically."""


@dataclass(frozen=True)
class ImportedMeshNode:
    """One imported mesh after Blender FBX import, before join."""

    name: str
    parent_name: str | None
    world_translation: tuple[float, float, float]
    world_mesh_center: tuple[float, float, float]
    world_mesh_size: tuple[float, float, float]


def inherited_root_translations_to_neutralize(
    nodes: tuple[ImportedMeshNode, ...] | list[ImportedMeshNode],
) -> dict[str, tuple[float, float, float]]:
    """Return descendant name → world translation to subtract.

    A parentless mesh whose own world geometry is already origin-local
    while its node translation is non-zero has a baked geometric
    translation. Descendants must not inherit that translation.

    A parentless mesh whose world geometry tracks its node translation
    is ordinary local-space geometry; descendants keep the inherited
    transform.

    A parentless mesh that looks baked is still left unchanged when the
    imported combined world of that root plus its descendants is already
    origin-local. Neutralizing those children would displace a correct
    multi-cell body.

    Any other non-zero parentless translation is left unchanged. The
    current all-world join remains valid for those files; inventing a
    correction without a baked-frame proof is refused.
    """
    items = tuple(nodes)
    if not items:
        return {}
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise AmbiguousFbxFrameError("imported mesh node names are not unique")
    by_name = {item.name: item for item in items}
    children: dict[str, list[str]] = {item.name: [] for item in items}
    for item in items:
        if item.parent_name is None:
            continue
        if item.parent_name not in children:
            continue
        children[item.parent_name].append(item.name)

    corrections: dict[str, tuple[float, float, float]] = {}
    for item in items:
        if item.parent_name is not None and item.parent_name in by_name:
            continue
        descendants = _descendants(item.name, children)
        if not descendants:
            continue
        translation = item.world_translation
        magnitude = _length(translation)
        if magnitude <= _TRANSLATION_EPS_M:
            continue
        center = item.world_mesh_center
        center_mag = _length(center)
        inherit_mag = _length(_sub(center, translation))
        origin_limit = max(_ORIGIN_ABS_M, _ORIGIN_RATIO * magnitude)
        inherit_limit = max(_INHERIT_ABS_M, _INHERIT_RATIO * magnitude)
        origin_local = center_mag <= origin_limit
        translation_local = inherit_mag <= inherit_limit
        if origin_local and translation_local:
            continue
        if translation_local:
            continue
        if not origin_local:
            continue
        longest = max(item.world_mesh_size)
        if longest < _MIN_ROOT_MESH_EXTENT_M:
            continue
        subtree = (item,) + tuple(by_name[name] for name in descendants if name in by_name)
        combined_center = _union_center(subtree)
        if _length(combined_center) <= origin_limit:
            # Imported world is already the block/model frame. Neutralizing
            # would move correctly placed children, as on HydrogenTank.
            continue
        for descendant in descendants:
            previous = corrections.get(descendant)
            if previous is not None and _length(_sub(previous, translation)) > _TRANSLATION_EPS_M:
                raise AmbiguousFbxFrameError(
                    "conflicting inherited translations for one mesh descendant"
                )
            corrections[descendant] = translation
    return corrections


def _descendants(name: str, children: dict[str, list[str]]) -> list[str]:
    found: list[str] = []
    stack = list(children.get(name, ()))
    while stack:
        current = stack.pop()
        found.append(current)
        stack.extend(children.get(current, ()))
    return found


def _union_center(nodes: tuple[ImportedMeshNode, ...] | list[ImportedMeshNode]) -> tuple[float, float, float]:
    mins = [None, None, None]
    maxs = [None, None, None]
    for item in nodes:
        half = tuple(axis * 0.5 for axis in item.world_mesh_size)
        low = _sub(item.world_mesh_center, half)
        high = (
            item.world_mesh_center[0] + half[0],
            item.world_mesh_center[1] + half[1],
            item.world_mesh_center[2] + half[2],
        )
        for i in range(3):
            mins[i] = low[i] if mins[i] is None else min(mins[i], low[i])
            maxs[i] = high[i] if maxs[i] is None else max(maxs[i], high[i])
    if any(value is None for value in mins):
        return (0.0, 0.0, 0.0)
    return tuple((mins[i] + maxs[i]) * 0.5 for i in range(3))


def _length(values: tuple[float, float, float]) -> float:
    return (values[0] ** 2 + values[1] ** 2 + values[2] ** 2) ** 0.5


def _sub(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


__all__ = [
    "AmbiguousFbxFrameError",
    "ImportedMeshNode",
    "inherited_root_translations_to_neutralize",
]
