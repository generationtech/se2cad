"""Operator entry for Windows-local canonical part generation.

Not a general SE2CAD CLI. Requires SE2CAD_GENERATED_ROOT or se2cad.local.json.
Default conversion remains untreated. Treated siblings are written only
when ``--edge-treatment chamfer`` is requested.
"""

from __future__ import annotations

import sys

from se2cad.library import EDGE_TREATMENT_CHAMFER, EDGE_TREATMENT_OFF, EdgeTreatmentRequest
from se2cad.solidworks.availability import solidworks_backend_status
from se2cad.solidworks.config import load_solidworks_backend_config
from se2cad.solidworks.generate import generate_canonical_parts


def _treatment_from_argv(argv: list[str]) -> EdgeTreatmentRequest:
    if not argv:
        return EDGE_TREATMENT_OFF
    if argv == ["--edge-treatment", "off"]:
        return EDGE_TREATMENT_OFF
    if argv == ["--edge-treatment", "chamfer"]:
        return EDGE_TREATMENT_CHAMFER
    print(
        "usage: python -m se2cad.solidworks [--edge-treatment chamfer]",
        file=sys.stderr,
    )
    raise SystemExit(2)


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
