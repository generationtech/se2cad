# SE2CAD plan M7–M15

Responsibility: what bounded units constitute the current approved program. This file carries no live status. Do not select work from this file.

Live status and the next executable unit: [SE2CAD_STATE.md](SE2CAD_STATE.md).
Program objective and exclusions: [SE2CAD_PROGRAM_M7.md](SE2CAD_PROGRAM_M7.md).
How to execute a unit: [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md).
Historical initial units (complete): [SE2CAD_PLAN.md](SE2CAD_PLAN.md).

Unit IDs use `S2C-<milestone>.<workstream>.<sequence>`.

Program authorization for M7–M15 is a completed documentation/governance action recorded in STATE. It is not a product milestone and is not an executable implementation unit.

Do not add milestones, work units, or cold-storage backlog items while executing a unit. Do not combine two of the nine approved features into one unit.

A listed prerequisite is met at DEV-COMPLETE unless the later unit consumes that unit’s QUALIFIED artifact or evidence. STATE names the next executable unit.

---

## Milestone M7 — Blueprint statistics

**Objective.** Produce useful blueprint and conversion statistics from data SE2CAD already parses and resolves.

**Completion outcome.** A CAD-neutral statistics result for a supported blueprint reports identity, grid type, counts, extents, dimensions, occupancy/coverage, and catalog/IR coverage that can be derived from the parser, catalog, and IR. No UI.

### S2C-7.1.1 — Blueprint and conversion statistics

**Objective.** Compute a structured, deterministic statistics result from a parsed blueprint plus catalog resolution and/or canonical IR.

**Rationale.** Operators and later milestones need a trustworthy summary of what a blueprint contains and how far the current converter can take it, without opening SolidWorks or inventing a UI.

**Prerequisites.** Initial program complete (S2C-6.1.1).

**Affected systems / expected areas.** A CAD-neutral statistics module; tests using the qualified acceptance fixture and synthetic blueprints; package exports as needed. No SolidWorks. No catalog identity redesign.

**Implementation requirements.**

- Derive statistics from existing parser, catalog, and IR fields wherever possible. Do not invent a second identity system.
- Include at least: blueprint/grid identity; grid size; block count; per-subtype and per-geometry-id counts; cell-axis extents and millimetre dimensions using the catalog pitch constant(s); occupancy or bounding-box coverage that can be computed from unique `Min` cells; orientation histogram; catalog resolution coverage for the blocks present.
- Fail closed on the same unsupported document shapes the parser already rejects. Do not silently drop blocks to make counts look complete.
- Keep the result CAD-neutral and deterministic.
- A narrow operator entry in the existing `python -m se2cad…` style is allowed if useful. Do not create a general CLI or UI.

**Explicit boundaries / out of scope.** GUI; preflight/strict/permissive conversion policy (M12); color, Small Grid, unknown-block filler, symmetry, print-shell, or library expansion.

**Development validation.** Tests prove fixture-derived counts, extents, and coverage against known S2C-1.1.1 / S2C-1.2.1 / S2C-3.1.1 values. Synthetic cases cover empty-illegal (already rejected), single-cell, negative coordinates, and mixed orientations. Tests do not instantiate SolidWorks.

**Quality/security assessment focus.** Untrusted blueprint paths; leaking absolute paths or secrets in messages; invented identities; silently omitting unresolvable blocks; scattering pitch literals.

**External validation.** None.

**Completion criteria.** Statistics module and tests exist; acceptance-fixture numbers match the qualified parser/catalog/IR record; STATE records evidence. QUALIFIED from automated tests.

---

## Milestone M8 — CAD component naming from SE data

**Objective.** Give each SolidWorks assembly component a deterministic, readable name derived from Space Engineers identity already present in the IR.

**Completion outcome.** Generated assemblies name components from SE subtype, location, and orientation (and uniqueness data already on the IR) without creating a second identity system.

### S2C-8.1.1 — Deterministic component names from IR

**Objective.** Define a CAD-neutral component-name function from existing IR fields and apply those names when inserting SolidWorks assembly components.

**Rationale.** Identity, subtype, coordinates, and orientation already flow through the pipeline. Default SolidWorks instance names do not preserve that meaning in large assemblies.

**Prerequisites.** S2C-7.1.1 (program sequence). Technical: S2C-5.1.1 / S2C-6.1.1 assembly path.

**Affected systems / expected areas.** CAD-neutral name helper; assembly placement/insertion; ordinary and live SolidWorks tests. Do not change the qualified `(R, t)` contract.

**Implementation requirements.**

- Names are deterministic, human-readable, and unique within one assembly.
- Source data is existing IR/parser identity: subtype, `Min`, Forward/Up as needed, and `source_index` or equivalent already-stored uniqueness. Do not introduce a parallel ID scheme that conflicts with `subtype_id` / `geometry_id`.
- Account for large assemblies and SolidWorks identifier constraints. If a full encoding exceeds a documented backend limit, use a specified truncation-plus-unique-suffix rule that remains traceable to the IR block.
- Apply the name at component insertion. Placement transforms, part files, and mate policy stay unchanged.
- Existing acceptance-fixture transform qualification must keep passing.

**Explicit boundaries / out of scope.** Color; renaming canonical `.SLDPRT` geometry identities; a new catalog key; UI.

**Development validation.** Unit tests of the name function: uniqueness, stability, collision of same subtype at different cells, omitted vs explicit orientation, unsafe-character rejection. Mock or hermetic assembly tests assert the chosen name is the name requested for insertion.

**Quality/security assessment focus.** Path/identifier injection via subtype strings; collisions in large grids; changing transforms while renaming; leaking machine paths into names.

**External validation.** Live SolidWorks integration must show that saved/reopened component names match the IR-derived names for the acceptance fixture (or an equivalent small IR). Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED.

**Completion criteria.** Name contract tested without SolidWorks; assembly writer applies it; DEV-COMPLETE from ordinary tests; QUALIFIED after live rename/reopen evidence in STATE.

---

## Milestone M9 — Blueprint block-color preservation

**Objective.** Parse per-block color, carry it as instance appearance through the IR, and assign a SolidWorks component appearance without baking color into reusable geometry.

**Completion outcome.** Geometry support and appearance support are independently reportable. Canonical parts stay uncolored library solids; instances receive converted appearance.

### S2C-9.1.1 — Parse color and carry CAD-neutral appearance

**Objective.** Read the blueprint color value, establish omitted-field semantics from evidence, and store a CAD-neutral appearance on the parsed representation and IR.

**Rationale.** Color is per-instance Space Engineers data. Downstream CAD can apply it only if the core carries it without SolidWorks types.

**Prerequisites.** S2C-8.1.1 (program sequence).

**Affected systems / expected areas.** Parser model, parser, IR, convert path, tests (synthetic XML plus omitted-color fixture behavior). No SolidWorks appearance calls.

**Implementation requirements.**

- Establish the on-disk color field and omitted default from local Space Engineers evidence and corroborating published sources before implementing, using the same standard as S2C-1.2.1 omitted `Min` / `BlockOrientation`. If the convention cannot be proven, stop and ask.
- Carry appearance semantically. Do not encode it as a geometry_id, recipe change, or catalog identity.
- Geometry support and appearance support must be independently reportable (a block may have supported geometry and default/unknown appearance, or the reverse once those states exist).
- Fail closed on malformed color payloads. Do not silently invent a color that the document did not specify, except the evidenced omitted default.
- The qualified acceptance fixture has no serialized color; omitted/default must not break current fixture tests.

**Explicit boundaries / out of scope.** SolidWorks appearance assignment (S2C-9.2.1); baking color into `.SLDPRT`; UI; treating color as a second block type.

**Development validation.** Tests for omitted default, explicit values, malformed values, and independence from subtype/geometry identity. Fixture parse/IR still match S2C-1.2.1 / S2C-3.1.1 identities and transforms.

**Quality/security assessment focus.** Untrusted numeric/XML color fields; collapsing appearance into geometry identity; changing omitted `Min`/orientation defaults while adding color.

**External validation.** None.

**Completion criteria.** Parser and IR carry appearance; tests prove omitted and explicit cases; STATE records the evidenced omitted-color mapping. QUALIFIED from automated tests.

### S2C-9.2.1 — Per-instance SolidWorks component appearance

**Objective.** Convert the IR appearance to an appropriate SolidWorks component appearance and assign it at assembly insertion without modifying reusable canonical parts.

**Rationale.** Appearance is an instance property. Library geometry must remain reusable across colors.

**Prerequisites.** S2C-9.1.1.

**Affected systems / expected areas.** CAD-neutral appearance conversion; SolidWorks assembly insertion; ordinary and live tests. Canonical part generation stays color-agnostic.

**Implementation requirements.**

- Convert the semantic appearance to the backend representation inside the SolidWorks package, not in parser/catalog/IR.
- Assign appearance on the inserted component (or equivalent instance override). Do not author color into canonical `.SLDPRT` files.
- Two instances of the same `geometry_id` with different colors must remain the same part file and different appearances.
- Missing or default appearance must not fail conversion of the qualified fixture.
- Independently report whether geometry and appearance were applied.

**Explicit boundaries / out of scope.** Material libraries as a product; painting library parts; print-shell coloring; changing transforms or names except as required to attach appearance.

