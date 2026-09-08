# Blueprint converter architecture

Responsibility: durable contract for parsing a blueprint into a CAD assembly via IR, catalog, transforms, and the block library. Not a capability claim.

This document is decided design. Whether converter stages exist is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Initial-program units are S2C-1.2.1 through S2C-6.1.1.

Companion decisions: [ADR-002](../adr/ADR-002_INTERMEDIATE_REPRESENTATION.md), [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md). Library side: [BLOCK_LIBRARY_ARCHITECTURE.md](BLOCK_LIBRARY_ARCHITECTURE.md).

## Pipeline

```
bp.sbc → parser → catalog resolve → IR + transform engine → library lookup → CAD backend → SLDASM
```

Responsibilities:

| Stage | Does | Does not |
| --- | --- | --- |
| Parser | Read supported `bp.sbc` safely; extract grid and per-block subtype, position, Forward, Up | Resolve geometry identity; compute CAD transforms; call SolidWorks |
| Definition catalog | Map exact subtype → geometry identity; expose grid pitch from one named constant | Load meshes; contain COM types; scan a game install |
| Transform engine | Compute exact placement from grid coordinate + orientation + pitch | Insert components; apply mates |
| Block library | Return canonical part + reference metadata | Parse blueprints |
| SolidWorks backend | Insert parts by transform; save assembly | Recalculate SE orientation; call Blender; build mate networks for fixed SE placement |

## Intermediate representation

The IR is CAD-neutral. It must be able to represent at least:

- grid identity
- grid size
- block subtype
- block grid coordinate
- forward direction
- up direction
- resolved geometry identity
- canonical transform
- information needed by downstream CAD backends that can be expressed without backend API types

It must not contain SolidWorks COM objects or API structures.

## Definition catalog

The catalog is repository-resident JSON, version-controlled with the code, and loaded by the packaged Python module. It is source-of-truth data, not a runtime database and not a scan of a Space Engineers installation.

Authoritative file: `src/se2cad/catalog/large_grid_armor.json`.
Loader: `se2cad.catalog.load_default_catalog`.
Large Grid cell pitch: `se2cad.catalog.LARGE_GRID_CELL_PITCH_MM` (2500 mm). Application code must use that name, not copy the literal.

Each catalog entry has two groups of fields that must not be collapsed:

| Group | Meaning | Fields |
| --- | --- | --- |
| Observed Space Engineers facts | Tokens taken from installed cube-block definitions | `subtype_id`, `type_id`, `cube_size`, `size` (cell occupancy), `block_topology`, `cube_topology` |
| SE2CAD decisions | Identities and policy owned by this project | `geometry_id`, `recipe_kind`, `support_status` |

`geometry_id` is an SE2CAD identity. It is not a Keen subtype. Distinct subtypes keep distinct geometry IDs.

Lookup is an exact, case-sensitive match of the parser `subtype_id` string. Unknown subtypes fail closed. Duplicate `subtype_id` or `geometry_id` values, unknown `recipe_kind` values, and malformed JSON are rejected at load.

Recipe vocabulary remains `native_procedural`, `sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, and `unsupported`. Naming a recipe is not an implementation of that recipe. The initial four Large Grid armor entries use `native_procedural` only.

The catalog must not store machine-specific paths or proprietary mesh/texture references. The normal conversion path must not open Space Engineers content files to resolve these four subtypes.

## Transforms

Coordinate and orientation transformation is an independent subsystem. It finishes before the SolidWorks backend is invoked.

Large Grid cell pitch is 2500 mm, from the single catalog/dimensional constant. Do not copy the literal through converter code.

Space Engineers orientation is expressed as Forward and Up. The exact basis mapping to the library reference frame is established with evidence in S2C-3.1.1. If it cannot be proven, stop and ask.

## SolidWorks backend

First CAD backend, isolated behind a boundary. Core parser, catalog, IR, and transforms must not import SolidWorks types.

Placement method: apply the calculated transform to each inserted component. Do not reconstruct fixed Space Engineers block placement with mates.

## Initial-program limits

The converter success path for this program is:

- one grid
- Large Grid
- only the four armor subtypes in [SE2CAD_PROGRAM.md](../governance/SE2CAD_PROGRAM.md)

Fail closed on multiple grids, unsupported grid size, missing required fields, or unknown subtypes. Do not silently drop blocks or substitute unsupported types.

Blender is not a converter stage. Print preparation is not a converter stage.
