"""Explicit transform-engine failure types."""


class TransformError(Exception):
    """Base class for placement-transform failures."""


class InvalidOrientationError(TransformError):
    """Forward and Up do not form a valid Space Engineers block orientation."""


class InvalidBlockSizeError(TransformError):
    """Block Size is not a positive integer cell triple."""


class InvalidModelOffsetError(TransformError):
    """ModelOffset is not an exact metre triple convertible to integer millimetres."""
