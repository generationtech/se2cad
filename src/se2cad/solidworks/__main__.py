"""Operator entry for Windows-local canonical part generation.

Not a general SE2CAD CLI. Requires SE2CAD_GENERATED_ROOT or se2cad.local.json.
"""

from __future__ import annotations

from se2cad.solidworks.availability import solidworks_backend_status
from se2cad.solidworks.config import load_solidworks_backend_config
from se2cad.solidworks.generate import generate_canonical_parts


def main() -> int:
    status = solidworks_backend_status()
    if not status.available:
        print(status.reason)
        return 2
    config = load_solidworks_backend_config()
    print(f"generated_root={config.generated_root} source={config.source}")
    for result in generate_canonical_parts(config):
        locator = result.locator
        print(
            f"{locator.identity.geometry_id} -> {locator.path} "
            f"volume_m3={result.after_reopen.volume_m3}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
