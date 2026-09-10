"""Classify an official SDK FBX as binary, valid ASCII, or unusable.

Classification is not a support grant. ASCII becomes usable only when
the bounded ASCII conversion path can validate mesh-bearing FBX 7.x.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from se2cad.solidworks.errors import SdkSourceError

FBX_BINARY_MAGIC = b"Kaydara FBX Binary"
FBX_BINARY_MAGIC_FULL = b"Kaydara FBX Binary  \x00\x1a\x00"
MAX_ASCII_FBX_BYTES = 32 * 1024 * 1024
_ASCII_VERSION_MIN = 7000
_ASCII_VERSION_MAX = 7400


class FbxSourceKind(str, Enum):
    BINARY = "binary"
    ASCII = "ascii"
    INVALID = "invalid"


@dataclass(frozen=True)
class FbxSourceClassification:
    """Deterministic source-format decision for one contained FBX file."""

    kind: FbxSourceKind
    path: Path
    size_bytes: int
    version: int | None
    reason: str | None


def ascii_fbx_conversion_available() -> bool:
    """Return whether this process can normalize official ASCII FBX.

    Ordinary tests patch this to prove ASCII stays unresolved when the
    conversion path is absent. Production always returns True.
    """
    return True


def classify_sdk_fbx(path: Path) -> FbxSourceClassification:
    """Read a contained SDK file and classify binary vs ASCII vs invalid."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SdkSourceError(f"authorized SDK source is unreadable: {path}: {exc}") from exc
    try:
        with path.open("rb") as handle:
            header = handle.read(max(len(FBX_BINARY_MAGIC_FULL), 64))
    except OSError as exc:
        raise SdkSourceError(f"authorized SDK source is unreadable: {path}: {exc}") from exc
    if header.startswith(FBX_BINARY_MAGIC):
        version = _binary_version(header)
        return FbxSourceClassification(
            kind=FbxSourceKind.BINARY,
            path=path,
            size_bytes=size,
            version=version,
            reason=None,
        )
    if size > MAX_ASCII_FBX_BYTES:
        return FbxSourceClassification(
            kind=FbxSourceKind.INVALID,
            path=path,
            size_bytes=size,
            version=None,
            reason=(
                f"SDK source is larger than the ASCII FBX limit "
                f"({size} > {MAX_ASCII_FBX_BYTES})"
            ),
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return FbxSourceClassification(
            kind=FbxSourceKind.INVALID,
            path=path,
            size_bytes=size,
            version=None,
            reason=f"SDK source is not a binary FBX and is not valid UTF-8 text: {exc}",
        )
    if not _looks_like_ascii_fbx(text):
        return FbxSourceClassification(
            kind=FbxSourceKind.INVALID,
            path=path,
            size_bytes=size,
            version=None,
            reason="SDK source is not a binary FBX and is not a valid ASCII FBX",
        )
    from se2cad.solidworks.sdk_ascii_fbx import validate_ascii_fbx

    try:
        version = validate_ascii_fbx(text)
    except SdkSourceError as exc:
        return FbxSourceClassification(
            kind=FbxSourceKind.INVALID,
            path=path,
            size_bytes=size,
            version=None,
            reason=str(exc),
        )
    if version < _ASCII_VERSION_MIN or version > _ASCII_VERSION_MAX:
        return FbxSourceClassification(
            kind=FbxSourceKind.INVALID,
            path=path,
            size_bytes=size,
            version=version,
            reason=f"ASCII FBX version {version} is outside 7.x conversion support",
        )
    return FbxSourceClassification(
        kind=FbxSourceKind.ASCII,
        path=path,
        size_bytes=size,
        version=version,
        reason=None,
    )


def require_usable_sdk_fbx(path: Path) -> FbxSourceClassification:
    """Accept binary FBX, or valid ASCII FBX when conversion is available."""
    classified = classify_sdk_fbx(path)
    if classified.kind is FbxSourceKind.BINARY:
        return classified
    if classified.kind is FbxSourceKind.ASCII:
        if not ascii_fbx_conversion_available():
            raise SdkSourceError(
                "ASCII FBX conversion is not available; "
                f"leaving {path.name} unresolved"
            )
        return classified
    raise SdkSourceError(
        classified.reason
        or f"SDK source is not a usable binary or ASCII FBX: {path.name}"
    )


def _binary_version(header: bytes) -> int | None:
    if len(header) < len(FBX_BINARY_MAGIC_FULL) + 4:
        return None
    if not header.startswith(FBX_BINARY_MAGIC_FULL):
        return None
    return int.from_bytes(
        header[len(FBX_BINARY_MAGIC_FULL) : len(FBX_BINARY_MAGIC_FULL) + 4],
        "little",
        signed=False,
    )


def _looks_like_ascii_fbx(text: str) -> bool:
    body = text.lstrip("\ufeff")
    for line in body.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith(";"):
            continue
        return stripped.startswith("FBXHeaderExtension:") or stripped.startswith("FBX")
    return False
