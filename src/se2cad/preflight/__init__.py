"""CAD-neutral conversion preflight (S2C-12.1.1).

Derived from the parser and catalog. Diagnoses what will convert and
what will not. Not a SolidWorks backend, not filler insertion, and not
a conversion-success claim.
"""

from se2cad.preflight.compute import (
    compute_conversion_preflight,
    compute_conversion_preflight_from_path,
    compute_conversion_preflight_from_xml,
)
from se2cad.preflight.model import (
    BlockPreflight,
    CatalogOutcome,
    ConversionPreflight,
)

__all__ = [
    "BlockPreflight",
    "CatalogOutcome",
    "ConversionPreflight",
    "compute_conversion_preflight",
    "compute_conversion_preflight_from_path",
    "compute_conversion_preflight_from_xml",
]
