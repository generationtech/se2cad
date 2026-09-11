"""Stable geometry identities for runtime-resolved vanilla TriangleMesh blocks."""

from __future__ import annotations

from se2cad.catalog.loader import checked_geometry_id
from se2cad.catalog.model import CellSize
from se2cad.ir.convert import empty_subtype_placement_key, runtime_placement_key
from se2cad.library.lookup import packaged_library_geometry_ids

VANILLA_RUNTIME_GEOMETRY_PREFIX = "vanilla_lg_1x1x1_"
VANILLA_RUNTIME_MULTICELL_PREFIX = "vanilla_lg_"
VANILLA_RUNTIME_EMPTY_TYPE_INFIX = "empty_"
_UNIT_CELL = CellSize(1, 1, 1)
_GEOMETRY_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")


def _snake_case_subtype(subtype_id: str) -> str:
    chars: list[str] = []
    length = len(subtype_id)
    for index, char in enumerate(subtype_id):
        if char.isupper() and index > 0:
            previous = subtype_id[index - 1]
            nxt = subtype_id[index + 1] if index + 1 < length else ""
            if previous.islower() or (nxt.islower() and previous.isupper()):
                chars.append("_")
        if char.isalnum():
            chars.append(char.lower())
        elif char in {"_", "-"}:
            chars.append("_")
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug


def vanilla_runtime_geometry_id(
    subtype_id: str,
    size: CellSize | None = None,
) -> str:
    """Derive a filesystem-safe vanilla runtime geometry identity.

    The identity is a function of SubtypeName and whether Size is the
    previously qualified 1×1×1 cell. It does not include operator paths,
    orientation, Min, or source index. Existing 1×1×1 IDs keep the
    ``vanilla_lg_1x1x1_`` prefix so qualified caches stay valid.
    Multi-cell identities use the size-neutral ``vanilla_lg_`` prefix.
    """
    if not isinstance(subtype_id, str) or subtype_id == "":
        raise ValueError("subtype_id must be a non-empty string")
    if size is not None and not isinstance(size, CellSize):
        raise ValueError("size must be a CellSize when supplied")
    slug = _snake_case_subtype(subtype_id)
    if slug == "" or slug[0] not in "abcdefghijklmnopqrstuvwxyz":
        raise ValueError(
            f"subtype_id {subtype_id!r} cannot form a safe vanilla geometry_id"
        )
    prefix = VANILLA_RUNTIME_GEOMETRY_PREFIX
    if size is not None and size != _UNIT_CELL:
        prefix = VANILLA_RUNTIME_MULTICELL_PREFIX
    identity = checked_geometry_id(
        f"{prefix}{slug}",
        f"vanilla geometry_id for {subtype_id!r}",
    )
    if identity in packaged_library_geometry_ids():
        raise ValueError(
            f"vanilla geometry_id {identity!r} collides with a packaged library identity"
        )
    return identity


def vanilla_runtime_geometry_id_for_empty_type(
    type_id: str,
    size: CellSize | None = None,
) -> str:
    """Derive a filesystem-safe identity for an empty-SubtypeId definition.

    The slug is the vanilla TypeId, marked ``empty_`` so it is not a
    pretend non-empty SubtypeId. The identity does not include Min,
    orientation, source index, or operator paths.
    """
    if not isinstance(type_id, str) or type_id == "":
        raise ValueError("type_id must be a non-empty string")
    if size is not None and not isinstance(size, CellSize):
        raise ValueError("size must be a CellSize when supplied")
    slug = _snake_case_subtype(type_id)
    if slug == "" or slug[0] not in "abcdefghijklmnopqrstuvwxyz":
        raise ValueError(
            f"type_id {type_id!r} cannot form a safe vanilla geometry_id"
        )
    prefix = VANILLA_RUNTIME_GEOMETRY_PREFIX
    if size is not None and size != _UNIT_CELL:
        prefix = VANILLA_RUNTIME_MULTICELL_PREFIX
    identity = checked_geometry_id(
        f"{prefix}{VANILLA_RUNTIME_EMPTY_TYPE_INFIX}{slug}",
        f"vanilla geometry_id for empty-subtype TypeId {type_id!r}",
    )
    if identity in packaged_library_geometry_ids():
        raise ValueError(
            f"vanilla geometry_id {identity!r} collides with a packaged library identity"
        )
    return identity
