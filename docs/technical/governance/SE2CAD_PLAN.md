# SE2CAD initial plan

Responsibility: what bounded units constitute the initial program. This file carries no live status. Do not select work from this file.

Live status and the next executable unit: [SE2CAD_STATE.md](SE2CAD_STATE.md).
Program objective and exclusions: [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md).
How to execute a unit: [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md).

Unit IDs use `S2C-<milestone>.<workstream>.<sequence>`.

Do not add milestones for TriangleMesh, Blender, print preparation, multi-grid, or mechanical subgrids. Those require a future human-authorized program.

---

## Milestone M0 — Repository and program foundation

Establish governance, architecture, ADRs, Cursor rules, repository contract, program charter, plan/state separation, ratchet, third-party asset policy, test doctrine, and the acceptance-fixture specification. No converter implementation.

### S2C-0.1.1 — Establish repository-driven engineering foundation

**Objective.** Leave the public repository in a condition where a fresh AI session, with no chat history, can determine what SE2CAD is, what this program is trying to accomplish, what architecture is decided, which questions remain open, what work is authorized, what the next bounded unit is, how to execute exactly one unit, how to test and assess it, how status advances, and what must never be committed.

**Rationale.** The repository, not conversation history, is durable engineering truth.

**Prerequisites.** None. This is the bootstrap unit.

**Affected systems / expected areas.** `.cursor/rules/`, `docs/`, `fixtures/README.md`, root `README.md`, empty `src/`, `tests/`, and `tools/` markers, `.gitignore` safety-net patterns. No application implementation.

**Implementation requirements.**

- Cursor rules: core authority, bounded development, quality/security, third-party assets.
- Onboarding, repository contract, engineering process, program, plan, state, ratchet.
- Architecture overview, block-library architecture, blueprint-converter architecture.
- ADR-001 through ADR-004.
- Initial acceptance-fixture specification.
- Public README that distinguishes planned architecture from implemented behavior.
- Binding third-party asset policy.
- Plan/state separation; one identifiable next implementation unit after bootstrap.

**Explicit boundaries / out of scope.** No M1 or later implementation. No proprietary game/SDK assets. No commit, tag, push, or release.

**Development validation.** Every bootstrap path and cross-reference resolves. README links resolve. Plan contains no live status. STATE is the only live status. Ratchet and Cursor rules agree with this process. No contradictory authority statements. No proprietary assets added.

**Quality/security assessment focus.** Authority ambiguity; multiple live-status sources; plan carrying status; ratchet allowing multi-unit execution; architecture mistaken for implementation; Apache-2.0 mistaken for a Keen-asset license; derived geometry assumed redistributable; QUALIFIED without evidence; initial-program scope leak (Blender/TriangleMesh/printing).

**External validation.** None. Repository inspection is sufficient.

**Completion criteria.** Structure and documents listed in the bootstrap session exist and agree; references resolve; STATE records what actually happened; exactly one next executable development unit is identified for information only.

---

## Milestone M1 — Blueprint ingestion and fixture

Obtain the human-authored four-block `bp.sbc`, parse supported single-grid blueprint XML safely, and extract block identity, position, and orientation.

### S2C-1.1.1 — Register the four-block acceptance fixture

**Objective.** Add the human-authored asymmetric Large Grid blueprint that uses only the four supported armor subtypes, with provenance, at the path specified in [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md).

**Rationale.** The fixture is the permanent regression and qualification asset for this program.

**Prerequisites.** S2C-0.1.1.

**Affected systems / expected areas.** `fixtures/`, [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md), STATE notes about fixture identity. No parser implementation.

**Implementation requirements.**

- Place `bp.sbc` (and any sibling blueprint metadata that is part of the user-authored fixture) at the specified path.
- Record provenance: author, that it is user-created (not a redistributed Keen asset), intended block composition, and that no game/SDK geometry is embedded.
- Confirm the fixture is single-grid Large Grid and uses only the four named subtypes, in varied orientations, and is asymmetric enough to catch axis swaps and reflection errors.
- Do not invent a substitute blueprint if the human-authored file is absent. Stop and ask.

**Explicit boundaries / out of scope.** Parser, catalog, IR, CAD, additional ships, Small Grid, functional blocks.

**Development validation.** Fixture exists at the specified path. Provenance file exists. A deterministic inspection (no SolidWorks) shows grid size, subtype set, block count, and that positions/orientations vary. Inspection must not require embedding extracted game meshes.

**Quality/security assessment focus.** Accidental game/SDK payload in the fixture tree; path/name confusion; provenance gaps; over-broad binary commit.

