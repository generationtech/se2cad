"""Insert canonical parts into a SolidWorks assembly by IR transform.

Live SolidWorks 2026 CDispatch evidence (revision 34.3.2, 2026-09-08):

- NewDocument(default assembly template, pref 9) returns GetType=2.
- AddComponent5(path, 0, '', False, '', 0, 0, 0) inserts a pre-opened part.
- IMathUtility.CreateTransform faults on this late-bound session (same
  class as IModeler array calls). Do not use it.
- IMathTransform.ArrayData accepts a VT_ARRAY|VT_R8 VARIANT tuple of 16
  doubles and rejects a raw Python list (list write corrupts translation).
- The first inserted component is auto-fixed. Select(True) +
  UnfixComponent clears that without adding placement mates.
- The assembly MateGroup folder exists and is empty after unfix.
- Transform2 ArrayData survives SaveAs / CloseDoc / OpenDoc(swDocASSEMBLY).

Placement is Transform2 only. Mates are not used to reconstruct SE pose.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.errors import AssemblyValidationError, SolidWorksComError
from se2cad.solidworks.placement import ComponentPlacement
from se2cad.solidworks.transform_pack import solidworks_arraydata
from se2cad.solidworks.units import BACKEND_LENGTH_TOLERANCE_M


def _com_fail(exc: BaseException, message: str) -> SolidWorksComError:
    return SolidWorksComError(f"{message}: {exc}")


def variant_r8(values: Sequence[float]) -> Any:
    """SAFEARRAY of doubles. Required for MathTransform.ArrayData on 2026 CDispatch."""
    import pythoncom
    import win32com.client

    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8,
        tuple(float(v) for v in values),
    )


def read_arraydata(component: Any) -> tuple[float, ...]:
    try:
        xform = com_get(component, "Transform2")
        raw = com_get(xform, "ArrayData")
    except Exception as exc:
        raise _com_fail(exc, "Transform2.ArrayData read failed") from exc
    if raw is None:
        raise AssemblyValidationError("Transform2.ArrayData returned None")
    data = tuple(float(v) for v in raw)
    if len(data) != 16:
        raise AssemblyValidationError(
            f"Transform2.ArrayData returned {len(data)} values, expected 16"
        )
    return data


def apply_arraydata(component: Any, data: Sequence[float]) -> None:
    try:
        xform = com_get(component, "Transform2")
        xform.ArrayData = variant_r8(data)
        component.Transform2 = xform
    except Exception as exc:
        raise _com_fail(exc, "setting Transform2.ArrayData failed") from exc


def unfix_component(assembly: Any, component: Any) -> None:
    try:
        fixed = bool(com_get(component, "IsFixed"))
    except Exception as exc:
        raise _com_fail(exc, "IsFixed failed") from exc
    if not fixed:
        return
    try:
        com_get(component, "Select", True)
        com_get(assembly, "UnfixComponent")
        assembly.ClearSelection2(True)
    except Exception as exc:
        raise _com_fail(exc, "UnfixComponent failed") from exc
    try:
        still_fixed = bool(com_get(component, "IsFixed"))
    except Exception as exc:
        raise _com_fail(exc, "IsFixed after unfix failed") from exc
    if still_fixed:
        raise AssemblyValidationError("component remained fixed after UnfixComponent")


def add_component(assembly: Any, part_path: Path) -> Any:
    try:
        component = assembly.AddComponent5(
            str(part_path),
            0,
            "",
            False,
            "",
            0.0,
            0.0,
            0.0,
        )
    except Exception as exc:
        raise _com_fail(exc, f"AddComponent5 failed for {part_path}") from exc
    if component is None:
        raise SolidWorksComError(f"AddComponent5 returned None for {part_path}")
    return component


def component_path(component: Any) -> Path:
    try:
        raw = com_get(component, "GetPathName")
    except Exception as exc:
        raise _com_fail(exc, "GetPathName failed") from exc
    if not raw:
        raise AssemblyValidationError("component GetPathName is empty")
    return Path(str(raw))


def list_components(assembly: Any) -> list[Any]:
    try:
        raw = com_get(assembly, "GetComponents", True)
    except Exception as exc:
        raise _com_fail(exc, "GetComponents failed") from exc
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [item for item in raw if item is not None]
    return [raw]


def mate_child_names(assembly: Any) -> tuple[str, ...]:
    """Names of features inside the assembly MateGroup, if any."""
    feat = com_get(assembly, "FirstFeature")
    mates = None
    while feat is not None:
        try:
            type_name = str(com_get(feat, "GetTypeName2") or "")
        except Exception:
            type_name = ""
        if type_name == "MateGroup":
            mates = feat
            break
        feat = com_get(feat, "GetNextFeature")
    if mates is None:
        return ()
    names: list[str] = []
    sub = com_get(mates, "GetFirstSubFeature")
    while sub is not None:
        names.append(str(com_get(sub, "Name")))
        sub = com_get(sub, "GetNextSubFeature")
    return tuple(names)


def document_type(model: Any) -> int:
    try:
        return int(com_get(model, "GetType"))
    except Exception as exc:
        raise _com_fail(exc, "GetType failed") from exc


@dataclass(frozen=True)
class PlacedComponent:
    placement: ComponentPlacement
    part_path: Path
    arraydata: tuple[float, ...]


def insert_placements(
    session: Any,
    assembly: Any,
    placements: Sequence[ComponentPlacement],
    part_paths: dict[str, Path],
) -> tuple[PlacedComponent, ...]:
    """Insert one component per placement and apply the IR transform directly."""
    placed: list[PlacedComponent] = []
    for placement in placements:
        part_path = part_paths[placement.geometry_id]
        component = add_component(assembly, part_path)
        unfix_component(assembly, component)
        data = solidworks_arraydata(placement.rotation, placement.position_mm)
        apply_arraydata(component, data)
        observed_path = component_path(component)
        if observed_path.name != placement.part_filename:
            raise AssemblyValidationError(
                "component was substituted: "
                f"expected {placement.part_filename}, got {observed_path}"
            )
        observed = read_arraydata(component)
        _assert_arraydata_close(observed, data, placement)
        if com_get(component, "GetMates") not in (None, (), []):
            raise AssemblyValidationError(
                f"component {placement.part_filename} has mates"
            )
        placed.append(
            PlacedComponent(
                placement=placement,
                part_path=observed_path,
                arraydata=observed,
            )
        )
    com_get(assembly, "EditRebuild3")
    children = mate_child_names(assembly)
    if children:
        raise AssemblyValidationError(
            f"assembly MateGroup is not empty: {children}"
        )
    return tuple(placed)


def _assert_arraydata_close(
    observed: tuple[float, ...],
    expected: tuple[float, ...],
    placement: ComponentPlacement,
) -> None:
    for index in range(9):
        if abs(observed[index] - expected[index]) > BACKEND_LENGTH_TOLERANCE_M:
            raise AssemblyValidationError(
                f"rotation ArrayData[{index}]={observed[index]} does not match "
                f"IR {expected[index]} for source_index={placement.source_index}"
            )
    for index in range(9, 12):
        if abs(observed[index] - expected[index]) > BACKEND_LENGTH_TOLERANCE_M:
            raise AssemblyValidationError(
                f"translation ArrayData[{index}]={observed[index]} does not match "
                f"IR {expected[index]} m for source_index={placement.source_index}"
            )
    if abs(observed[12] - 1.0) > BACKEND_LENGTH_TOLERANCE_M:
        raise AssemblyValidationError(
            f"transform scale {observed[12]} is not 1 for "
            f"source_index={placement.source_index}"
        )


def assert_assembly_matches(
    assembly: Any,
    placements: Sequence[ComponentPlacement],
    generated_root: Path,
) -> tuple[PlacedComponent, ...]:
    """Read components after generate or reopen and fail closed on mismatch."""
    doc_type = document_type(assembly)
    if doc_type != 2:
        raise AssemblyValidationError(
            f"document type {doc_type} is not swDocASSEMBLY (2)"
        )
    components = list_components(assembly)
    if len(components) != len(placements):
        raise AssemblyValidationError(
            f"expected {len(placements)} components, found {len(components)}"
        )
    children = mate_child_names(assembly)
    if children:
        raise AssemblyValidationError(
            f"assembly MateGroup is not empty: {children}"
        )

    remaining = list(placements)
    matched: list[PlacedComponent] = []
    for component in components:
        path = component_path(component)
        try:
            path.relative_to(generated_root)
        except ValueError as exc:
            raise AssemblyValidationError(
                f"component path {path} escapes generated root {generated_root}"
            ) from exc
        data = read_arraydata(component)
        mates = com_get(component, "GetMates")
        if mates not in (None, (), []):
            raise AssemblyValidationError(f"component {path.name} has mates")
        index = _index_matching_placement(remaining, path.name, data)
        if index is None:
            raise AssemblyValidationError(
                f"no remaining IR placement matches {path.name} "
                f"transform {data[:12]}"
            )
        placement = remaining.pop(index)
        if path.name != placement.part_filename:
            raise AssemblyValidationError(
                "component was substituted: "
                f"expected {placement.part_filename}, got {path}"
            )
        matched.append(
            PlacedComponent(placement=placement, part_path=path, arraydata=data)
        )
    if remaining:
        raise AssemblyValidationError(
            f"{len(remaining)} IR placements were not found in the assembly"
        )
    return tuple(matched)


def _index_matching_placement(
    remaining: Iterable[ComponentPlacement],
    filename: str,
    data: tuple[float, ...],
) -> int | None:
    remaining_list = list(remaining)
    for index, placement in enumerate(remaining_list):
        if placement.part_filename != filename:
            continue
        expected = solidworks_arraydata(placement.rotation, placement.position_mm)
        try:
            _assert_arraydata_close(data, expected, placement)
        except AssemblyValidationError:
            continue
        return index
    return None
