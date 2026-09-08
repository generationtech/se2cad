"""Load and validate the repository-resident definition catalog.

The packaged JSON file is the runtime source. Installed Space Engineers
definitions are evidence used to author that file, not a runtime input.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from se2cad.catalog.errors import CatalogValidationError
from se2cad.catalog.model import (
    CatalogEntry,
    CellSize,
    DefinitionCatalog,
    ObservedDefinition,
    RecipeKind,
    SupportStatus,
)

_PACKAGED_CATALOG_NAME = "large_grid_armor.json"
_SUPPORTED_SCHEMA_VERSION = 1
_REQUIRED_TOP_LEVEL = frozenset({"schema_version", "entries"})
_REQUIRED_ENTRY = frozenset({"subtype_id", "observed", "se2cad"})
_REQUIRED_OBSERVED = frozenset(
    {"type_id", "cube_size", "size", "block_topology", "cube_topology"}
)
_REQUIRED_SE2CAD = frozenset({"geometry_id", "recipe_kind", "support_status"})
_REQUIRED_SIZE = frozenset({"x", "y", "z"})


def default_catalog_path() -> Path:
    """Filesystem path of the packaged catalog, when one exists.

    Used by tests and packaging. Runtime lookup must call
    :func:`load_default_catalog`, which reads the package resource.
    """
    return Path(str(files("se2cad.catalog").joinpath(_PACKAGED_CATALOG_NAME)))


def load_default_catalog() -> DefinitionCatalog:
    """Load the authoritative repository catalog shipped with this package."""
    resource = files("se2cad.catalog").joinpath(_PACKAGED_CATALOG_NAME)
    try:
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise CatalogValidationError(
            f"packaged catalog {_PACKAGED_CATALOG_NAME!r} is missing"
        ) from exc
    return load_catalog_text(text, source=_PACKAGED_CATALOG_NAME)


def load_catalog_file(path: Path) -> DefinitionCatalog:
    """Load a catalog JSON file from an explicit local path.

    ``path`` is an operator- or test-selected file. It is never taken from
    blueprint content.
    """
    catalog_path = Path(path)
    if not catalog_path.is_file():
        raise CatalogValidationError(
            f"catalog path is not a file: {catalog_path}"
        )
    text = catalog_path.read_text(encoding="utf-8")
    return load_catalog_text(text, source=str(catalog_path.name))


def load_catalog_text(text: str, *, source: str = "<string>") -> DefinitionCatalog:
    """Parse and validate catalog JSON text."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CatalogValidationError(
            f"{source}: catalog JSON is malformed: {exc}"
        ) from exc
    return _catalog_from_data(data, source=source)


def _catalog_from_data(data: Any, *, source: str) -> DefinitionCatalog:
    if not isinstance(data, dict):
        raise CatalogValidationError(f"{source}: catalog root must be an object")
    _require_keys(data, _REQUIRED_TOP_LEVEL, where=f"{source} root")
    version = data["schema_version"]
    if version != _SUPPORTED_SCHEMA_VERSION:
        raise CatalogValidationError(
            f"{source}: unsupported schema_version {version!r}"
        )
    raw_entries = data["entries"]
    if not isinstance(raw_entries, list):
        raise CatalogValidationError(f"{source}: entries must be an array")
    entries: list[CatalogEntry] = []
    seen_subtypes: set[str] = set()
    seen_geometry: set[str] = set()
    for index, raw in enumerate(raw_entries):
        loc = f"{source} entries[{index}]"
        entry = _entry_from_data(raw, loc)
        if entry.subtype_id in seen_subtypes:
            raise CatalogValidationError(
                f"{loc}: duplicate subtype_id {entry.subtype_id!r}"
            )
        if entry.geometry_id in seen_geometry:
            raise CatalogValidationError(
                f"{loc}: duplicate geometry_id {entry.geometry_id!r}"
            )
        seen_subtypes.add(entry.subtype_id)
        seen_geometry.add(entry.geometry_id)
        entries.append(entry)
    return DefinitionCatalog(entries=tuple(entries))