**External validation.** Human architect confirms this is the intended Space Engineers object and that provenance is accurate.

**Completion criteria.** Fixture and provenance are in tree; inspection notes are recorded in STATE; human confirmation is recorded before QUALIFIED. Without human confirmation the unit may be DEV-COMPLETE only.

### S2C-1.2.1 — Safe single-grid blueprint parser

**Objective.** Parse a supported single-grid Large Grid `bp.sbc` and extract, for each block, subtype, grid coordinate, forward direction, and up direction, including the acceptance fixture.

**Rationale.** Downstream IR and transforms need a deterministic, safe reading of blueprint XML.

**Prerequisites.** S2C-0.1.1, S2C-1.1.1.

**Affected systems / expected areas.** `src/` parser, `tests/` parser-domain tests, fixture-driven tests. No catalog resolution beyond raw subtype strings. No IR, transforms, or CAD.

**Implementation requirements.**

- If implementation language has not been confirmed by the human architect, stop and ask. The repository template is Python-oriented; language remains a human technology selection.
- Accept a filesystem path to `bp.sbc`.
- Parse XML safely (no external entities; bounded resource use).
- Support only single-grid Large Grid blueprints for this unit's success path.
- Extract grid identity, grid size, and per-block subtype, Min (or equivalent grid position), Forward, and Up.
- Fail closed on malformed XML, missing required fields, multiple grids, or unsupported grid size. Do not silently drop blocks.
- Include deterministic tests from synthetic XML and from the acceptance fixture.

**Explicit boundaries / out of scope.** Definition catalog, geometry identity, transforms, SolidWorks, TriangleMesh, multi-grid recovery.

**Development validation.** Tests cover happy-path fixture extraction, varied orientations present in the fixture, malformed XML, XXE/entity abuse rejected, missing fields, and multiple-grid rejection. Tests prove extracted values, not merely that a function was called.

**Quality/security assessment focus.** XML parser hazards; path traversal; huge-file behavior; secret or absolute-path leakage in errors; silent data loss.

**External validation.** None.

**Completion criteria.** Parser module and tests exist; fixture extracts expected subtype/position/orientation tuples recorded from S2C-1.1.1 inspection; unsafe XML is rejected; STATE records evidence.

---

## Milestone M2 — Definition and catalog model

Represent supported block definitions and distinguish blueprint subtype from canonical geometry identity.

### S2C-2.1.1 — Catalog for the four Large Grid armor types

**Objective.** Provide a definition catalog that recognizes the four initial armor subtypes, maps each to a canonical geometry identity, and exposes Large Grid cell-pitch data through one named constant (2500 mm).

**Rationale.** The converter must resolve blueprint subtypes to library identities without baking SolidWorks types into the catalog.

**Prerequisites.** S2C-1.2.1.

**Affected systems / expected areas.** Catalog model in `src/`, catalog tests, a single dimensional-constant module or equivalent. No mesh loading. No CAD.

**Implementation requirements.**

