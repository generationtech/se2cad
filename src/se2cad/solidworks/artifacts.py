"""Deterministic canonical-part filenames and generated-root containment."""

from __future__ import annotations

from pathlib import Path

import re

from se2cad.catalog.constants import FILLER_GEOMETRY_ID
from se2cad.library import (
    EDGE_TREATMENT_OFF,
    EdgeTreatmentKind,
    EdgeTreatmentRequest,
    TreatmentError,
    all_library_records,
    chamfer_size_token,
    lookup_recipe,
    validate_chamfer_setback_mm,
)
from se2cad.solidworks.errors import (
    AssemblyIdentityError,
    GeneratedRootError,
    UnknownCanonicalPartError,
)

CANONICAL_PART_SUFFIX = ".SLDPRT"
CANONICAL_ASSEMBLY_SUFFIX = ".SLDASM"
TREATED_PART_STEM_SUFFIX = "_chamfer"
_ASSEMBLY_IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_TREATED_FILENAME_RE = re.compile(
    r"^([a-z][a-z0-9_]*)_chamfer_([0-9]+(?:\.[0-9]+)?)mm\.SLDPRT$"
)

_CANONICAL_GEOMETRY_IDS: tuple[str, ...] = (
    "large_armor_block",
    "large_armor_slope",
    "large_armor_corner",
    "large_armor_corner_inv",
)


def canonical_geometry_ids() -> tuple[str, ...]:
    """Return the four initial-program geometry identities, in catalog order."""
    return _CANONICAL_GEOMETRY_IDS


def _library_geometry_ids() -> frozenset[str]:
    return frozenset(record.geometry_id for record in all_library_records()) | {
        FILLER_GEOMETRY_ID
    }


def logical_part_filename(geometry_id: str) -> str:
    """Deterministic SLDPRT filename from a catalog geometry identity."""
    if geometry_id not in _library_geometry_ids():
        raise UnknownCanonicalPartError(
            f"no deterministic canonical artifact name for {geometry_id!r}"
        )
    lookup_recipe(geometry_id)
    return f"{geometry_id}{CANONICAL_PART_SUFFIX}"


def is_canonical_artifact_filename(filename: str) -> bool:
    """True when filename is a library-owned untreated canonical part."""
    return filename in {logical_part_filename(gid) for gid in _library_geometry_ids()}


def treated_artifact_key(geometry_id: str, request: EdgeTreatmentRequest) -> str:
    """Shared generation/lookup stem: ``{geometry_id}_chamfer_{size}mm``.

    Size is part of artifact identity. Algorithm/version suffixes are
    not. The generic ``{geometry_id}_chamfer`` stem is never returned.
    """
    if geometry_id not in _library_geometry_ids():
        raise UnknownCanonicalPartError(
            f"no deterministic treated artifact name for {geometry_id!r}"
        )
    lookup_recipe(geometry_id)
    if request.kind is not EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK:
        raise UnknownCanonicalPartError(
            "no treated artifact name for treatment "
            f"{request.kind.value!r}"
        )
    return f"{geometry_id}{TREATED_PART_STEM_SUFFIX}_{chamfer_size_token(request.setback_mm)}"


def logical_treated_part_filename(
    geometry_id: str,
    request: EdgeTreatmentRequest,
) -> str:
    """Deterministic sibling SLDPRT name for a requested edge treatment.

    Treatment is not a new ``geometry_id``. The untreated
    ``{geometry_id}.SLDPRT`` name is never returned here.
    """
    return f"{treated_artifact_key(geometry_id, request)}{CANONICAL_PART_SUFFIX}"


def is_treated_artifact_filename(filename: str) -> bool:
    """True when filename is a size-specific treated sibling.

    The historical generic ``{geometry_id}_chamfer.SLDPRT`` name is not
    a treated artifact under this contract.
    """
    if not filename or Path(filename).name != filename:
        return False
    if any(sep in filename for sep in ("/", "\\")):
        return False
    match = _TREATED_FILENAME_RE.fullmatch(filename)
    if match is None:
        return False
    geometry_id, raw_size = match.group(1), match.group(2)
    if geometry_id not in _library_geometry_ids():
        return False
    try:
        setback = validate_chamfer_setback_mm(float(raw_size))
        expected = logical_treated_part_filename(
            geometry_id,
            EdgeTreatmentRequest(
                kind=EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK,
                setback_mm=setback,
            ),
        )
    except (TypeError, ValueError, TreatmentError, UnknownCanonicalPartError):
        return False
    return filename == expected