**Development validation.** Ordinary tests assert conversion math and that part-generation plans remain color-free. Hermetic tests assert the assembly writer is asked to apply per-instance appearance.

**Quality/security assessment focus.** Baking color into shared parts; COM misuse; appearance applied in a second frame; silent drop of color.

**External validation.** Live SolidWorks integration reads instance appearance (programmatic material/color/appearance query) for at least two colors plus a default, without a change to canonical part files. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED.

**Completion criteria.** Instance appearance applied; parts remain reusable; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE.

---

## Milestone M10 — Printable block-edge definition

**Objective.** Provide an optional geometry treatment that defines printable block edges without disturbing the qualified reference frame or placement dimensions.

**Completion outcome.** When requested, generated solids include a defined edge treatment applicable beyond the four proof-of-concept recipes, and explicit blueprint assembly generation consumes size-specific treated sibling artifacts on demand. Untreated conversion remains the default and stays dimensionally correct.

### S2C-10.1.1 — Optional block-edge treatment contract

**Objective.** Specify optional block-edge definition as a geometry treatment with a measurable contract, written for solids generally rather than for four named armor IDs.

**Rationale.** Edge definition is conceptually simple; applying it reliably to arbitrary later geometry requires a solid-oriented contract now.

**Prerequisites.** S2C-9.2.1 (program sequence). Technical: S2C-4.1.1 recipes and S2C-3.1.1 frame.

**Affected systems / expected areas.** Library/geometry contract; CAD-neutral treatment description testable on native-procedural solids. No requirement to finish SolidWorks generation here.

**Implementation requirements.**

- Treat edge definition as optional. Default conversion remains untreated (qualified M0–M6 path unchanged).
- Preserve the canonical local frame, cell envelope used for placement, and millimetre pitch. Do not add a second insert offset.
- Define measurable properties (for example: treatment present when requested, envelope relationship, volume change bounds, untreated identity unchanged).
- Express the treatment as an operation on solid/edge geometry so later imported or complex parts can use the same contract. Do not hard-code the four initial `geometry_id` values as the only applicable set.
- Do not bake the treatment into reusable library identity as if it were a new subtype.

**Explicit boundaries / out of scope.** SolidWorks materialization of treated parts (S2C-10.2.1); print-shell (M15); slicer export; requiring a physical print to judge usefulness.

**Development validation.** Tests on native-procedural recipes (and at least one non-ID-specific solid description) prove optional on/off, frame/envelope invariants, and that applicability is not a four-ID allowlist.

**Quality/security assessment focus.** Silent default-on that breaks the acceptance fixture; frame drift; treating the feature as a new block type; Keen-mesh import.

**External validation.** None.

**Completion criteria.** Contract and CAD-neutral tests exist; untreated default preserved. QUALIFIED from automated tests.

### S2C-10.2.1 — Generate optional treated canonical parts

**Objective.** Apply the S2C-10.1.1 treatment in SolidWorks part generation when requested, without changing untreated canonical parts or placement.

**Rationale.** The library path must actually produce treated solids for the current native recipes while leaving the untreated artifacts the acceptance fixture uses.

**Prerequisites.** S2C-10.1.1.

**Affected systems / expected areas.** SolidWorks part-generation path; artifact naming/containment for optional treated outputs; ordinary and live tests.

**Implementation requirements.**

- Produce treated parts only when the optional treatment is requested.
- Untreated `large_armor_*.SLDPRT` (and their lookup) remain the default conversion parts.
- If treated artifacts need distinct filenames, they must stay under the generated root, remain deterministic, and must not overwrite untreated canonical parts.
- Placement still uses the qualified `(R, t)` and untreated reference frame.
- Mechanism (feature on a configuration, sibling artifact, or other in-boundary approach) must not require a new CAD backend or remoting. If choosing among those options is a significant architectural tradeoff, stop and ask.

**Explicit boundaries / out of scope.** Blueprint assembly consumption of treated siblings (S2C-10.3.1); physical print judgment; TriangleMesh implementation; changing M9 appearance rules; print-shell.

**Development validation.** Ordinary tests assert untreated default paths are unchanged and treated generation is requested only when enabled.

**Quality/security assessment focus.** Overwriting untreated parts; writes outside the generated root; COM misuse; accidental commit of CAD.

**External validation.** Live SolidWorks integration generates treated and untreated parts, validates one solid body, and checks the S2C-10.1.1 measurable properties. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED.

**Completion criteria.** Optional treated parts generate; untreated default and placement remain qualified; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE.

### S2C-10.3.1 — Assemble using optional treated parts

**Objective.** When explicitly requested, blueprint assembly generation resolves and inserts treated sibling parts without changing default untreated assembly behavior, catalog or IR identity, or placement.

**Rationale.** S2C-10.2.1 produces treated sibling artifacts. Default assembly still inserts untreated `{geometry_id}.SLDPRT`. This unit closes that consumption gap.

**Prerequisites.** S2C-10.2.1. This unit was inserted by a human-authorized amendment after S2C-11.1.1 was already QUALIFIED. It does not reopen or invalidate S2C-11.1.1.

**Affected systems / expected areas.** SolidWorks assembly part resolution, assemble operator entry, ordinary and live tests. Do not change parser, catalog, IR, recipes, or the qualified `(R, t)` contract.

**Implementation requirements.**

- Default assembly remains untreated: `python -m se2cad.solidworks.assemble <blueprint.sbc>` continues resolving `{geometry_id}.SLDPRT`.
- Add explicit treated assembly selection, preferably `python -m se2cad.solidworks.assemble <blueprint.sbc> --edge-treatment chamfer`, matching the existing part-generation spelling unless that entry’s structure requires an equivalent compatible form.
- Explicit chamfer assembly resolves `{geometry_id}_chamfer.SLDPRT`.
- Do not create a new `geometry_id` or subtype; do not change catalog or IR identity; do not change parsing; do not change qualified `(R, t)`; do not introduce placement corrections; do not overwrite untreated parts; do not silently fall back to untreated parts.
- If explicitly requested treated artifacts are missing, fail closed with useful diagnostics.
- Existing deterministic component naming and per-instance appearance must continue to operate.
- `_chamfer` is an artifact treatment, not part of the Space Engineers block’s semantic identity.
- Protect default untreated assembly behavior with regression tests.

**Explicit boundaries / out of scope.** Catalog identity expansion (S2C-11.2.1); recipe selection; print-shell; changing untreated generation; physical print; a general CLI or UI.

**Development validation.** Ordinary tests prove default assemble still names untreated `{geometry_id}.SLDPRT`, explicit chamfer selection names treated siblings, and missing treated artifacts fail closed. IR transforms, component-name requests, and appearance requests remain unchanged.

**Quality/security assessment focus.** Silent fallback to untreated parts; overwrite of untreated artifacts; baking `_chamfer` into catalog/IR identity; path escape; changing transforms or adding mates.

**External validation.** Ordinary tests plus the existing live SolidWorks integration path (`SE2CAD_SOLIDWORKS_INTEGRATION`). Establish, as applicable: untreated selection still resolves untreated parts; explicit chamfer selection resolves treated siblings; expected component count; unchanged IR transforms; deterministic names; per-instance appearance; save/close/reopen persistence; no unexpected mates or placement corrections; untreated artifacts are not modified. Add no named opscheck unless an important requirement cannot be established that way. Required for QUALIFIED.

**Completion criteria.** Explicit treated assembly consumes treated siblings; default untreated assembly remains qualified; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE.

### S2C-10.4.1 — Configurable, demand-driven chamfer variants

**Objective.** Make the already-qualified chamfer treatment configurable by size, name treated artifacts for that size, generate those variants only when a blueprint demands them, and fall back to untreated parts when a geometry is not chamfer-capable.

**Rationale.** S2C-10.2.1 / S2C-10.3.1 used a single implicit 50 mm sibling name and expected treated parts to exist before assemble. Operators need other sizes, lazy generation, and an explicit capability decision that does not treat every supported geometry as chamferable.

**Prerequisites.** S2C-10.3.1. This unit was inserted by a human-authorized amendment after S2C-12.2.1 was already QUALIFIED and before S2C-13.1.1. It does not reopen or invalidate S2C-10.3.1, M11, or M12. It was not part of the original M10 plan.

**Affected systems / expected areas.** Edge-treatment request/size validation; treated artifact naming; library chamfer capability; assemble demand generation and fallback reporting; narrow explicit part-generation entry; ordinary and live tests.

**Implementation requirements.**

