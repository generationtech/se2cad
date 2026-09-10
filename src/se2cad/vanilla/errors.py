"""Failures for demand-driven vanilla TriangleMesh resolution."""


class VanillaResolutionError(Exception):
    """Vanilla runtime resolution cannot proceed safely."""


class VanillaRootError(VanillaResolutionError):
    """Game-content or SDK root is missing or invalid where resolution needs it."""


class VanillaLookupError(VanillaResolutionError):
    """Exact subtype lookup failed closed (duplicate, unsafe XML, or path)."""
