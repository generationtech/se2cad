"""Walk a validated install root for cube-block definition ``.sbc`` files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from se2cad.discovery.config import (
    DiscoveryConfig,
    contained_file,
    load_discovery_config,
)
from se2cad.discovery.errors import DiscoveryParseError, DiscoveryPathError
from se2cad.discovery.model import DiscoveredDefinition, DiscoveryReport
from se2cad.discovery.parse import parse_cube_block_definitions_file

# Observed vanilla / ModSDK locations. Do not walk the whole install.
_DEFINITION_RELATIVE_DIRS = (
    Path("Content") / "Data" / "CubeBlocks",
    Path("Data") / "CubeBlocks",
)


def discover_cube_block_definitions(
    *,
    game_root: Optional[Path] = None,
    sdk_root: Optional[Path] = None,
    config: Optional[DiscoveryConfig] = None,
) -> DiscoveryReport:
    """Discover observed cube-block facts from configured local trees."""
    resolved = config or load_discovery_config(
        game_root=game_root, sdk_root=sdk_root
    )
    definitions: list[DiscoveredDefinition] = []
    files_read: list[str] = []
    seen: dict[str, DiscoveredDefinition] = {}
    if resolved.game_root is not None:
        _discover_one_root(
            resolved.game_root,
            source_kind="game",
            definitions=definitions,
            files_read=files_read,
            seen=seen,
        )
    if resolved.sdk_root is not None:
        _discover_one_root(
            resolved.sdk_root,
            source_kind="sdk",
            definitions=definitions,
            files_read=files_read,
            seen=seen,
        )
    definitions.sort(key=lambda item: (item.subtype_id, item.source_kind))
    files_read.sort()
    return DiscoveryReport(
        definitions=tuple(definitions),
        files_read=tuple(files_read),
        game_root_configured=resolved.game_root is not None,
        sdk_root_configured=resolved.sdk_root is not None,
    )


def _discover_one_root(
    root: Path,
    *,
    source_kind: str,
    definitions: list[DiscoveredDefinition],
    files_read: list[str],
    seen: dict[str, DiscoveredDefinition],
) -> None:
    definition_dirs = _definition_directories(root)
    if not definition_dirs:
        raise DiscoveryPathError(
            f"{source_kind} root has no cube-block definition directory: {root}"
        )
    sbc_files: list[tuple[Path, str]] = []
    for directory in definition_dirs:
        for candidate in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() != ".sbc":
                continue
            contained = contained_file(root, candidate)
            relative = contained.relative_to(root).as_posix()
            sbc_files.append((contained, relative))
    if not sbc_files:
        raise DiscoveryPathError(
            f"{source_kind} root has no cube-block definition .sbc files: {root}"
        )
    for path, relative in sbc_files:
        parsed = parse_cube_block_definitions_file(
            path, source_kind=source_kind, source_relative=relative
        )
        files_read.append(f"{source_kind}:{relative}")
        for item in parsed:
            prior = seen.get(item.subtype_id)
            if prior is not None and not _same_observed_facts(prior, item):
                raise DiscoveryParseError(
                    f"conflicting observed facts for {item.subtype_id!r}: "
                    f"{prior.source_kind}:{prior.source_relative} vs "
                    f"{item.source_kind}:{item.source_relative}"
                )
            if prior is None:
                seen[item.subtype_id] = item
                definitions.append(item)


def _definition_directories(root: Path) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for relative in _DEFINITION_RELATIVE_DIRS:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            raise DiscoveryPathError(
                f"definition directory {candidate} escapes root {root}"
            ) from None
        if not candidate.is_dir():
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        found.append(candidate)
    return found


def _same_observed_facts(
    left: DiscoveredDefinition, right: DiscoveredDefinition
) -> bool:
    return (
        left.subtype_id == right.subtype_id
        and left.type_id == right.type_id
        and left.cube_size == right.cube_size
        and left.size == right.size
        and left.block_topology == right.block_topology
        and left.cube_topology == right.cube_topology
    )
