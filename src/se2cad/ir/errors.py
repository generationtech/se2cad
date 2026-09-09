"""IR and IR-derived identifier failures."""


class IrError(Exception):
    """Base class for canonical-IR construction and derived-identifier failures."""


class ComponentNameError(IrError):
    """An IR block cannot be turned into a safe unique component name."""