- Support `python -m se2cad.solidworks.assemble <blueprint.sbc> --edge-treatment chamfer --chamfer-mm <value>`.
- Existing 50 mm behavior remains the default when chamfer is requested without an explicit size.
- Validate `5 mm <= chamfer_mm <= 250 mm`. Reject values outside the range and non-finite values. Do not silently clamp.
- `--chamfer-mm` is valid only with `--edge-treatment chamfer`. Untreated/default assembly remains unchanged.
- Treated artifact identity includes the chamfer size, for example `large_armor_block_chamfer_50mm.SLDPRT`. Use one deterministic shared naming/key function for generation and lookup.
- Do not put the chamfer suffix or size into the SolidWorks component instance name.
- Do not add treatment algorithm/version suffixes. If the chamfer implementation changes later, old generated variants are deleted and regenerated.
- Do not eagerly generate chamfer variants for the entire library. Assembly generates only the exact size-specific part a blueprint needs, reusing it when present.
- Introduce an explicit CAD/library chamfer-capability decision, separate from catalog `support_status`, recipe kind, and SE subtype identity. Qualified Box / Slope / Corner / InvCorner constructions remain chamfer-capable. Future imported/mesh-derived/hand-authored geometry must not inherit capability automatically.
- If chamfer is requested and a geometry is not chamfer-capable, use the untreated part, report the fallback, and do not claim the assembly was fully treated.
- Fail closed for invalid size, generation failure of a chamfer-capable geometry, inability to open/save the exact treated artifact, path ambiguity, and other existing SolidWorks generation failures. Do not fall back to another size, the generic `*_chamfer.SLDPRT` name, or untreated geometry when the geometry was declared chamfer-capable.
- Keep `python -m se2cad.solidworks --edge-treatment chamfer` narrow: the qualified/tested set only. Blueprint assembly is the primary demand-driven producer.

**Explicit boundaries / out of scope.** Blueprint parser semantics; catalog identity; IR transforms; component naming rules; appearance; unknown-block policy; filler semantics; M11 recipe selection; Small Grid; symmetry; print-shell; runtime game/SDK scanning; OBJ import; new geometry recipes; algorithm-version compatibility; committing generated CAD.

**Development validation.** Ordinary tests cover default 50 mm, at least one alternate valid size, range boundaries, invalid/NaN/Inf rejection, `--chamfer-mm` without chamfer rejected, size-specific naming, reuse of the same geometry+size, distinct artifacts for distinct sizes, demand generation of only required parts, unchanged untreated assembly, fail-closed capable generation failure, untreated fallback for non-capable geometry with a structured report, component names without chamfer suffixes, IR-tied transforms/appearance, no path escape, and no eager all-library generation.

**Quality/security assessment focus.** Filename collisions between sizes; stale generic `*_chamfer.SLDPRT` reuse; path injection via artifact identity; silent fallback on true generation failure; accidental eager catalog generation; treatment capability granting catalog support; component-name contamination; untreated source-part modification; writes escaping the generated root.

**External validation.** Ordinary tests plus the existing live SolidWorks integration path (`SE2CAD_SOLIDWORKS_INTEGRATION`). Establish: two distinct chamfer sizes produce distinct `.SLDPRT` artifacts; an assembly requesting one size consumes those exact parts; a later request reuses already-created treated parts; untreated base `.SLDPRT` files remain unchanged; default untreated assembly still consumes untreated parts; at least one intentional non-chamfer-capable probe falls back and is reported if that can be done safely with existing test architecture; document-count/session hygiene remains acceptable. If a safe live unsupported-chamfer probe would require inventing unrelated production geometry, prove that subcase in ordinary tests and record why live evidence was not appropriate. Required for QUALIFIED.

**Completion criteria.** Configurable demand-driven chamfer variants exist; untreated default remains qualified; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE.

---

## Milestone M11 — SDK-driven vanilla block library expansion

**Objective.** Expand the vanilla Large Grid block library using operator-local SDK/game definition evidence and automation for the easy majority, plus a durable exception/long-tail workflow.

**Completion outcome.** Discovery, identity resolution, provenance, recipe selection, generation/validation, and exception handling exist. Automatable vanilla Large Grid blocks can be cataloged and generated without becoming a runtime SE/SDK dependency. Unusual blocks are explicit exceptions, not silent support. ADR-004 remains binding.

This milestone is expected to need more units than the others. It does not require every vanilla block to use the same geometry technique, and it does not require 100% vanilla coverage.

### S2C-11.1.1 — Operator-local definition discovery

**Objective.** Discover vanilla cube-block definitions from an operator-configured local Space Engineers and/or ModSDK tree, without making that tree a runtime conversion dependency.

**Rationale.** Catalog growth needs current identity and definition facts. Those facts live in an operator-owned install that must not be committed.

**Prerequisites.** S2C-10.2.1 (program sequence).

**Affected systems / expected areas.** Library-build discovery (not the runtime converter); local-path configuration following the existing env / uncommitted `se2cad.local.json` pattern unless the human architect records a different choice; tests with synthetic definition trees. No packaged game assets.

**Implementation requirements.**

- If install-path configuration is still an open human decision, reuse the established local-config pattern or stop and ask. Do not invent remoting, scanning of arbitrary disks, or a runtime game dependency on the conversion path.
- Read operator-supplied paths only after validation/normalization. Treat definition XML as untrusted.
- Extract identity and observed definition facts needed for catalog authoring (subtype, type, cube size, occupancy, topology tokens, and other definition fields the catalog already models). Do not copy meshes, FBX, MWM, or textures into the repository.
- Discovery is a library-build/evidence tool. `parse_blueprint` / `build_canonical_blueprint` / assembly generation must still run from packaged catalog + `bp.sbc` alone.
- Small Grid identities may be recorded as observed facts. Do not implement Small Grid conversion here (M13).

**Explicit boundaries / out of scope.** Committing Keen assets; generating parts; changing runtime lookup to scan an install; TriangleMesh construction; Small Grid conversion.

**Development validation.** Tests use SE2CAD-authored synthetic definition files. Path escape, missing root, and malformed definition XML fail closed. Ordinary tests do not require a real game install.

**Quality/security assessment focus.** Path traversal; committing proprietary files; XXE in definition XML; making conversion require Steam/SDK; machine paths in packaged catalog.

**External validation.** None required for QUALIFIED. An operator-local discovery run may be recorded in STATE as additional evidence; it is not a named opscheck.

**Completion criteria.** Discovery module exists; synthetic tests pass; runtime conversion remains install-free. QUALIFIED from automated tests.

### S2C-11.2.1 — Catalog identity expansion

**Objective.** Grow the repository-resident catalog with vanilla Large Grid identities resolved from discovery evidence, keeping observed facts distinct from SE2CAD decisions.

**Rationale.** Runtime conversion must keep using packaged catalog data, not a live game scan.

**Prerequisites.** S2C-11.1.1. Sequencing: execute only after S2C-10.3.1 is QUALIFIED (human-authorized M10 insertion after M11 had started).

**Affected systems / expected areas.** Catalog schema/loader as needed; packaged catalog data; tests. Schema version must change if new fields are added; unknown fields remain rejected.

**Implementation requirements.**

- Add catalog entries for vanilla Large Grid identities that this unit is prepared to record. Distinct subtypes keep distinct `geometry_id` values.
- Preserve `observed` vs `se2cad` separation. `support_status` and `recipe_kind` remain explicit.
- Do not store machine paths or proprietary asset references in packaged catalog JSON.
- Runtime lookup stays exact, case-sensitive, and install-free.
- Do not silently mark a block `supported` without a recorded recipe decision (S2C-11.3.1 may still be `unsupported` / pending).

**Explicit boundaries / out of scope.** Geometry generation; recipe-selection policy completion for the long tail; Small Grid activation; permissive filler (M12).

**Development validation.** Loader tests for new/updated schema; duplicate identity rejection; neutrality (no `/home/`, `C:\`, `.mwm`, `.fbx` in packaged data); conversion of the original four subtypes unchanged.

**Quality/security assessment focus.** Asset-path smuggling; duplicate geometry IDs; schema drift accepted silently; support claimed without recipes.

**External validation.** None.

**Completion criteria.** Packaged catalog can represent the expanded identity set; original four entries remain correct; tests pass. QUALIFIED from automated tests.

### S2C-11.3.1 — Geometry provenance and recipe selection

**Objective.** Record geometry provenance and select a recipe kind per expanded identity: automation for the easy majority, explicit exceptions for the long tail.

**Rationale.** Not every vanilla block should use the same production technique. Provenance and exceptions must be durable before mass generation.

**Prerequisites.** S2C-11.2.1.

**Affected systems / expected areas.** Library-build metadata / exception records; recipe-kind assignment; tests. No committing of extracted meshes.

**Implementation requirements.**

- Classify identities into the existing strategy vocabulary (`native_procedural`, `sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, `unsupported`) from evidence, not convenience.
- Record provenance at the metadata level (what was observed, what SE2CAD decided). Do not embed game/SDK geometry in the repo.
- Define a durable exception/long-tail record: why a block is not in the automatable set, and that it must not be reported as supported.
- CubeTopology-class armor is the expected automatable majority. TriangleMesh and unusual relationships are expected long-tail. Do not implement a full TriangleMesh pipeline here.
- If a classification would require redistributing Keen-derived CAD, stop and ask ([ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md)).

**Explicit boundaries / out of scope.** Generating the entire vanilla set; Blender; runtime SDK; claiming general TriangleMesh support.

**Development validation.** Tests prove every catalogued expanded identity has an explicit recipe kind and support status; exception records are queryable; no implicit default-to-supported.

**Quality/security assessment focus.** Silent support; provenance gaps; treating SDK paths as redistributable; collapsing geometry classes.

**External validation.** None.

**Completion criteria.** Selection/exception model exists; automatable vs long-tail is explicit. QUALIFIED from automated tests.

### S2C-11.4.1 — Automated generation for the automatable majority

**Objective.** Implement automated canonical-part generation for identities classified as automatable, and prove it on a representative set larger than the original four.

**Rationale.** One session cannot author every vanilla part by hand. The machine that covers the easy majority must exist and be evidenced.

