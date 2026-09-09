"""Operator-local cube-block definition discovery (S2C-11.1.1).

Library-build evidence only. Runtime conversion still uses the packaged
catalog and ``bp.sbc``. This package is not imported by ``se2cad``'s
public conversion surface.
"""

from se2cad.discovery.config import (
    GAME_ROOT_ENV,
    SDK_ROOT_ENV,
    DiscoveryConfig,
    contained_file,
    load_discovery_config,
)
from se2cad.discovery.discover import discover_cube_block_definitions
from se2cad.discovery.errors import (
    DiscoveryConfigError,
    DiscoveryError,
    DiscoveryParseError,
    DiscoveryPathError,
)
from se2cad.discovery.model import DiscoveredDefinition, DiscoveryReport
from se2cad.discovery.parse import (
    parse_cube_block_definitions_file,
    parse_cube_block_definitions_xml,
)

__all__ = [
    "GAME_ROOT_ENV",
    "SDK_ROOT_ENV",
    "DiscoveredDefinition",
    "DiscoveryConfig",
    "DiscoveryConfigError",
    "DiscoveryError",
    "DiscoveryParseError",
    "DiscoveryPathError",
    "DiscoveryReport",
    "contained_file",
    "discover_cube_block_definitions",
    "load_discovery_config",
    "parse_cube_block_definitions_file",
    "parse_cube_block_definitions_xml",
]
