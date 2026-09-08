"""Deterministic canonical-part filenames and generated-root containment."""

from __future__ import annotations

from pathlib import Path

from se2cad.library import lookup_recipe
from se2cad.solidworks.errors import GeneratedRootError, UnknownCanonicalPartError

CANONICAL_PART_SUFFIX = ".SLDPRT"

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
    """Permit overwrite only of an existing SE2CAD canonical artifact name."""
    if not destination.exists():
        return
    if not is_canonical_artifact_filename(destination.name):
        raise GeneratedRootError(
            f"refusing to overwrite unrelated file {destination}"
        )
