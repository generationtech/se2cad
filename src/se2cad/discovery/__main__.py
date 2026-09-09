"""Operator entry for library-build cube-block definition discovery.

Not a general SE2CAD CLI. Usage: python -m se2cad.discovery
Requires SE2CAD_GAME_ROOT, SE2CAD_SDK_ROOT, or se2cad.local.json.
"""

from __future__ import annotations

import sys

from se2cad.discovery.discover import discover_cube_block_definitions
from se2cad.discovery.errors import DiscoveryError
from se2cad.discovery.model import DiscoveryReport


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        print("usage: python -m se2cad.discovery")
        return 2
    try:
        report = discover_cube_block_definitions()
    except DiscoveryError as exc:
        _print_operator_text(str(exc))
        return 2
    _print_operator_text(_format_report(report))
    return 0


def _format_report(report: DiscoveryReport) -> str:
    lines = [
        f"definition_count={len(report.definitions)}",
        f"files_read={len(report.files_read)}",
        f"game_root_configured={str(report.game_root_configured).lower()}",
        f"sdk_root_configured={str(report.sdk_root_configured).lower()}",
    ]
    for item in report.definitions:
        topology = item.cube_topology if item.cube_topology is not None else ""
        size = f"{item.size.x}x{item.size.y}x{item.size.z}"
        lines.append(
            f"{item.subtype_id}\t{item.type_id}\t{item.cube_size}\t"
            f"{size}\t{item.block_topology}\t{topology}\t"
            f"{item.source_kind}:{item.source_relative}"
        )
    return "\n".join(lines)


def _print_operator_text(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe = text.encode(encoding, errors="backslashreplace").decode(encoding)
    print(safe)


if __name__ == "__main__":
    raise SystemExit(main())