**Prerequisites.** S2C-11.3.1, S2C-4.2.1.

**Affected systems / expected areas.** Library recipes / library-build generation; SolidWorks generation reuse; artifact containment; tests. Generated parts stay local cache.

**Implementation requirements.**

- Automate generation for the classified automatable class. Do not assume one construction technique for every remaining vanilla block.
- Prove the path on a defined representative subset beyond the original four (the unit records which identities).
- Reuse the qualified canonical frame and Windows-local COM backend. Do not add remoting or Blender on the runtime path.
- Validate generated parts with the existing solid-body / envelope / fail-closed rules as applicable.
- Runtime conversion still must not require SE/SDK.

**Explicit boundaries / out of scope.** Resolving the entire long tail; committing `.SLDPRT`; publication of Keen-derived parts.

**Development validation.** Ordinary tests cover recipe/plan construction and fail-closed paths without SolidWorks.

**Quality/security assessment focus.** Overwrite of unrelated files; generated-root escape; COM misuse; runtime SDK coupling; proprietary files added to git.

**External validation.** Live SolidWorks integration generates and revalidates the representative automatable subset. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED.

**Completion criteria.** Automation exists; representative subset generated and validated; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE.

### S2C-11.5.1 — Long-tail exceptions and expansion regression

**Objective.** Finish the milestone’s durable exception workflow and regression so expansion cannot silently misrepresent support or reintroduce an SDK runtime dependency.

**Rationale.** The long tail is where unusual blocks, asset relationships, and validation failures accumulate. That workflow must outlive one generation run.

**Prerequisites.** S2C-11.4.1.

**Affected systems / expected areas.** Exception workflow; catalog/library consistency tests; conversion regression (four-block fixture and expanded identities); documentation of the leftover set.

**Implementation requirements.**

- Exception handling is explicit: failed generation, unclassified blocks, and unsupported recipe kinds cannot appear as successful supported conversion.
- Record the leftover/long-tail set in repository-owned metadata (not chat).
- Add regression that: the original four-block fixture still converts; runtime modules do not open a game/SDK install; packaged catalog still forbids asset paths.
- Apply automation across the remainder of the classified automatable set as far as one bounded session can complete with evidence. Residual automatable items stay listed, not silently dropped.
- Do not claim 100% vanilla coverage.

**Explicit boundaries / out of scope.** M12 preflight/filler policy; Small Grid conversion; print-shell; committing leftovers as fake support.

**Development validation.** Tests for exception states, support-status honesty, fixture regression, and install-free imports.

**Quality/security assessment focus.** Silent skip; support/status drift; asset leakage; conversion requiring SDK.

**External validation.** None beyond any live generation already required by S2C-11.4.1, unless this unit itself generates additional parts. If it does, use `SE2CAD_SOLIDWORKS_INTEGRATION` for those parts before QUALIFIED.

**Completion criteria.** Exception workflow and regression exist; leftover set recorded; STATE does not claim universal vanilla support. QUALIFIED when the unit’s named evidence is recorded.

### S2C-11.6.1 — Demand-driven qualified base-part materialization

**Objective.** Make untreated canonical SolidWorks parts lazy, demand-driven artifacts for already-qualified library constructions, in the same spirit as the qualified chamfer cache.

**Rationale.** A read-only survey of a copied Space Engineers installation observed 1465 unique vanilla SubtypeIds (903 Large Grid, 562 Small Grid). The packaged catalog currently contains eight identities, and only those eight are presently safe to materialize with qualified constructions. Three apparent additional Slope/Corner/InvCorner candidates are hidden round-armor aliases and must not be auto-bound to the planar recipes. 64 Large Grid CubeTopology identities are automatable-in-principle but lack qualified constructions; the majority of the Large Grid remainder is TriangleMesh / long-tail. Existing assemble can lazily generate chamfer siblings, but a missing untreated base `.SLDPRT` still fails closed. Assembly should not require a prior bulk generation step for the already-qualified set, and runtime conversion must not scan the game or SDK install.

**Prerequisites.** S2C-11.5.1 and S2C-10.4.1. This unit was inserted by a human-authorized sequencing amendment after S2C-12.2.1 and S2C-10.4.1 were already QUALIFIED and after Small Grid was deliberately postponed. It does not rewrite original M11 history, does not reopen M12 policy semantics, and does not start S2C-13.1.1.

**Affected systems / expected areas.** Narrow shared untreated-part materialization used by assembly; assembly/materialization reporting; ordinary and live tests; operator assemble reporting. Explicit part-generation utility remains.

**Implementation requirements.**

- When assembly needs a supported, library-bound `geometry_id`, resolve the exact untreated canonical path `{geometry_id}.SLDPRT`.
- Reuse that artifact when it exists. If it is missing and the geometry has an already-qualified library construction, generate only that required untreated canonical part, save it under the normal generated root, and continue assembly.
- If the geometry does not have an already-qualified builder, do not improvise, do not derive a new recipe, do not scan SE definitions or SDK assets, and leave handling to existing strict/permissive policy.
- Repeated instances of the same `geometry_id` during one assembly generate at most once. Later assemblies reuse the previously generated base part.
- Scope is the currently library-bound qualified records, including the original and heavy armor families already supported. The designated filler may be generated lazily when permissive assembly actually requires it and its qualified native builder exists.
- Prefer reusing existing qualified generation functions. The mechanism must be callable by assembly without invoking broad “generate all parts” behavior and without shelling out to the CLI.
- Chamfer assembly first ensures the untreated base exists (reuse or lazy generate), then ensures the exact size-specific `{geometry_id}_chamfer_{size}mm.SLDPRT` sibling. Do not regenerate untreated parts merely because a chamfer sibling is requested. Do not reintroduce `*_chamfer.SLDPRT`. Untreated assembly does not generate chamfer siblings.
- Fail closed for true materialization errors, including a claimed qualified builder whose generation fails, a missing usable `.SLDPRT`, a wrong artifact path, SolidWorks open/save failure, generated-root escape, and filename/path ambiguity. Do not silently use the filler when a supported geometry with a qualified builder fails to generate.
- Preserve the existing explicit generation capability for the current qualified set. Do not create a “generate thousands of vanilla parts” workflow.
- Extend existing assembly/result reporting narrowly enough that an operator can tell unused reuse from on-demand untreated generation, and can still see chamfer reuse/generation and existing policy substitution.

**Explicit boundaries / out of scope.** Expanding the packaged catalog; stamping automatable remainder; promoting new identities to supported; adding CubeTopology constructions; binding hidden `LargeRoundArmor_*` aliases; importing FBX/MWM/OBJ; inspecting Model/Sides at runtime; changing catalog `support_status`, `geometry_id`, IR, transforms, component naming, appearance, chamfer capability, strict/permissive policy, or filler identity; Small Grid; symmetry; print-shell; inventing S2C-11.7.1 or later units.

**Development validation.** Ordinary tests cover: missing supported untreated part generated on demand; existing supported untreated part reused; same `geometry_id` generated once; only required supported IDs generated; unrelated library parts not eagerly generated; second assembly reuses generated bases; qualified-builder generation failure fails closed; unsupported/unknown permissive still uses filler; unsupported/unknown strict still refuses; no catalog support expansion; no runtime `stamp_automatable_remainder`; hidden round aliases are not treated as qualified planar geometry; component names, transforms, and appearance unchanged; generated-root containment enforced; chamfer can bootstrap missing base then size-specific sibling; untreated assembly does not generate chamfer siblings; default explicit part-generation utility remains intact.

**Quality/security assessment focus.** Eager generation of unrelated library parts; duplicate generation within one assembly; wrong `geometry_id` → filename resolution; generated-root path escape; silent fallback after supported generation failure; accidental mutation of catalog support decisions; runtime dependency on SE/SDK install; hidden `LargeRoundArmor_*` planar misclassification; untreated-part overwrite when reuse should occur; chamfer/base dependency ordering errors; filler accidentally entering the normal supported library.

**External validation.** Ordinary tests plus the existing live SolidWorks integration path (`SE2CAD_SOLIDWORKS_INTEGRATION`). Establish: a known qualified untreated `.SLDPRT` absent from a controlled generated root is created on demand and consumed; a later assemble reuses that artifact; a blueprint requiring more than one supported `geometry_id` produces only the needed base parts; permissive filler still reaches a complete assembly when an unsupported/unknown block is present; if practical, chamfer assembly bootstraps missing untreated base → treated sibling → assembly; operator documents are not closed; SolidWorks `RevisionNumber` and document count are recorded before/after. Required for QUALIFIED.

**Completion criteria.** Demand-driven qualified base-part materialization exists; explicit bulk generation of the current qualified set remains; no claim of universal vanilla support; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE. After qualification, stop and report. Do not automatically restore or start S2C-13.1.1.

### S2C-11.7.1 — Single-identity SDK-FBX materialization experiment

**Objective.** Bind exactly `LargeBlockSmallHydrogenThrust` to one authorized `sdk_mesh_direct` recipe and generate a reusable canonical `{geometry_id}.SLDPRT` from the official ModSDK FBX on demand.

**Rationale.** Big Red demand analysis showed sixteen `LargeBlockSmallHydrogenThrust` instances becoming filler. This unit proves one complete SDK-FBX builder path without generalizing TriangleMesh support.

