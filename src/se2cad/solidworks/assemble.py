"""Generate a transform-placed SolidWorks assembly from a qualified IR.

Uses already-generated canonical SLDPRT files. Does not author parts,
does not reinterpret Space Engineers orientation, and does not add mates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.ir.model import CanonicalBlueprint
from se2cad.library import EDGE_TREATMENT_CHAMFER, EDGE_TREATMENT_OFF, EdgeTreatmentRequest
from se2cad.policy import ConversionPolicy, ConversionRefusedError
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
    needed = tuple(dict.fromkeys(item.geometry_id for item in placements))
    part_paths = require_canonical_part_files(
        resolved.generated_root, treatment, geometry_ids=needed
    )
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
    policy: ConversionPolicy = ConversionPolicy.STRICT,
) -> GeneratedAssembly:
    """Parse a blueprint through the qualified pipeline and write an SLDASM.

    Default policy is strict. Pass ``ConversionPolicy.PERMISSIVE`` to
    insert the designated filler for unknown or unsupported blocks.
    """
    resolved = resolve_recipes_from_blueprint(Path(blueprint_path), policy=policy)
    return generate_assembly_from_ir(resolved.ir, config, treatment)


def _parse_assemble_argv(
    argv: list[str],
) -> tuple[Path, EdgeTreatmentRequest, ConversionPolicy] | None:
    """Parse ``<blueprint.sbc> [--edge-treatment chamfer] [--policy permissive]``.

    Matches the part-generation treatment spelling. Default policy is
    strict. Unknown flags fail closed.
    """
    usage = (
        "usage: python -m se2cad.solidworks.assemble "
        "<blueprint.sbc> [--edge-treatment chamfer] [--policy permissive]"
    )
    if not argv or argv[0].startswith("-"):
        print(usage)
        return None
    blueprint = Path(argv[0])
    treatment = EDGE_TREATMENT_OFF
    policy = ConversionPolicy.STRICT
    seen_treatment = False
    seen_policy = False
    rest = argv[1:]
    index = 0
    while index < len(rest):
        token = rest[index]
        if token == "--edge-treatment":
            if seen_treatment or index + 1 >= len(rest):
                print(usage)
                return None
            value = rest[index + 1]
            if value == "off":
                treatment = EDGE_TREATMENT_OFF
            elif value == "chamfer":
                treatment = EDGE_TREATMENT_CHAMFER
            else:
                print(usage)
                return None
            seen_treatment = True
            index += 2
            continue
        if token == "--policy":
            if seen_policy or index + 1 >= len(rest):
                print(usage)
                return None
            value = rest[index + 1]
            if value == ConversionPolicy.STRICT.value:
                policy = ConversionPolicy.STRICT
            elif value == ConversionPolicy.PERMISSIVE.value:
                policy = ConversionPolicy.PERMISSIVE
            else:
                print(usage)
                return None
            seen_policy = True
            index += 2
            continue
        print(usage)
        return None
    return blueprint, treatment, policy


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
    blueprint, request, policy = parsed
    config = load_solidworks_backend_config()
    try:
        result = generate_assembly(
            blueprint, config, treatment=request, policy=policy
        )
    except ConversionRefusedError as exc:
        print(exc)
        return 2
    print(f"generated_root={config.generated_root} source={config.source}")
    print(f"{result.identity} -> {result.path} components={len(result.after_reopen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