def logical_assembly_part_filename(
    geometry_id: str,
    request: EdgeTreatmentRequest | None = None,
) -> str:
    """SLDPRT name used at assembly insert for the requested treatment.

    Default and ``EDGE_TREATMENT_OFF`` keep the untreated canonical name.
    An explicit chamfer request names the treated sibling. Treatment is
    not a new ``geometry_id``.
    """
    chosen = EDGE_TREATMENT_OFF if request is None else request
    if not chosen.enabled:
        return logical_part_filename(geometry_id)
    return logical_treated_part_filename(geometry_id, chosen)


def treated_artifact_path_for(
    root: Path,
    geometry_id: str,
    request: EdgeTreatmentRequest,
) -> Path:
    """Absolute destination for one treated sibling, inside the root."""
    filename = logical_treated_part_filename(geometry_id, request)
    return contained_destination(root, filename)


def part_artifact_path(
    root: Path,
    geometry_id: str,
    request: EdgeTreatmentRequest | None = None,
) -> Path:
    """Destination for default untreated or requested treated generation."""
    chosen = EDGE_TREATMENT_OFF if request is None else request
    untreated = artifact_path_for(root, geometry_id)
    if not chosen.enabled:
        return untreated
    destination = treated_artifact_path_for(root, geometry_id, chosen)
    if destination == untreated or destination.name == untreated.name:
        raise GeneratedRootError(
            "treated destination must not overwrite an untreated canonical part"
        )
    if is_canonical_artifact_filename(destination.name):
        raise GeneratedRootError(
            "treated destination must not use an untreated canonical filename"
        )
    return destination


def logical_assembly_filename(identity: str) -> str:
    """Deterministic SLDASM filename from a blueprint identity subtype."""
    if not identity or not _ASSEMBLY_IDENTITY_RE.fullmatch(identity):
        raise AssemblyIdentityError(
            f"cannot derive a safe assembly filename from identity {identity!r}"
        )
    return f"{identity}{CANONICAL_ASSEMBLY_SUFFIX}"


def is_assembly_artifact_filename(filename: str) -> bool:
    """True when filename is a single-segment SE2CAD assembly artifact name."""
    if not filename.endswith(CANONICAL_ASSEMBLY_SUFFIX):
        return False
    stem = filename[: -len(CANONICAL_ASSEMBLY_SUFFIX)]
    return bool(stem) and _ASSEMBLY_IDENTITY_RE.fullmatch(stem)


def resolve_generated_root(root: Path) -> Path:
    """Resolve the generated root. The directory need not exist yet."""
    resolved = Path(root).expanduser().resolve()
    if resolved.exists() and not resolved.is_dir():
        raise GeneratedRootError(
            f"generated root {resolved} exists and is not a directory"
        )
    return resolved


def artifact_path_for(root: Path, geometry_id: str) -> Path:
    """Absolute destination path for one canonical part, inside the root."""
    filename = logical_part_filename(geometry_id)
    return contained_destination(root, filename)


def assembly_path_for(root: Path, identity: str) -> Path:
    """Absolute destination path for one generated assembly, inside the root."""
    return contained_destination(root, logical_assembly_filename(identity))


def contained_destination(root: Path, filename: str) -> Path:
    """Resolve ``root / filename`` and reject paths that escape the root.

    ``filename`` must be a single path segment. Regeneration may overwrite
    only an existing SE2CAD-owned canonical artifact of that exact name.
    """
    if not filename or filename in {".", ".."}:
        raise GeneratedRootError(f"invalid artifact filename {filename!r}")
    if Path(filename).name != filename:
        raise GeneratedRootError(
            f"artifact filename must be a single path segment, got {filename!r}"
        )
    if any(sep in filename for sep in ("/", "\\")):
        raise GeneratedRootError(
            f"artifact filename must not contain a path separator: {filename!r}"
        )

    resolved_root = resolve_generated_root(root)
    destination = (resolved_root / filename).resolve()
    try:
        destination.relative_to(resolved_root)
    except ValueError:
        raise GeneratedRootError(
            f"destination {destination} escapes generated root {resolved_root}"
        ) from None
    return destination


def assert_overwrite_is_canonical(destination: Path) -> None:
    """Permit overwrite only of an existing SE2CAD-owned generated artifact."""
    if not destination.exists():
        return
    if is_canonical_artifact_filename(destination.name):
        return
    if is_treated_artifact_filename(destination.name):
        return
    if is_assembly_artifact_filename(destination.name):
        return
    raise GeneratedRootError(
        f"refusing to overwrite unrelated file {destination}"
    )
