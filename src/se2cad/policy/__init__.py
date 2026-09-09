"""CAD-neutral conversion policy (S2C-12.2.1).

Strict refuses unknown or unsupported blocks and surfaces preflight
diagnostics. Permissive inserts the designated filler identity while
preserving original SE subtype, appearance, and pose. Default is strict.
Not a SolidWorks backend and not a general CLI.
"""

from se2cad.policy.convert import (
    convert_blueprint,
    convert_blueprint_from_path,
    convert_blueprint_from_xml,
)
from se2cad.policy.errors import (
    ConversionPolicyError,
    ConversionRefusedError,
    UnknownConversionPolicyError,
)
from se2cad.policy.model import ConversionPolicy, ConversionResult

__all__ = [
    "ConversionPolicy",
    "ConversionPolicyError",
    "ConversionRefusedError",
    "ConversionResult",
    "UnknownConversionPolicyError",
    "convert_blueprint",
    "convert_blueprint_from_path",
    "convert_blueprint_from_xml",
]
