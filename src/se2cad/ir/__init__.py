"""Canonical CAD-neutral intermediate representation (S2C-3.1.1)."""

from se2cad.ir.convert import build_canonical_blueprint
from se2cad.ir.model import CanonicalBlock, CanonicalBlueprint, CanonicalGrid

__all__ = [
    "CanonicalBlock",
    "CanonicalBlueprint",
    "CanonicalGrid",
    "build_canonical_blueprint",
]