**Prerequisites.** S2C-11.6.1 and S2C-12.4.1. This unit was inserted by a human-authorized experiment after S2C-12.4.1 was QUALIFIED and after the human postponed Small Grid. It does not rewrite original M11 history, does not start S2C-13.1.1, and does not invent S2C-11.8.x.

**Affected systems / expected areas.** One packaged catalog entry; one `SdkMeshRecipe` library bind; a narrow selection/leftover exception; demand-driven SolidWorks generation that resolves one operator-local FBX; ordinary and live tests.

**Implementation requirements.**

- Bind only `LargeBlockSmallHydrogenThrust` → `large_block_small_hydrogen_thrust`.
- Preserve the existing lazy cache: missing `{geometry_id}.SLDPRT` generates once; later instances and assemblies reuse it.
- Resolve `Models/Cubes/Large/HydrogenThrusterSmall` under the configured SDK root. Do not scan an install or infer other FBX names.
- Normalize scale, origin, and orientation in the generated part. Do not special-case assembly transforms.
- Fail closed if this supported builder fails. Do not silently substitute filler.
- `chamfer_capable` remains false.

**Explicit boundaries / out of scope.** Other thrusters; Small Grid; multi-cell placement; generic mesh healing; whole-vanilla catalog; OBJ export; committing Keen FBX or derived SLDPRT; inventing a later unit.

**Development validation.** Ordinary tests cover the one identity, path containment, missing root/FBX, traversal, generate-once/reuse, remaining unknowns as filler, strict acceptance of the target, chamfer refusal, no Small Grid, no install scan, provenance, and generated-root containment.

**Quality/security assessment focus.** SDK-root escape; wrong/LOD/construction/MWM file; scale or axis error; silent filler after supported-builder failure; global `SDK_MESH_*` enablement; generated Keen-derived artifacts entering git; temp-file leakage.

**External validation.** Live SolidWorks: minimal armor+thrust assemble with generate then reuse; Big Red permissive assemble under a gitignored generated root. Required for QUALIFIED.

**Completion criteria.** The one identity is supported conversion; Big Red uses one reusable thruster part for all sixteen instances; no general SDK-mesh or universal vanilla claim; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE. After qualification, next executable unit was none until the human later authorized S2C-11.8.1.

### S2C-11.8.1 — Demand-driven vanilla TriangleMesh resolution for eligible Large Grid 1×1×1 blocks

**Objective.** When a catalog-unknown Large Grid 1×1×1 vanilla TriangleMesh identity is encountered, resolve its official definition and corresponding SDK FBX on demand, create a transient runtime bind for the existing lazy materializer, and continue conversion with a real part.

**Rationale.** S2C-11.7.1 proved one complete SDK-FBX builder. Remaining Big Red unknowns were still fillers solely because they were not hand-bound. This unit removes one-at-a-time packaged registration for identities that satisfy conservative eligibility rules.

**Prerequisites.** S2C-11.7.1. This unit was inserted by a human-authorized amendment after S2C-11.7.1 was QUALIFIED and after the human postponed Small Grid. It does not rewrite original M11 history, does not start S2C-13.1.1, and does not invent a later unit.

**Affected systems / expected areas.** A narrow `se2cad.vanilla` resolver; library runtime overlay; preflight/policy ordering; reuse of the S2C-11.7.1 SDK source/convert/materialize path; ordinary and live tests.

**Implementation requirements.**

- Packaged catalog hits keep existing behavior. Do not mutate the packaged catalog on disk.
- Eligible automatic resolution requires all of: Large Grid; vanilla definition found; size 1×1×1; `BlockTopology == TriangleMesh`; exactly one clear primary Model; corresponding official binary SDK FBX under the configured SDK root; no required subpart/composite handling; no path ambiguity.
- Derive a deterministic `vanilla_lg_1x1x1_*` geometry_id. `chamfer_capable` is false.
- Fail closed to existing unknown/unsupported policy when any eligibility condition is not met.
- Once a runtime bind is supported, builder failure must not become filler.
- Reuse the existing lazy materializer. No eager or whole-SDK generation.
- Operator game-content and SDK roots reuse `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT` and `se2cad.local.json`.

**Explicit boundaries / out of scope.** Small Grid; multi-cell placement; CubeTopology expansion; whole vanilla catalog; OBJ export; ASCII-FBX conversion; inventing a later unit.

**Development validation.** Ordinary tests cover packaged bypass, the S2C-11.7.1 thruster, dynamic 1×1×1 resolve, determinism, no catalog persistence, Small Grid / multi-cell / CubeTopology / missing or ambiguous Model rejection, missing roots, missing definition, duplicate SubtypeId, missing or ASCII FBX, traversal, Construction/LOD non-selection, builder-failure ≠ filler, generate-once/reuse, chamfer disabled, unknown modded filler, strict accept/reject, per-instance colors.

**Quality/security assessment focus.** Path escape; hostile XML; duplicate SubtypeId; case-insensitive filename ambiguity; Construction/LOD/interior selection; arbitrary MWM→FBX substitution; catalog/runtime collision; silent support before a usable binary FBX; supported-builder failure becoming filler; whole-install catalog expansion; Keen-derived artifacts entering git.

**External validation.** Live SolidWorks: synthetic armor+thrust+two new families generate then reuse; Big Red permissive assemble under a gitignored generated root. Required for QUALIFIED.

**Completion criteria.** Eligible unknowns become real parts; remaining identities stay unresolved for an exact recorded reason; no universal vanilla claim; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE. After qualification, next executable unit was none until the human later authorized S2C-11.9.1.

### S2C-11.9.1 — ASCII SDK-FBX conversion support for existing eligible Large Grid 1×1×1 TriangleMesh blocks

**Objective.** Allow the already-qualified demand-driven SDK-mesh path to consume official ASCII FBX source files when every other S2C-11.8.1 eligibility rule is already satisfied.

**Rationale.** After S2C-11.8.1, Big Red’s remaining 1×1×1 fillers were official ASCII FBX (`LargeBlockConveyor`, `LargeBlockGyro`). Blender 5.2 rejects ASCII FBX. This unit is a source-format extension, not a new support-resolution architecture.

**Prerequisites.** S2C-11.8.1. This unit was inserted by a human-authorized amendment after S2C-11.8.1 was QUALIFIED and after the human postponed Small Grid. It does not rewrite original M11 history, does not start S2C-13.1.1, and does not invent a later unit.

**Affected systems / expected areas.** SDK source classification; bounded ASCII FBX 7.x normalization under generated work; Blender host diagnostics; reuse of the qualified binary-FBX convert/import/materialize path; ordinary and live tests.

**Implementation requirements.**

- Preserve S2C-11.8.1 resolver behavior and fail-closed support semantics.
- Do not grant support by deleting the binary-only check. ASCII is eligible only when the conversion path can produce the same downstream artifact contract as binary FBX.
- Binary FBX stays on the existing path and is not routed through ASCII normalization.
- Intermediate artifacts stay under gitignored generated/temp storage, do not overwrite official SDK FBX, and do not escape configured roots.
- If Blender remains in the pipeline, do not trust process exit code alone; require the expected STL and surface script exceptions.
- Shared recipe normalization only; no per-instance Conveyor/Gyro assembly transforms.
- No packaged catalog persistence and no hand registration of Conveyor/Gyro.

**Explicit boundaries / out of scope.** Multi-cell placement; Small Grid; CubeTopology expansion; OBJ export; redesign of the runtime vanilla resolver; a general-purpose FBX conversion framework; animation or mechanical-subpart architecture; inventing a later unit.

**Development validation.** Ordinary tests cover binary acceptance, ASCII eligibility only when conversion is available, invalid/truncated/random `.fbx` fail-closed, path containment, classification determinism, Blender diagnostics, transient overlay, Conveyor/Gyro resolve without catalog registration, generate-once/reuse, chamfer false, scale sanity, no whole-SDK conversion, and unchanged Small Grid / multi-cell / CubeTopology behavior.

**Quality/security assessment focus.** Hostile or oversized ASCII; path injection; temp/cache collision; binary/ASCII misclassification; subprocess quoting; source overwrite; Blender success without artifact; facet-normal modal; silent filler after support; accidental multi-cell or Small Grid activation; Keen-derived artifacts entering git.

**External validation.** Live SolidWorks: synthetic armor+binary-mesh+Conveyor+Gyro generate then reuse; Big Red permissive assemble under a gitignored generated root. Required for QUALIFIED.

**Completion criteria.** Official ASCII FBX for already-eligible 1×1×1 TriangleMesh becomes a real cached part; remaining identities stay unresolved for an exact recorded reason; no universal FBX or vanilla claim; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence in STATE. After qualification, next executable unit was none until the human later authorized S2C-11.10.1.

### S2C-11.10.1 — Multi-cell placement metadata and CAD-neutral transform foundation

**Objective.** Represent Size and ModelOffset as CAD-neutral placement metadata and compute occupied Min/Max plus occupancy-center translation for arbitrary block Size, without enabling multi-cell runtime support.

**Rationale.** After S2C-11.9.1, Big Red’s remaining fillers are only multi-cell identities. A read-only investigation established Keen’s generic occupied-Max and occupancy-center placement rule. This unit qualifies that math independently so a later authorized unit can consume it. It does not grant support.

