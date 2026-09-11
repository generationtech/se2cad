# SE2CAD program M7–M15

Responsibility: why the current approved development program exists — objective, doctrine, architectural boundaries, milestone order, end state, and exclusions. Not live status and not a unit catalog.

This is the executable development program after the completed initial proof-of-concept. It does not reopen the initial program and does not replace its historical charter.

Historical initial program (complete): [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md).
Units for this program (no live status): [SE2CAD_PLAN_M7.md](SE2CAD_PLAN_M7.md).
Live status: [SE2CAD_STATE.md](SE2CAD_STATE.md).
How to execute a unit: [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md).
Architecture: [ARCHITECTURE_OVERVIEW.md](../architecture/ARCHITECTURE_OVERVIEW.md).

## Objective

Extend the qualified four-block Large Grid converter into a broader, still-bounded CAD reconstruction capability by delivering exactly these nine approved features, in this order:

1. Blueprint statistics
2. CAD component naming from Space Engineers data
3. Blueprint block-color preservation
4. Printable block-edge definition
5. SDK-driven vanilla block library expansion
6. Blueprint compatibility and unknown-block handling
7. Small Grid support
8. Symmetry detection
9. Automatic print-shell generation

The program is complete when those nine milestones meet the completion outcomes in [SE2CAD_PLAN_M7.md](SE2CAD_PLAN_M7.md) and STATE records the evidence.

## Relationship to the initial program

The initial M0–M6 program is complete and remains historical truth. Its units, fixture, coordinate contract, catalog split, CAD-neutral IR, transform engine, native armor recipes, Windows-local SolidWorks backend, and transform-placed assembly path stay in force.

This program continues from M7. It does not rewrite M0–M6, does not reopen ADR-001 through ADR-004, and does not invent additional product features.

## Doctrine

The two primary processes remain:

**A. Block library / asset preparation** — canonical reusable CAD representations plus metadata.

**B. Blueprint converter / assembly generator** — parse, resolve, transform, instantiate, assemble.

**C. Print preparation** is authorized in this program only as automatic print-shell generation (M15). It is not a general slicer, STL/3MF, or physical-print subsystem.

The runtime converter still asks the library for a part and reference metadata. It must not require Space Engineers or the ModSDK at conversion time. Operator-local game/SDK paths may be used for library-build discovery and evidence, consistent with [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).

## Architectural boundaries

These remain current truth. Do not reopen them while executing this program.

- CAD-neutral IR between parsing and backends ([ADR-002](../adr/ADR-002_INTERMEDIATE_REPRESENTATION.md)).
- Independent transform engine. Grid pitch lives in named catalog constants, not scattered literals. Large Grid remains `LARGE_GRID_CELL_PITCH_MM` (2500). Small Grid, when added, uses a second named constant rather than forking the pipeline.
- SolidWorks assemblies use calculated transforms, not mate networks that reconstruct fixed SE placement ([ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md)).
- Supported types resolve to reusable canonical parts ([ADR-001](../adr/ADR-001_CANONICAL_BLOCK_LIBRARY.md)).
- Reusable block geometry stays distinct from per-instance appearance.
- Geometry support and appearance support stay independently reportable.
- Blender is not on the runtime conversion path.
- CubeTopology and TriangleMesh remain different geometry classes. Do not force one production mechanism.
- SolidWorks is the first backend. Core parser, catalog, IR, transforms, statistics, component names, preflight, and symmetry stay backend-neutral.
- Generated CAD remains local cache and is not committed or published by default.
- Apache-2.0 does not relicense Keen, Microsoft, SolidWorks, or other third-party assets ([ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md)).

Authorized expansions of those boundaries — not replacements — are listed in the milestones: IR may carry appearance; the parser may accept Small Grid; unknown blocks may use an explicit filler under a named permissive policy; print-shell generation may consume IR and library solids.

## Milestone order

Use the repository milestone IDs `M7` through `M15`. Unit IDs remain `S2C-<milestone>.<workstream>.<sequence>`.

| Milestone | Title |
| --- | --- |
| M7 | Blueprint statistics |
| M8 | CAD component naming from SE data |
| M9 | Blueprint block-color preservation |
| M10 | Printable block-edge definition |
| M11 | SDK-driven vanilla block library expansion |
| M12 | Blueprint compatibility and unknown-block handling |
| M13 | Small Grid support |
| M14 | Symmetry detection |
| M15 | Automatic print-shell generation |

Do not reorder, merge, or split these milestones. Do not start a later milestone’s first unit until STATE authorizes it. Sequencing prerequisites in the plan enforce this order even when a later milestone has no data dependency on the immediately previous one.

A listed prerequisite is met at DEV-COMPLETE unless the later unit consumes that unit’s QUALIFIED artifact or evidence (typically a live SolidWorks part or assembly). STATE names the next executable unit.

A 2026-09-09 human-authorized amendment inserted S2C-10.3.1 into M10 after S2C-11.1.1 was already QUALIFIED. That change does not create a tenth milestone, does not reorder M7–M15, and does not invalidate S2C-11.1.1. STATE records the exception and the next executable unit.

A later 2026-09-09 human-authorized amendment inserted S2C-10.4.1 into M10 after S2C-12.2.1 was already QUALIFIED and before S2C-13.1.1. That repair improves already-qualified M10 edge-treatment behavior. It does not rewrite original M10 planning, does not start M13, and does not invalidate S2C-10.3.1, M11, or M12. STATE records the exception and the next executable unit.

