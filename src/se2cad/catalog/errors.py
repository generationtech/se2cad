"""Explicit definition-catalog failure types."""


class CatalogError(Exception):
    """Base class for all catalog load and lookup failures."""


class CatalogValidationError(CatalogError):
    """Catalog data is missing required structure or violates the schema."""


class UnknownSubtypeError(CatalogError):
    """Lookup used a subtype identity that is not in the catalog."""
