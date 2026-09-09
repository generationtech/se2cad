"""Deterministic canonical-part filenames and generated-root containment."""

from __future__ import annotations

from pathlib import Path

import re

from se2cad.library import (
    EDGE_TREATMENT_OFF,
    EdgeTreatmentKind,
    EdgeTreatmentRequest,
    lookup_recipe,
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

_CANONICAL_GEOMETRY_IDS: tuple[str, ...] = (
    "large_armor_block",
    "large_armor_slope",
    "large_armor_corner",
    "large_armor_corner_inv",
)


def canonical_geometry_ids() -> tuple[str, ...]:
    """Return the four initial-program geometry identities, in catalog order."""
    return _CANONICAL_GEOMETRY_IDS


def logical_part_filename(geometry_id: str) -> str:
    """Deterministic SLDPRT filename from a catalog geometry identity."""
    if geometry_id not in _CANONICAL_GEOMETRY_IDS:
        # Unknown IDs fail closed even if a library recipe exists later.
        try:
            lookup_recipe(geometry_id)
        except Exception:
            pass
        raise UnknownCanonicalPartError(
            f"no deterministic canonical artifact name for {geometry_id!r}"
        )
    return f"{geometry_id}{CANONICAL_PART_SUFFIX}"


def is_canonical_artifact_filename(filename: str) -> bool:
    """True when filename is exactly one of the four SE2CAD-owned names."""
    return filename in {logical_part_filename(gid) for gid in _CANONICAL_GEOMETRY_IDS}


def logical_treated_part_filename(
    geometry_id: str,
    request: EdgeTreatmentRequest,
) -> str:
    """Deterministic sibling SLDPRT name for a requested edge treatment.

    Treatment is not a new ``geometry_id``. The untreated
    ``{geometry_id}.SLDPRT`` name is never returned here.
    """
    if geometry_id not in _CANONICAL_GEOMETRY_IDS:
        try:
            lookup_recipe(geometry_id)
        except Exception:
            pass
        raise UnknownCanonicalPartError(
            f"no deterministic treated artifact name for {geometry_id!r}"
        )
    if request.kind is not EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK:
        raise UnknownCanonicalPartError(
            "no treated artifact name for treatment "
            f"{request.kind.value!r}"
        )
    return f"{geometry_id}{TREATED_PART_STEM_SUFFIX}{CANONICAL_PART_SUFFIX}"


def is_treated_artifact_filename(filename: str) -> bool:
    """True when filename is a known treated sibling of a canonical part."""
    return filename in {
        logical_treated_part_filename(
            gid,
            EdgeTreatmentRequest(kind=EdgeTreatmentKind.CHAMFER_EQUAL_SETBACK),
        )
        for gid in _CANONICAL_GEOMETRY_IDS
    }


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
