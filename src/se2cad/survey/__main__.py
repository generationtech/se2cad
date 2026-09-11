"""Operator entry for the CAD-neutral compatibility survey.

Not a general SE2CAD CLI. Usage:

    python -m se2cad.survey <blueprint-or-prefab.sbc> [--markdown <out.md>]

Exit 0 means a report was produced. That is not conversion success and
not a support grant.
"""

from __future__ import annotations

import sys
from pathlib import Path

from se2cad.parser import BlueprintParseError
from se2cad.survey.compute import compute_compatibility_survey_from_path
from se2cad.survey.report import format_survey_markdown


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    markdown_path: Path | None = None
    positional: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--markdown":
            if index + 1 >= len(args):
                print("usage: python -m se2cad.survey <blueprint.sbc> [--markdown <out.md>]")
                return 2
            markdown_path = Path(args[index + 1])
            index += 2
            continue
        positional.append(token)
        index += 1
    if len(positional) != 1:
        print("usage: python -m se2cad.survey <blueprint.sbc> [--markdown <out.md>]")
        return 2
    try:
        survey = compute_compatibility_survey_from_path(positional[0])
    except BlueprintParseError as exc:
        _print_operator_text(str(exc))
        return 2
    text = format_survey_markdown(survey)
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(text, encoding="utf-8")
    _print_operator_text(_format_summary(survey))
    return 0


def _format_summary(survey) -> str:
    structural = survey.structural
    return "\n".join(
        [
            f"identity={structural.identity or ''}",
            f"kind={structural.kind.value}",
            f"sha256={structural.sha256}",
            f"grids={structural.grid_count}",
            f"block_count={survey.block_count}",
            f"unique={survey.unique_identity_count}",
            f"supported={survey.supported_instance_count}",
            f"packaged={survey.packaged_instance_count}",
            f"runtime={survey.runtime_instance_count}",
            f"unsupported_known={survey.unsupported_known_instance_count}",
            f"unknown_unresolved={survey.unknown_unresolved_instance_count}",
            f"supported_percent={survey.cumulative.current_supported_percent}",
            (
                "top_causes="
                + ",".join(cause.value for cause in survey.cumulative.top_causes)
            ),
            "conversion_performed=false",
            "support_granted=false",
        ]
    )


def _print_operator_text(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe = text.encode(encoding, errors="backslashreplace").decode(encoding)
    print(safe)


if __name__ == "__main__":
    raise SystemExit(main())
