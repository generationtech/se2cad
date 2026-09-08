"""Windows-local SolidWorks COM session. Imported only when COM is requested."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from se2cad.solidworks.availability import require_solidworks_backend
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.errors import SolidWorksBackendUnavailableError, SolidWorksComError


def _wrap_com(exc: BaseException, message: str) -> SolidWorksComError:
    return SolidWorksComError(f"{message}: {exc}")


@dataclass
class SolidWorksSession:
    """One local SolidWorks application attachment.

    Documents opened by this session are closed on exit. The SolidWorks
    process is not quit, so an operator session is not destroyed.
    """

    config: SolidWorksBackendConfig
    app: Any = None
    constants: Any = None
    started_application: bool = False
    _open_titles: list[str] = field(default_factory=list)
    _com_initialized: bool = False

    def __enter__(self) -> SolidWorksSession:
        require_solidworks_backend()
        try:
            import pythoncom
            import win32com.client
        except ImportError as exc:
            raise SolidWorksBackendUnavailableError(
                f"pywin32 is not importable: {exc}"
            ) from exc
        try:
            pythoncom.CoInitialize()
            self._com_initialized = True
        except Exception as exc:
            raise _wrap_com(exc, "CoInitialize failed") from exc

        try:
            try:
                win32com.client.GetActiveObject("SldWorks.Application")
                self.started_application = False
            except Exception:
                self.started_application = True
            self.app = win32com.client.gencache.EnsureDispatch("SldWorks.Application")
            self.constants = win32com.client.constants
        except Exception as exc:
            self._co_uninitialize()
            raise SolidWorksBackendUnavailableError(
                f"cannot attach to SldWorks.Application: {exc}"
            ) from exc

        try:
            self.app.Visible = bool(self.config.visible)
        except Exception as exc:
            self.close()
            raise _wrap_com(exc, "failed to set SolidWorks Visible") from exc
        return self

    def _co_uninitialize(self) -> None:
        if not self._com_initialized:
            return
        try:
            import pythoncom

            pythoncom.CoUninitialize()
        except Exception:
            pass
        self._com_initialized = False

    def revision(self) -> str:
        try:
            return str(self.app.RevisionNumber())
        except Exception as exc:
            raise _wrap_com(exc, "RevisionNumber failed") from exc

    def part_template(self) -> str:
        if self.config.part_template is not None:
            return str(self.config.part_template)
        try:
            template = self.app.GetUserPreferenceStringValue(
                self.constants.swDefaultTemplatePart
            )
        except Exception as exc:
            raise _wrap_com(
                exc, "GetUserPreferenceStringValue(swDefaultTemplatePart) failed"
            ) from exc
        if not template:
            raise SolidWorksComError(
                "SolidWorks default part template is empty; set "
                "SE2CAD_SOLIDWORKS_PART_TEMPLATE"
            )
        return str(template)

    def new_part(self) -> Any:
        template = self.part_template()
        try:
            model = self.app.NewDocument(template, 0, 0.0, 0.0)
        except Exception as exc:
            raise _wrap_com(exc, f"NewDocument failed for template {template}") from exc
        if model is None:
            raise SolidWorksComError(f"NewDocument returned None for {template}")
        title = self._title(model)
        if title:
            self._open_titles.append(title)
        return model

    def save_as(self, model: Any, destination: Path) -> None:
        previous = self._title(model)
        path = str(destination)
        try:
            constants = self.constants
            version = constants.swSaveAsCurrentVersion
            options = constants.swSaveAsOptions_Silent
        except Exception:
            version = 0
            options = 1
        try:
            import pythoncom
            import win32com.client

            errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            ok = model.Extension.SaveAs(
                path, version, options, None, errors, warnings
            )
        except Exception as exc:
            raise _wrap_com(exc, f"SaveAs failed for {path}") from exc
        if not ok:
            raise SolidWorksComError(f"SaveAs returned false for {path}")
        if not destination.is_file():
            raise SolidWorksComError(
                f"SaveAs claimed success but file does not exist: {destination}"
            )
        self._retitle(model, previous)

    def _retitle(self, model: Any, previous: str) -> None:
        current = self._title(model)
        if previous in self._open_titles:
            self._open_titles.remove(previous)
        if current and current not in self._open_titles:
            self._open_titles.append(current)

    def close_doc(self, model: Any) -> None:
        title = self._title(model)
        try:
            if title:
                self.app.CloseDoc(title)
            elif hasattr(model, "Close"):
                model.Close()
        except Exception as exc:
            raise _wrap_com(exc, f"CloseDoc failed for {title!r}") from exc
        if title in self._open_titles:
            self._open_titles.remove(title)

    def open_part(self, path: Path) -> Any:
        try:
            import pythoncom
            import win32com.client

            errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            model = self.app.OpenDoc6(
                str(path),
                self.constants.swDocPART,
                self.constants.swOpenDocOptions_Silent,
                "",
                errors,
                warnings,
            )
        except Exception as exc:
            raise _wrap_com(exc, f"OpenDoc6 failed for {path}") from exc
        if model is None:
            raise SolidWorksComError(f"OpenDoc6 returned None for {path}")
        title = self._title(model)
        if title:
            self._open_titles.append(title)
        return model

    def get_modeler(self) -> Any:
        try:
            modeler = self.app.GetModeler()
        except Exception as exc:
            raise _wrap_com(exc, "GetModeler failed") from exc
        if modeler is None:
            raise SolidWorksComError("GetModeler returned None")
        return modeler

    def _title(self, model: Any) -> str:
        try:
            return str(model.GetTitle())
        except Exception:
            return ""

    def close(self) -> None:
        titles = list(self._open_titles)
        for title in titles:
            try:
                self.app.CloseDoc(title)
            except Exception:
                pass
            if title in self._open_titles:
                self._open_titles.remove(title)
        self._co_uninitialize()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()


def session_environment_report(session: SolidWorksSession) -> dict[str, str]:
    """Facts needed for STATE. Does not inspect Space Engineers."""
    revision = session.revision()
    try:
        import win32com

        pywin32_version = str(getattr(win32com, "__version__", "unknown"))
    except Exception:
        pywin32_version = "unknown"
    return {
        "solidworks_revision": revision,
        "pywin32_version": pywin32_version,
        "progid": "SldWorks.Application",
        "started_application": str(session.started_application),
    }
