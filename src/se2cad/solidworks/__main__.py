"""Operator entry for Windows-local canonical part generation.

Not a general SE2CAD CLI. Requires SE2CAD_GENERATED_ROOT or se2cad.local.json.
Default conversion remains untreated. This entry writes treated siblings
only for the four initial-program identities when
``--edge-treatment chamfer`` is requested. Blueprint assembly is the
primary demand-driven producer of size-specific chamfer variants.
"""

from __future__ import annotations

import sys

from se2cad.library import (
    EDGE_TREATMENT_CHAMFER,
    EDGE_TREATMENT_OFF,
    EdgeTreatmentRequest,
    TreatmentError,
    chamfer_treatment,
    parse_chamfer_mm_token,
)
from se2cad.solidworks.availability import solidworks_backend_status
from se2cad.solidworks.config import load_solidworks_backend_config
from se2cad.solidworks.generate import generate_canonical_parts


def _treatment_from_argv(argv: list[str]) -> EdgeTreatmentRequest:
    usage = (
        "usage: python -m se2cad.solidworks "
        "[--edge-treatment chamfer] [--chamfer-mm <value>]"
    )
    if not argv:
        return EDGE_TREATMENT_OFF
    treatment_kind: str | None = None
    chamfer_mm_raw: str | None = None
    seen_treatment = False
    seen_chamfer_mm = False
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--edge-treatment":
            if seen_treatment or index + 1 >= len(argv):
                print(usage, file=sys.stderr)
                raise SystemExit(2)
            value = argv[index + 1]
            if value not in {"off", "chamfer"}:
                print(usage, file=sys.stderr)
                raise SystemExit(2)
            treatment_kind = value
            seen_treatment = True
            index += 2
            continue
        if token == "--chamfer-mm":
            if seen_chamfer_mm or index + 1 >= len(argv):
                print(usage, file=sys.stderr)
                raise SystemExit(2)
            chamfer_mm_raw = argv[index + 1]
            seen_chamfer_mm = True
            index += 2
            continue
        print(usage, file=sys.stderr)
        raise SystemExit(2)
    try:
        if chamfer_mm_raw is not None and treatment_kind != "chamfer":
            raise TreatmentError(
                "--chamfer-mm is valid only when --edge-treatment chamfer is selected"
            )
        if treatment_kind in {None, "off"}:
            return EDGE_TREATMENT_OFF
        if chamfer_mm_raw is None:
            return EDGE_TREATMENT_CHAMFER
        return chamfer_treatment(parse_chamfer_mm_token(chamfer_mm_raw))
    except TreatmentError as exc:
        print(exc, file=sys.stderr)
        print(usage, file=sys.stderr)
        raise SystemExit(2) from exc


def main(argv: list[str] | None = None) -> int:
    request = _treatment_from_argv(sys.argv[1:] if argv is None else argv)
    status = solidworks_backend_status()
    if not status.available:
        print(status.reason)
        return 2
    config = load_solidworks_backend_config()
    print(f"generated_root={config.generated_root} source={config.source}")
    for result in generate_canonical_parts(config, treatment=request):
        locator = result.locator
        print(
            f"{locator.identity.geometry_id} -> {locator.path} "
            f"volume_m3={result.after_reopen.volume_m3} "
            f"treatment_applied={result.treatment_applied}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
