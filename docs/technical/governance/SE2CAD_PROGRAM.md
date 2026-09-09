# SE2CAD initial program

Responsibility: why the initial proof-of-concept program existed — objective, doctrine, architectural boundaries, end state, and exclusions. Historical charter. Not live status and not a unit catalog.

This program is complete. Do not select work from this file.

Current approved program: [SE2CAD_PROGRAM_M7.md](SE2CAD_PROGRAM_M7.md).
Current units (no live status): [SE2CAD_PLAN_M7.md](SE2CAD_PLAN_M7.md).
Historical units: [SE2CAD_PLAN.md](SE2CAD_PLAN.md).
Live status: [SE2CAD_STATE.md](SE2CAD_STATE.md).
Architecture: [ARCHITECTURE_OVERVIEW.md](../architecture/ARCHITECTURE_OVERVIEW.md).

## Objective

Given a single-grid Large Grid Space Engineers `bp.sbc` containing only:

- `LargeBlockArmorBlock`
- `LargeBlockArmorSlope`
- `LargeBlockArmorCorner`
- `LargeBlockArmorCornerInv`

automatically generate a SolidWorks assembly whose block count, position, and orientation reproduce the Space Engineers object using canonical reusable block parts.

The initial fixture is a deliberately asymmetric user-created Space Engineers object using those four subtypes in varied orientations. It is intended as a permanent regression and qualification asset. See [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md).

## Doctrine

SE2CAD converts Space Engineers ship blueprints into engineering CAD representations.

Two primary architectural processes exist:

**A. Block library / asset preparation** — build and maintain canonical reusable CAD representations of supported block types, plus metadata for coordinate systems, reference frames, geometry strategy, and placement semantics.

**B. Blueprint converter / assembly generator** — parse a supported blueprint, resolve definitions, calculate exact transforms, instantiate canonical CAD parts, and generate a SolidWorks assembly.

The runtime converter must not care how a canonical part was created. It asks the block library for the part and its reference metadata.

A future process **C. Print preparation** may convert generated CAD into consolidated printable geometry. It is downstream and out of scope for this program.

## Architectural boundaries

These decisions are current truth. Do not reopen them while executing this program. Rationale lives in the ADRs.

- CAD-neutral intermediate representation between parsing and backends ([ADR-002](../adr/ADR-002_INTERMEDIATE_REPRESENTATION.md)).
- Independent transform engine; Large Grid cell pitch 2500 mm in one named constant.
- SolidWorks assemblies use calculated transforms, not mate networks that reconstruct fixed SE placement ([ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md)).
- Supported types resolve to reusable canonical parts ([ADR-001](../adr/ADR-001_CANONICAL_BLOCK_LIBRARY.md)).
- Blender is not on the runtime conversion path.
- CubeTopology and TriangleMesh are different geometry classes; this program covers only native armor (CubeTopology-class) parts.
- SolidWorks is the first backend. Core parser, catalog, IR, and transforms stay backend-neutral.

Implementation language is a human technology-selection decision. It is not locked by this charter.

## End state

This program is complete when the permanent asymmetric four-block fixture converts to a SolidWorks assembly that matches the source object in block count, position, and orientation, using four reusable canonical armor parts, with evidence recorded in STATE.

Matching tolerances and the exact comparison method are defined by unit S2C-6.1.1 and the fixture specification. They are not defined here.

## Exclusions

Do not let these leak into early implementation merely because the longer-term architecture acknowledges them:

- TriangleMesh functional or detail blocks
- Blender integration
- general FBX/MWM conversion
- print optimization, STL/3MF generation, mesh merging, shell detection, automatic hollowing
- multiple grids, subgrids, pistons, rotors, hinges
- connectors as mechanical relationships
- docked small ships
- unsupported-block substitution
- reverse conversion back into Space Engineers

Future programs may address those after human authorization. This plan must not grow milestones for them.