**Prerequisites.** S2C-11.9.1. This unit was inserted by a human-authorized amendment after S2C-11.9.1 was QUALIFIED and after the human postponed Small Grid. It does not rewrite original M11 history, does not start S2C-13.1.1, and does not invent a later resolver or materialization unit.

**Affected systems / expected areas.** CAD-neutral transform engine; IR construction inputs; policy/preflight consumers of `canonical_block_from_parsed`; ordinary tests. No packaged-catalog change. No SolidWorks live generation.

**Implementation requirements.**

- Supply Size and ModelOffset as an immutable placement value object to IR construction. Keep `ParsedBlock` blueprint-only. Do not bind `CanonicalBlock` to the vanilla resolver.
- `Min` is the occupied AABB minimum. Size is local Right/Up/Back before orientation. `Max = Min + abs(R · (Size − 1))` with componentwise abs after rotation.
- Translation is occupancy-center times pitch plus one rotated ModelOffset, converted from Keen metres to millimetres. Definition `Center` is not CAD translation.
- 1×1×1 plus zero ModelOffset must reproduce the qualified cell-center transform exactly.
- Existing packaged/library 1×1×1 identities continue to work without a game-content root. Do not globally assume unknown blocks are 1×1×1.
- Reject invalid Size at the transform boundary. Invalid orientations continue to fail closed.

**Explicit boundaries / out of scope.** Multi-cell runtime support; relaxing the S2C-11.8.1 1×1×1 eligibility gate; generating multi-cell SolidWorks parts; changing the packaged catalog; Small Grid; CubeTopology expansion; subtype-specific placement hacks; raising the imported-mesh envelope limit; inventing the subsequent resolver/materialization unit.

**Development validation.** Ordinary tests cover 1×1×1 exact regression including the acceptance fixture; all 24 orientations; multiple Size shapes including Big Red reference vectors; half-cell and integer occupancy centers; ModelOffset rotation/units/once-only; Center ignored; invalid Size; unchanged vanilla multi-cell unresolved status; unchanged Big Red 126/10/0/10 when that fixture and roots are available; install-free packaged armor; no SolidWorks types in transform/IR.

**Quality/security assessment focus.** Size axis swap; signed rotation before abs; half-cell truncation; Center used in translation; ModelOffset axes/units/double application; game-content leaking into the transform engine; accidental multi-cell support; unknown blocks silently assigned Size=1; acceptance-transform change; determinant regression; subtype-specific hacks.

**External validation.** None. This is a CAD-neutral integer-grid foundation. A SolidWorks live run is not required.

**Completion criteria.** Generalized placement math is implemented and qualified; current 1×1×1 transforms are unchanged; multi-cell identities remain runtime-ineligible; no multi-cell CAD parts were generated; no resolver eligibility was broadened; no Small Grid work occurred. After qualification, next executable unit is none.

---

## Milestone M12 — Blueprint compatibility and unknown-block handling

**Objective.** Add a deliberate preflight model plus strict and permissive conversion behavior for unknown or unsupported blocks.

**Completion outcome.** Strict mode refuses unsupported conversion with useful diagnostics. Permissive mode uses a designated filler CAD representation while preserving original SE identity, location, and orientation. Support is never silently misrepresented.

### S2C-12.1.1 — Conversion preflight

**Objective.** Produce a structured preflight report for a parsed blueprint against the catalog: what will convert, what will not, and why.

**Rationale.** Catalog machinery already fail-closes on unknown subtypes. Operators need a batch diagnosis before assembly generation, without silent drops.

**Prerequisites.** S2C-11.5.1 (program sequence). Technical: parser + catalog + statistics fields from M7 as useful inputs.

**Affected systems / expected areas.** CAD-neutral preflight module; tests; optional reuse of M7 statistics. No filler insertion yet.

**Implementation requirements.**

- Report each block’s subtype, `Min`, catalog outcome, geometry support, and appearance support when appearance exists (M9). Those supports stay independently reportable.
- Unknown, unsupported, and supported are distinct outcomes. Do not alias unknown to a supported armor type.
- The report is sufficient to decide strict vs permissive without running SolidWorks.
- Fail closed on malformed blueprints using existing parser rules.

**Explicit boundaries / out of scope.** Performing permissive substitution (S2C-12.2.1); UI; changing M11 recipe kinds.

**Development validation.** Tests for all-supported fixture (clean preflight), unknown subtype, catalog-unsupported, mixed documents, and independence of geometry vs appearance flags.

**Quality/security assessment focus.** Silent omission; path leakage in diagnostics; treating preflight success as conversion success.

**External validation.** None.

**Completion criteria.** Preflight result is testable and complete for the blocks present. QUALIFIED from automated tests.

### S2C-12.2.1 — Strict and permissive unknown-block conversion

**Objective.** Implement strict refusal with diagnostics and permissive conversion that inserts a designated filler part while preserving SE identity and pose.

**Rationale.** Strict mode is the honest default for unsupported work. Permissive mode must remain visibly and semantically a filler.

**Prerequisites.** S2C-12.1.1.

**Affected systems / expected areas.** Conversion policy; catalog/library filler identity; IR fields that preserve original subtype; assembly insertion; tests.

**Implementation requirements.**

- Strict: refuse conversion when any block is unknown or unsupported. Surface the preflight diagnostics. Do not emit a partial assembly as success.
- Permissive: convert, placing a designated filler CAD representation at the original `Min`, Forward, and Up. Preserve the original SE subtype (and appearance if present) on the IR. Filler `geometry_id` / `support_status` must not claim the block is a supported library type.
- Filler is an explicit SE2CAD representation, not a silent reuse of `large_armor_block` as if the unknown block were armor.
- Policy is selected by an explicit caller/operator setting. Do not default to permissive in a way that hides failures.
- Unknown-block handling must not silently skip blocks.

**Explicit boundaries / out of scope.** Inventing real geometry for unknown mods; multi-grid; changing M11 long-tail classifications except to consume them.

**Development validation.** Tests: strict fails on one unknown; permissive emits N IR instances for N blocks; filler identity distinct; pose equals `cell_center_mm` + `rotation_from_forward_up`; preflight counts match conversion decisions.

**Quality/security assessment focus.** Silent substitution as armor; default-permissive; dropped blocks; filler overwriting a real part filename.

**External validation.** Live SolidWorks integration for a small permissive IR (filler + one real part) proving pose and distinct filler part. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED.

**Completion criteria.** Both policies exist and are tested; DEV-COMPLETE from ordinary tests; QUALIFIED after live filler-assembly evidence in STATE.

### S2C-12.3.1 — Vanilla object-builder parser compatibility

**Objective.** Let ordinary vanilla Space Engineers cube-block-derived object builders pass through the parser as block records so existing strict/permissive policy can decide what to do with them.

**Rationale.** A moderately complicated Large Grid blueprint (Big Red) failed at `CubeBlocks[1]` with `UnsupportedBlueprintError` for `xsi:type='MyObjectBuilder_Thrust'` before policy could run. Keen serializes `CubeBlocks` as `MyObjectBuilder_CubeBlock` elements whose `xsi:type` is the runtime builder. Parser rejection of those types made permissive substitution unreachable for ordinary vanilla functional blocks. This unit grants no new geometry support.

**Prerequisites.** S2C-12.2.1. This unit was inserted by a human-authorized compatibility amendment after S2C-11.6.1 was QUALIFIED and after the human postponed Small Grid. It does not rewrite original M12 history, does not expand the packaged catalog, and does not start S2C-13.1.1.

**Affected systems / expected areas.** Blueprint parser acceptance of cube-block object-builder types; parsed-block retention of `xsi:type` where useful; existing preflight/policy consumption of those records; ordinary tests; Big Red as read-only live investigation/qualification input. No new recipes.

**Implementation requirements.**

- Inspect the current parser and tests. Broaden acceptance only enough to represent ordinary vanilla cube-block-derived object builders.
- Do not maintain an ever-growing allowlist of `MyObjectBuilder_Thrust`, `MyObjectBuilder_Reactor`, and similar literals. Use a structural rule based on Space Engineers `CubeBlocks` serialization and repository evidence.
- Preserve subtype, placement, orientation, appearance, source index, and object-builder type where available. `SubtypeName` remains the primary runtime identity. Do not contaminate `geometry_id` with object-builder type.
- Parser decides representability. Catalog/policy decide support, refusal, and filler substitution.
- Fail closed on missing/unusable required fields, malformed XML, non-cube-block entries, multi-grid/subgrid structures already outside scope, and any case that would force invented identity.
- Do not silently synthesize block identity. Do not accept arbitrary `xsi:type` strings or non-block XML merely because a type attribute exists.

**Explicit boundaries / out of scope.** Thruster or other functional CAD; catalog expansion; CubeTopology families; FBX/MWM/OBJ import; Small Grid; multi-grid; mechanical connections; inventing later units.

**Development validation.** Ordinary tests cover: existing `MyObjectBuilder_CubeBlock` unchanged; `MyObjectBuilder_Thrust` and several other functional builders parse without a literal allowlist; fields and source order survive; unknown functional blocks reach strict refusal and permissive filler; supported armor unchanged; preflight reports those identities; malformed/unusable/non-block cases remain rejected; no catalog, recipe, Small Grid, or runtime SE/SDK scan expansion.

