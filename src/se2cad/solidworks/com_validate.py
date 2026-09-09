"""Validate a live SolidWorks part against a qualified construction plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from se2cad.library import EDGE_TREATMENT_MIN_VOLUME_RATIO
from se2cad.solidworks.com_bind import com_get
from se2cad.solidworks.errors import CanonicalPartValidationError, SolidWorksComError
from se2cad.solidworks.recipe_plan import ConstructionPlan, ExpectedSolid
from se2cad.solidworks.units import BACKEND_LENGTH_TOLERANCE_M, volume_tolerance_m3

# Center-of-mass check is looser than length because mass-property APIs
# accumulate more floating-point noise. Still local to this backend.
BACKEND_COM_TOLERANCE_M = 1e-3


@dataclass(frozen=True)
class PartValidation:
    solid_body_count: int
    sheet_body_count: int
    bounding_box_min_m: tuple[float, float, float]
    bounding_box_max_m: tuple[float, float, float]
    volume_m3: float
    center_of_mass_m: tuple[float, float, float]
    face_count: int | None = None


def _as_tuple6(raw: Any) -> tuple[float, ...]:
    if raw is None:
        raise CanonicalPartValidationError("GetPartBox returned None")
    values = tuple(float(v) for v in raw)
    if len(values) != 6:
        raise CanonicalPartValidationError(
            f"GetPartBox returned {len(values)} values, expected 6"
        )
    return values


def _bodies(part: Any, body_type: int) -> list[Any]:
    try:
        raw = com_get(part, "GetBodies2", body_type, False)
    except Exception as exc:
        raise SolidWorksComError(f"GetBodies2 failed: {exc}") from exc
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [body for body in raw if body is not None]
    return [raw]


def _face_count(bodies: list[Any]) -> int | None:
    """Best-effort solid face count. None when the live API is unavailable."""
    total = 0
    readable = False
    for body in bodies:
        try:
            total += int(com_get(body, "GetFaceCount"))
            readable = True
            continue
        except Exception:
            pass
        try:
            faces = com_get(body, "GetFaces")
        except Exception:
            continue
        if faces is None:
            continue
        if isinstance(faces, (list, tuple)):
            total += len([face for face in faces if face is not None])
        else:
            total += 1
        readable = True
    if not readable:
        return None
    return total


def _is_solid_body(body: Any) -> bool:
    for name in ("IsSolid", "get_IsSolid"):
        attr = getattr(body, name, None)
        if callable(attr):
            try:
                return bool(attr())
            except Exception:
                continue
        if attr is not None and not callable(attr):
            return bool(attr)
    try:
        return bool(body.GetType() == 0)
    except Exception:
        return False


def read_part_validation(session: Any, model: Any) -> PartValidation:
    """Read body inventory, envelope, volume, and center of mass."""
    constants = session.constants
    try:
        solid_type = constants.swSolidBody
        sheet_type = constants.swSheetBody
    except Exception:
        solid_type = 0
        sheet_type = 1

    solids = _bodies(model, solid_type)
    sheets = _bodies(model, sheet_type)
    if any(not _is_solid_body(body) for body in solids):
        raise CanonicalPartValidationError(
            "GetBodies2(swSolidBody) returned a non-solid body"
        )

    try:
        box = _as_tuple6(com_get(model, "GetPartBox", True))
    except CanonicalPartValidationError:
        raise
    except Exception as exc:
        raise SolidWorksComError(f"GetPartBox failed: {exc}") from exc

    try:
        extension = com_get(model, "Extension")
        mass = com_get(extension, "CreateMassProperty")
        if mass is None:
            raise CanonicalPartValidationError("CreateMassProperty returned None")
        if hasattr(mass, "UseSystemUnits"):
            mass.UseSystemUnits = True
        volume = float(com_get(mass, "Volume"))
        com = com_get(mass, "CenterOfMass")
        if com is None:
            raise CanonicalPartValidationError("CenterOfMass returned None")
        com_xyz = tuple(float(v) for v in com)
        if len(com_xyz) != 3:
            raise CanonicalPartValidationError(
                f"CenterOfMass returned {len(com_xyz)} values, expected 3"
            )
    except CanonicalPartValidationError:
        raise
    except Exception as exc:
        raise SolidWorksComError(f"mass properties failed: {exc}") from exc

    return PartValidation(
        solid_body_count=len(solids),
        sheet_body_count=len(sheets),
        bounding_box_min_m=(box[0], box[1], box[2]),
        bounding_box_max_m=(box[3], box[4], box[5]),
        volume_m3=volume,
        center_of_mass_m=(com_xyz[0], com_xyz[1], com_xyz[2]),
        face_count=_face_count(solids),
    )


def _near(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def _near_point(
    actual: tuple[float, float, float],
    expected: tuple[float, float, float],
    tolerance: float,
) -> bool:
    return all(_near(a, e, tolerance) for a, e in zip(actual, expected))


def assert_matches_plan(observed: PartValidation, expected: ExpectedSolid) -> None:
    """Fail closed on body-count, envelope, volume, or frame mismatch."""
    if observed.solid_body_count != 1:
        raise CanonicalPartValidationError(
            f"expected exactly one solid body, found {observed.solid_body_count}"
        )
    if observed.sheet_body_count != 0:
        raise CanonicalPartValidationError(
            f"surface/sheet bodies are not accepted: found {observed.sheet_body_count}"
        )

    extent = expected.bounding_box_max_m[0] - expected.bounding_box_min_m[0]
    length_tol = BACKEND_LENGTH_TOLERANCE_M
    volume_tol = volume_tolerance_m3(extent)

    if not _near_point(
        observed.bounding_box_min_m, expected.bounding_box_min_m, length_tol
    ) or not _near_point(
        observed.bounding_box_max_m, expected.bounding_box_max_m, length_tol
    ):
        raise CanonicalPartValidationError(
            "bounding box does not match the qualified cell envelope: "
            f"got min={observed.bounding_box_min_m} max={observed.bounding_box_max_m}, "
            f"expected min={expected.bounding_box_min_m} "
            f"max={expected.bounding_box_max_m}"
        )
    if not _near(observed.volume_m3, expected.volume_m3, volume_tol):
        raise CanonicalPartValidationError(
            f"volume {observed.volume_m3} m^3 does not match "
            f"qualified {expected.volume_m3} m^3 "
            f"(tolerance {volume_tol} m^3)"
        )
    if not _near_point(
        observed.center_of_mass_m, expected.center_of_mass_m, BACKEND_COM_TOLERANCE_M
    ):
        raise CanonicalPartValidationError(
            f"center of mass {observed.center_of_mass_m} m does not match "
            f"qualified {expected.center_of_mass_m} m "
            f"(tolerance {BACKEND_COM_TOLERANCE_M} m)"
        )


def _box_contains(
    outer_min: tuple[float, float, float],
    outer_max: tuple[float, float, float],
    inner_min: tuple[float, float, float],
    inner_max: tuple[float, float, float],
    tolerance: float,
) -> bool:
    return all(
        inner_min[i] >= outer_min[i] - tolerance
        and inner_max[i] <= outer_max[i] + tolerance
        for i in range(3)
    )


def assert_matches_treatment_contract(
    untreated: PartValidation,
    treated: PartValidation,
    *,
    envelope_min_m: tuple[float, float, float],
    envelope_max_m: tuple[float, float, float],
    min_ratio: float = EDGE_TREATMENT_MIN_VOLUME_RATIO,
) -> None:
    """Fail closed when a treated solid misses the S2C-10.1.1 measurables."""
    if treated.solid_body_count != 1:
        raise CanonicalPartValidationError(
            f"treated part expected one solid body, found {treated.solid_body_count}"
        )
    if treated.sheet_body_count != 0:
        raise CanonicalPartValidationError(
            "treated part must not contain sheet bodies: "
            f"found {treated.sheet_body_count}"
        )
    if treated.volume_m3 >= untreated.volume_m3:
        raise CanonicalPartValidationError(
            "treated volume did not decrease: "
            f"treated={treated.volume_m3} untreated={untreated.volume_m3}"
        )
    if untreated.volume_m3 <= 0.0:
        raise CanonicalPartValidationError("untreated volume is not positive")
    ratio = treated.volume_m3 / untreated.volume_m3
    if ratio < min_ratio:
        raise CanonicalPartValidationError(
            "treated volume exceeds the change bound: "
            f"ratio={ratio} min={min_ratio}"
        )
    length_tol = BACKEND_LENGTH_TOLERANCE_M
    if not _box_contains(
        untreated.bounding_box_min_m,
        untreated.bounding_box_max_m,
        treated.bounding_box_min_m,
        treated.bounding_box_max_m,
        length_tol,
    ):
        raise CanonicalPartValidationError(
            "treated solid left the untreated envelope: "
            f"treated min={treated.bounding_box_min_m} "
            f"max={treated.bounding_box_max_m}"
        )
    if not _box_contains(
        envelope_min_m,
        envelope_max_m,
        treated.bounding_box_min_m,
        treated.bounding_box_max_m,
        length_tol,
    ):
        raise CanonicalPartValidationError(
            "treated solid left the placement cell envelope: "
            f"treated min={treated.bounding_box_min_m} "
            f"max={treated.bounding_box_max_m}"
        )
    if (
        untreated.face_count is not None
        and treated.face_count is not None
        and treated.face_count <= untreated.face_count
    ):
        raise CanonicalPartValidationError(
            "treated face count did not increase: "
            f"treated={treated.face_count} untreated={untreated.face_count}"
        )


def validate_model(session: Any, model: Any, plan: ConstructionPlan) -> PartValidation:
    observed = read_part_validation(session, model)
    assert_matches_plan(observed, plan.expected)
    return observed
