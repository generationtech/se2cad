"""Explicit block-library failure types."""


class LibraryError(Exception):
    """Base class for block-library lookup and recipe failures."""


class UnknownGeometryError(LibraryError):
    """Lookup used a geometry identity that has no library recipe."""


class UnsupportedTopologyError(LibraryError):
    """CubeTopology is automatable-class but has no native construction."""


class InvalidSolidError(LibraryError):
    """A mesh is not a closed manifold solid the treatment can consume."""


class TreatmentError(LibraryError):
    """Optional edge treatment was requested and cannot be applied."""