**Quality/security assessment focus.** Accidental accept-every-`xsi:type`; malformed XML becoming accepted; loss of fail-closed required fields; parser taking on policy/catalog responsibility; object-builder type changing CAD identity; catalog support expansion; Small Grid bleed; source-index/order changes; appearance regressions; filler substitution for malformed blocks; runtime game/SDK dependency.

**External validation.** Ordinary tests plus read-only Big Red parse/preflight and `python -m se2cad.solidworks.assemble c:\SE-blueprints\bigred_bp.sbc --policy permissive`. Live SolidWorks is required if that command reaches assembly. If Big Red hits a new unrelated structural blocker after the parser fix, stop and record it rather than widening the unit. Required for QUALIFIED as evidence permits.

**Completion criteria.** Ordinary vanilla object-builder types parse as block records; existing policy is reachable; no new geometry support is claimed; DEV-COMPLETE from ordinary tests; QUALIFIED after the named Big Red / live evidence, or after an evidenced independent blocker is recorded. After qualification, stop and report. Do not automatically start S2C-13.1.1.

### S2C-12.4.1 — Safe assembly filename derivation

**Objective.** Separate the logical Space Engineers blueprint/assembly identity from the filesystem-safe SolidWorks assembly filename so an ordinary identity such as `Big Red` can produce a deterministic `.SLDASM` under the generated root.

**Rationale.** After S2C-12.3.1, Big Red parsed, preflighted, and reached permissive policy (136 blocks, 65 supported, 71 unknown fillers). Assembly then failed closed with `AssemblyIdentityError` because identity validation and filename validation were the same `^[A-Za-z0-9][A-Za-z0-9._-]*$` rule. The space is a demonstrated real-blueprint blocker, not a reason to accept arbitrary identity strings as paths.

**Prerequisites.** S2C-12.3.1. This unit was inserted by a human-authorized compatibility amendment after S2C-12.3.1 was QUALIFIED and after the human postponed Small Grid. It does not rewrite original M12 history, does not expand catalog or CAD support, and does not start S2C-13.1.1.

**Affected systems / expected areas.** Assembly filename derivation from IR `identity_subtype`; generated-root containment; ordinary tests; Big Red as live qualification input. Logical identity fields, component names, part filenames, catalog identity, IR transforms, appearance, and materialization identity stay unchanged.

**Implementation requirements.**

- Keep the ShipBlueprint / IR identity as the logical value (`Big Red` remains `Big Red` where identity is represented).
- Derive one deterministic, Windows-safe, single-segment `.SLDASM` filename from that identity.
- Already-safe identities such as `se2cad-test1` retain their current filename.
- Do not solve this by weakening path validation or accepting the raw identity as a filesystem path.
- Distinct identities that collide under naive space-to-underscore mapping, including `Big Red` and `Big_Red`, must not silently share one filename.
- Path separators, `..`, absolute Windows paths, and UNC-like identities must not escape the generated root. Existing `contained_destination` remains authoritative.
- Handle Windows-invalid characters, trailing space/dot, empty identity, and reserved device names. Fail closed when no safe derivation is possible.
- Do not use process-randomized `hash()`. If a digest is used, it must be deterministic. Do not add a registry.

**Explicit boundaries / out of scope.** New block geometry; catalog support expansion; CubeTopology constructions; FBX/MWM/OBJ import; Small Grid; changing S2C-12.3.1 parser compatibility, strict/permissive policy, designated filler, S2C-11.6.1 materialization, or S2C-10.4.1 chamfer behavior; inventing a later unit.

**Development validation.** Ordinary tests cover: stable already-safe names; `Big Red` derives a safe filename while remaining the logical identity; repeated derivation is stable; `Big Red` / `Big_Red` do not collide; separators, `..`, absolute, and UNC identities cannot escape; Windows-invalid and reserved names are safe; empty identity fails closed; containment remains independently enforced; component/part/materialization/policy/catalog/Small Grid behavior is unchanged.

**Quality/security assessment focus.** Path traversal; absolute and UNC injection; reserved Windows names; invalid characters; normalization collisions; case-insensitive collisions; nondeterminism; logical-identity mutation; component/part rename; overwrite of an unrelated assembly; generated-root escape.

**External validation.** Ordinary tests plus `python -m se2cad.solidworks.assemble C:\SE-blueprints\bigred_bp.sbc --policy permissive`. Live SolidWorks is required if that command reaches assembly. If Big Red hits a new unrelated downstream blocker after filename derivation, stop and record it rather than widening the unit. Required for QUALIFIED as evidence permits.

**Completion criteria.** Logical identity stays distinct from the derived assembly filename; `Big Red` proceeds beyond the previous filename blocker or an evidenced independent blocker is recorded; no new geometry support is claimed; DEV-COMPLETE from ordinary tests; QUALIFIED after the named Big Red / live evidence. After qualification, stop and report. Do not automatically start S2C-13.1.1.

---

## Milestone M13 — Small Grid support

**Objective.** Convert single-grid Small Grid blueprints through the same semantic pipeline using centralized pitch and transforms.

**Completion outcome.** Small Grid is not a forked converter. Pitch is a named constant. Fixtures and orientation/placement tests cover the expanded matrix.

### S2C-13.1.1 — Small Grid semantic path

**Objective.** Accept single-grid Small Grid blueprints in parser, catalog, IR, transforms, and native recipes without forking the pipeline.

**Rationale.** `cell_center_mm` already takes a pitch argument. Grid size is already an IR field. The missing pieces are an enum value, a named Small Grid pitch, catalog entries, and parser acceptance.

**Prerequisites.** S2C-12.4.1 (program sequence).

**Affected systems / expected areas.** `GridSize`, catalog constants, parser, catalog entries for the Small Grid counterparts of supported armor (and any M11 Small Grid identities this unit activates), IR/transform pitch selection, library recipes parameterized by grid pitch. No SolidWorks.

**Implementation requirements.**

- Add `SMALL_GRID_CELL_PITCH_MM` from evidenced Keen `CubeSizes Small` (expected 500 mm). Do not scatter `500` through call sites. Do not change `LARGE_GRID_CELL_PITCH_MM`.
- Parser accepts `GridSizeEnum` Small or Large for a single grid. Multiple grids still fail closed.
- Catalog/library records include grid size. Small and Large identities remain distinct.
- Transforms use the pitch for that grid. Canonical frame axes do not change.
- Reuse M12 preflight/policy; do not write a second unknown-block system.
- Synthetic XML is sufficient for this unit’s tests. Do not invent a human-authored `bp.sbc` if a later CAD fixture is absent.

**Explicit boundaries / out of scope.** SolidWorks Small Grid part/assembly generation (S2C-13.2.1); multi-grid; docked small ships.

**Development validation.** Tests: Small Grid parse; rejection of mixed/multi grid; pitch 500 mm translations; 24-orientation matrix still unique; Large Grid fixture unchanged.

**Quality/security assessment focus.** Pitch mix-up; forked IR; scattering literals; accidental Large-to-Small aliasing of subtype strings.

**External validation.** None.

**Completion criteria.** Semantic path exists; Large Grid regressions pass. QUALIFIED from automated tests.

### S2C-13.2.1 — Small Grid parts, assembly, and placement fixtures

**Objective.** Generate Small Grid canonical parts and transform-placed assemblies, with orientation/placement regression coverage.

**Rationale.** The geometry/library/test matrix grows here. Placement bugs will not be caught by Large Grid-only artifacts.

**Prerequisites.** S2C-13.1.1.

**Affected systems / expected areas.** Library records/recipes for Small Grid; SolidWorks generation and assembly; fixtures with provenance; ordinary and live tests.

**Implementation requirements.**

- Produce reusable Small Grid canonical parts for the supported Small Grid armor set this unit activates, in the same local frame scaled by Small Grid pitch.
- Assembly insertion uses IR `(R, t)` with Small Grid translations (0.5 m cell pitch).
- Add sufficient fixtures: synthetic orientation/placement cases, plus a provenance-recorded user-authored Small Grid `bp.sbc` if the operator supplies one. If that human-authored file is required for QUALIFIED and is absent, stop and ask; do not invent a substitute ship.
- Cover mixed orientations and at least one negative-axis translation, analogous to the Large Grid fixture purpose.
- Large Grid generated names and the M0–M6 fixture path must keep working.

**Explicit boundaries / out of scope.** Multi-grid; mechanical subgrids; claiming all vanilla Small Grid blocks if M11 did not classify them.

**Development validation.** Ordinary tests for Small Grid filenames, pitch, and placements. Large Grid ordinary suite remains green.

**Quality/security assessment focus.** Overwriting Large Grid parts; wrong pitch in `ArrayData`; fixture without provenance; game assets in fixtures.

**External validation.** Live SolidWorks integration generates Small Grid parts and an assembly whose reopened transforms match the Small Grid IR. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED. A user-authored fixture, if used, needs the same human-identity confirmation pattern as S2C-1.1.1 before QUALIFIED.

**Completion criteria.** Small Grid parts and assemblies generate; regressions exist; DEV-COMPLETE from ordinary tests; QUALIFIED after live evidence (and fixture confirmation if applicable) in STATE.

---

## Milestone M14 — Symmetry detection

