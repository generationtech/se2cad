"""CAD-neutral blueprint and conversion statistics (S2C-7.1.1).

Derived from the parser, catalog, and (when all blocks resolve) the same
fields the IR uses. Not a SolidWorks backend and not a general CLI.
"""

from se2cad.statistics.compute import (
    compute_blueprint_statistics,
    compute_blueprint_statistics_from_path,
    compute_blueprint_statistics_from_xml,
)
from se2cad.statistics.model import (
    AxisRange,
    BlueprintStatistics,
    CatalogCoverage,
    CellExtents,
    MillimetreSize,
    NamedCount,
    Occupancy,
    OrientationCount,
)

__all__ = [
    "AxisRange",
    "BlueprintStatistics",
    "CatalogCoverage",
    "CellExtents",
    "MillimetreSize",
    "NamedCount",
    "Occupancy",
    "OrientationCount",
    "compute_blueprint_statistics",
    "compute_blueprint_statistics_from_path",
    "compute_blueprint_statistics_from_xml",
]