def _entry_from_data(raw: Any, loc: str) -> CatalogEntry:
    if not isinstance(raw, dict):
        raise CatalogValidationError(f"{loc}: entry must be an object")
    _require_keys(raw, _REQUIRED_ENTRY, where=loc)
    subtype_id = _exact_identity(raw["subtype_id"], f"{loc}.subtype_id")
    observed = _observed_from_data(raw["observed"], f"{loc}.observed")
    se2cad = raw["se2cad"]
    if not isinstance(se2cad, dict):
        raise CatalogValidationError(f"{loc}.se2cad: must be an object")
    _require_keys(se2cad, _REQUIRED_SE2CAD, where=f"{loc}.se2cad")
    geometry_id = _exact_identity(se2cad["geometry_id"], f"{loc}.se2cad.geometry_id")
    recipe_kind = _recipe_kind(se2cad["recipe_kind"], f"{loc}.se2cad.recipe_kind")
    support_status = _support_status(
        se2cad["support_status"], f"{loc}.se2cad.support_status"
    )
    return CatalogEntry(
        subtype_id=subtype_id,
        observed=observed,
        geometry_id=geometry_id,
        recipe_kind=recipe_kind,
        support_status=support_status,
    )


def _observed_from_data(raw: Any, loc: str) -> ObservedDefinition:
    if not isinstance(raw, dict):
        raise CatalogValidationError(f"{loc}: must be an object")
    _require_keys(raw, _REQUIRED_OBSERVED, where=loc)
    return ObservedDefinition(
        type_id=_exact_identity(raw["type_id"], f"{loc}.type_id"),
        cube_size=_exact_identity(raw["cube_size"], f"{loc}.cube_size"),
        size=_cell_size(raw["size"], f"{loc}.size"),
        block_topology=_exact_identity(
            raw["block_topology"], f"{loc}.block_topology"
        ),
        cube_topology=_exact_identity(
            raw["cube_topology"], f"{loc}.cube_topology"
        ),
    )


def _cell_size(raw: Any, loc: str) -> CellSize:
    if not isinstance(raw, dict):
        raise CatalogValidationError(f"{loc}: must be an object")
    _require_keys(raw, _REQUIRED_SIZE, where=loc)
    return CellSize(
        x=_positive_int(raw["x"], f"{loc}.x"),
        y=_positive_int(raw["y"], f"{loc}.y"),
        z=_positive_int(raw["z"], f"{loc}.z"),
    )


def _recipe_kind(value: Any, loc: str) -> RecipeKind:
    if not isinstance(value, str):
        raise CatalogValidationError(f"{loc}: recipe_kind must be a string")
    try:
        return RecipeKind(value)
    except ValueError:
        raise CatalogValidationError(
            f"{loc}: unknown recipe_kind {value!r}"
        ) from None


def _support_status(value: Any, loc: str) -> SupportStatus:
    if not isinstance(value, str):
        raise CatalogValidationError(f"{loc}: support_status must be a string")
    try:
        return SupportStatus(value)
    except ValueError:
        raise CatalogValidationError(
            f"{loc}: unknown support_status {value!r}"
        ) from None


def _exact_identity(value: Any, loc: str) -> str:
    if not isinstance(value, str) or value == "":
        raise CatalogValidationError(f"{loc}: must be a non-empty string")
    return value


def _positive_int(value: Any, loc: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogValidationError(f"{loc}: must be an integer")
    if value < 1:
        raise CatalogValidationError(f"{loc}: must be >= 1")
    return value


def _require_keys(raw: dict[str, Any], required: frozenset[str], *, where: str) -> None:
    missing = sorted(required.difference(raw))
    if missing:
        raise CatalogValidationError(
            f"{where}: missing required field(s): {', '.join(missing)}"
        )
    unexpected = sorted(set(raw).difference(required))
    if unexpected:
        raise CatalogValidationError(
            f"{where}: unexpected field(s): {', '.join(unexpected)}"
        )
