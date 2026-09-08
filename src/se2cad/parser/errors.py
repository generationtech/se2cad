"""Explicit blueprint-parser failure types."""


class BlueprintParseError(Exception):
    """Base class for all blueprint parse failures."""


class MalformedXmlError(BlueprintParseError):
    """XML is not well-formed, or uses constructs this parser will not load."""


class UnsupportedBlueprintError(BlueprintParseError):
    """Document structure is outside the S2C-1.2.1 support set."""


class InvalidFieldError(BlueprintParseError):
    """A supported field is present but has an unusable value."""


class MissingRequiredFieldError(BlueprintParseError):
    """A required field is absent or empty."""
