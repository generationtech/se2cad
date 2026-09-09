"""Library-build definition-discovery failures."""


class DiscoveryError(Exception):
    """Base class for operator-local definition discovery failures."""


class DiscoveryConfigError(DiscoveryError):
    """Game/SDK root configuration is missing or invalid."""


class DiscoveryPathError(DiscoveryError):
    """A configured or discovered path is missing, not a directory, or escapes."""


class DiscoveryParseError(DiscoveryError):
    """A cube-block definition file is malformed or uses rejected XML."""