- Represent supported definitions for `LargeBlockArmorBlock`, `LargeBlockArmorSlope`, `LargeBlockArmorCorner`, and `LargeBlockArmorCornerInv`.
- Distinguish blueprint subtype from canonical geometry identity.
- Record grid size and cell pitch without scattering `2500` through call sites.
- Unknown subtypes fail closed (no silent substitution).
- Catalog records may name a geometry strategy. For these four types the strategy is `native_procedural`. Other strategy names (`sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, `unsupported`) are vocabulary only and must not gain implementations here.

**Explicit boundaries / out of scope.** TriangleMesh recipes, SDK/FBX lookup, IR assembly, transforms, part production.

**Development validation.** Tests resolve each of the four subtypes, reject unknown subtypes, and read cell pitch from the single constant.

**Quality/security assessment focus.** Silent unsupported-block handling; duplicated pitch literals; catalog accidentally importing backend types.

**External validation.** None.

**Completion criteria.** Four entries exist; subtype versus geometry identity is testable; unknown subtypes fail closed; pitch is centralized.

---

## Milestone M3 — Canonical IR and transforms

Define the CAD-neutral IR and compute exact placement transforms from Space Engineers orientation semantics.

### S2C-3.1.1 — Canonical IR and exact placement transforms

**Objective.** Define the canonical IR and a transform engine that, given catalog-resolved blocks, computes exact CAD placement transforms for Large Grid cells using Forward/Up and the 2500 mm pitch.

**Rationale.** Placement must be calculated before any SolidWorks backend runs, and must be testable without COM.

**Prerequisites.** S2C-2.1.1.

**Affected systems / expected areas.** IR types, transform engine, orientation tests. No SolidWorks. No part files.

**Implementation requirements.**

- IR can represent grid identity, grid size, block subtype, block grid coordinate, forward, up, resolved geometry identity, canonical transform, and fields downstream backends need that remain CAD-neutral.
- IR contains no SolidWorks COM objects or API structures.
- Transform engine is a separate subsystem. It consumes parsed + catalog-resolved data and writes canonical transforms.
- Encode Space Engineers orientation semantics (Forward and Up) into a rotation consistent with the later library reference-frame contract. If the exact basis cannot be proven from existing evidence, stop and ask rather than guessing a convention that would silently misplace blocks.
- Asymmetric orientation tests: same subtype in several Forward/Up combinations; prove distinct transforms; catch axis swap and left/right reflection errors.
- Use the catalog cell-pitch constant; do not re-litigate 2500 mm.

**Explicit boundaries / out of scope.** SolidWorks insertion, mates, Blender, multi-grid, mechanical joints, part geometry construction.

**Development validation.** Unit tests for IR construction, pitch application, and a matrix of orientations for all four subtypes. Tests do not instantiate SolidWorks.

**Quality/security assessment focus.** Orientation edge cases; left-handed/right-handed confusion; nondeterministic matrix formatting; leaking backend types into IR.

**External validation.** None. Physical comparison against Space Engineers is deferred to S2C-6.1.1.

**Completion criteria.** IR and transform engine exist; orientation tests pass; IR remains CAD-neutral; STATE records any convention that had to be confirmed with the human architect.

---

## Milestone M4 — Canonical native armor block library

Native CAD geometry strategy for the four armor types, a reference-frame contract, and reusable canonical parts. No Blender.

### S2C-4.1.1 — Library contract, reference frames, and native armor recipes

**Objective.** Specify the block-library record, the canonical origin/reference-frame contract used by transforms, and native procedural geometry recipes for the four armor solids.

**Rationale.** Runtime conversion asks the library for a part and metadata. Recipes and frames must be explicit before SolidWorks part production.

**Prerequisites.** S2C-3.1.1.

**Affected systems / expected areas.** Library metadata model, reference-frame documentation or encoded contract, native geometry recipes testable without SolidWorks (analytic or mesh-free solid description). No Blender. No SDK meshes. No assembly backend.

**Implementation requirements.**

- Library record can express identity, grid size, geometry strategy, reference frame, and placement semantics needed to instantiate a part.
- The four armor types use `native_procedural` recipes (cube, slope, corner, inverse corner) whose dimensions match Large Grid pitch.
- Origin and axis contract is written so S2C-3.1.1 transforms and later SolidWorks insertion agree.
- Recipes are SE2CAD-authored constructive geometry, not imported Keen meshes.
- No Blender dependency.

**Explicit boundaries / out of scope.** Emitting SLDPRT, assembly generation, TriangleMesh strategies, SDK file location.

**Development validation.** Tests that recipes produce the expected solid topology/dimensions (for example vertex/face counts or constructive feature trees) and that reference-frame metadata is present for each of the four identities.

**Quality/security assessment focus.** Frame mismatch with the transform engine; embedding or reading game assets; treating recipes as redistributable Keen derivatives (they must remain native SE2CAD solids).

**External validation.** None.

**Completion criteria.** Contract and four recipes exist and are tested without SolidWorks; frames are consistent with S2C-3.1.1.

### S2C-4.2.1 — Produce reusable SolidWorks canonical parts

**Objective.** Produce one reusable SolidWorks part per supported armor geometry identity, using the native recipes and reference-frame contract, suitable for repeated assembly insertion.

**Rationale.** The converter instantiates canonical parts; it does not regenerate armor geometry per blueprint block.

**Prerequisites.** S2C-4.1.1.

**Affected systems / expected areas.** SolidWorks part-production path, part output location, library lookup from geometry identity to part path. No assembly of a ship. No Blender.

**Implementation requirements.**

- Create canonical SLDPRT (or equivalent SolidWorks part documents) for the four identities.
- Parts obey the reference-frame contract.
- Production is repeatable enough that a second run does not silently change the contract.
- Do not import Keen FBX/MWM. Do not use Blender.
- Record whether the resulting parts are SE2CAD-authored native solids (expected) and therefore eligible for the human architect to commit. Do not commit them in the agent session unless asked.

**Explicit boundaries / out of scope.** Assembly generation, mates, fixture conversion, TriangleMesh parts, publishing parts as a Keen-derived pack.

**Development validation.** Development evidence may include automation logs and mocked SolidWorks adapters. That is not SolidWorks application evidence.

**Quality/security assessment focus.** COM misuse; overwrite of unrelated documents; temp-file leakage; accidental commit of unrelated SolidWorks content; path injection.

**External validation.** A real SolidWorks session opens each of the four parts and confirms they match the native recipes (solid present, expected envelope, expected reference orientation). Required for QUALIFIED.

**Completion criteria.** Four canonical parts are produced by the library path; lookup by geometry identity works; DEV-COMPLETE may be recorded from development evidence; QUALIFIED only after the SolidWorks inspection above is evidenced in STATE.

---

## Milestone M5 — SolidWorks assembly backend

Automation boundary, direct component insertion, transform placement without mates, assembly save.

### S2C-5.1.1 — Transform-placed SolidWorks assembly generation

**Objective.** Given a canonical IR with transforms and a library of the four canonical parts, generate a SolidWorks assembly by inserting each component with its calculated transform and saving the assembly. Do not use mates to reconstruct fixed SE placement.

**Rationale.** Ships with hundreds or thousands of blocks must not create an equivalent mate network.

**Prerequisites.** S2C-3.1.1, S2C-4.2.1.

**Affected systems / expected areas.** SolidWorks backend boundary, assembly writer, tests with a mocked adapter plus (for QUALIFIED) a real assembly save. No print pipeline. No Blender.

**Implementation requirements.**

- Clear automation boundary: core IR/transform code does not import SolidWorks COM types.
- Insert components by transform; no SE-placement mate network.
- Save an assembly to a designated output path.
- Behavior is deterministic/re-runnable where feasible (same IR → same component count and transforms).
- Fail closed if a geometry identity has no library part.
- Do not write outside the designated output path.

**Explicit boundaries / out of scope.** Mate-based reconstruction, multi-grid, mechanical constraints, STL/3MF, in-place part editing of canonical library parts.

**Development validation.** Tests with a fake backend assert insertion count, part identities, transforms, no-mate policy, and path handling. These can support DEV-COMPLETE.

**Quality/security assessment focus.** COM misuse; arbitrary overwrite; command injection if any process wrapper exists; nondeterminism; coupling IR to COM; proprietary template leakage.

**External validation.** A real SolidWorks session generates and opens an assembly from a small IR (need not be the full qualification comparison). Required for QUALIFIED.

**Completion criteria.** Backend exists behind a boundary; mock tests pass; no mate network for SE placement; QUALIFIED only with evidenced SolidWorks generation.

---

## Milestone M6 — Four-block vertical qualification

End-to-end conversion of the permanent fixture and evidence that closes the initial program.

### S2C-6.1.1 — Qualify the four-block acceptance fixture

**Objective.** Convert the permanent asymmetric fixture end-to-end and demonstrate that the SolidWorks assembly matches the Space Engineers object in block count, position, and orientation, using the four canonical parts.

**Rationale.** This is the initial program end state.

**Prerequisites.** S2C-1.1.1, S2C-1.2.1, S2C-5.1.1 (and thus M2–M4).

**Affected systems / expected areas.** End-to-end wiring if not already composed, qualification record in STATE, any comparison tolerances documented beside the fixture spec. No new block types. No scope expansion.

**Implementation requirements.**

- Run fixture → parser → catalog → IR/transforms → library → SolidWorks assembly.
- Compare block count, positions, and orientations against fixture-derived expected values (and, where the human provides it, against observed Space Engineers structure).
- Record evidence: commands, outputs, comparison results, SolidWorks artifact identity.
- Use only the four supported subtypes. Fail closed if the fixture ever contains anything else.
- Close the initial program in STATE only if the end-state definition in [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md) is genuinely met.

**Explicit boundaries / out of scope.** New subtypes, Blender, printing, multi-grid, substituting unsupported blocks, declaring a follow-on program.

**Development validation.** Automated comparison of IR transforms to expected fixture-derived values. That alone is not QUALIFIED.

**Quality/security assessment focus.** False QUALIFIED claims; loosened tolerances that hide orientation bugs; leftover proprietary outputs committed; silent skipping of blocks to make counts match.

**External validation.** SolidWorks artifact inspected; positions/orientations compared to the fixture and to the intended SE object as defined in [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md). Required for QUALIFIED and for program close.

**Completion criteria.** Evidence recorded in STATE; mismatches explained or fixed; program marked complete in STATE only when the end state is met. DEV-COMPLETE is allowed if conversion wiring and automated IR comparison pass but SolidWorks/SE comparison is still outstanding.
