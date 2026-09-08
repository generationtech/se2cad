"""Logical artifact identity versus physical local path.

A locator may be bound only after generate, validate, save, and reopen
succeed. The physical path is runtime-only and is never written into
authoritative catalog data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.solidworks.artifacts import logical_part_filename


@dataclass(frozen=True)
class LogicalPartIdentity:
    """Catalog geometry identity plus its deterministic filename."""

    geometry_id: str
    filename: str

    @classmethod
    def from_geometry_id(cls, geometry_id: str) -> LogicalPartIdentity:
        return cls(
            geometry_id=geometry_id,
            filename=logical_part_filename(geometry_id),
        )


@dataclass(frozen=True)
class BoundPartLocator:
    """Locator returned only after a successful generate/validate/save/reopen."""

    identity: LogicalPartIdentity
    path: Path
    generated: bool
    validated: bool
    saved: bool
    reopened: bool

    def __post_init__(self) -> None:
        if not (
            self.generated and self.validated and self.saved and self.reopened
        ):
            raise ValueError(
                "a part locator may be bound only after generate, validate, "
                "save, and reopen all succeed"
            )
        if self.identity.filename != self.path.name:
            raise ValueError(
                "bound locator path name must match the logical filename"
            )
