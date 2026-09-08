"""Backend availability without importing pywin32 at package import time."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass

from se2cad.solidworks.errors import SolidWorksBackendUnavailableError


@dataclass(frozen=True)
class BackendAvailability:
    """Observed process capability. Not a SolidWorks session."""

    python_com_modules: bool
    windows: bool
    available: bool
    reason: str


def _windows() -> bool:
    return sys.platform == "win32"


def _pywin32_present() -> bool:
    return (
        importlib.util.find_spec("win32com") is not None
        and importlib.util.find_spec("pythoncom") is not None
    )


def solidworks_backend_status() -> BackendAvailability:
    """Inspect this process. Does not launch SolidWorks."""
    windows = _windows()
    com = _pywin32_present()
    if not windows:
        return BackendAvailability(
            python_com_modules=com,
            windows=False,
            available=False,
            reason=(
                "SolidWorks backend requires a Windows process with "
                "pywin32 and a local SolidWorks 2026 installation"
            ),
        )
    if not com:
        return BackendAvailability(
            python_com_modules=False,
            windows=True,
            available=False,
            reason="pywin32 (win32com/pythoncom) is not installed",
        )
    return BackendAvailability(
        python_com_modules=True,
        windows=True,
        available=True,
        reason="Windows process with pywin32; SolidWorks session not opened",
    )


def solidworks_backend_available() -> bool:
    return solidworks_backend_status().available


def require_solidworks_backend() -> BackendAvailability:
    """Fail closed when COM/pywin32/Windows is unavailable."""
    status = solidworks_backend_status()
    if not status.available:
        raise SolidWorksBackendUnavailableError(status.reason)
    return status
