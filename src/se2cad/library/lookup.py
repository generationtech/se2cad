"""Exact geometry-identity lookup into the native armor library."""

from __future__ import annotations

from se2cad.library.errors import UnknownGeometryError
from se2cad.library.model import LibraryRecord, NativeSolidRecipe
from se2cad.library.recipes import LIBRARY_RECORDS

_BY_GEOMETRY_ID: dict[str, LibraryRecord] = {}
for _record in LIBRARY_RECORDS:
    if _record.geometry_id in _BY_GEOMETRY_ID:
        raise RuntimeError(
            f"duplicate library geometry_id {_record.geometry_id!r}"
        )
    _BY_GEOMETRY_ID[_record.geometry_id] = _record


def all_library_records() -> tuple[LibraryRecord, ...]:
    """Return the four initial Large Grid armor library records, in order."""
    return LIBRARY_RECORDS


def lookup_record(geometry_id: str) -> LibraryRecord:
    """Resolve an exact catalog geometry identity. No aliases or folding."""
    try:
        return _BY_GEOMETRY_ID[geometry_id]
    except KeyError:
        raise UnknownGeometryError(
            f"unknown geometry_id {geometry_id!r}"
        ) from None


def lookup_recipe(geometry_id: str) -> NativeSolidRecipe:
    """Return the unique native recipe for a catalog geometry identity."""
    return lookup_record(geometry_id).recipe
