"""SolidWorks backend failures. Independent of pywin32."""


class SolidWorksBackendError(Exception):
    """Base class for Windows-local SolidWorks backend failures."""


class SolidWorksBackendUnavailableError(SolidWorksBackendError):
    """COM, pywin32, or SolidWorks is not available in this process."""


class SolidWorksConfigError(SolidWorksBackendError):
    """Generated-root or backend configuration is missing or invalid."""


class GeneratedRootError(SolidWorksBackendError):
    """A write would escape the configured generated root or overwrite a foreign file."""


class SolidWorksComError(SolidWorksBackendError):
    """A COM call failed. The original exception is chained when available."""


class CanonicalPartValidationError(SolidWorksBackendError):
    """A generated or reopened part failed body, envelope, or volume checks."""


class UnknownCanonicalPartError(SolidWorksBackendError):
    """No deterministic artifact identity exists for the given geometry_id."""


class MissingCanonicalPartError(SolidWorksBackendError):
    """A required generated canonical SLDPRT is absent from the generated root."""


class AssemblyIdentityError(SolidWorksBackendError):
    """The IR identity cannot be turned into a safe assembly filename."""


class AssemblyValidationError(SolidWorksBackendError):
    """A generated or reopened assembly failed component, transform, or mate checks."""
