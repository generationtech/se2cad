"""Resolve catalog identities from observed definition facts.

Library-build authoring. Runtime lookup still uses the packaged catalog.
This module does not import discovery, scan an install, or generate geometry.
"""

from __future__ import annotations

from se2cad.catalog.constants import CATALOG_CUBE_SIZE_LARGE, CATALOG_SCHEMA_VERSION
from se2cad.catalog.errors import CatalogValidationError
from se2cad.catalog.loader import checked_geometry_id
from se2cad.catalog.model import (
    CatalogEntry,
    DefinitionCatalog,
    ObservedIdentity,
    RecipeKind,
    SupportStatus,
)

# Recorded S2C-2.1.1 geometry identities. New subtypes use the derived rule.
_PRESERVED_GEOMETRY_IDS = {
    "LargeBlockArmorBlock": "large_armor_block",
    "LargeBlockArmorSlope": "large_armor_slope",
    "LargeBlockArmorCorner": "large_armor_corner",
    "LargeBlockArmorCornerInv": "large_armor_corner_inv",
}


def geometry_id_for_subtype(subtype_id: str) -> str:
    """Return the SE2CAD geometry identity for a subtype.

    Distinct subtypes keep distinct IDs. The identity is never the Keen
    subtype string.
    """
    if subtype_id == "":
        raise CatalogValidationError("subtype_id: must be a non-empty string")
    preserved = _PRESERVED_GEOMETRY_IDS.get(subtype_id)
    if preserved is not None:
        return preserved
    derived = _snake_case_identity(subtype_id)
    if derived == subtype_id:
        derived = f"lg_{derived}"
    return derived


def expand_catalog_identities(
    identities: tuple[ObservedIdentity, ...] | list[ObservedIdentity],
    *,
    existing: DefinitionCatalog | None = None,
) -> DefinitionCatalog:
    """Build a catalog from observed Large Grid identities.

    Existing SE2CAD decisions are preserved. New identities are recorded
    as ``unsupported`` / ``unsupported`` until a later recipe decision.
    Small Grid identities are not activated.
    """
    by_subtype: dict[str, CatalogEntry] = {}
    order: list[str] = []
    if existing is not None:
        for entry in existing.entries:
            by_subtype[entry.subtype_id] = entry
            order.append(entry.subtype_id)

    seen_input: set[str] = set()
    new_order: list[str] = []
    for identity in identities:
        subtype_id = identity.subtype_id
        if subtype_id == "":
            raise CatalogValidationError("subtype_id: must be a non-empty string")
        if subtype_id in seen_input:
            raise CatalogValidationError(f"duplicate subtype_id {subtype_id!r}")
        seen_input.add(subtype_id)
        if identity.observed.cube_size != CATALOG_CUBE_SIZE_LARGE:
            continue
        prior = by_subtype.get(subtype_id)
        if prior is not None:
            if prior.observed != identity.observed:
                raise CatalogValidationError(
                    f"conflicting observed facts for {subtype_id!r}"
                )
            continue
        entry = CatalogEntry(
            subtype_id=subtype_id,
            observed=identity.observed,
            geometry_id=checked_geometry_id(
                geometry_id_for_subtype(subtype_id),
                f"se2cad.geometry_id for {subtype_id!r}",
            ),
            recipe_kind=RecipeKind.UNSUPPORTED,
            support_status=SupportStatus.UNSUPPORTED,
        )
        by_subtype[subtype_id] = entry
        new_order.append(subtype_id)

    new_order.sort()
    entries = [by_subtype[subtype] for subtype in order + new_order]
    _assert_unique_geometry_ids(entries)
    return DefinitionCatalog(entries=tuple(entries))


def catalog_to_data(catalog: DefinitionCatalog) -> dict[str, object]:
    """Serialize a catalog to schema-version JSON data. Paths are not added."""
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "entries": [_entry_to_data(entry) for entry in catalog.entries],
    }


def _entry_to_data(entry: CatalogEntry) -> dict[str, object]:
    observed: dict[str, object] = {
        "type_id": entry.observed.type_id,
        "cube_size": entry.observed.cube_size,
        "size": {
            "x": entry.observed.size.x,
            "y": entry.observed.size.y,
            "z": entry.observed.size.z,
        },
        "block_topology": entry.observed.block_topology,
    }
    if entry.observed.cube_topology is not None:
        observed["cube_topology"] = entry.observed.cube_topology
    return {
        "subtype_id": entry.subtype_id,
        "observed": observed,
        "se2cad": {
            "geometry_id": entry.geometry_id,
            "recipe_kind": entry.recipe_kind.value,
            "support_status": entry.support_status.value,
        },
    }


def _snake_case_identity(subtype_id: str) -> str:
    chars: list[str] = []
    length = len(subtype_id)
    for index, char in enumerate(subtype_id):
        if char.isupper() and index > 0:
            previous = subtype_id[index - 1]
            nxt = subtype_id[index + 1] if index + 1 < length else ""
            if previous.islower() or (nxt.islower() and previous.isupper()):
                chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def _assert_unique_geometry_ids(entries: list[CatalogEntry]) -> None:
    seen: set[str] = set()
    for entry in entries:
        if entry.geometry_id in seen:
            raise CatalogValidationError(
                f"duplicate geometry_id {entry.geometry_id!r}"
            )
        if entry.geometry_id == entry.subtype_id:
            raise CatalogValidationError(
                f"geometry_id must be distinct from subtype_id {entry.subtype_id!r}"
            )
        seen.add(entry.geometry_id)
