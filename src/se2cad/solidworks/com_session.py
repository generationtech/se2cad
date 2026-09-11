"""Windows-local SolidWorks COM session. Imported only when COM is requested."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from se2cad.solidworks.availability import require_solidworks_backend
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.errors import SolidWorksBackendUnavailableError, SolidWorksComError

# Late-bound CDispatch (SolidWorks 2026 / pywin32 312) cannot run makepy, so
# win32com.client.constants has no SolidWorks enums. Values below are the
# published API enumerations; swDefaultTemplatePart=8 was confirmed against
# a live 34.3.2 session (GetUserPreferenceStringValue → Part.prtdot).
_FALLBACK_CONSTANTS = {
    "swDefaultTemplatePart": 8,
    "swDefaultTemplateAssembly": 9,  # live 34.3.2 → Assembly.asmdot
    "swDocPART": 1,
    "swDocASSEMBLY": 2,  # live 34.3.2 GetType of NewDocument(asmdot)
    "swOpenDocOptions_Silent": 1,
    "swSaveAsCurrentVersion": 0,
    "swSaveAsOptions_Silent": 1,
    "swSolidBody": 0,
    "swSheetBody": 1,
    "swEndCondMidPlane": 6,
    "swEndCondThroughAll": 1,
    "swStartSketchPlane": 0,
    "swRefPlaneReferenceConstraint_Coincident": 4,
    "swCreateFacesBodyActionKnit": 1,
    "swCreateFeatureBodyCheck": 1,
    "swCreateFeatureBodySimplify": 2,
    "SWBODYCUT": 1593,
    "swAddComponentConfigOptions_CurrentSelectedConfig": 0,
    # Official Name2 remarks: set fails when this toggle is True.
    "swExtRefUpdateCompNames": 18,
    # Published swChamferType_e / swFeatureChamferOption_e.
    "swChamferAngleDistance": 1,
    "swChamferDistanceDistance": 2,
    "swChamferVertex": 3,
    "swChamferEqualDistance": 16,
    "swFeatureChamferFlipDirection": 1,
    "swFeatureChamferKeepFeature": 2,
    "swFeatureChamferTangentPropagation": 4,
    # Published STL/VRML import preferences. Graphics + mm avoids the
    # solid-heal / Import Diagnostics modal that can hang LoadFile2 when
    # Visible is false. Values from swUserPreferenceIntegerValue_e /
    # swImportStlVrmlModelType_e / swLengthUnit_e / swUserPreferenceToggle_e.
    "swImportStlVrmlModelType": 208,
    "swImportStlVrmlUnits": 210,
    "swImportStlVrmlModelType_Graphics": 0,
    "swMM": 0,
    "swImportAutoRunImportDiagnostics": 291,
}


def _wrap_com(exc: BaseException, message: str) -> SolidWorksComError:
    return SolidWorksComError(f"{message}: {exc}")


class _SolidWorksConstants:
    """Typelib constants when makepy exists; otherwise published fallbacks."""

    def __init__(self, generated: Any = None) -> None:
        self._generated = generated

    def __getattr__(self, name: str) -> int:
        if self._generated is not None:
            try:
                return int(getattr(self._generated, name))
            except Exception:
                pass
        if name in _FALLBACK_CONSTANTS:
            return _FALLBACK_CONSTANTS[name]
        raise AttributeError(name)


def _solidworks_constants(win32com_client: Any) -> _SolidWorksConstants:
    return _SolidWorksConstants(getattr(win32com_client, "constants", None))


def _attach_sldworks(win32com_client: Any) -> tuple[Any, bool]:
    """Attach to a local SldWorks.Application.

    Prefer the running instance. Use late-bound Dispatch. Do not require
    gencache.EnsureDispatch: SolidWorks 2026 GetTypeInfo fails and makepy
    cannot be automated.
    """
    try:
        app = win32com_client.GetActiveObject("SldWorks.Application")
        started = False
    except Exception:
        app = win32com_client.Dispatch("SldWorks.Application")
        started = True
    dynamic = getattr(win32com_client, "dynamic", None)
    if dynamic is not None and hasattr(dynamic, "Dispatch"):
        # A local makepy cache can make Dispatch return an early-bound
        # wrapper. SolidWorks 2026 GetTypeInfo is incomplete; stay late-bound.
        app = dynamic.Dispatch(app)
    if app is None:
        raise SolidWorksBackendUnavailableError(
            "SldWorks.Application dispatch returned None"
        )
    return app, started


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
    _stl_import_previous: tuple[int, int, bool] | None = None

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
            self.app, self.started_application = _attach_sldworks(win32com.client)
            self.constants = _solidworks_constants(win32com.client)
        except SolidWorksBackendUnavailableError:
            self._co_uninitialize()
            raise
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
            return str(com_get(self.app, "RevisionNumber"))
        except Exception as exc:
            raise _wrap_com(exc, "RevisionNumber failed") from exc

    def part_template(self) -> str:
        if self.config.part_template is not None:
            return str(self.config.part_template)
        try:
            template = self.app.GetUserPreferenceStringValue(
                int(self.constants.swDefaultTemplatePart)
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

    def assembly_template(self) -> str:
        try:
            template = self.app.GetUserPreferenceStringValue(
                int(self.constants.swDefaultTemplateAssembly)
            )
        except Exception as exc:
            raise _wrap_com(
                exc,
                "GetUserPreferenceStringValue(swDefaultTemplateAssembly) failed",
            ) from exc
        if not template:
            raise SolidWorksComError(
                "SolidWorks default assembly template is empty"
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

    def new_assembly(self) -> Any:
        template = self.assembly_template()
        try:
            model = self.app.NewDocument(template, 0, 0.0, 0.0)
        except Exception as exc:
            raise _wrap_com(
                exc, f"NewDocument failed for assembly template {template}"
            ) from exc
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
            # IModelDoc2.SaveAs is the live 2026 late-bound path.
            # Extension.SaveAs rejects Python None for ExportData
            # (DISP_E_TYPEMISMATCH on argument 4).
            ok = com_get(model, "SaveAs", path)
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

    def close_named(self, name: str) -> None:
        """Close a document by title if SolidWorks still has it open."""
        if not name:
            return
        try:
            self.app.CloseDoc(name)
        except Exception:
            pass
        if name in self._open_titles:
            self._open_titles.remove(name)

    def close_doc(self, model: Any) -> None:
        title = self._title(model)
        if not title:
            return
        try:
            self.app.CloseDoc(title)
        except Exception as exc:
            raise _wrap_com(exc, f"CloseDoc failed for {title!r}") from exc
        if title in self._open_titles:
            self._open_titles.remove(title)

    def open_imported_mesh(self, path: Path) -> Any:
        """Open an intermediate mesh file as a SolidWorks part document.

        Imported SDK meshes are graphics bodies. Solid knit and automatic
        Import Diagnostics stay disabled for the whole session so a later
        identity cannot restore a hanging solid-heal preference mid-batch.
        """
        self._ensure_graphics_stl_import()
        return self._open_imported_mesh(path)

    def _ensure_graphics_stl_import(self) -> None:
        if self._stl_import_previous is not None:
            return
        self._stl_import_previous = self._prepare_graphics_stl_import()

    def _open_imported_mesh(self, path: Path) -> Any:
        last_error: Exception | None = None
        for name, args in (
            ("LoadFile2", (str(path), "")),
            ("LoadFile", (str(path),)),
            (
                "OpenDoc",
                (str(path), int(self.constants.swDocPART)),
            ),
        ):
            try:
                result = com_get(self.app, name, *args)
            except Exception as exc:
                last_error = exc
                continue
            model = result
            if isinstance(result, bool):
                if not result:
                    last_error = SolidWorksComError(f"{name} returned false for {path}")
                    continue
                try:
                    model = com_get(self.app, "ActiveDoc")
                except Exception as exc:
                    last_error = exc
                    continue
            if model is None or isinstance(model, bool):
                last_error = SolidWorksComError(
                    f"{name} did not produce a document for {path}"
                )
                continue
            title = self._title(model)
            if title:
                self._open_titles.append(title)
            return model
        raise _wrap_com(
            last_error or SolidWorksComError("no importer"),
            f"could not import mesh {path}",
        )

    def _prepare_graphics_stl_import(self) -> tuple[int, int, bool]:
        model_pref = int(self.constants.swImportStlVrmlModelType)
        units_pref = int(self.constants.swImportStlVrmlUnits)
        diag_pref = int(self.constants.swImportAutoRunImportDiagnostics)
        try:
            previous_model = int(
                com_get(self.app, "GetUserPreferenceIntegerValue", model_pref)
            )
            previous_units = int(
                com_get(self.app, "GetUserPreferenceIntegerValue", units_pref)
            )
            previous_diag = bool(
                com_get(self.app, "GetUserPreferenceToggle", diag_pref)
            )
        except Exception as exc:
            raise _wrap_com(exc, "failed to read STL import preferences") from exc
        try:
            self.app.SetUserPreferenceIntegerValue(
                model_pref,
                int(self.constants.swImportStlVrmlModelType_Graphics),
            )
            self.app.SetUserPreferenceIntegerValue(
                units_pref,
                int(self.constants.swMM),
            )
            self.app.SetUserPreferenceToggle(diag_pref, False)
        except Exception as exc:
            raise _wrap_com(exc, "failed to set graphics STL import preferences") from exc
        return previous_model, previous_units, previous_diag

    def _restore_stl_import_preferences(
        self, previous: tuple[int, int, bool]
    ) -> None:
        previous_model, previous_units, previous_diag = previous
        try:
            self.app.SetUserPreferenceIntegerValue(
                int(self.constants.swImportStlVrmlModelType),
                previous_model,
            )
            self.app.SetUserPreferenceIntegerValue(
                int(self.constants.swImportStlVrmlUnits),
                previous_units,
            )
            self.app.SetUserPreferenceToggle(
                int(self.constants.swImportAutoRunImportDiagnostics),
                previous_diag,
            )
        except Exception as exc:
            raise _wrap_com(exc, "failed to restore STL import preferences") from exc

    def open_part(self, path: Path) -> Any:
        try:
            model = com_get(
                self.app,
                "OpenDoc",
                str(path),
                int(self.constants.swDocPART),
            )
        except Exception as exc:
            raise _wrap_com(exc, f"OpenDoc failed for {path}") from exc
        if model is None:
            self.close_named(path.stem)
            self.close_named(path.name)
            try:
                model = com_get(
                    self.app,
                    "OpenDoc",
                    str(path),
                    int(self.constants.swDocPART),
                )
            except Exception as exc:
                raise _wrap_com(exc, f"OpenDoc retry failed for {path}") from exc
        if model is None or isinstance(model, bool):
            raise SolidWorksComError(f"OpenDoc returned None for {path}")
        title = self._title(model)
        if title and title not in self._open_titles:
            self._open_titles.append(title)
        return model

    def open_assembly(self, path: Path) -> Any:
        try:
            model = com_get(
                self.app,
                "OpenDoc",
                str(path),
                int(self.constants.swDocASSEMBLY),
            )
        except Exception as exc:
            raise _wrap_com(exc, f"OpenDoc failed for {path}") from exc
        if model is None:
            raise SolidWorksComError(f"OpenDoc returned None for {path}")
        title = self._title(model)
        if title:
            self._open_titles.append(title)
        return model

    def get_modeler(self) -> Any:
        try:
            modeler = com_get(self.app, "GetModeler")
        except Exception as exc:
            raise _wrap_com(exc, "GetModeler failed") from exc
        if modeler is None:
            raise SolidWorksComError("GetModeler returned None")
        return modeler

    def _title(self, model: Any) -> str:
        try:
            value = com_get(model, "GetTitle")
        except Exception:
            return ""
        return str(value) if value is not None else ""

    def close(self) -> None:
        titles = list(self._open_titles)
        for title in titles:
            try:
                self.app.CloseDoc(title)
            except Exception:
                pass
            if title in self._open_titles:
                self._open_titles.remove(title)
        if self._stl_import_previous is not None and self.app is not None:
            try:
                self._restore_stl_import_preferences(self._stl_import_previous)
            except Exception:
                pass
            self._stl_import_previous = None
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
