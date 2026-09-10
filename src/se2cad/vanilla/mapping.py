"""Map a vanilla primary Model path to an official SDK mesh stem.

This is the only place a ``.mwm`` suffix is rewritten to the official
SDK mesh relationship. The rewrite is exact-stem only: no LOD,
construction, or interior sibling selection.
"""

from __future__ import annotations

from pathlib import Path

from se2cad.vanilla.errors import VanillaLookupError

_GAME_MODEL_SUFFIX = ".mwm"
_FORBIDDEN_NAME_PARTS = ("lod", "construction")


def sdk_stem_from_vanilla_model(model_path: str) -> str:
    """Return the operator-root-relative SDK stem for one primary Model."""
    parts = _safe_model_parts(model_path)
    return "/".join(parts)


def contained_game_model_path(game_root: Path, model_path: str) -> Path:
    """Return the intended game-content model path. File need not exist.

    Containment is required. The path must stay under the configured
    game-content root and use the definition's ``Models/...`` relationship.
    """
    parts = _safe_model_parts(model_path, keep_suffix=True)
    resolved_root = game_root.expanduser().resolve()
    candidate = resolved_root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise VanillaLookupError(
            f"model path {candidate} escapes configured game-content root "
            f"{resolved_root}"
        ) from exc
    return candidate


def _safe_model_parts(
    model_path: str,
    *,
    keep_suffix: bool = False,
) -> tuple[str, ...]:
    if not isinstance(model_path, str) or model_path.strip() == "":
        raise VanillaLookupError("primary Model path is missing")
    normalized = model_path.replace("\\", "/").strip()
    if normalized.startswith("/") or normalized.startswith("\\"):
        raise VanillaLookupError("primary Model path must not be absolute")
    if ":" in normalized:
        raise VanillaLookupError("primary Model path must not contain a drive")
    if not normalized.lower().endswith(_GAME_MODEL_SUFFIX):
        raise VanillaLookupError(
            "primary Model must use the official game mesh suffix"
        )
    stem = normalized[: -len(_GAME_MODEL_SUFFIX)]
    if stem.lower().endswith(_GAME_MODEL_SUFFIX):
        raise VanillaLookupError("primary Model path is not a single mesh file")
    relative = normalized if keep_suffix else stem
    parts = Path(relative).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise VanillaLookupError(
            "primary Model path must stay inside the game-content root"
        )
    if parts[0].lower() != "models":
        raise VanillaLookupError(
            "primary Model path must stay under the Models tree"
        )
    if any(
        any(token in part.lower() for token in _FORBIDDEN_NAME_PARTS)
        for part in parts
    ):
        raise VanillaLookupError(
            "primary Model must not name LOD or construction files"
        )
    return parts
