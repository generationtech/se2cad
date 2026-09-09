"""Generate a transform-placed SolidWorks assembly from a qualified IR.

Uses already-generated canonical SLDPRT files. Does not author parts,
does not reinterpret Space Engineers orientation, and does not add mates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.ir.model import CanonicalBlueprint
from se2cad.library import EDGE_TREATMENT_CHAMFER, EDGE_TREATMENT_OFF, EdgeTreatmentRequest
from se2cad.solidworks.artifacts import (
    assembly_path_for,
    assert_overwrite_is_canonical,
)
from se2cad.solidworks.availability import require_solidworks_backend
from se2cad.solidworks.com_assemble import (
    PlacedComponent,
    allow_component_name2_set,
    assert_assembly_matches,
    document_type,
    insert_placements,
    restore_component_name2_preference,
)
from se2cad.solidworks.com_session import SolidWorksSession
from se2cad.solidworks.config import SolidWorksBackendConfig, load_solidworks_backend_config
from se2cad.solidworks.errors import AssemblyValidationError
from se2cad.solidworks.pipeline import resolve_recipes_from_blueprint
from se2cad.solidworks.placement import (
    ComponentPlacement,
    placements_from_ir,
    require_canonical_part_files,
)


@dataclass(frozen=True)
class GeneratedAssembly:
    path: Path
    identity: str
    placements: tuple[ComponentPlacement, ...]
    after_save: tuple[PlacedComponent, ...]
    after_reopen: tuple[PlacedComponent, ...]


def assembly_destination(
    config: SolidWorksBackendConfig,
    identity: str,
) -> Path:
    destination = assembly_path_for(config.generated_root, identity)
    assert_overwrite_is_canonical(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def generate_assembly_from_ir(
    ir: CanonicalBlueprint,
    config: SolidWorksBackendConfig | None = None,
    treatment: EdgeTreatmentRequest | None = None,
) -> GeneratedAssembly:
    """Insert one component per IR block using the qualified (R, t).

    Default assembly inserts untreated ``{geometry_id}.SLDPRT``. Pass
    ``EDGE_TREATMENT_CHAMFER`` to insert treated siblings. Missing
    treated artifacts fail closed; they are not replaced by untreated
    parts.
    """
    require_solidworks_backend()
    resolved = config if config is not None else load_solidworks_backend_config()
    identity = ir.identity_subtype
    if not identity:
        raise AssemblyValidationError("canonical IR has no identity_subtype")
    placements = placements_from_ir(ir, treatment)
    part_paths = require_canonical_part_files(resolved.generated_root, treatment)
    destination = assembly_destination(resolved, identity)

    opened_parts: list[object] = []
    assembly = None
    with SolidWorksSession(resolved) as session:
        previous_update_names = allow_component_name2_set(session)
        try:
            try:
                for path in part_paths.values():
                    opened_parts.append(session.open_part(path))
                assembly = session.new_assembly()
                if document_type(assembly) != 2:
                    raise AssemblyValidationError(
                        f"NewDocument did not produce swDocASSEMBLY, got {document_type(assembly)}"
                    )
                insert_placements(session, assembly, placements, part_paths)
                after_save = assert_assembly_matches(
                    assembly, placements, resolved.generated_root
                )
                session.save_as(assembly, destination)
            finally:
                if assembly is not None:
                    session.close_doc(assembly)
                for part in opened_parts:
                    session.close_doc(part)

            reopened = session.open_assembly(destination)
            try:
                after_reopen = assert_assembly_matches(
                    reopened, placements, resolved.generated_root
                )
            finally:
                session.close_doc(reopened)
        finally:
            restore_component_name2_preference(session, previous_update_names)

    return GeneratedAssembly(
        path=destination,
        identity=identity,
        placements=placements,
        after_save=after_save,
        after_reopen=after_reopen,
    )


def generate_assembly(
    blueprint_path: Path,
    config: SolidWorksBackendConfig | None = None,
    treatment: EdgeTreatmentRequest | None = None,
) -> GeneratedAssembly:
    """Parse a blueprint through the qualified pipeline and write an SLDASM."""
    resolved = resolve_recipes_from_blueprint(Path(blueprint_path))
    return generate_assembly_from_ir(resolved.ir, config, treatment)


def _parse_assemble_argv(
    argv: list[str],
) -> tuple[Path, EdgeTreatmentRequest] | None:
    """Parse ``<blueprint.sbc> [--edge-treatment chamfer]``.

    Matches the part-generation spelling. Unknown flags fail closed.
    """
    usage = (
        "usage: python -m se2cad.solidworks.assemble "
        "<blueprint.sbc> [--edge-treatment chamfer]"
    )
    if not argv or argv[0].startswith("-"):
        print(usage)
        return None
    blueprint = Path(argv[0])
    flags = argv[1:]
    if not flags:
        return blueprint, EDGE_TREATMENT_OFF
    if flags == ["--edge-treatment", "off"]:
        return blueprint, EDGE_TREATMENT_OFF
    if flags == ["--edge-treatment", "chamfer"]:
        return blueprint, EDGE_TREATMENT_CHAMFER
    print(usage)
    return None


def main(argv: list[str] | None = None) -> int:
    import sys

    from se2cad.solidworks.availability import solidworks_backend_status

    status = solidworks_backend_status()
    if not status.available:
        print(status.reason)
        return 2
    parsed = _parse_assemble_argv(sys.argv[1:] if argv is None else argv)
    if parsed is None:
        return 2
    blueprint, request = parsed
    config = load_solidworks_backend_config()
    result = generate_assembly(blueprint, config, treatment=request)
    print(f"generated_root={config.generated_root} source={config.source}")
    print(f"{result.identity} -> {result.path} components={len(result.after_reopen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
