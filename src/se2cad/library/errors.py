"""Explicit block-library failure types."""


class LibraryError(Exception):
    """Base class for block-library lookup and recipe failures."""


class UnknownGeometryError(LibraryError):
    """Lookup used a geometry identity that has no library recipe."""
