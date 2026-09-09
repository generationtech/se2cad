"""CAD-neutral assembly component names from existing IR fields.

Names are a derived identifier, not a second catalog key and not a
geometry_id. Source data is subtype, Min, Forward/Up, and source_index.
SolidWorks COM types are not used here.

The requested name is the FeatureManager short name (Name2 set). Live
SolidWorks Name2 get appends ``-{instance}``; that suffix is a backend
mapping, not part of this encoding.

The length cap is an SE2CAD-specified identifier bound so untrusted
subtype strings cannot produce arbitrarily long names, while ordinary
vanilla encodings (including the four qualified armor subtypes) fit
untruncated. Overflow uses prefix truncation plus the unique
``_{source_index}`` suffix so the name stays traceable to the IR block.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from se2cad.ir.errors import ComponentNameError
from se2cad.ir.model import CanonicalBlock
from se2cad.parser.model import Direction, GridCoordinate

COMPONENT_NAME_MAX_LENGTH = 80
_SUBTYPE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def component_name(
    subtype_id: str,
    grid_min: GridCoordinate | tuple[int, int, int],
    forward: Direction | str,
    up: Direction | str,
    source_index: int,
) -> str:
    """Return a deterministic, human-readable, unique-per-index name."""
    subtype = _require_subtype(subtype_id)
    x, y, z = _require_min(grid_min)
    fwd = _require_direction(forward, "forward")
    upward = _require_direction(up, "up")
    index = _require_source_index(source_index)
    suffix = f"_{index}"
    full = f"{subtype}_x{x}_y{y}_z{z}_{fwd}_{upward}{suffix}"
    if len(full) <= COMPONENT_NAME_MAX_LENGTH:
        return full
    if len(suffix) >= COMPONENT_NAME_MAX_LENGTH:
        raise ComponentNameError(
            f"source_index suffix {suffix!r} exceeds "
            f"COMPONENT_NAME_MAX_LENGTH={COMPONENT_NAME_MAX_LENGTH}"
        )
    prefix = full[: -len(suffix)]
    return prefix[: COMPONENT_NAME_MAX_LENGTH - len(suffix)] + suffix


def component_name_from_block(block: CanonicalBlock) -> str:
    """Derive the component name from one canonical IR block."""
    return component_name(
        block.subtype_id,
        block.grid_min,
        block.forward,
        block.up,
        block.source_index,
    )


def component_names_from_blocks(blocks: Iterable[CanonicalBlock]) -> tuple[str, ...]:
    """Name every block and fail closed if the set is not unique."""
    names = tuple(component_name_from_block(block) for block in blocks)
    if len(set(names)) != len(names):
        raise ComponentNameError("component names are not unique within the assembly")
    return names


def _require_subtype(subtype_id: str) -> str:
    if not isinstance(subtype_id, str) or not _SUBTYPE_RE.fullmatch(subtype_id):
        raise ComponentNameError(
            f"subtype_id {subtype_id!r} is not a safe component-name token"
        )
    return subtype_id


def _require_min(grid_min: GridCoordinate | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(grid_min, GridCoordinate):
        values = (grid_min.x, grid_min.y, grid_min.z)
    elif isinstance(grid_min, tuple) and len(grid_min) == 3:
        values = (grid_min[0], grid_min[1], grid_min[2])
    else:
        raise ComponentNameError(f"grid_min {grid_min!r} is not a 3-int cell")
    if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
        raise ComponentNameError(f"grid_min {grid_min!r} is not a 3-int cell")
    return values


def _require_direction(value: Direction | str, label: str) -> str:
    if isinstance(value, Direction):
        return value.value
    if isinstance(value, str):
        try:
            return Direction(value).value
        except ValueError:
            pass
    raise ComponentNameError(f"invalid {label} {value!r}")


def _require_source_index(source_index: int) -> int:
    if isinstance(source_index, bool) or not isinstance(source_index, int):
        raise ComponentNameError(f"source_index {source_index!r} is not a non-negative int")
    if source_index < 0:
        raise ComponentNameError(f"source_index {source_index} is negative")
    return source_index
