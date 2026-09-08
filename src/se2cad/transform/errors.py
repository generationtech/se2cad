"""Explicit transform-engine failure types."""


class TransformError(Exception):
    """Base class for placement-transform failures."""


class InvalidOrientationError(TransformError):
    """Forward and Up do not form a valid Space Engineers block orientation."""
