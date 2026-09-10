"""Exact geometry-identity lookup into the native armor library."""

from __future__ import annotations

import threading

from se2cad.library.errors import UnknownGeometryError
from se2cad.library.model import GeometryRecipe, LibraryRecord
from se2cad.library.recipes import (
    FILLER_LIBRARY_RECORD,
    LIBRARY_RECORDS,
    ORIGINAL_LIBRARY_BINDINGS,
    REPRESENTATIVE_AUTOMATABLE_BINDINGS,
)
from se2cad.library.sdk_bind import LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECORD

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
if LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECORD.geometry_id in _BY_GEOMETRY_ID:
    raise RuntimeError(
        "duplicate library geometry_id "
        f"{LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECORD.geometry_id!r}"
    )
_BY_GEOMETRY_ID[LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECORD.geometry_id] = (
    LARGE_BLOCK_SMALL_HYDROGEN_THRUST_RECORD
)
_PACKAGED_GEOMETRY_IDS = frozenset(_BY_GEOMETRY_ID)
_RUNTIME_LOCK = threading.Lock()
_RUNTIME_RECORDS: dict[str, LibraryRecord] = {}


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
        with _RUNTIME_LOCK:
            record = _RUNTIME_RECORDS.get(geometry_id)
        if record is None:
            raise UnknownGeometryError(
                f"unknown geometry_id {geometry_id!r}"
            ) from None
        return record


def lookup_recipe(geometry_id: str) -> GeometryRecipe:
    """Return the unique recipe for a catalog geometry identity."""
    return lookup_record(geometry_id).recipe


def packaged_library_geometry_ids() -> frozenset[str]:
    """Return packaged library identities only. Runtime overlays are excluded."""
    return _PACKAGED_GEOMETRY_IDS


def register_runtime_library_record(record: LibraryRecord) -> None:
    """Register a transient runtime bind. Does not persist the catalog."""
    if record.geometry_id in _BY_GEOMETRY_ID:
        raise ValueError(
            f"runtime geometry_id {record.geometry_id!r} collides with a "
            "packaged library identity"
        )
    with _RUNTIME_LOCK:
        existing = _RUNTIME_RECORDS.get(record.geometry_id)
        if existing is not None and existing != record:
            raise ValueError(
                f"runtime geometry_id {record.geometry_id!r} is already bound "
                "to a different record"
            )
        _RUNTIME_RECORDS[record.geometry_id] = record


def clear_runtime_library_records() -> None:
    """Drop transient runtime binds. Tests use this for isolation."""
    with _RUNTIME_LOCK:
        _RUNTIME_RECORDS.clear()


def bound_library_geometry_ids() -> frozenset[str]:
    """Return every geometry_id that lookup can resolve, including filler."""
    with _RUNTIME_LOCK:
        return frozenset(_BY_GEOMETRY_ID) | frozenset(_RUNTIME_RECORDS)


def geometry_supports_chamfer(geometry_id: str) -> bool:
    """Return the explicit library chamfer-capability flag.

    This is not catalog ``support_status``, recipe kind, or subtype
    identity. Unknown geometry_id values fail closed.
    """
    return lookup_record(geometry_id).chamfer_capable
