"""Exact geometry-identity lookup into the native armor library."""

from __future__ import annotations

from se2cad.library.errors import UnknownGeometryError
from se2cad.library.model import LibraryRecord, NativeSolidRecipe
from se2cad.library.recipes import (
    FILLER_LIBRARY_RECORD,
    LIBRARY_RECORDS,
    ORIGINAL_LIBRARY_BINDINGS,
    REPRESENTATIVE_AUTOMATABLE_BINDINGS,
)

_BY_GEOMETRY_ID: dict[str, LibraryRecord] = {}
for _record in LIBRARY_RECORDS:
    if _record.geometry_id in _BY_GEOMETRY_ID:
        raise RuntimeError(
            f"duplicate library geometry_id {_record.geometry_id!r}"
        )
    _BY_GEOMETRY_ID[_record.geometry_id] = _record
if FILLER_LIBRARY_RECORD.geometry_id in _BY_GEOMETRY_ID:
    raise RuntimeError(
        f"duplicate library geometry_id {FILLER_LIBRARY_RECORD.geometry_id!r}"
    )
_BY_GEOMETRY_ID[FILLER_LIBRARY_RECORD.geometry_id] = FILLER_LIBRARY_RECORD


def all_library_records() -> tuple[LibraryRecord, ...]:
    """Return bound native-armor library records, in catalog order."""
    return LIBRARY_RECORDS


def original_library_geometry_ids() -> tuple[str, ...]:
    """Return the four initial-program geometry identities."""
    return tuple(geometry_id for geometry_id, _topology in ORIGINAL_LIBRARY_BINDINGS)


def representative_automatable_geometry_ids() -> tuple[str, ...]:
    """Return the S2C-11.4.1 representative automatable subset."""
    return tuple(
        geometry_id for geometry_id, _topology in REPRESENTATIVE_AUTOMATABLE_BINDINGS
    )


def filler_library_record() -> LibraryRecord:
    """Return the designated unknown-block filler. Not a supported armor type."""
    return FILLER_LIBRARY_RECORD


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


def geometry_supports_chamfer(geometry_id: str) -> bool:
    """Return the explicit library chamfer-capability flag.

    This is not catalog ``support_status``, recipe kind, or subtype
    identity. Unknown geometry_id values fail closed.
    """
    return lookup_record(geometry_id).chamfer_capable
