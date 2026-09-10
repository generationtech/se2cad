"""Stable geometry identities for runtime-resolved vanilla 1x1x1 blocks."""

from __future__ import annotations

from se2cad.catalog.loader import checked_geometry_id
from se2cad.library.lookup import packaged_library_geometry_ids

VANILLA_RUNTIME_GEOMETRY_PREFIX = "vanilla_lg_1x1x1_"
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


def vanilla_runtime_geometry_id(subtype_id: str) -> str:
    """Derive a filesystem-safe vanilla runtime geometry identity.

    The identity is a function of SubtypeName only. It does not include
    operator paths. The ``vanilla_lg_1x1x1_`` prefix keeps it distinct
    from hand-authored packaged identities.
    """
    if not isinstance(subtype_id, str) or subtype_id == "":
        raise ValueError("subtype_id must be a non-empty string")
    slug = _snake_case_subtype(subtype_id)
    if slug == "" or slug[0] not in "abcdefghijklmnopqrstuvwxyz":
        raise ValueError(
            f"subtype_id {subtype_id!r} cannot form a safe vanilla geometry_id"
        )
    identity = checked_geometry_id(
        f"{VANILLA_RUNTIME_GEOMETRY_PREFIX}{slug}",
        f"vanilla geometry_id for {subtype_id!r}",
    )
    if identity in packaged_library_geometry_ids():
        raise ValueError(
            f"vanilla geometry_id {identity!r} collides with a packaged library identity"
        )
    return identity
