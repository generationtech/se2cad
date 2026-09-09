"""CAD-neutral conversion-policy values.

Policy decides whether unknown or unsupported blocks refuse conversion
or receive the designated filler. It does not invent real geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from se2cad.ir.model import CanonicalBlueprint
from se2cad.preflight.model import ConversionPreflight


class ConversionPolicy(str, Enum):
    """Explicit conversion modes. Strict is the default."""

    STRICT = "strict"
    PERMISSIVE = "permissive"


@dataclass(frozen=True)
class ConversionResult:
    """One policy-controlled conversion. Not a SolidWorks session."""

    policy: ConversionPolicy
    preflight: ConversionPreflight
    ir: CanonicalBlueprint
    filler_count: int
