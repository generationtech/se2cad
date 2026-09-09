"""Dimensional constants owned by the definition catalog.

Large Grid cell pitch is the single named constant required by the
architecture. Do not copy the literal into call sites.
"""

# SE2CAD unit. Keen Configuration.sbc records CubeSizes Large="2.5" (meters).
LARGE_GRID_CELL_PITCH_MM = 2500

# Packaged catalog JSON schema. Bump when fields are added or requiredness changes.
CATALOG_SCHEMA_VERSION = 2

# Observed CubeSize token that this catalog may record. Small Grid is M13.
CATALOG_CUBE_SIZE_LARGE = "Large"

# Designated permissive-mode filler identity. Not a cube-block subtype and
# not a supported armor geometry_id. Unknown and catalog-unsupported
# blocks may receive this identity under an explicit permissive policy.
FILLER_GEOMETRY_ID = "se2cad_unknown_filler"