**Objective.** Define what SE2CAD means by symmetry, then detect it in a useful, testable, CAD-neutral form.

**Completion outcome.** Symmetry information exists and is tested independently of print-shell generation and CAD optimization.

### S2C-14.1.1 — Symmetry definition

**Objective.** Write a precise, testable definition of blueprint symmetry for SE2CAD before implementing a detector.

**Rationale.** The mathematics is easy to gesture at; reliability across ships, orientations, types, colors, and imperfect symmetry depends on an explicit contract.

**Prerequisites.** S2C-13.2.1 (program sequence).

**Affected systems / expected areas.** Durable symmetry contract (architecture or specification document this unit adds/updates); examples as tests or fixtures. No detector beyond what is needed to make the definition executable as tests of the contract itself.

**Implementation requirements.**

- Define which symmetries are in scope (for example grid-aligned reflections and/or 90° rotations) and which are not.
- State whether subtype, orientation, color/appearance, and grid size participate in equality.
- State how imperfect symmetry is reported (exact match only vs explicit residual). Do not hide residuals.
- Output is CAD-neutral data. Do not couple the definition to print-shell generation, mate reduction, or part merging.
- If two materially different definitions are both defensible, stop and ask.

**Explicit boundaries / out of scope.** Detector implementation (S2C-14.2.1); using symmetry to change CAD; M15.

**Development validation.** Contract examples: asymmetric acceptance fixture is not symmetric; a synthetic mirrored pair is; color-mismatch and subtype-mismatch cases follow the written rules.

**Quality/security assessment focus.** Vague “mostly symmetric” claims; coupling to M15; changing placement semantics.

**External validation.** None.

**Completion criteria.** Definition is in-repo and testable. QUALIFIED from those tests plus the written contract.

### S2C-14.2.1 — Symmetry detection

**Objective.** Implement detection that emits the S2C-14.1.1 result for arbitrary single-grid blueprints in the supported IR.

**Rationale.** Later consumers may not exist yet. The milestone still must produce useful, testable information.

**Prerequisites.** S2C-14.1.1.

**Affected systems / expected areas.** CAD-neutral detector; tests across orientations, types, colors if present, Large and Small Grid. No SolidWorks requirement.

**Implementation requirements.**

- Consume parser/IR data already in the pipeline. Do not require SolidWorks.
- Follow S2C-14.1.1 exactly, including imperfect-symmetry reporting.
- Remain useful if M15 never reads the result.
- Do not modify assembly generation to “optimize” from symmetry.

**Explicit boundaries / out of scope.** Print-shell; CAD instancing optimization; multi-grid symmetry.

**Development validation.** Tests for the contract examples, rotated-but-symmetric ships, color/type sensitivity, and the asymmetric acceptance fixture.

**Quality/security assessment focus.** False positives on near-symmetry; order dependence; using CAD tessellation instead of IR.

**External validation.** None.

**Completion criteria.** Detector matches the contract; tests pass. QUALIFIED from automated tests.

---

## Milestone M15 — Automatic print-shell generation

**Objective.** Produce a robust printable exterior solid from an SE2CAD assembly/IR by removing internals, preserving important exterior geometry, and closing cavities — as a defined geometry-processing subsystem.

**Completion outcome.** “Print shell” is defined in-repo. Semantic exterior/interior reasoning is separate from CAD solid operations. Resulting solids have regression and validity evidence. No claim of general arbitrary-geometry robustness without that evidence.

This is the final and largest milestone.

### S2C-15.1.1 — Print-shell definition

**Objective.** Define what a print shell means for SE2CAD before implementing generation.

**Rationale.** Without a definition, “remove internals” and “close cavities” are unbounded.

**Prerequisites.** S2C-14.2.1 (program sequence). Detection output must not be a required input to this definition.

**Affected systems / expected areas.** Durable print-shell contract. No production solid generation.

**Implementation requirements.**

- Define exterior vs interior, which cavities close, what exterior geometry is preserved, and what validity means (solid body, closed, positive volume, relationship to source envelope).
- Separate semantic occupancy/exterior reasoning from CAD Boolean/solid operations in the contract.
- State explicit non-goals (slicer, physical print, general mesh repair, arbitrary TriangleMesh robustness).
- State how pathological cases fail closed or are reported as out of scope.
- Do not require M14 symmetry results.
- If two materially different product definitions are both defensible, stop and ask.

**Explicit boundaries / out of scope.** Implementing the generator; STL/3MF product export; physical printing.

**Development validation.** Contract examples as tests: a hollow 2×2×2 box of blocks has a defined interior; a single block’s shell is defined; disconnected exterior features follow the written rule.

**Quality/security assessment focus.** Unbounded robustness claims; coupling to symmetry or slicers; treating the definition as already implemented.

**External validation.** None.

**Completion criteria.** In-repo definition plus example tests. QUALIFIED from that evidence.

### S2C-15.2.1 — Semantic exterior and interior classification

**Objective.** Classify cells or blocks as exterior, interior, or excluded using IR/occupancy, according to S2C-15.1.1, without CAD Booleans.

**Rationale.** Semantic reasoning should be testable without SolidWorks.

**Prerequisites.** S2C-15.1.1.

**Affected systems / expected areas.** CAD-neutral classification module; fixtures/synthetics; tests.

**Implementation requirements.**

- Use grid occupancy, supported geometry, and the written definition. Filler/unknown cells follow M12 semantics (do not pretend they are armor).
- Emit a structured classification the solid-generation unit can consume.
- Work for Large Grid and, after M13, Small Grid via pitch/grid-size already on the IR.
- Do not call SolidWorks.

**Explicit boundaries / out of scope.** Producing the CAD solid (S2C-15.3.1); slicer export.

**Development validation.** Tests for the S2C-15.1.1 examples, the acceptance fixture (asymmetric — no false interior), and at least one enclosed cavity case.

**Quality/security assessment focus.** Classifying unsupported blocks as solid armor; grid-size errors; nondeterministic sets.

**External validation.** None.

**Completion criteria.** Classifier exists and matches the definition on the named cases. QUALIFIED from automated tests.

### S2C-15.3.1 — Print-shell solid generation

**Objective.** Generate valid CAD solids for the classified print shell, separating CAD operations from the semantic classifier.

**Rationale.** Closing cavities and subtracting internals is a SolidWorks/solid-modeling problem once the semantic set is known.

**Prerequisites.** S2C-15.2.1, S2C-5.1.1.

**Affected systems / expected areas.** Print-shell generation behind a boundary; SolidWorks (or CAD-neutral solid ops plus SW backend) as appropriate; generated-root containment; ordinary and live tests.

**Implementation requirements.**

- Consume S2C-15.2.1 classification plus library solids. Do not re-derive SE orientation in the backend.
- Produce solids that meet S2C-15.1.1 validity requirements.
- Writes stay under the configured generated root. Do not overwrite unrelated documents or untreated canonical library parts.
- Pathological cases follow the definition: fail closed or report out of scope. Do not claim general arbitrary-geometry robustness.
- Do not add remoting, Blender-on-runtime, or a second placement frame.

**Explicit boundaries / out of scope.** Physical print; general mesh repair; requiring symmetry; STL/3MF as a productized exporter unless already incidental to validation.

**Development validation.** Ordinary tests for path handling, fail-closed pathology, and that the backend consumes classification data rather than re-parsing SE semantics.

**Quality/security assessment focus.** COM misuse; destructive edits to library parts; writes outside the generated root; oversize Booleans accepted as success without validity checks.

**External validation.** Live SolidWorks integration produces a shell solid for at least one enclosed-cavity fixture and the validity checks named in S2C-15.1.1. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED.

**Completion criteria.** Generator exists; DEV-COMPLETE from ordinary tests; QUALIFIED after live validity evidence in STATE.

### S2C-15.4.1 — Print-shell regression and validity evidence

**Objective.** Close the program with regression and validity evidence for print-shell solids, including named pathological cases, without over-claiming robustness.

**Rationale.** This subsystem is large enough that a distinct qualification unit is warranted, as M6 was for the initial converter.

**Prerequisites.** S2C-15.3.1.

**Affected systems / expected areas.** End-to-end wiring if needed; regression tests; STATE qualification record.

**Implementation requirements.**

- Regression: acceptance-fixture assembly path still matches S2C-6.1.1 placement rules; classifier + generator stay consistent with S2C-15.1.1.
- Validity evidence for resulting solids: body/closed/volume/envelope checks recorded with commands and results.
- Include pathological cases the definition names (open hulls, single-block, thin walls, mixed support/filler as applicable). Outcomes must match the definition (success, fail closed, or explicit out of scope).
- Do not claim general arbitrary-geometry robustness unless evidence covers that claim (it will not, unless this unit actually produced it).

**Explicit boundaries / out of scope.** New product features; slicer/physical print qualification; inventing a follow-on program.

**Development validation.** Automated regression of classification + any CAD-neutral validity predicates.

**Quality/security assessment focus.** False QUALIFIED; loosened validity; leftover proprietary outputs committed; claiming a later program.

**External validation.** Live SolidWorks evidence for the named success fixtures. Use `SE2CAD_SOLIDWORKS_INTEGRATION`. Required for QUALIFIED and for program close.

**Completion criteria.** Evidence recorded in STATE; residual limits stated honestly; program marked complete in STATE only when the M7–M15 end state is met.