A 2026-09-10 human-authorized amendment inserted S2C-11.6.1 into M11 after S2C-12.2.1 and S2C-10.4.1 were already QUALIFIED, and after the human postponed Small Grid. That unit makes already-qualified untreated canonical parts demand-driven. It does not rewrite original M11 history, does not expand the packaged catalog, does not start M13, and does not invent later M11 units. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-12.3.1 into M12 after S2C-11.6.1 was already QUALIFIED and after the human postponed Small Grid. That unit lets ordinary vanilla cube-block object builders parse as block records so existing policy can run. It does not rewrite original M12 history, does not add CAD support for functional blocks, does not expand the packaged catalog, does not start M13, and does not invent later units. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-12.4.1 into M12 after S2C-12.3.1 was already QUALIFIED and after the human postponed Small Grid. That unit separates logical ShipBlueprint identity from a deterministic Windows-safe SolidWorks assembly filename. It does not rewrite original M12 history, does not add CAD support, does not expand the packaged catalog, does not start M13, and does not invent later units. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-11.7.1 into M11 after S2C-12.4.1 was already QUALIFIED and after the human postponed Small Grid. That unit is a single-identity SDK-FBX materialization experiment for `LargeBlockSmallHydrogenThrust` only. It deliberately crosses the previously unqualified `sdk_mesh_direct` recipe boundary for that one bind. It does not rewrite original M11 history, does not claim general SDK-mesh or universal vanilla support, does not start M13, and did not invent S2C-11.8.x at that time. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-11.8.1 into M11 after S2C-11.7.1 was already QUALIFIED and after the human postponed Small Grid. That unit adds demand-driven vanilla TriangleMesh resolution for eligible Large Grid 1×1×1 blocks. It generalizes source resolution, not universal geometry. It does not rewrite original M11 history, does not expand the packaged catalog, does not start multi-cell placement, CubeTopology expansion, Small Grid, or OBJ export, and does not invent a later unit. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-11.9.1 into M11 after S2C-11.8.1 was already QUALIFIED and after the human postponed Small Grid. That unit extends the already-qualified SDK-mesh builder so official ASCII FBX can be consumed when every other S2C-11.8.1 eligibility rule is already satisfied. It is a source-format extension, not a new resolver or a general FBX framework. It does not rewrite original M11 history, does not expand the packaged catalog, does not start multi-cell placement, CubeTopology expansion, Small Grid, or OBJ export, and does not invent a later unit. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-11.10.1 into M11 after S2C-11.9.1 was already QUALIFIED and after the human postponed Small Grid. That unit qualifies CAD-neutral Size/ModelOffset occupancy-center placement math without granting multi-cell runtime support. It does not rewrite original M11 history, does not expand the packaged catalog, does not start Small Grid, CubeTopology expansion, or OBJ export, and does not invent a later unit. STATE records the exception. Small Grid remains postponed until the human later directs it.

A later 2026-09-10 human-authorized amendment inserted S2C-11.11.1 into M11 after S2C-11.10.1 was already QUALIFIED and after the human postponed Small Grid. That unit removes only the blanket 1×1×1 runtime gate so already-eligible Large Grid vanilla TriangleMesh identities can materialize and place through the existing demand-driven path. It does not rewrite original M11 history, does not expand the packaged catalog, does not start Small Grid, CubeTopology expansion, or OBJ export, and does not invent a later unit. STATE records the exception. Small Grid remains postponed until the human later directs it.

## Qualification model

Status words are defined in [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md). STATE is the only live status.

- DEV-COMPLETE means the unit’s development validation passed, a distinct quality/security assessment was performed, and verified findings were remediated.
- QUALIFIED means DEV-COMPLETE plus any external or application validation that unit explicitly names, with recorded evidence.
- Do not invent external validation merely to obtain QUALIFIED.
- Prefer automated tests, fixtures, generated artifacts, and programmatic inspection.
- Where a unit must prove a SolidWorks document fact, use the existing live integration pattern (`SE2CAD_SOLIDWORKS_INTEGRATION`) rather than a separate operator ritual.

## Opschecks

An opscheck is an exceptional operator procedure used only when automated tests and the existing live-integration machinery cannot establish a required external fact.

This program defines **no named opschecks**. SolidWorks, Space Engineers, the ModSDK, Windows, Blender, and physical printing appearing in a workflow is not by itself a reason to create one.

## End state

This program is complete when all nine milestones are QUALIFIED (or a unit’s documented DEV-COMPLETE-only bar is met and no remaining unit requires more) and STATE records that fact.

Matching method and tolerances for CAD placement remain those established by S2C-6.1.1 and [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md) unless a later unit records a justified, tested change.

## Exclusions (cold storage)

These remain outside this approved program. Do not pull them into executable scope because adjacent work looks useful:

- multi-grid ships, subgrids, pistons, rotors, hinges
- connectors as mechanical relationships
- docked small ships
- reverse conversion back into Space Engineers
- Blender as a runtime conversion stage
- a general FBX/MWM end-user conversion product
- a completed TriangleMesh functional-block library (M11 may classify and except such blocks; that is not delivery of the class)
- slicer integration, automated STL/3MF publishing, or physical-print automation
- additional CAD backends
- a polished general CLI or any GUI
- items that exist only in an external ChatGPT Library or other cold-storage backlog

Do not invent work beyond this program. A later program requires a new human authorization recorded in the repository.
