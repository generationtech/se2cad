# SE2CAD state

Responsibility: what has actually happened. This is the only authoritative live program-status location.

How status words are used: [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md).
Current unit definitions (no live status): [SE2CAD_PLAN_M7.md](SE2CAD_PLAN_M7.md).
Current program: [SE2CAD_PROGRAM_M7.md](SE2CAD_PROGRAM_M7.md).
Historical initial units: [SE2CAD_PLAN.md](SE2CAD_PLAN.md).

## Current program

**Current approved program:** M7–M15. Charter [SE2CAD_PROGRAM_M7.md](SE2CAD_PROGRAM_M7.md). Units [SE2CAD_PLAN_M7.md](SE2CAD_PLAN_M7.md).

The nine milestones, in order, are: blueprint statistics; CAD component naming; block-color preservation; printable block-edge definition; SDK-driven vanilla library expansion; compatibility and unknown-block handling; Small Grid; symmetry detection; automatic print-shell generation.

No implementation milestone is ACTIVE. Cold-storage backlog remains outside this program. Do not invent work beyond it.

A 2026-09-09 human-authorized amendment inserted S2C-10.3.1 into M10 after S2C-11.1.1 was already QUALIFIED. M11 has started; that history is preserved. A later 2026-09-09 human-authorized amendment inserted S2C-10.4.1 into M10 after S2C-12.2.1 was already QUALIFIED and before S2C-13.1.1. That repair does not rewrite original M10 planning. A 2026-09-10 human-authorized amendment inserted S2C-11.6.1 into M11 after S2C-12.2.1 and S2C-10.4.1 were already QUALIFIED, and after the human postponed Small Grid. That insertion does not rewrite original M11 history. A later 2026-09-10 human-authorized amendment inserted S2C-12.3.1 into M12 after S2C-11.6.1 was already QUALIFIED and after the human postponed Small Grid. That insertion does not rewrite original M12 history. A later 2026-09-10 human-authorized amendment inserted S2C-12.4.1 into M12 after S2C-12.3.1 was already QUALIFIED and after the human postponed Small Grid. That insertion does not rewrite original M12 history. A later 2026-09-10 human-authorized amendment inserted S2C-11.7.1 into M11 after S2C-12.4.1 was already QUALIFIED and after the human postponed Small Grid. That insertion does not rewrite original M11 history. A later 2026-09-10 human-authorized amendment inserted S2C-11.8.1 into M11 after S2C-11.7.1 was already QUALIFIED and after the human postponed Small Grid. That insertion does not rewrite original M11 history. A later 2026-09-10 human-authorized amendment inserted S2C-11.9.1 into M11 after S2C-11.8.1 was already QUALIFIED and after the human postponed Small Grid. That insertion does not rewrite original M11 history. S2C-11.1.1 remains QUALIFIED. S2C-10.3.1 is QUALIFIED. S2C-10.4.1 is QUALIFIED. S2C-11.2.1 is QUALIFIED. S2C-11.3.1 is QUALIFIED. S2C-11.4.1 is QUALIFIED. S2C-11.5.1 is QUALIFIED. S2C-11.6.1 is QUALIFIED. S2C-11.7.1 is QUALIFIED. S2C-11.8.1 is QUALIFIED. S2C-11.9.1 is QUALIFIED. S2C-12.1.1 is QUALIFIED. S2C-12.2.1 is QUALIFIED. S2C-12.3.1 is QUALIFIED. S2C-12.4.1 is QUALIFIED. S2C-13.1.1 remains PLANNED and is postponed. There is no next executable unit until the human later directs one.

**Historical initial program (complete):** four Large Grid armor subtypes, single grid, SolidWorks assembly via canonical reusable parts. See [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md) and [SE2CAD_PLAN.md](SE2CAD_PLAN.md).

The initial program end state is met. The unchanged four-block Large Grid acceptance fixture converts through parser, catalog, canonical IR, qualified geometry recipes, qualified canonical SolidWorks parts, and transform-placed assembly generation to a reopened native `se2cad-test1.SLDASM` whose 24 component identities, IR-derived names, and transforms match the fixture-derived IR. Generated canonical `.SLDPRT` and `.SLDASM` files remain local cache and are not committed.

Public capability text in [README.md](../../../README.md) matches the qualified initial capability plus QUALIFIED S2C-7.1.1 blueprint statistics, QUALIFIED S2C-8.1.1 component names, QUALIFIED S2C-9.1.1 CAD-neutral `ColorMaskHSV` appearance, QUALIFIED S2C-9.2.1 per-instance SolidWorks component appearance, QUALIFIED S2C-10.1.1 optional block-edge treatment contract, QUALIFIED S2C-10.2.1 optional treated canonical parts, QUALIFIED S2C-10.3.1 explicit treated-part assembly selection, QUALIFIED S2C-10.4.1 configurable demand-driven chamfer variants, QUALIFIED S2C-11.1.1 operator-local definition discovery, QUALIFIED S2C-11.2.1 catalog identity expansion, QUALIFIED S2C-11.3.1 geometry provenance and recipe selection, QUALIFIED S2C-11.4.1 automated generation of the representative heavy-armor subset, QUALIFIED S2C-11.5.1 leftover/long-tail exception workflow and expansion regression, QUALIFIED S2C-11.6.1 demand-driven qualified base-part materialization, QUALIFIED S2C-12.1.1 conversion preflight, QUALIFIED S2C-12.2.1 strict and permissive unknown-block conversion, QUALIFIED S2C-12.3.1 vanilla object-builder parser compatibility, QUALIFIED S2C-12.4.1 safe assembly filename derivation, and QUALIFIED S2C-11.7.1 single-identity SDK-FBX materialization of `LargeBlockSmallHydrogenThrust`, QUALIFIED S2C-11.8.1 demand-driven vanilla TriangleMesh resolution for eligible Large Grid 1×1×1 blocks, and QUALIFIED S2C-11.9.1 ASCII SDK-FBX conversion support for those already-eligible identities. Generated parts and assemblies remain local cache; live SolidWorks 2026 end-to-end qualification of the acceptance fixture is recorded only here. STATE does not claim universal vanilla support. Remaining later M13 units through M15 are approved, not implemented. S2C-13.1.1 is postponed.

## Next executable unit

None. S2C-11.9.1 is QUALIFIED. S2C-13.1.1 Small Grid semantic path remains PLANNED and is postponed by explicit human authorization. Do not start it unless the human later directs that. Do not invent a later S2C unit, general SDK-mesh support, SolidWorks Small Grid part generation, multi-cell placement, CubeTopology expansion, a whole vanilla catalog, OBJ export, multi-grid, symmetry, print-shell, or later units. Universal vanilla blueprint compatibility is not claimed. Universal FBX support is not claimed.

## Unit status

### Initial program (complete)

| Unit | Status | Evidence |
| --- | --- | --- |
| S2C-0.1.1 | QUALIFIED | Bootstrap documents and rules exist; local links resolve; plan has no live status; no M1+ implementation; no proprietary game/SDK assets; distinct assessment recorded below; findings remediated. External validation was not required. |
| S2C-1.1.1 | QUALIFIED | Operator-supplied `bp.sbc` registered unmodified at the specified path; `PROVENANCE.md` present; deterministic inspection recorded below; human architect confirmed this is the intended `se2cad-test1` object; distinct assessment recorded below; no verified findings requiring remediation. |
| S2C-1.2.1 | QUALIFIED | Python parser and tests exist; qualified acceptance fixture extracts expected subtype/position/orientation values; unsafe and unsupported XML is rejected; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-2.1.1 | QUALIFIED | Packaged JSON catalog and loader exist; four Large Grid armor subtypes resolve to distinct SE2CAD geometry IDs; unknown/malformed/duplicate catalog data fails closed; acceptance fixture 24 blocks resolve; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-3.1.1 | QUALIFIED | CAD-neutral IR and integer transform engine exist; 24 fixture blocks convert through parser+catalog; all 24 legal Forward/Up orientations are unique right-handed integer rotations; invalid pairs fail closed; distinct assessment recorded below; no verified findings requiring remediation after test-scan false positives were corrected. External validation was not required. |
| S2C-4.1.1 | QUALIFIED | Library records and four native-procedural recipes exist; catalog geometry IDs resolve 1:1; recipes consume the qualified S2C-3.1.1 frame and `LARGE_GRID_CELL_PITCH_MM`; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-4.2.1 | QUALIFIED | Windows-local late-bound COM backend. Ordinary suite 145 tests OK (1 integration skipped). Live SW 2026 `RevisionNumber` 34.3.2 generated, validated, saved, closed, reopened, and revalidated all four canonical parts under the gitignored generated root. FeatureManager box + hypotenuse-plane `FeatureCut4` produces Corner and InvCorner. Library `part_locator` remains unbound. No generated parts committed. |
| S2C-5.1.1 | QUALIFIED | Ordinary suite 167 tests OK (2 integration skipped). Live SW 2026 `RevisionNumber` 34.3.2 inserted 24 fixture components from qualified SLDPRT files, applied IR ArrayData transforms, saved a native `se2cad-test1.SLDASM`, closed, reopened, and revalidated counts 9/12/2/1, representative translations/orientations, identity defaults, empty MateGroup, and generated-root containment. No generated assembly committed. |
| S2C-6.1.1 | QUALIFIED | Ordinary suite 176 tests OK (2 integration skipped). Live SW 2026 `RevisionNumber` 34.3.2 regenerated the four canonical parts, wrote `se2cad-test1.SLDASM` from the unchanged fixture, and matched all 24 reopened component transforms to the qualified IR. Fixture SHA-256 unchanged. No generated CAD committed. |

### M7–M15 program

| Unit | Status | Evidence |
| --- | --- | --- |
| M7–M15 program authorization | QUALIFIED | Current program/plan exist; historical M0–M6 preserved; ratchet/onboarding/process/rules point at STATE-named current docs; no product implementation; no named opschecks; next unit S2C-7.1.1 is PLANNED. Distinct assessment recorded below. |
| S2C-7.1.1 | QUALIFIED | CAD-neutral `se2cad.statistics` exists; fixture identity/counts/extents/occupancy/orientations/catalog coverage match the qualified parser/catalog/IR record; synthetic single-cell, negative, mixed-orientation, unknown-subtype, and parser-rejected cases covered; ordinary suite 198 tests, 2 skipped, OK. External validation was not required. Distinct assessment recorded below. |
| S2C-8.1.1 | QUALIFIED | CAD-neutral `component_name` from subtype/`Min`/Forward/Up/`source_index`; assembly writer sets Name2 at insert. Ordinary suite 212 tests, 2 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: all 24 save/reopen short names match the IR encoding; transforms and canonical `.SLDPRT` filenames unchanged. Distinct assessment recorded below. |
| S2C-9.1.1 | QUALIFIED | Parser/IR carry CAD-neutral `ColorMaskHSV`; omitted maps to `(0.0, -1.0, 0.0)`; `AppearanceSupport` independent of geometry `SupportStatus`. Ordinary suite 233 tests, 2 skipped, OK. External validation was not required. Distinct assessment recorded below. |
| S2C-9.2.1 | QUALIFIED | HSV-offset → RGB in `se2cad.solidworks.appearance`; `IComponent2.MaterialPropertyValues` instance override at insert. Ordinary suite 251 tests, 3 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: fixture 24 default appearances; synthetic two colors plus default on one `large_armor_block.SLDPRT`; canonical part SHA-256 unchanged. Distinct assessment recorded below. |
| S2C-10.1.1 | QUALIFIED | CAD-neutral equal-setback chamfer on convex manifold edges; default off; not a new `geometry_id`. Ordinary suite 267 tests, 3 skipped, OK. External validation was not required. Distinct assessment recorded below. |
| S2C-10.2.1 | QUALIFIED | Sibling `{geometry_id}_chamfer.SLDPRT` under the generated root when `EDGE_TREATMENT_CHAMFER` is requested. Untreated `large_armor_*.SLDPRT` remain the default. Ordinary suite 283 tests, 4 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: treated and untreated parts, one solid body, S2C-10.1.1 measurables. Distinct assessment recorded below. |
| S2C-10.3.1 | QUALIFIED | Default assemble still names untreated `{geometry_id}.SLDPRT`. Explicit `--edge-treatment chamfer` names `{geometry_id}_chamfer.SLDPRT` and fails closed if siblings are missing. Ordinary suite 323 tests, 5 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: treated 24-component `se2cad-test1.SLDASM` save/reopen used `*_chamfer.SLDPRT`; IR transforms, names, and default appearance unchanged; untreated part hashes unchanged; subsequent default assemble used untreated filenames. Distinct assessment recorded below. |
| S2C-10.4.1 | QUALIFIED | Configurable `--chamfer-mm` (default 50, range 5–250, no clamp). Size-specific `{geometry_id}_chamfer_{size}mm.SLDPRT`. Demand-driven generation of chamfer-capable geometry only; non-capable filler falls back untreated and is reported. Ordinary suite 458 tests, 8 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: distinct 50 mm and 75 mm artifacts; demand assemble consumed the exact size; reuse left the 75 mm hash unchanged; untreated `{geometry_id}.SLDPRT` unchanged within the probe; default untreated fixture assemble still used untreated parts; filler fallback reported. Distinct assessment [below](#qualitysecurity-assessment-s2c-1041). |
| S2C-11.1.1 | QUALIFIED | Library-build `se2cad.discovery` reads operator-configured game/SDK `.sbc` trees into observed catalog fields. Ordinary suite 309 tests, 4 skipped, OK. Runtime conversion remains install-free. External validation was not required. Distinct assessment recorded below. |
| S2C-11.2.1 | QUALIFIED | Schema v2 catalog records eight Large Grid identities; original four remain `native_procedural` / `supported`; four heavy-armor counterparts are `unsupported`. `expand_catalog_identities` resolves discovery-shaped observed facts. Ordinary suite 338 tests, 5 skipped, OK. External validation was not required. Distinct assessment recorded below. |
| S2C-11.3.1 | QUALIFIED | `select_catalog_recipes` classifies CubeTopology-class `CubeBlock` armor as `native_procedural` / automatable and TriangleMesh / unusual relationships as queryable long-tail exceptions. Packaged heavy-armor identities are `native_procedural` / `unsupported`. Ordinary suite 355 tests, 5 skipped, OK. External validation was not required. Distinct assessment recorded below. |
| S2C-11.4.1 | QUALIFIED | `recipe_for_topology` stamps Box/Slope/Corner/InvCorner constructions onto distinct geometry IDs. Representative subset is the four heavy-armor identities; they are `native_procedural` / `supported`. Ordinary suite 367 tests, 6 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2 generated, validated, saved, closed, reopened the four heavy parts under the gitignored generated root. Distinct assessment recorded below. |
| S2C-11.5.1 | QUALIFIED | `evaluate_leftover_set` / packaged `leftover_set.json` record leftover and completed automatable identities. Failed generation, unclassified identities, and unsupported recipe kinds cannot report as supported conversion. Ordinary suite 385 tests, 6 skipped, OK. External validation was not required; no additional parts were generated. Distinct assessment recorded below. |
| S2C-11.6.1 | QUALIFIED | Assembly lazily materializes already-qualified untreated `{geometry_id}.SLDPRT` files and reuses existing ones. Only demanded library-bound identities are generated. Hidden `LargeRoundArmor_*` aliases are not bound. Ordinary suite 479 tests, 9 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: missing `large_armor_block.SLDPRT` created on demand and reused; two-geometry assemble generated only slope; chamfer bootstrapped missing corner base then `*_chamfer_50mm.SLDPRT`; permissive filler completed. Distinct assessment [below](#qualitysecurity-assessment-s2c-1161). |
| S2C-11.7.1 | QUALIFIED | One authorized `sdk_mesh_direct` bind: `LargeBlockSmallHydrogenThrust` → `large_block_small_hydrogen_thrust`. Ordinary suite 526 tests, 11 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: minimal armor+thrust generate-then-reuse; Big Red permissive 136/81/55 with 16 instances of one 4385751-byte thruster part. Distinct assessment [below](#qualitysecurity-assessment-s2c-1171). |
| S2C-11.8.1 | QUALIFIED | Demand-driven vanilla Large Grid 1×1×1 TriangleMesh resolution. Ordinary suite 541 tests, 11 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: synthetic armor+thrust+light+battery generate-then-reuse; Big Red permissive 136/115/21 with 13 auto-resolved identities and 34 real instances. Distinct assessment [below](#qualitysecurity-assessment-s2c-1181). |
| S2C-11.9.1 | QUALIFIED | ASCII SDK-FBX conversion for already-eligible Large Grid 1×1×1 TriangleMesh. Ordinary suite 577 tests, 11 skipped, OK excluding untracked Small Grid WIP. Live SW 2026 `RevisionNumber` 34.3.2: synthetic armor+thrust+2×Conveyor+Gyro generate-then-reuse; Big Red permissive 136/126/10 with Conveyor×9 and Gyro×2 now real parts. Distinct assessment [below](#qualitysecurity-assessment-s2c-1191). |
| S2C-12.1.1 | QUALIFIED | CAD-neutral `se2cad.preflight` exists; fixture 24 blocks are `all_supported`; unknown, catalog-unsupported, mixed documents, and independent geometry/appearance flags covered; ordinary suite 404 tests, 6 skipped, OK. External validation was not required. Distinct assessment recorded below. |
| S2C-12.2.1 | QUALIFIED | CAD-neutral `se2cad.policy` exists; strict refuses unknown/unsupported with preflight diagnostics; permissive emits N IR instances with designated filler `se2cad_unknown_filler`; ordinary suite 428 tests, 7 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2: two-component permissive `se2cad-filler-probe.SLDASM` save/reopen used distinct `se2cad_unknown_filler.SLDPRT` at the IR pose. Distinct assessment [below](#qualitysecurity-assessment-s2c-1221). |
| S2C-12.3.1 | QUALIFIED | Parser accepts `CubeBlocks` items serialized as `MyObjectBuilder_CubeBlock` with a well-formed `MyObjectBuilder_*` `xsi:type`. Ordinary suite 502 tests, 10 skipped, OK. Big Red (136 blocks, 15 builder types) parses and preflights: supported 65 / unknown 71. Permissive policy emits 136 IR instances and 71 fillers. Live assemble of Big Red reached materialization then `AssemblyIdentityError` for identity `'Big Red'`. Live SW 2026 `RevisionNumber` 34.3.2 completed synthetic Thrust+armor `se2cad-ob-probe.SLDASM`. Distinct assessment [below](#qualitysecurity-assessment-s2c-1231). |
| S2C-12.4.1 | QUALIFIED | Logical ShipBlueprint identity stays distinct from a deterministic Windows-safe `.SLDASM` stem. Already-safe names such as `se2cad-test1.SLDASM` are unchanged. `Big Red` becomes `Big_Red+ffe1ed5b9381.SLDASM` without colliding with `Big_Red`. Ordinary suite 511 tests, 11 skipped, OK. Live SW 2026 `RevisionNumber` 34.3.2 assembled Big Red permissive 136/71 and synthetic `se2cad name probe`. Distinct assessment [below](#qualitysecurity-assessment-s2c-1241). |
| S2C-13.1.1 | PLANNED | |
| S2C-13.2.1 | PLANNED | |
| S2C-14.1.1 | PLANNED | |
| S2C-14.2.1 | PLANNED | |
| S2C-15.1.1 | PLANNED | |
| S2C-15.2.1 | PLANNED | |
| S2C-15.3.1 | PLANNED | |
| S2C-15.4.1 | PLANNED | |

## Session history

### 2026-09-10 — S2C-11.9.1 QUALIFIED

Human-authorized ASCII SDK-FBX conversion support after S2C-11.8.1 was QUALIFIED and after the human postponed Small Grid. Did not start S2C-13.1.1. Did not start Small Grid, multi-cell placement, CubeTopology expansion, OBJ export, or a general-purpose FBX framework. Did not redesign the S2C-11.8.1 runtime vanilla resolver. Did not invent a later unit. Did not commit, tag, or push. Did not commit Keen FBX or derived SLDPRT. Official `Conveyor.FBX` and `Gyroscope.FBX` hashes were unchanged after the live runs.

This extends the already-qualified demand-driven SDK-mesh builder. Runtime vanilla resolution remains the S2C-11.8.1 architecture. Support is still granted only after exact vanilla identity, primary Model, contained SDK source, recognized source format, available conversion path, and downstream builder contract. Arbitrary text named `.fbx` stays unresolved. Binary FBX is not routed through ASCII normalization.

Inspection of operator-local official sources (not modified):

| Identity | Definition | Model | SDK FBX | Format |
| --- | --- | --- | --- | --- |
| `LargeBlockConveyor` | Large 1×1×1 TriangleMesh | `Models\Cubes\Large\conveyor.mwm` | `Models\Cubes\large\Conveyor.FBX` | ASCII 7.2.0 / 6,674,173 bytes / SHA-256 `367deea7f97e8229677f882beda8435869ec218fe41eddd27260bd7b1d7665f1` |
| `LargeBlockGyro` | Large 1×1×1 TriangleMesh | `Models\Cubes\Large\gyroscope.mwm` | `Models\Cubes\large\Gyroscope.FBX` | ASCII 7.2.0 / 6,642,613 bytes / SHA-256 `19dbf593f03cc5d38f9053cfc8cad9f984da0deb7ed958c4208e3f5317927c82` |

Blender 5.2 `import_scene.fbx` rejects ASCII (`ASCII FBX files are not supported`). No other already-installed automatable importer was present. Chosen path: bounded ASCII FBX 7.x node-tree transcoder → mesh-preserving binary FBX 7200 under gitignored generated work → existing Blender binary import and Rx+90° / ×1000 recipe. Detection: prefix `Kaydara FBX Binary` is binary; otherwise UTF-8 text must start as `FBXHeaderExtension` / `FBX` and parse as mesh-bearing FBX 7.1–7.4 (32 MB / 200k nodes / depth 40 / 2M array values). Intermediate files never overwrite the official SDK FBX and must stay under the generated root.

Gyro is a static completed official primary model (14 Geometry / 15 Model in source). No animation or mechanical-subpart architecture was added.

Ordinary verification excluding untracked Small Grid WIP: `.\.venv\Scripts\python.exe` suite 577 tests, 11 skipped, OK.

Live operator roots (not hard-coded in tracked production code): `SE2CAD_GAME_ROOT=C:\SE2CAD-SE\Game\Content`, `SE2CAD_SDK_ROOT=C:\SE2CAD-SE\ModSDK\OriginalContent`, `SE2CAD_BLENDER_EXE` Blender 5.2. Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count 0 before and after targeted and Big Red runs.

Targeted probe `generated/s2c-11.9.1-probe`: armor + packaged thrust + two `LargeBlockConveyor` + one `LargeBlockGyro`. Conveyor/Gyro were not packaged catalog entries. First generation (~193 s) wrote four parts; the two Conveyor instances shared `vanilla_lg_1x1x1_large_block_conveyor.SLDPRT`. Second run (~33 s) generated `()` and reused all four. Assembly `se2cad-1191-probe.SLDASM` saved and reopened (5 components). No modal SolidWorks warning required interaction.

Big Red before (after S2C-11.8.1): 136 / supported 115 / unknown 21 / unsupported 0 / fillers 21.

Big Red after, `generated/s2c-11.9.1-bigred`: 136 / supported 126 / unknown 10 / unsupported 0 / fillers 10. Auto-resolved 15 unique identities / 45 instances, including newly real `LargeBlockConveyor` ×9 and `LargeBlockGyro` ×2. Completing assemble reused already-written Conveyor/Gyro/battery/connector/cockpit/thrust/armor/filler and generated the remaining 13 identities (~657 s). Second assemble (~289 s) generated `()` and reused all 21 geometry IDs. Derived filename `Big_Red+ffe1ed5b9381.SLDASM`. 136 components.

Reopened envelopes (metres): Conveyor ≈ 2.54×3.76×2.54, center Y ≈ 0.64 m; Gyro ≈ 2.50×2.25×2.50; FrontLight ≈ 2.50 cube; packaged thrust ≈ 2.59×2.59×2.48. Shared recipe Rx+90° / ×1000 only. No per-instance Conveyor/Gyro assembly correction. Surrounding armor/thruster/light identities reused existing parts.

Remaining fillers are only the known multi-cell identities: `LargeBlockLandingGear` 4 (1×2×3), `LargeBlockLargeHydrogenThrust` 3 (3×3×3), `LargeHydrogenTank` 1 (3×3×3), `LargeBlockRadioAntenna` 1 (1×6×2), `LargeOreDetector` 1 (1×1×2).

Verified remediations during live qualification:

- Blender can exit 0 after a script exception. Host requires the STL, surfaces `SE2CAD_BLENDER_SCRIPT_FAILED` / traceback / `{report}.error.txt`, and does not trust exit code alone.
- Unconditional Blender `normals_make_consistent` on binary `Light.FBX` left SolidWorks `LoadFile2` blocked with an empty document and no visible modal. Repair is now opt-in `--repair-normals` and is requested only for ASCII-normalized sources. Binary FrontLight then imported unattended (4,519,674-byte part).
- A hung `LoadFile2` leaked an exclusive lock on the work STL after `CloseDoc`. Conversion now allocates a writable work name by exclusive create, and `cleanup_work_dir` ignores locked leftovers instead of failing a later generate.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Packaged catalog | 9 entries unchanged; no runtime identities persisted |
| `all_library_records()` | still 8 native armor |
| Leftover set | unchanged; `Slope2Base` only leftover |
| Official ASCII FBX | Conveyor/Gyro SHA-256 unchanged; sources not written |
| Big Red parse / preflight | 136 blocks; supported 126 / unknown 10 / unsupported 0 |
| Big Red permissive policy | 136 IR instances; 10 fillers |
| Newly real identities | Conveyor 9 and Gyro 2 share one part each |
| Session hygiene | `started_application` False; leftover document count 0; revision 34.3.2 |
| Generated artifacts | gitignored `generated/s2c-11.9.1-probe/` and `generated/s2c-11.9.1-bigred/` |

No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Distinct assessment [below](#qualitysecurity-assessment-s2c-1191).

### 2026-09-10 — S2C-11.8.1 QUALIFIED

Human-authorized demand-driven vanilla TriangleMesh resolution after S2C-11.7.1 was QUALIFIED and after the human postponed Small Grid. Did not start S2C-13.1.1. Did not start Small Grid, multi-cell placement, CubeTopology expansion, a whole vanilla catalog, or OBJ export. Did not invent a later unit. Did not commit, tag, or push. Did not commit Keen FBX or derived SLDPRT.

S2C-11.7.1 proved the first SDK-FBX builder for the packaged `LargeBlockSmallHydrogenThrust` bind. S2C-11.8.1 generalizes source resolution: catalog-unknown Large Grid 1×1×1 TriangleMesh identities may receive a transient runtime bind. The packaged catalog is unchanged (9 entries). `all_library_records()` remains 8 native armor. Leftover set is unchanged. Runtime geometry IDs use `vanilla_lg_1x1x1_*`. `chamfer_capable` is false. Policy order is packaged record, else eligible vanilla resolution, else unknown/unsupported. A runtime-supported builder failure does not become filler.

Targeted CubeBlocks lookup indexes operator `Data/CubeBlocks` `*.sbc` once per game-content root and skips empty-SubtypeId siblings, so Logistics 1×1×1 definitions can be recovered without a whole-file parser rewrite. Eligibility requires CubeSize Large, size 1×1×1, TriangleMesh, one primary Model, no Subparts, and a contained official binary SDK FBX. ASCII FBX is unresolved, not supported.

Ordinary verification excluding untracked Small Grid WIP: `.\.venv\Scripts\python.exe` suite 541 tests, 11 skipped, OK.

Live operator roots (not hard-coded in tracked production code): `SE2CAD_GAME_ROOT=C:\SE2CAD-SE\Game\Content`, `SE2CAD_SDK_ROOT=C:\SE2CAD-SE\ModSDK\OriginalContent`, `SE2CAD_BLENDER_EXE` Blender 5.2.1. Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count 0 before and after. Operator documents were not closed.

Targeted probe `generated/s2c-11.8.1-probe`: armor + packaged thrust + `LargeBlockFrontLight` + `LargeBlockBatteryBlock`. First generation wrote `vanilla_lg_1x1x1_large_block_front_light.SLDPRT` (4547427) and `vanilla_lg_1x1x1_large_block_battery_block.SLDPRT` (3458867). Two light instances shared one part with distinct colors (red vs blue). Reuse twice generated `()`. Transforms remained generic cell-center placements. Assembly `se2cad-1181-probe.SLDASM` saved and reopened (5 components).

Big Red before (after S2C-11.7.1): 136 / supported 81 / unknown 55 / unsupported 0 / fillers 55.

Big Red after, `generated/s2c-11.8.1-bigred` (~915 s generate, ~243 s reuse): 136 / supported 115 / unknown 21 / unsupported 0 / fillers 21. Auto-resolved 13 unique identities / 34 instances. Second assemble generated `()` and reused 19 geometry IDs. Derived filename `Big_Red+ffe1ed5b9381.SLDASM`. 136 components.

Auto-resolved: `LargeBlockFrontLight` 8, `LargeCameraBlock` 4, `LargeBlockSmallContainer` 4, `LargeBlockBatteryBlock` 2, `Connector` 2, `LargeSymbolB/D/E/G/I/R` 2 each, `LargeBlockCockpitIndustrial` 1, `LargeBlockRemoteControl` 1.

Remaining fillers: `LargeBlockConveyor` 9 (ASCII FBX), `LargeBlockGyro` 2 (ASCII FBX), `LargeBlockLandingGear` 4 (1×2×3), `LargeBlockLargeHydrogenThrust` 3 (3×3×3), `LargeHydrogenTank` 1 (3×3×3), `LargeBlockRadioAntenna` 1 (1×6×2), `LargeOreDetector` 1 (1×1×2).

Verified remediations: ASCII FBX is rejected before support grant; missing-STL errors now include Blender stderr; imported-mesh minimum envelope lowered from 1.0 m to 0.05 m so small 1×1×1 meshes are not treated as forgotten-scale defects.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Packaged catalog | 9 entries unchanged; no runtime identities persisted |
| `all_library_records()` | still 8 native armor |
| Leftover set | unchanged; `Slope2Base` only leftover |
| Big Red parse / preflight | 136 blocks; supported 115 / unknown 21 / unsupported 0 |
| Big Red permissive policy | 136 IR instances; 21 fillers |
| Session hygiene | `started_application` False; leftover document count 0; revision 34.3.2 |
| Generated artifacts | gitignored `generated/s2c-11.8.1-probe/` and `generated/s2c-11.8.1-bigred/` |

No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Distinct assessment [below](#qualitysecurity-assessment-s2c-1181).

### 2026-09-10 — S2C-11.7.1 QUALIFIED

Human-authorized single-identity SDK-FBX experiment after S2C-12.4.1 was QUALIFIED and after the human postponed Small Grid. Target is only `LargeBlockSmallHydrogenThrust`. Did not start S2C-13.1.1. Did not invent S2C-11.8.x, general SDK-mesh support, Small Grid conversion, multi-cell placement, other thrusters, OBJ export, or a whole-vanilla catalog. Did not commit, tag, or push. Did not commit Keen FBX or derived SLDPRT.

Classification of TriangleMesh remains long-tail. Packaged leftover metadata is unchanged: eight completed automatable armor identities and leftover `Slope2Base`. The ninth catalog entry is the authorized bind, not an automatable CubeTopology leftover.

Library: `SdkMeshRecipe` with official ModSDK stem `Models/Cubes/Large/HydrogenThrusterSmall`, `source_type=official_modsdk`, `apply_imported_object_transforms=True`, `additional_scale=1000.0`, `rotation_xyz_deg=(90,0,0)`, `chamfer_capable=False`. `all_library_records()` remains the eight native armor identities. Lookup registers the SDK record like filler. Library `*.py` still forbids a `.fbx` string.

Generation resolves the configured SDK root (`SE2CAD_SDK_ROOT` / `se2cad.local.json` `sdk_root`), contains `HydrogenThrusterSmall.fbx` (case-insensitive name), converts through a bounded Blender subprocess to STL under generated `_se2cad_sdk_work/`, imports with SolidWorks `LoadFile2` then `ActiveDoc`, saves `{geometry_id}.SLDPRT`, closes by name, and reopens. Blender already applies Keen `RescaleFactor=0.01`; the recipe does not apply 0.01 again. Recipe Rx +90° maps imported +Y (nozzle) onto SE2CAD +Z (Backward). STL numbers are millimetres so `additional_scale=1000` yields a ~2.59 m envelope in SolidWorks. Fail closed on builder failure; no silent filler. `materialize.py` and `assemble.py` do not mention `SE2CAD_SDK_ROOT` or `OriginalContent`.

Ordinary verification excluding untracked Small Grid WIP: `.\.venv\Scripts\python.exe` suite 526 tests, 11 skipped, OK.

Live operator root `SE2CAD_SDK_ROOT=C:\SE2CAD-SE\ModSDK\OriginalContent` (not hard-coded in tracked production code). Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count 0 before and after. Operator documents were not closed.

Minimal probe `generated/s2c-11.7.1-min-probe`: armor + thrust, 2 components, generate then reuse, 85.179 s. Transforms remained generic (`Forward=Down`, `Up=Forward` → 2.5 m translation).

Big Red first assemble `generated/s2c-11.7.1-bigred` (~236 s): 136 blocks; preflight supported 81 / unknown 55 / unsupported 0; permissive fillers 55; IR 136. Generated four armor + filler + `large_block_small_hydrogen_thrust`. 16 thrust instances all used `large_block_small_hydrogen_thrust.SLDPRT` (~4385751 bytes). Derived filename `Big_Red+ffe1ed5b9381.SLDASM`. `generic_transforms` True. Nine orientations among the 16 thrusters: `(Backward,Down)`, `(Backward,Up)`, `(Down,Left)`, `(Forward,Down)`, `(Forward,Left)`, `(Left,Backward)`, `(Right,Forward)`, `(Up,Forward)`, `(Up,Right)`.

Big Red reuse (~152 s): generated `()`; reused armor + thrust + filler; 136 components.

Verified remediations during live qualification: on-disk extension `.FBX` compared case-insensitively; `InsertFromFile2` absent on SW 2026 late-bound COM; `LoadFile4` type-mismatch replaced by `LoadFile2` + `ActiveDoc`; missing ×1000 produced a ~0.00259 m envelope and was corrected; `OpenDoc` could return a stale tiny leftover, so generation now `close_named` before import/reopen and uses a fresh generated work root.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Packaged catalog | 9 entries; eight armor unchanged; one authorized thrust bind |
| `all_library_records()` | still 8 native armor |
| Leftover set | unchanged; `Slope2Base` only leftover |
| Big Red parse / preflight | 136 blocks; supported 81 / unknown 55 / unsupported 0 |
| Big Red permissive policy | 136 IR instances; 55 fillers |
| Thruster instances | 16 of one reusable `large_block_small_hydrogen_thrust.SLDPRT` |
| Session hygiene | `started_application` False; leftover document count 0; revision 34.3.2 |
| Generated artifacts | gitignored `generated/s2c-11.7.1-min-probe/` and `generated/s2c-11.7.1-bigred/` |

No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Distinct assessment [below](#qualitysecurity-assessment-s2c-1171).

### 2026-09-10 — S2C-12.4.1 QUALIFIED

Human-authorized compatibility amendment and bounded implementation after S2C-12.3.1 was QUALIFIED. Discovered by the Big Red permissive assembly probe: parse/preflight/policy and demand-driven materialization succeeded, then `AssemblyIdentityError: cannot derive a safe assembly filename from identity 'Big Red'`. Did not start S2C-13.1.1. Did not invent Small Grid conversion, geometry-family expansion, FBX/MWM/OBJ import, catalog support, or later units. Did not commit, tag, or push.

Scope is filename derivation only. It grants no new block or CAD support. Universal vanilla compatibility is not claimed. Small Grid remains postponed.

Inspection before the change: ShipBlueprint `Id/@Subtype` is stored as `identity_subtype` through parser, IR, preflight, statistics, and policy. `logical_assembly_filename` required that same string to match `^[A-Za-z0-9][A-Za-z0-9._-]*$`, so identity validation and filename validation were one rule. `contained_destination` already rejected separators and root escape. No reusable slug helper existed; component-name subtype validation was left untouched. Big Red's logical identity is `Big Red`; its grid `DisplayName` is `Kolyma` and is not used for the assembly filename.

Implementation: already-safe identities keep their current stem (`se2cad-test1.SLDASM`). Other identities keep the logical value and receive `{readable}+{sha256-utf8[:12]}.SLDASM`. The `+` marker cannot appear in a passthrough stem, so `Big Red` and `Big_Red` cannot silently share a file. `contained_destination` remains the containment authority.

`python -m se2cad.solidworks.assemble C:\SE-blueprints\bigred_bp.sbc --policy permissive` with `SE2CAD_GENERATED_ROOT=generated/s2c-12.4.1-probe` completed. CLI: `Big Red -> ...\Big_Red+ffe1ed5b9381.SLDASM components=136`. Base parts generated: `large_armor_block`, `large_armor_slope`, `large_armor_corner`, `large_armor_corner_inv`, `se2cad_unknown_filler`. Substituted geometry `se2cad_unknown_filler` (71 IR fillers). Save and reopen succeeded.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count 0 before and after. Operator documents were not closed.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration.SolidWorksIntegrationTests.test_spaced_assembly_identity_saves_derived_filename -v` — 1 test, OK, 5.328 s.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Logical identity | `Big Red` on parse, IR, policy, and `GeneratedAssembly.identity` |
| Derived filename | `Big_Red+ffe1ed5b9381.SLDASM` (160448) |
| Big Red parse / preflight | 136 blocks; supported 65 / unknown 71 / unsupported 0 |
| Big Red permissive policy | 136 IR instances; 71 fillers |
| Big Red assemble | 136 reopened components; materialization generated the four armor parts plus filler |
| Session hygiene | `started_application` False; leftover document count 0; revision 34.3.2 |
| Generated artifacts | gitignored `generated/s2c-12.4.1-probe/` |

Ordinary verification excluding untracked Small Grid WIP: `.\.venv\Scripts\python.exe` suite 511 tests, 11 skipped, 1.922 s, OK. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-10 — S2C-12.3.1 QUALIFIED

Human-authorized compatibility amendment and bounded implementation after S2C-11.6.1 was QUALIFIED. Motivated by Big Red failing at `CubeBlocks[1]` with `UnsupportedBlueprintError` for `xsi:type='MyObjectBuilder_Thrust'` before policy. Did not start S2C-13.1.1. Did not invent Small Grid conversion, geometry-family expansion, FBX/MWM/OBJ import, catalog support, or later units. Did not commit, tag, or push.

Scope is parser compatibility only. It grants no new geometry support. Universal vanilla compatibility is not claimed. Small Grid remains postponed.

Parser rule before: `CubeBlocks` children had to be element `MyObjectBuilder_CubeBlock`, and a present `xsi:type` had to equal that same literal. Parser rule after: the element must still be `MyObjectBuilder_CubeBlock`; a present `xsi:type` must be a Keen `MyObjectBuilder_*` identifier (`^MyObjectBuilder_[A-Za-z][A-Za-z0-9_]*$`); omitted `xsi:type` still means `MyObjectBuilder_CubeBlock`. Existing field fail-closed rules are unchanged. `ParsedBlock.object_builder_type` retains the token; `subtype_id` remains the catalog key; IR/`geometry_id` are not contaminated.

Read-only Big Red inspection (`c:\SE-blueprints\bigred_bp.sbc`, 141422 bytes, unmodified): one Large Grid, one `CubeBlocks`, 136 blocks, all element `MyObjectBuilder_CubeBlock`, no empty `SubtypeName`, no `SubBlocks`/`MultiBlock*`, no second grid.

| `xsi:type` | Count |
| --- | --- |
| `MyObjectBuilder_CubeBlock` | 77 |
| `MyObjectBuilder_Thrust` | 19 |
| `MyObjectBuilder_Conveyor` | 9 |
| `MyObjectBuilder_ReflectorLight` | 8 |
| `MyObjectBuilder_LandingGear` | 4 |
| `MyObjectBuilder_CameraBlock` | 4 |
| `MyObjectBuilder_CargoContainer` | 4 |
| `MyObjectBuilder_BatteryBlock` | 2 |
| `MyObjectBuilder_ShipConnector` | 2 |
| `MyObjectBuilder_Gyro` | 2 |
| `MyObjectBuilder_OxygenTank` | 1 |
| `MyObjectBuilder_Cockpit` | 1 |
| `MyObjectBuilder_RadioAntenna` | 1 |
| `MyObjectBuilder_RemoteControl` | 1 |
| `MyObjectBuilder_OreDetector` | 1 |

Parse completed. Preflight: 136 blocks, supported 65 (24/21/12/8 light armor), unknown 71, unsupported 0. CubeBlocks[1] is now `LargeBlockSmallHydrogenThrust` / unknown, not a parser failure. Strict refuses 71 unknown. Permissive emits 136 IR instances, filler_count 71, real parts for the four supported armor identities.

`python -m se2cad.solidworks.assemble c:\SE-blueprints\bigred_bp.sbc --policy permissive` with `SE2CAD_GENERATED_ROOT=generated/s2c-12.3.1-probe` reached demand-driven materialization of `large_armor_block.SLDPRT` (58728), `large_armor_slope.SLDPRT` (60527), `large_armor_corner.SLDPRT` (70257), `large_armor_corner_inv.SLDPRT` (74678), and `se2cad_unknown_filler.SLDPRT` (59095), then failed closed with `AssemblyIdentityError: cannot derive a safe assembly filename from identity 'Big Red'`. That space-in-identity filename rule is an independent out-of-scope blocker. It was not widened.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Operator documents were not closed. Post-run `GetDocumentCount` 0.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration.SolidWorksIntegrationTests.test_functional_object_builder_reaches_permissive_filler -v` — 1 test, OK, 6.711 s after an order-independent reopen assertion fix.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Big Red parse / preflight | 136 blocks; 15 builder types; supported 65 / unknown 71 |
| Big Red permissive policy | 136 IR instances; 71 fillers; armor keeps real `geometry_id` values |
| Big Red assemble | policy and materialization reached; blocked on `'Big Red'` filename |
| Synthetic live assemble | `se2cad-ob-probe.SLDASM` (60292): armor part + filler at IR pose for `MyObjectBuilder_Thrust` |
| Session hygiene | `started_application` False; leftover document count 0; revision 34.3.2 |
| Generated artifacts | gitignored `generated/s2c-12.3.1-probe/` |

Ordinary verification excluding untracked Small Grid WIP: `.\.venv\Scripts\python.exe` suite 502 tests, 10 skipped, 0.830 s, OK. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-10 — S2C-11.6.1 QUALIFIED

Human-authorized sequencing amendment and bounded implementation after S2C-12.2.1 and S2C-10.4.1 were QUALIFIED. Did not start S2C-13.1.1. Did not invent Small Grid conversion, symmetry, print-shell, mesh import, or later M11 units. Did not expand the packaged catalog, stamp automatable remainder, bind hidden `LargeRoundArmor_*` aliases, or change M12 policy semantics. Did not commit, tag, or push.

A read-only survey of the copied SE installation motivated the narrow scope: 1465 unique vanilla SubtypeIds observed (903 Large Grid, 562 Small Grid); packaged catalog still contains 8 identities; only those 8 are safe to materialize with qualified constructions; three apparent extra Slope/Corner/InvCorner candidates are hidden round-armor aliases; 64 Large Grid CubeTopology identities remain automatable-in-principle without qualified constructions. Runtime conversion still does not scan `C:\SE2CAD-SE\Game\Content\` or `C:\SE2CAD-SE\ModSDK\OriginalContent\`.

Assembly now demand-drives already-qualified untreated `{geometry_id}.SLDPRT` files through `se2cad.solidworks.materialize`. Existing files are reused. Missing identities generate at most once per assembly via the existing `generate_canonical_parts` path. Identities without a qualified builder fail closed and are not replaced by the filler. Chamfer assembly ensures the untreated base first, then the exact size-specific `{geometry_id}_chamfer_{size}mm.SLDPRT` sibling. Explicit `python -m se2cad.solidworks` still defaults to the original four. `GeneratedAssembly.materialization_report` distinguishes untreated reuse/generation, treated reuse/generation, and existing policy substitution.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). `SE2CAD_GENERATED_ROOT=generated`. Operator documents were not closed. Live probe used gitignored `generated/s2c-11.6.1-probe/`. Post-run `GetDocumentCount` 0.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration.SolidWorksIntegrationTests.test_demand_driven_base_parts_are_generated_and_reused -v` — 1 test, OK, 65.541 s.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Missing base generated | empty probe root; `se2cad-base-lazy` created `large_armor_block.SLDPRT` (59252) and consumed it |
| Reuse | second assemble left that SHA-256 unchanged (`b3f6938a…`) and reported `reused=large_armor_block` |
| Demand only | two-geometry assemble added `large_armor_slope.SLDPRT` (60750); no corner-inv, no heavy-armor, no chamfer siblings yet |
| Chamfer bootstrap | missing `large_armor_corner.SLDPRT` then `large_armor_corner_chamfer_50mm.SLDPRT` (78967); assembly consumed the 50 mm sibling; no generic `*_chamfer.SLDPRT` |
| Permissive filler | `se2cad-base-filler.SLDASM` used distinct `se2cad_unknown_filler.SLDPRT` (58460) |
| Session hygiene | `started_application` False; leftover document count 0; revision 34.3.2 before/after |
| Generated artifacts | gitignored `generated/s2c-11.6.1-probe/`; `git check-ignore` reports the new parts and assemblies |

Ordinary verification excluding untracked Small Grid WIP: `.\.venv\Scripts\python.exe` suite 479 tests, 9 skipped, 0.779 s, OK. Untracked `tests/test_small_grid.py` remains out of scope and was not executed as this unit. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-10.4.1 QUALIFIED

Human-authorized insertion after S2C-12.2.1 was QUALIFIED and before S2C-13.1.1. Did not start S2C-13.1.1. Did not invent Small Grid conversion, symmetry, or print-shell. Did not change parser, catalog identity, IR transforms, component naming, appearance, unknown-block policy, filler semantics, or M11 recipe selection. Did not add algorithm-version compatibility. Did not commit, tag, or push.

Chamfer size is configurable. `--edge-treatment chamfer` without `--chamfer-mm` remains 50 mm. Valid range is 5–250 mm inclusive; NaN/Inf and out-of-range values fail closed and are not clamped. `--chamfer-mm` is valid only with chamfer. Treated artifact identity is `{geometry_id}_chamfer_{size}mm.SLDPRT` via one shared `treated_artifact_key`. Component names stay on existing IR/SE data. Assembly generates only demanded chamfer-capable variants and reuses an exact existing file. `LibraryRecord.chamfer_capable` is an explicit CAD/library flag: qualified Box/Slope/Corner/InvCorner records are true; the designated filler is false. Non-capable geometry uses the untreated part and is listed in `AssemblyTreatmentReport`. Capable generation failure does not fall back. Explicit `python -m se2cad.solidworks --edge-treatment chamfer` still writes only the original four identities.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). `SE2CAD_GENERATED_ROOT=generated`. Operator documents were not closed. `GetDocumentCount` is a late-bound property, not a method.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration.SolidWorksIntegrationTests.test_configurable_chamfer_is_demand_driven_and_reusable -v` — 1 test, OK, 34.418 s after remediations. Earlier same-class run: 8 tests, 1 ERROR (`GetDocumentCount()`), then 7 OK including treated 50 mm generate/assemble, 291.978 s. A later discover with the integration flag left set ran all 8 live tests — 458 tests, OK, 328.852 s.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Distinct sizes | `large_armor_block_chamfer_50mm.SLDPRT` (76055) and `large_armor_block_chamfer_75mm.SLDPRT` (77057); SHA-256 differ |
| Demand / reuse | 75 mm assemble created/consumed the exact 75 mm part; second 75 mm request left that file hash unchanged; no `large_heavy_block_*_chamfer_75mm.SLDPRT` |
| Untreated parts | Probe asserted untreated `large_armor_block.SLDPRT` hash unchanged across treated generate/assemble. Later default fixture assemble in `test_treated_assembly_consumes_treated_siblings` used `{geometry_id}.SLDPRT` |
| Fallback | Permissive two-block probe: armor used `large_armor_block_chamfer_75mm.SLDPRT`; unknown subtype used `se2cad_unknown_filler.SLDPRT`; report `treated=1` `untreated_fallback=1`; no filler chamfer sibling |
| Session hygiene | Live probe `GetDocumentCount` equal before/after; `started_application` False |
| Generated artifacts | gitignored `generated/`; `git check-ignore` reports the new size-specific parts and `se2cad-chamfer-75.SLDASM` / `se2cad-chamfer-fallback.SLDASM` |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 458 tests, 8 skipped, 0.709 s, OK. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-12.2.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-13.1.1. Did not invent Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change M11 recipe kinds or leftover metadata. Did not alias unknown subtypes to `large_armor_block`. Did not default assemble or `convert_blueprint` to permissive. Did not commit, tag, or push.

Conversion policy is CAD-neutral in `se2cad.policy`. Strict is the default: unknown or unsupported blocks raise `ConversionRefusedError` with preflight counts and do not emit a partial IR or assembly as success. Permissive must be requested. It converts every parsed block, assigning designated filler `geometry_id` `se2cad_unknown_filler` while preserving original subtype, appearance, `Min`, Forward, and Up. Filler `support_status` and `recipe_kind` on those IR blocks remain `unsupported`. `build_canonical_blueprint` remains the catalog-resolve path and still fail-closes on unknown subtypes. Assembly generation and `python -m se2cad.solidworks.assemble` use policy and default to strict. Operator entry `python -m se2cad.policy <blueprint.sbc> [--policy strict|permissive]` exits 0 only when conversion produced an IR.

The filler is a library-only identity: smaller axis-aligned box (`FILLER_HALF_EXTENT_MM` = pitch/5), observed topology `Filler`, filename `se2cad_unknown_filler.SLDPRT`. It is not a catalog cube-block subtype and is not in `all_library_records()`. Default part generation remains the original four.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count after the live run was 0. `SE2CAD_GENERATED_ROOT=generated`.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration.SolidWorksIntegrationTests.test_permissive_filler_assembly_keeps_pose_and_distinct_part -v` — 1 test, OK, 14.206 s. A later `unittest discover -s tests -v` with the same integration flag left set ran all 7 live integration tests including that probe plus the qualified fixture assemble path — 428 tests, 0 skipped, 257.695 s, OK.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Permissive probe | 2 components: `large_armor_block.SLDPRT` + `se2cad_unknown_filler.SLDPRT`; filler subtype `NotACatalogSubtype`; translation `(2.5, 0, 0)` m; Down/Forward axes match IR |
| Generated artifacts | gitignored `generated/`; `se2cad_unknown_filler.SLDPRT` (58150), `se2cad-filler-probe.SLDASM` (59883) |
| Operator documents | leftover document count 0 |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 428 tests, 7 skipped, 0.692 s, OK. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-12.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-12.2.1. Did not invent filler substitution, Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change runtime `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` / assembly generation. Did not change M11 recipe kinds or leftover metadata. Did not generate SolidWorks parts. Did not commit, tag, or push.

Preflight is CAD-neutral diagnosis in `se2cad.preflight`. Each parsed block reports subtype, `Min`, catalog outcome, geometry support, and appearance support. `supported`, `unsupported`, and `unknown` are distinct. Unknown is not aliased to a supported armor type. `all_supported` is the later strict-versus-permissive input; producing a report is not conversion. Operator entry `python -m se2cad.preflight <blueprint.sbc>` exits 0 when a report is produced, including when `all_supported` is false, and always prints `conversion_performed=false`. Malformed documents fail closed through the existing parser.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 404 tests, 6 skipped, 0.750 s, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. QUALIFIED from automated tests as the unit allows. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-11.5.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-12.1.1. Did not invent preflight, Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change runtime `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` / default `generate_canonical_parts()` to scan an install or to generate every automatable vanilla block. Did not assign `sdk_mesh_direct` or `sdk_mesh_manifold`. Did not force Slope2Base or other residual topologies through one construction. Did not claim 100% vanilla coverage. Did not generate additional SolidWorks parts. Did not commit, tag, or push.

Leftover handling is explicit and durable in `src/se2cad/catalog/leftover_set.json`. Failed generation, unclassified identities, and unsupported recipe kinds cannot appear as successful supported conversion. The classified automatable remainder with a known construction is already the packaged eight identities; `stamp_automatable_remainder` returned empty. Residual automatable CubeTopology `Slope2Base` stays listed as `missing_construction`. Coverage claim is `not_universal_vanilla`.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 385 tests, 6 skipped, 0.617 s, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. QUALIFIED from automated tests as the unit allows. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-11.4.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-11.5.1. Did not invent preflight, Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change runtime `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` / default `generate_canonical_parts()` to scan an install or to generate every automatable vanilla block. Did not assign `sdk_mesh_direct` or `sdk_mesh_manifold`. Did not force Slope2Base or other unknown topologies through one construction. Did not commit, tag, or push.

CubeTopology tokens `Box`, `Slope`, `Corner`, and `InvCorner` stamp the qualified native constructions onto any valid SE2CAD `geometry_id`. The representative automatable subset beyond the original four is `large_heavy_block_armor_block`, `large_heavy_block_armor_slope`, `large_heavy_block_armor_corner`, and `large_heavy_block_armor_corner_inv`. Those packaged identities are now `native_procedural` / `supported`. Default part generation still names the original four. Other automatable-class topologies fail closed with `UnsupportedTopologyError`.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count was 0 before the live run and 0 after. `SE2CAD_GENERATED_ROOT=generated`.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 6 tests, OK, 566.041 s.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Representative parts | `large_heavy_block_armor_block.SLDPRT` (59061), `large_heavy_block_armor_slope.SLDPRT` (60364), `large_heavy_block_armor_corner.SLDPRT` (69837), `large_heavy_block_armor_corner_inv.SLDPRT` (75092) |
| Validation | one solid body, zero sheet bodies, volumes match the matching original-four recipes (15.625 / 7.8125 / 2.6041667 / 13.020833 m³) |
| Default generate | still the original four `large_armor_*.SLDPRT` |
| Generated artifacts | gitignored `generated/`; `git check-ignore` reports the four heavy parts |
| Operator documents | none closed; leftover document count 0 |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 367 tests, 6 skipped, 1.054 s, OK. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-11.3.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-11.4.1. Did not invent automated generation, preflight, Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change runtime `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` / assembly generation to scan an install. Did not mark expanded identities `supported`. Did not add library recipes or generate parts. Did not assign `sdk_mesh_direct` or `sdk_mesh_manifold`. Did not commit, tag, or push.

CubeTopology-class `CubeBlock` armor is classified `native_procedural` from observed facts. TriangleMesh, missing CubeTopology, unusual type/topology, and Small Grid are long-tail `unsupported` with distinct exception reasons. Support is never granted by selection. Existing supported original-four decisions are preserved. Exception records are queryable and cannot report as supported.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 355 tests, 5 skipped, 0.565 s, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. QUALIFIED from automated tests as the unit allows. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-11.2.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-11.3.1. Did not invent recipe selection, preflight, Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change runtime `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` / assembly generation to scan an install. Did not mark expanded identities `supported`. Did not add library recipes or generate parts. Did not commit, tag, or push.

Packaged catalog schema is 2. `cube_topology` may be omitted. Small Grid `cube_size` is rejected at load. `supported` requires a recipe kind other than `unsupported`. `expand_catalog_identities` preserves existing SE2CAD decisions, skips Small Grid, and records new Large Grid identities as `unsupported`. Distinct subtypes keep distinct `geometry_id` values. No machine paths or mesh references are stored.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 338 tests, 5 skipped, 0.577 s, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No live game/SDK tree was used; QUALIFIED from automated tests as the unit allows. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-10.3.1 QUALIFIED

Executed the next unit named by STATE: live SolidWorks qualification only. Did not re-implement assembly selection. Did not start S2C-11.2.1. Did not invent catalog identity expansion, recipe selection, preflight, Small Grid, symmetry, or print-shell. Did not close operator documents. Did not write to `C:\SE2CAD-generated\`. Did not commit, tag, or push.

Attached running SW 2026 `RevisionNumber` 34.3.2 (`GetActiveObject`, `started_application` False). Document count was 0 before the live run and 0 after. `SE2CAD_GENERATED_ROOT=generated`.

Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 5 tests, OK, 242.837 s.

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Treated assembly | 24 components; filenames `{geometry_id}_chamfer.SLDPRT`; `geometry_id` / names / `(R, t)` / default appearance unchanged; `_chamfer` not in component names |
| Untreated assemble after | 24 `{geometry_id}.SLDPRT`; same identity `se2cad-test1.SLDASM` overwritten as previously recorded residual |
| Untreated parts | SHA-256 unchanged across treated generate and treated assemble |
| Generated artifacts | gitignored `generated/`; `git check-ignore` reports parts and assemblies |
| Operator root | `C:\SE2CAD-generated\` mtimes unchanged (last write 11:54) |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 323 tests, 5 skipped, 0.531 s, OK. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-10.3.1 DEV-COMPLETE

Executed the next unit named by STATE. Did not start S2C-11.2.1. Did not invent catalog identity expansion, recipe selection, preflight, Small Grid, symmetry, or print-shell. Did not create a general CLI or UI. Did not bake `_chamfer` into catalog or IR identity. Did not change qualified `(R, t)`, component names, or per-instance appearance. Did not overwrite untreated `{geometry_id}.SLDPRT`. Did not commit, tag, or push.

Default `generate_assembly()` / `python -m se2cad.solidworks.assemble <blueprint.sbc>` still resolves untreated `{geometry_id}.SLDPRT`. Explicit `python -m se2cad.solidworks.assemble <blueprint.sbc> --edge-treatment chamfer` resolves treated siblings. Missing treated artifacts raise `MissingCanonicalPartError` and do not fall back to untreated files.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 323 tests, 5 skipped, 0.524 s, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. Live `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 5 tests, ERROR. Attached SW 2026 `RevisionNumber` 34.3.2 already had `large_armor_*.SLDPRT` and `se2cad-test1.SLDASM` open from `C:\SE2CAD-generated\` plus an untitled `Part1`. OpenDoc returned None / SaveAs returned false for same-named parts. Operator documents were not closed. Two leftover repo-`generated/` documents from the failed run were closed. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-10.3.1 inserted (human-authorized sequencing amendment)

Governance/planning amendment only. Did not implement S2C-10.3.1. Did not start S2C-11.2.1. Did not modify or undo QUALIFIED S2C-11.1.1. Did not modify production code or tests. Did not commit, tag, or push.

Human sequencing decision after discovery of the treated-part assembly-consumption gap: S2C-10.2.1 generates `{geometry_id}_chamfer.SLDPRT` siblings, but assembly still always inserts untreated `{geometry_id}.SLDPRT`. M11 had already started. S2C-11.1.1 was already QUALIFIED. S2C-11.2.1 had not started. The architect authorized inserting S2C-10.3.1 into M10 as the next unit, then resuming at S2C-11.2.1.

This does not rewrite history to imply M11 never started. S2C-10.1.1, S2C-10.2.1, and S2C-11.1.1 remain QUALIFIED with their original evidence. M10 now has three units. The program remains M7–M15.

### 2026-09-09 — S2C-11.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-11.2.1. Did not invent catalog identity expansion, recipe selection, preflight, Small Grid conversion, symmetry, or print-shell. Did not create a general CLI or UI. Did not change runtime `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` / assembly generation to scan an install. Did not copy meshes, FBX, MWM, or textures. Did not commit, tag, or push.

Discovery is a library-build evidence tool, not a converter stage. Install roots reuse the established env / uncommitted `se2cad.local.json` pattern: `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT` and JSON keys `game_root` / `sdk_root`. Shared local-config allowed keys now also include those roots so one `se2cad.local.json` can hold SolidWorks and discovery paths. Walks only `Content/Data/CubeBlocks` and `Data/CubeBlocks` `*.sbc` files. Records subtype, type, cube size, occupancy, topology tokens, and root-relative source. Small Grid and TriangleMesh identities are observed facts. `geometry_id` is not assigned.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 309 tests, 4 skipped, 0.996 s, OK. Fixture SHA-256 unchanged. No live game/SDK tree was present on this host; QUALIFIED from synthetic tests as the unit allows. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-10.2.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-11.1.1. Did not invent library expansion, preflight, Small Grid, symmetry, or print-shell. Did not create a general CLI or UI. Did not bake the treatment into `geometry_id`, catalog identity, recipes, or untreated canonical filenames. Did not add a second insert offset or change placement. Did not commit, tag, or push.

Mechanism is a sibling artifact, not a configuration on the untreated part and not a new CAD backend. Requested generation writes `{geometry_id}_chamfer.SLDPRT` under the configured generated root. Default `generate_canonical_parts()` and `python -m se2cad.solidworks` still write untreated `large_armor_*.SLDPRT`. Assembly placement still names those untreated files.

SolidWorks materialization is a local `InsertFeatureChamfer` after the qualified untreated construction. Live 34.3.2: published `swChamferEqualDistance` (16) inserts a no-op Chamfer feature; equal 50 mm face setback is `swChamferDistanceDistance` (2) with Width and OtherDist both 0.05 m, then `ForceRebuild3`. InvCorner’s three notch edges sit on the hypotenuse cut plane; including them returns None, so they are skipped (local chamfer of a live-concave edge). Measurables are recorded in [S2C-10.2.1 treated canonical parts](#s2c-1021-treated-canonical-parts).

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 283 tests, 4 skipped, 0.396 s, OK. `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 4 tests, OK (three existing tests 112.799 s on the first live pass; treated test OK in 43.961 s after the InvCorner filter). Fixture SHA-256 unchanged. Untreated part SHA-256 unchanged across treated generation. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-10.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-10.2.1. Did not invent library expansion, preflight, Small Grid, symmetry, or print-shell. Did not create a general CLI or UI. Did not generate treated SolidWorks parts. Did not bake the treatment into `geometry_id`, catalog identity, recipes, canonical part filenames, or part-generation plans. Did not add a second insert offset or change the qualified frame, cell envelope, or pitch. Did not commit, tag, or push.

The treatment is an operation on a closed mesh: `apply_edge_treatment` / `EDGE_TREATMENT_OFF` (default) / `EDGE_TREATMENT_CHAMFER`. Setback is `EDGE_TREATMENT_SETBACK_MM` (50 mm) along each incident face. Concave edges are not treated. `lookup_recipe` remains the untreated qualified solid. Measurables and the generic (non-ID) box are recorded in [S2C-10.1.1 edge-treatment contract](#s2c-1011-edge-treatment-contract).

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 267 tests, 3 skipped, 0.343 s, OK. Fixture SHA-256 unchanged. No SolidWorks treated-part generation. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-09 — S2C-9.2.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-10.1.1. Did not invent edges, library expansion, preflight, Small Grid, symmetry, or print-shell. Did not create a general CLI or UI. Did not bake color into `geometry_id`, recipes, catalog identity, canonical part filenames, or part-generation plans. Did not change omitted `Min` / `BlockOrientation` / `ColorMaskHSV` defaults. Did not commit, tag, or push.

Conversion is inside the SolidWorks package: Keen `HSVOffsetToHSV` deltas (`SATURATION_DELTA` 0.8, `VALUE_DELTA` 0.45 from the official wiki citing those methods), clamp S/V to `[0, 1]`, then standard HSV-to-RGB. Omitted `(0, -1, 0)` becomes display HSV `(0, 0, 0.45)` / RGB `(0.45, 0.45, 0.45)`. The assembly writer assigns 8-bit-truncated RGB as `IComponent2.MaterialPropertyValues` on the inserted component. `PlacedComponent` reports `geometry_applied` and `appearance_applied` independently. Default appearance does not fail the qualified fixture.

Conversion mapping is recorded in [S2C-9.2.1 appearance conversion](#s2c-921-appearance-conversion). This Windows host still has no local `VRage.Game.dll`; deltas are published-wiki plus current ModAPI method names.

Live SW 2026 `RevisionNumber` 34.3.2 (`SE2CAD_GENERATED_ROOT=generated`):

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Fixture assembly | `generated/se2cad-test1.SLDASM`; 24 default instance RGB `114/255` (0.45 truncated); names and transforms unchanged |
| Color assembly | `generated/se2cad-color1.SLDASM`; three `large_armor_block` instances: default gray, red `(1,0,0)`, blue `(0,0,1)` |
| Canonical parts | SHA-256 unchanged across the color assembly write; filenames remain `large_armor_*.SLDPRT` |
| MaterialPropertyValues | 8-bit truncation: written 0.45 reads back `114/255`; comparison allowance `1/255` |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 251 tests, 3 skipped, 0.271 s, OK. `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 3 tests, OK, 69.481 s after remediations. Generated artifacts stayed under `generated/` and are gitignored. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-08 — S2C-9.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-9.2.1. Did not invent SolidWorks appearance assignment, edges, library expansion, preflight, Small Grid, symmetry, or print-shell. Did not create a general CLI or UI. Did not bake color into `geometry_id`, recipes, catalog identity, or canonical part filenames. Did not change omitted `Min` / `BlockOrientation` defaults. Did not commit, tag, or push.

On-disk field is `ColorMaskHSV` (`SerializableVector3` attributes `x`/`y`/`z`). Omitted default is HSV-offset `(0.0, -1.0, 0.0)` (`DEFAULT_COLOR_MASK_HSV`). Parser records `color_serialized` and independently reportable `AppearanceSupport` (`default` vs `explicit`). IR copies those fields without reinterpretation. Malformed payloads fail closed; they do not invent the omitted default.

Omitted-color mapping evidence is recorded in [S2C-9.1.1 omitted-color mapping](#s2c-911-omitted-color-mapping). This Windows host has no local Space Engineers install; the default vector is from published Keen source plus current ModAPI, corroborated by the qualified fixture omitting `ColorMaskHSV` on all 24 blocks.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 233 tests, 2 skipped, 0.236 s, OK. Fixture SHA-256 unchanged. No SolidWorks appearance calls. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD.

### 2026-09-08 — S2C-8.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-9.1.1. Did not invent color, edges, library expansion, preflight, Small Grid, symmetry, or print-shell. Did not create a general CLI or UI. Did not change the qualified parser, catalog JSON, IR transform contract, recipes, or canonical part filenames. Did not commit, tag, or push.

Implemented `se2cad.ir.naming` as a CAD-neutral derived identifier: `{subtype}_x{X}_y{Y}_z{Z}_{Forward}_{Up}_{source_index}`. Unsafe subtype characters are rejected. `COMPONENT_NAME_MAX_LENGTH` is 80 with prefix truncation plus `_{source_index}`. Omitted and explicit identity Forward/Up produce the same name. `geometry_id` and filesystem paths are not encoded. The assembly writer applies the short name via `IComponent2.Name2` after `Select`. Official Name2 remarks plus live 34.3.2: set is a no-op while `swExtRefUpdateCompNames` (enum 18) is True, and an unselected assignment is also a no-op. The writer forces that toggle False from insert through SaveAs/reopen, then restores the prior value.

Acceptance-fixture names (SHA-256 unchanged; all 24 unique; max length 50):

| Cell | Name |
| --- | --- |
| `(0,0,0)` | `LargeBlockArmorBlock_x0_y0_z0_Forward_Up_0` |
| `(1,0,0)` | `LargeBlockArmorBlock_x1_y0_z0_Forward_Up_1` |
| `(0,0,-1)` Down/Forward | `LargeBlockArmorSlope_x0_y0_z-1_Down_Forward_14` |
| `(1,1,0)` Down/Right | `LargeBlockArmorSlope_x1_y1_z0_Down_Right_15` |
| `(5,2,-2)` | `LargeBlockArmorBlock_x5_y2_z-2_Forward_Up_23` |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 212 tests, 2 skipped, 0.250 s, OK. `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 2 tests, OK, 39.180 s. Generated artifacts stayed under `generated/` and are gitignored. Canonical part filenames remain `large_armor_*.SLDPRT`.

### 2026-09-08 — S2C-7.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-8.1.1. Did not invent a conversion policy, color, Small Grid, unknown-block filler, symmetry, print-shell, or library expansion. Did not create a general CLI or UI. Did not change the qualified parser, catalog, IR, transform, recipe, or SolidWorks contracts. Did not commit, tag, or push.

Implemented `se2cad.statistics` as a CAD-neutral derived report from parsed blueprint fields plus per-block catalog lookup. Unknown subtypes stay in block and subtype counts and are reported as unresolved; they are not assigned a `geometry_id` and are not dropped. Occupancy is unique `Min` cells versus the inclusive cell AABB. Millimetre size is cell span times `catalog.large_grid_cell_pitch_mm`. Narrow operator entry: `python -m se2cad.statistics <blueprint.sbc>`.

Acceptance-fixture statistics (SHA-256 unchanged):

| Check | Result |
| --- | --- |
| Identity | `se2cad-test1`; ShipBlueprint display U+E030 + `Kolyma`; grid `se2cad-test1`; Large |
| Blocks | 24; subtypes 9 / 2 / 1 / 12 (sorted names); geometry IDs 9 / 2 / 1 / 12 |
| Extents | x 0..5, y 0..2, z -2..1; size 15000 × 7500 × 10000 mm |
| Occupancy | 24 unique `Min` / 72 AABB cells; coverage `1/3` |
| Orientations | Forward/Up 15, Down/Forward 5, Down/Right 1, Forward/Right 1, Down/Left 1, Backward/Down 1 |
| Catalog | 24/24 resolved |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 198 tests, 2 skipped, 0.231 s, OK. Operator path printed the table above (U+E030 escaped as `\ue030` on cp1252). No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. No `src/` parser, catalog, IR, transform, library, or SolidWorks product edits.

### 2026-09-08 — M7–M15 program authorization QUALIFIED

Executed the human-authorized documentation/planning unit. Did not implement product features. Did not start S2C-7.1.1. Did not move cold-storage backlog into executable scope. Did not commit, tag, or push.

Created the current program charter and unit catalog. Preserved the completed initial M0–M6 program as historical. Updated STATE, process, onboarding, repository contract, ratchet, Cursor rules, architecture pointers, fixture spec pointer, fixtures README, and public README so a fresh session can select only the next approved unit from this file.

Verification: 154 local Markdown/MDC links resolve. `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 176 tests, 2 skipped, 0.262 s, OK. No `src/` or `tests/` product changes. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed `.sldprt`/`.sldasm`. One-off link-check script was not left in `tools/`.

### 2026-09-08 — S2C-6.1.1 QUALIFIED

Executed the next unit named by STATE. Did not invent a new implementation milestone, change the fixture, change the canonical frame, change the transform contract, change the qualified geometry recipes, introduce Space Engineers or ModSDK as a runtime dependency, change the Windows-local COM architecture, add remoting, or add a new major dependency. Did not commit, tag, push, or publish. Did not commit generated `.SLDPRT` or `.SLDASM`.

End-to-end wiring already existed (`resolve_recipes_from_blueprint` → `generate_canonical_parts` → `generate_assembly`). This unit added ordinary all-24 comparison tests, strengthened the live integration test to compare every reopened component to the packed IR, and recorded the comparison method beside the fixture specification.

Authoritative input remains `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc`. Expected pose is the qualified parser → catalog → S2C-3.1.1 IR. Space Engineers was not opened in this session; the intended SE object is the S2C-1.1.1-confirmed fixture. Comparison method:

| Layer | Allowance |
| --- | --- |
| Fixture SHA-256, parser/catalog/IR identities, integer `(R, t)` | Exact |
| Placement vs IR | Exact |
| SolidWorks `ArrayData` vs packed IR, and save/reopen | `BACKEND_LENGTH_TOLERANCE_M` = `1e-6` m |

Live evidence used exact 16-double equality for all 24 components (stricter than the recorded 1e-6 m allowance).

Operator path (`SE2CAD_GENERATED_ROOT=generated`, revision 34.3.2):

```
python -m se2cad.solidworks
python -m se2cad.solidworks.assemble fixtures/acceptance/four-block-armor-asymmetric/bp.sbc
```

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` (8967 bytes), unchanged |
| Grid | exactly one `Large` CubeGrid; identity `se2cad-test1` |
| Blocks | 24; subtypes 9 / 12 / 2 / 1; all 24 catalog-resolved; all 24 IR instances |
| Parts | `generated/large_armor_block.SLDPRT` (57975), `large_armor_slope.SLDPRT` (60630), `large_armor_corner.SLDPRT` (69464), `large_armor_corner_inv.SLDPRT` (75312); volumes 15.625 / 7.8125 / 2.6041667 / 13.020833 m³ |
| Assembly | `generated/se2cad-test1.SLDASM` (80542 bytes); `GetType` 2; 24 components |
| Geometry counts | `large_armor_block` 9, `large_armor_slope` 12, `large_armor_corner` 2, `large_armor_corner_inv` 1 |
| All 24 transforms | packed IR `ArrayData` match after save and after reopen; axes = qualified rotation columns |
| Distinct orientations | Forward/Up identity (15 omitted), Down/Forward (5), Down/Right (1), Forward/Right (1), Down/Left (1), Backward/Down (1) |
| Translations | `Min * 2.5` m with no half-cell; negative Z preserved (`(0,0,-1)` → `(0,0,-2.5)` m) |
| Mates | MateGroup empty; no `AddMate` |
| Root / Git | all five artifacts under `C:\Users\ken\Documents\se2cad\generated`; `git check-ignore` reports `/generated/` |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 176 tests, 2 skipped, 0.224 s, OK. `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 2 tests, OK, 42.569 s. Operator path then reproduced the four parts and the 24-component assembly. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed `.sldprt`/`.sldasm`.

### 2026-09-08 — S2C-5.1.1 QUALIFIED

Executed the next unit named by STATE. Did not start S2C-6.1.1. Did not commit, tag, push, or publish. Did not commit generated `.SLDPRT` or `.SLDASM`. Did not change the qualified IR transform contract, the canonical part frame, or the Windows-local COM/pywin32 stack. Did not introduce mates as a placement requirement or add remoting.

Implemented CAD-neutral placement (`placements_from_ir`) and SolidWorks `ArrayData` packing (`solidworks_arraydata`) from the qualified S2C-3.1.1 `(R, t)`. Assembly writer inserts pre-opened canonical parts with `AddComponent5`, unfixes the auto-fixed first component, writes `Transform2.ArrayData` as `VARIANT(VT_ARRAY|VT_R8, 16-tuple)`, and saves a native SLDASM under the configured generated root. Missing parts, unknown geometry IDs, unsafe assembly identities, path escapes, component substitution, and non-empty MateGroup children fail closed.

Official 2026 CreateTransform / ArrayData pages remain JS-rendered. Packing was taken from the published 16-double contract (X/Y/Z axis rows = component axes, translation metres, scale 1) plus live 34.3.2 CDispatch evidence. `IMathUtility.CreateTransform` server-faults on this late-bound session; a raw Python list write corrupts translation. Those calls are not used.

Live reopen evidence (`SE2CAD_GENERATED_ROOT=generated`, revision 34.3.2):

| Check | Result |
| --- | --- |
| Artifact | `generated/se2cad-test1.SLDASM` (80648 bytes after the post-remediation rerun) |
| `GetType` | 2 (`swDocASSEMBLY`) |
| Components | 24; geometry counts `large_armor_block` 9, `large_armor_slope` 12, `large_armor_corner` 2, `large_armor_corner_inv` 1 |
| `(0,0,0)` | identity rotation; translation `(0,0,0)` m; part `large_armor_block.SLDPRT` |
| `(1,0,0)` | translation `(2.5,0,0)` m |
| `(0,0,-1)` Down/Forward | axes = qualified rotation columns; translation `(0,0,-2.5)` m |
| `(1,1,0)` Down/Right | axes = qualified columns, not row-major; translation `(2.5,2.5,0)` m |
| Omitted orientations | 15 identity matrices |
| Save / close / reopen | Transform2 ArrayData unchanged |
| Mates | `GetMates` None; MateGroup folder empty; no `AddMate` |
| Substitution | each `GetPathName` basename matches the IR `geometry_id` filename |
| Root | assembly and referenced parts under `C:\Users\ken\Documents\se2cad\generated` |

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 167 tests, 2 skipped, 0.220 s, OK. `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 2 tests, OK, 39.008 s first run; both tests OK again after remediations. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. `git check-ignore` reports the four parts and `se2cad-test1.SLDASM`. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed `.sldprt`/`.sldasm`.

### 2026-09-08 — S2C-4.2.1 QUALIFIED (Corner / InvCorner)

Resumed S2C-4.2.1 from DEV-COMPLETE on the operator Windows 11 VM. Did not start S2C-5.1.1. Did not commit, tag, push, or publish. Did not commit generated `.SLDPRT`. Did not change recipes, the canonical frame, or the COM/pywin32 stack.

Inspected the failed IModeler knit and 3D-sketch loft paths, official 2026 FeatureManager method pages (JS-rendered; signatures from published FeatureCut4 / InsertRefPlane lists), and live late-bound CDispatch. Rejected IModeler (`CreatePlanarSurface2` / `CreateBodyFromBox3` RPC_E_SERVERFAULT), `InsertProtrusionBlend2` (None with 3D sketches and with 2D+point), `FeatureExtrusion2` UpToVertex (None for T1 0–12), and `SelectByID2` (Callout type-mismatch). `SelectByID` and sketch-point `Select2` work.

Chosen path: consume the qualified hypotenuse face (recipe `faces[-1]`) as three 3D-sketch points; `InsertRefPlane` coincident×3 (constraint 4, marks 0/1/2); oversized 2D rectangle on that plane; `FeatureCut4` 27-arg through-all. `Dir=True` keeps the apex half-space (Corner); `Dir=False` keeps the complement (InvCorner). Direction is computed from the recipe-face normal so winding is not hard-coded. Same FeatureManager session as box/slope. No boolean `Operations2`, no mesh import, no remoting.

Live reopen evidence (`SE2CAD_GENERATED_ROOT=generated`, revision 34.3.2):

| Artifact | Bytes | Solids | Sheets | BBox (m) | Volume (m³) | CoM (m) | Save/reopen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `large_armor_block.SLDPRT` | 58873 | 1 | 0 | ±1.25³ | 15.625 | (0, 0, 0) | OK |
| `large_armor_slope.SLDPRT` | 60010 | 1 | 0 | ±1.25³ | 7.8125 | (0, −1/3, −1/3)×1.25 | OK |
| `large_armor_corner.SLDPRT` | 69962 | 1 | 0 | ±1.25³ | 2.6041667 | (0.625, −0.625, −0.625) | OK |
| `large_armor_corner_inv.SLDPRT` | 75675 | 1 | 0 | ±1.25³ | 13.020833 | (−0.125, 0.125, 0.125) | OK |

Volumes and CoM match the qualified recipes. Generated root `C:\Users\ken\Documents\se2cad\generated` is gitignored (`/generated/`). `.gitignore` check-ignore reports all four files. Library records still have `part_locator=None`.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 145 tests, 1 skipped, OK. `SE2CAD_SOLIDWORKS_INTEGRATION=1` `unittest tests.test_solidworks_integration -v` — 1 test, OK, 20.091 s. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed `.sldprt`.

### 2026-09-08 — S2C-4.2.1 Windows qualification (partial)

Resumed S2C-4.2.1 on the operator Windows 11 VM with SolidWorks 2026 visible/running. Did not start S2C-5.1.1. Did not commit, tag, push, or publish. Did not commit generated `.SLDPRT`.

Operator preflight: Python 3.14.7 x64; pywin32 312; `win32com.client.Dispatch("SldWorks.Application")` returns `CDispatch`; `RevisionNumber` = 34.3.2; SE2CAD installed editable with `pip install -e .[solidworks]`.

The first ordinary Windows run was 130 tests, 2 failures, 1 skipped. Both failures were host assumptions from Linux DEV-COMPLETE, not a requirement that availability be False on Windows. Production `solidworks_backend_available()` correctly reports True when `sys.platform == "win32"` and pywin32 is present. Tests were changed to simulate Linux / missing pywin32 instead of reading the live host. `test_generate_fails_closed_when_backend_is_unavailable` now forces unavailability so the ordinary suite cannot attach to SolidWorks. Config tests isolate `SE2CAD_SOLIDWORKS_VISIBLE`.

Live attach then failed on `gencache.EnsureDispatch` (GetTypeInfo / makepy cannot run). Remediated to late-bound `GetActiveObject` / `Dispatch` plus published enum fallbacks. `swDefaultTemplatePart=8` was confirmed live (`Part.prtdot`). `FeatureExtrusion2` on this 2026 CDispatch requires 23 arguments. `IModelDoc2.SaveAs` works; `Extension.SaveAs(..., None, ...)` type-mismatches ExportData. `CreateMassProperty` / `FirstFeature` / `RevisionNumber` are late-bound properties. `OpenDoc` is used for reopen after early-bound `OpenDoc6` rejected VARIANT error arguments.

Box and slope succeeded through generate / validate / save / reopen into `generated/` (gitignored). Corner remains blocked: `IModeler.CreatePlanarSurface2` and `CreateBodyFromBox3` raise RPC_E_SERVERFAULT; `InsertProtrusionBlend2` with two 3D sketches returns None. InvCorner was not reached.

Verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 143 tests, 1 skipped, OK. Integration with `SE2CAD_SOLIDWORKS_INTEGRATION=1` still errors on Corner. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed `.sldprt`.

### 2026-09-07 — S2C-0.1.1

Executed the bootstrap unit authorized by the repository-foundation session.

Created Cursor rules, onboarding, repository contract, ratchet, engineering process, program, plan, this state file, architecture overview, block-library and converter architecture, ADR-001 through ADR-004, acceptance-fixture specification, fixtures README, empty `src/`, `tests/`, and `tools/` markers, public README, and `.gitignore` safety-net patterns for common proprietary extensions.

Did not implement M1 or later. Did not commit, tag, push, or release. Did not add Space Engineers or Keen SDK assets.

Verification: required paths present; local Markdown/MDC links resolved after this file was added; no application modules under `src/` or `tests/`; no `.mwm`, `.fbx`, `.dds`, `.hkt`, or game-content trees added.

### 2026-09-07 — S2C-0.1.1 bootstrap review remediations

Corrected two bootstrap documentation defects before first commit. Did not start S2C-1.1.1. Did not change architecture, plan sequencing, unit status, or scope. Did not commit.

- Removed the claim that `LICENSE` contains unfinished placeholder copyright fields. `LICENSE` was pre-existing and was not modified by bootstrap. The appendix `[yyyy]` / `[name of copyright owner]` text is standard Apache License 2.0 apply-to-your-work example instructions, not repository placeholders.
- Narrowed ADR-004 so `native_procedural` authorship without Keen mesh import is not treated as settling copyright, derivative-work, ownership, or redistribution status.

### 2026-09-07 — S2C-1.1.1

Registered the operator-supplied human-authored Space Engineers blueprint as the initial acceptance fixture. Did not implement a parser, catalog, IR, or CAD path. Did not modify `bp.sbc`. Did not commit, tag, push, or release.

An earlier attempt in this same bounded unit stopped because the file was absent. The operator then placed `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc`. This session resumed from that point.

Created `fixtures/acceptance/four-block-armor-asymmetric/PROVENANCE.md` from operator-stated authorship facts plus file inspection. Human architect confirmed the registered `bp.sbc` is the intended `se2cad-test1` acceptance object.

Verification: SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` (8967 bytes, UTF-8, CRLF) was unchanged after inspection and after writing provenance and this state file. Inspection notes are below. No application modules were added under `src/`, `tests/`, or `tools/`. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or game-content trees were added.

### 2026-09-07 — S2C-1.2.1

Executed the next unit named by STATE. The human architect explicitly selected Python as the implementation language; that selection is recorded in this file only.

Implemented a stdlib `xml.etree.ElementTree` parser that reads an operator-selected `bp.sbc` path and returns a CAD-neutral parsed representation. No CLI. No catalog, IR, transforms, or SolidWorks code.

Omitted-field defaults were established from local Space Engineers evidence plus published Keen/source corroboration before they were implemented. Details are under “S2C-1.2.1 omitted-field semantics” below.

Verification: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 32 tests, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` was unchanged before and after this unit. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or game-content trees were added. Did not commit, tag, push, or release. Did not start S2C-2.1.1.

### 2026-09-07 — S2C-2.1.1

Executed the next unit named by STATE. Did not start S2C-3.1.1. Did not commit, tag, push, or release.

Authored a repository-resident JSON catalog and stdlib loader from current local Space Engineers definition evidence. Catalog lookup is exact/case-sensitive and independent of XML parsing, CAD transforms, and game-install scanning. Large Grid cell pitch is `LARGE_GRID_CELL_PITCH_MM` in `src/se2cad/catalog/constants.py`.

Observed definition facts and SE2CAD mapping decisions are stored in separate JSON objects. Details are under “S2C-2.1.1 catalog evidence” below.

Verification: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 58 tests, OK after remediation. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` was unchanged before and after this unit. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or game-content trees were added. Parser modules under `src/se2cad/parser/` were not modified.

### 2026-09-07 — S2C-3.1.1

Executed the next unit named by STATE. Did not start S2C-4.1.1. Did not commit, tag, push, or release.

Implemented a CAD-neutral IR (`src/se2cad/ir/`) and a separate integer transform engine (`src/se2cad/transform/`). Public entrypoints: `build_canonical_blueprint`, `rotation_from_forward_up`, `cell_center_mm`. Rotation is a 3×3 orthonormal integer matrix (column-vector convention). Translation uses `LARGE_GRID_CELL_PITCH_MM` only.

Space Engineers direction vectors, handedness, Forward/Up construction, and Min-to-cell-center mapping were established from current local assemblies before the mapping was implemented. Details are under “S2C-3.1.1 coordinate evidence” below. The durable contract is in [BLUEPRINT_CONVERTER_ARCHITECTURE.md](../architecture/BLUEPRINT_CONVERTER_ARCHITECTURE.md).

Verification: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 85 tests, OK. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` was unchanged before and after this unit. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or game-content trees were added. Parser modules under `src/se2cad/parser/` and catalog data under `src/se2cad/catalog/` were not modified. No SolidWorks, geometry-solid, or library-storage code.

### 2026-09-07 — S2C-4.1.1

Executed the next unit named by STATE. Did not start S2C-4.2.1. Did not commit, tag, push, or release. Did not decide where generated canonical SLDPRT documents will live.

Implemented `src/se2cad/library/`: shared canonical local frame, library records, and four native-procedural recipes. Public entrypoints: `lookup_recipe`, `lookup_record`, `all_library_records`, `CANONICAL_LOCAL_FRAME`. The library consumes `SE_DIRECTION_VECTORS` and `LARGE_GRID_CELL_PITCH_MM`; it does not define a second coordinate system. Part locators remain unbound.

The durable library-side contract is in [BLOCK_LIBRARY_ARCHITECTURE.md](../architecture/BLOCK_LIBRARY_ARCHITECTURE.md). Geometry evidence is under “S2C-4.1.1 geometry evidence” below.

Verification: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 103 tests, OK after remediation. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` was unchanged before and after this unit. No `.mwm`, `.fbx`, `.dds`, `.hkt`, `.sldprt`, or game-content trees were added. Parser modules under `src/se2cad/parser/`, catalog data under `src/se2cad/catalog/`, IR under `src/se2cad/ir/`, and transforms under `src/se2cad/transform/` were not modified.

### 2026-09-07 — S2C-4.2.1 blocked before implementation

Executed the next unit named by STATE. Did not implement a SolidWorks backend, bind `part_locator`, emit `.SLDPRT`, add COM/remoting dependencies, or start S2C-5.1.1. Did not commit, tag, push, or release.

Inspected the qualified library contract, this Linux host, and current official SolidWorks 2026 API capability. Completing the unit requires human decisions that STATE already listed as open. Those decisions are now on the critical path; they were not settled here.

Verification: no `src/se2cad` product modules were added or modified by this session. No `.sldprt` was created. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` was not used as an input and was not modified. Details are under “S2C-4.2.1 environment and API evidence” below.

### 2026-09-07 — S2C-4.2.1 implementation after human architecture decisions

Resumed the blocked unit after the human architect resolved the OS split, clone model, blueprint transport, Windows execution model, pywin32 authorization, remoting exclusion, generated-artifact policy, generated-root configuration, locator contract, and ADR-004 publication boundary. Did not start S2C-5.1.1. Did not commit, tag, push, or publish.

Recorded those decisions in [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md), [ARCHITECTURE_OVERVIEW.md](../architecture/ARCHITECTURE_OVERVIEW.md), [BLUEPRINT_CONVERTER_ARCHITECTURE.md](../architecture/BLUEPRINT_CONVERTER_ARCHITECTURE.md), and [BLOCK_LIBRARY_ARCHITECTURE.md](../architecture/BLOCK_LIBRARY_ARCHITECTURE.md). Implemented `se2cad.solidworks`: CAD-neutral config/naming/units/plans/pipeline plus a Windows-only COM adapter. Authoritative library `part_locator` values remain unbound. Catalog JSON was not modified.

This Linux host still has no SolidWorks 2026 session, Wine prefix, pywin32, or reachable Windows VM (`virsh list --all` empty; `VBoxManage list vms` empty; no Windows SSH host). Official 2026 help pages remain JS-rendered; COM argument lists were taken from official method-page existence plus static/CodeStack signatures, not from a live typelib. No `.SLDPRT` was generated.

Verification: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 130 tests, 1 skipped (`SE2CAD_SOLIDWORKS_INTEGRATION` unset), OK after one wording-false-positive remediation. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, `.sldprt`, or game-content trees added. Parser, catalog data, IR, transform, and recipe geometry were not changed.

## Resolved technology selections

These are human-architect technology selections recorded as live decisions. They are not architectural ADRs and were not invented as a new planning artifact.

| Decision | Resolution | Recorded |
| --- | --- | --- |
| Implementation language | Python | S2C-1.2.1. Confirmed by the human architect for this unit. |
| SolidWorks COM interop | pywin32, Windows-only optional extra (`solidworks`) | S2C-4.2.1. Confirmed by the human architect. |
| SolidWorks execution | Windows-local in-process COM in the SolidWorks VM; no remoting | S2C-4.2.1. Confirmed by the human architect. |
| Generated canonical SLDPRT home | Configurable local generated root; not committed; not catalog paths | S2C-4.2.1. Confirmed by the human architect. |
| Optional local game / SDK install path | `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT` and `game_root` / `sdk_root` in uncommitted `se2cad.local.json`; library-build only | S2C-11.1.1. Reused the established local-config pattern. |

## Open questions

These are not invitations to decide them inside an unrelated unit.

- CLI / entrypoint shape. S2C-4.2.1 added only `python -m se2cad.solidworks` as a Windows operator entry, not a general CLI. S2C-5.1.1 added `python -m se2cad.solidworks.assemble <blueprint.sbc>` on the same terms. S2C-7.1.1 added `python -m se2cad.statistics <blueprint.sbc>` on the same terms. S2C-8.1.1 applied names on the existing assemble path and did not add an operator entry. S2C-10.2.1 added only `--edge-treatment chamfer` on the existing part-generation entry. S2C-11.1.1 added `python -m se2cad.discovery` on the same terms. S2C-10.3.1 added the same `--edge-treatment chamfer` spelling on the existing assemble entry. S2C-12.1.1 added `python -m se2cad.preflight <blueprint.sbc>` on the same terms. S2C-6.1.1 and the M7–M15 authorization did not invent a general CLI. Later units may add a narrow `python -m se2cad…` entry; they must not create a general CLI or GUI.

Resolved in S2C-6.1.1 and no longer open: numeric position/orientation comparison method. IR `(R, t)` is exact. SolidWorks `ArrayData` allowance is `BACKEND_LENGTH_TOLERANCE_M` (`1e-6` m). Recorded in [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md) and in this file.

Resolved in S2C-4.2.1 and no longer open: generated SLDPRT location (local generated root); Linux-to-Windows invocation (out of scope; operator-managed clones and blueprint copy); SolidWorks configuration for this unit (`SE2CAD_GENERATED_ROOT` / `se2cad.local.json` / optional part-template env); in-process Windows COM vs remoting (COM, no remoting); pywin32 as a Windows-only optional dependency.

Resolved in S2C-11.1.1 and no longer open: optional local game or SDK install path. Library-build discovery uses `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT` and `game_root` / `sdk_root` in the existing uncommitted `se2cad.local.json`. The Windows SolidWorks conversion path still does not require it.

## Known blockers

None. The prior same-named-document attach blocker for S2C-10.3.1 is cleared: this session attached to revision 34.3.2 with document count 0 and completed live qualification.

## S2C-1.1.1 fixture inspection

Ad-hoc read-only inspection of `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc` (Python `xml.etree.ElementTree.fromstring` plus structural scans). Not a product parser.

| Check | Result |
| --- | --- |
| XML well-formed | Yes. Root `Definitions`. No BOM. No `<!DOCTYPE`, `<!ENTITY`, non-predefined entity references, or XInclude. |
| CubeGrid count | 1. Nested `CubeGrid` elements: 0. |
| GridSizeEnum | `Large` (only value present). |
| Identity | ShipBlueprint `Id` Subtype = `se2cad-test1`. CubeGrid `DisplayName` = `se2cad-test1`. ShipBlueprint `DisplayName` = U+E030 + `Kolyma` (as stored). `WorkshopId` = `0`. |
| CubeBlocks | 24. All `xsi:type` = `MyObjectBuilder_CubeBlock`. |
| Subtype allowlist | Only `LargeBlockArmorBlock` (9), `LargeBlockArmorSlope` (12), `LargeBlockArmorCorner` (2), `LargeBlockArmorCornerInv` (1). All four present. No other `SubtypeName` values. |
| Positions | 24 unique `Min` coordinates. One omitted `Min` (treated as origin for inspection). Explicit `Min`: 23. Ranges: x 0..5, y 0..2, z -2..1. Negative z present (`-1`, `-2`). Vertical displacement: y ∈ {0,1,2}. Not confined to one axis-aligned plane. |
| Orientations | 15 omitted `BlockOrientation`. Explicit pairs: `Down/Forward` (5), `Down/Right` (1), `Forward/Right` (1), `Down/Left` (1), `Backward/Down` (1). |
| Small Grid / subgrids / functional-mechanical | No `GridSizeEnum` = Small. No second grid. Document `xsi:type` set is only `MyObjectBuilder_ShipBlueprintDefinition` and `MyObjectBuilder_CubeBlock`. Keyword scan for common functional/mechanical names: no hits. |

Omitted `Min` / `BlockOrientation` are recorded as omitted. Inspection did not invent default Forward/Up names for omitted orientation.

## S2C-1.2.1 parser evidence

Product parser: `src/se2cad/parser/`. Public entrypoints `parse_blueprint(path)` and `parse_blueprint_xml(text)`.

Observed output for `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc`:

| Check | Result |
| --- | --- |
| SHA-256 before / after | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` / unchanged |
| GridSizeEnum | Large |
| CubeGrid count | 1 |
| Block count | 24, document order preserved, no drops |
| Subtype counts | `LargeBlockArmorBlock` 9, `LargeBlockArmorSlope` 12, `LargeBlockArmorCorner` 2, `LargeBlockArmorCornerInv` 1 |
| Positions | 24 unique. One omitted `Min` applied as (0, 0, 0). Range x 0..5, y 0..2, z -2..1 |
| Orientations | 15 omitted `BlockOrientation` applied as Forward/Up. Explicit pairs: Down/Forward 5, Down/Right 1, Forward/Right 1, Down/Left 1, Backward/Down 1 |
| Identity | ShipBlueprint Id Subtype `se2cad-test1`; CubeGrid DisplayName `se2cad-test1`; ShipBlueprint DisplayName preserved as U+E030 + `Kolyma` |

These counts live in tests as fixture expectations, not as parser constants.

## S2C-1.2.1 omitted-field semantics

**Omitted `Min`** means grid coordinate `(0, 0, 0)`. The parser still records `min_serialized=False` so later validation can distinguish omission from an explicit origin.

**Omitted `BlockOrientation`** means `Forward` / `Up` (`SerializableBlockOrientation.Identity`). The parser records `orientation_serialized=False`.

Local Space Engineers evidence:

- Operator-local `Blueprints/local/se2cad-test1/bp.sbc` is byte-identical to the qualified fixture (same SHA-256). The first cube block omits `Min` and sits beside explicit `Min` values `(1,0,0)` … `(4,0,0)` and `(0,0,1)`.
- Current local `SpaceEngineers/Bin64/VRage.Game.dll` still exports `ShouldSerializeMin` and `ShouldSerializeBlockOrientation`.
- Current local `VRage.Math.xml` documents `Base6Directions.Direction` as Forward, Backward, Left, Right, Up, Down and axes ForwardBackward / LeftRight / UpDown.

Internet / published-source corroboration (not a substitute for the local evidence):

- Keen published `MyObjectBuilder_CubeBlock`: `Min` defaults to `SerializableVector3I(0,0,0)` and `ShouldSerializeMin()` is `Min != (0,0,0)`.
- Same type: `BlockOrientation` defaults to `SerializableBlockOrientation.Identity` and `ShouldSerializeBlockOrientation()` is `!= Identity`.
- `SerializableBlockOrientation.Identity` is `(Base6Directions.Direction.Forward, Base6Directions.Direction.Up)`.
- Current Keen ModAPI docs still list both `ShouldSerialize*` methods on `MyObjectBuilder_CubeBlock`.

XmlSerializer omits a field when `ShouldSerializeX()` is false; deserialization then uses the field initializer. That is the mapping implemented here.

## S2C-9.1.1 omitted-color mapping

**Omitted `ColorMaskHSV`** means HSV-offset `(0.0, -1.0, 0.0)` (`DEFAULT_COLOR_MASK_HSV`). The parser records `color_serialized=False` and `appearance_support=default`.

**Explicit `ColorMaskHSV`** is the `x`/`y`/`z` attribute vector stored as `ColorMaskHSV.h/s/v`. The parser records `color_serialized=True` and `appearance_support=explicit`. An explicit `(0, -1, 0)` is not collapsed to omitted.

This is the same XmlSerializer `ShouldSerializeX` / field-initializer pattern as omitted `Min` and `BlockOrientation`.

Local / repository evidence:

- The qualified acceptance fixture serializes no `ColorMaskHSV` on any of its 24 cube blocks (SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31`, unchanged).
- This Windows host has no Steam `libraryfolders.vdf`, no `VRage.Game.dll`, and no `%APPDATA%\SpaceEngineers` tree. WSL is not installed. A local `ShouldSerializeColorMaskHSV` export was therefore not re-read in this session.

Internet / published-source corroboration:

- Keen published `MyObjectBuilder_CubeBlock`: `ColorMaskHSV = new SerializableVector3(0f, -1f, 0f)` and `ShouldSerializeColorMaskHSV()` is `ColorMaskHSV != new SerializableVector3(0f, -1f, 0f)`.
- Keen published `SerializableVector3` uses `[XmlAttribute] x/y/z`.
- Current Keen ModAPI still lists `ColorMaskHSV` and `ShouldSerializeColorMaskHSV()` on `MyObjectBuilder_CubeBlock`.
- 2017 Doxygen dump of the same type records the same `(0f, -1f, 0f)` initializer.

RGB conversion and SolidWorks assignment are out of scope for S2C-9.1.1.

## S2C-9.2.1 appearance conversion

**HSV-offset → display HSV** is Keen `MyColorPickerConstants.HSVOffsetToHSV`: add `SATURATION_DELTA` 0.8 to S and `VALUE_DELTA` 0.45 to V, wrap H into `[0, 1)`, clamp S/V to `[0, 1]`.

**Display HSV → RGB** is standard 0–1 HSV-to-RGB (`ColorExtensions.HSVtoColor` hue contract).

**Omitted / explicit default** `(0, -1, 0)` → HSV `(0, 0, 0.45)` → RGB `(0.45, 0.45, 0.45)` → SolidWorks 8-bit `114/255`.

**Backend assignment** is `IComponent2.MaterialPropertyValues` (nine doubles, RGB prefix) on the assembly component. Canonical `.SLDPRT` generation does not receive color.

Published-source corroboration:

- Official Space Engineers wiki Data Types cites `HSVOffsetToHSV` / `HSVToHSVOffset` as saturation minus 0.8 and value minus 0.45.
- Current Keen ModAPI still lists `MyColorPickerConstants.HSVOffsetToHSV`, `SATURATION_DELTA`, `VALUE_DELTA`, and `ColorExtensions.HSVtoColor`.
- Live SolidWorks 2026 revision 34.3.2 stores component RGB as 8-bit truncated channels.

This host still has no local `VRage.Game.dll`, so the float deltas were not re-exported from a game install.

## S2C-10.1.1 edge-treatment contract

Optional equal-setback chamfer of convex manifold edges. Default is off. The operation consumes a closed mesh and does not name the four initial `geometry_id` values.

| Constant | Value |
| --- | --- |
| `EDGE_TREATMENT_SETBACK_MM` | 50 |
| `EDGE_TREATMENT_MIN_VOLUME_RATIO` | 0.85 |

| Solid | Untreated → treated faces | Convex edges treated | Volume ratio |
| --- | --- | --- | --- |
| `large_armor_block` | 6 → 18 | 12 | 0.997648 |
| `large_armor_slope` | 5 → 14 | 9 | 0.996398 |
| `large_armor_corner` | 4 → 10 | 6 | 0.992515 |
| `large_armor_corner_inv` | 7 → 19 | 12 | 0.997081 |
| Generic box 2000×1600×1200 mm (no `geometry_id`) | treated; 12 convex edges | 12 | above the 0.85 bound |

Placement invariants after a chamfer request: `CANONICAL_LOCAL_FRAME` unchanged; `additional_offset_mm` remains `(0, 0, 0)`; treated vertices stay inside the untreated bounds and the cell envelope; the armor-block face interiors still meet `±half_extent` on each axis. `lookup_recipe` vertices, faces, and catalog identities are unchanged. An L-prism with no catalog identity classifies exactly one concave edge and is not an allowlist entry.

The CAD-neutral realization clips by each convex edge's chamfer half-space. That coincides with a local edge chamfer on these recipes and on convex solids. SolidWorks materialization is recorded in [S2C-10.2.1 treated canonical parts](#s2c-1021-treated-canonical-parts).

## S2C-10.2.1 treated canonical parts

Optional treated siblings are generated only when requested. Untreated `large_armor_*.SLDPRT` remain the default conversion parts and the assembly-insert names.

| Artifact | Role |
| --- | --- |
| `{geometry_id}.SLDPRT` | Untreated default; lookup and placement unchanged |
| `{geometry_id}_chamfer.SLDPRT` | Treated sibling; same `geometry_id`; generated root only |

Live SW 2026 `RevisionNumber` 34.3.2 (`SE2CAD_GENERATED_ROOT=generated`):

| Check | Result |
| --- | --- |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |
| Untreated parts | still one solid body; volumes 15.625 / 7.8125 / 2.604167 / 13.020833 m³ |
| Treated filenames | `large_armor_block_chamfer.SLDPRT` (76121), `large_armor_slope_chamfer.SLDPRT` (77652), `large_armor_corner_chamfer.SLDPRT` (79083), `large_armor_corner_inv_chamfer.SLDPRT` (89026) |
| Untreated SHA-256 after treated write | unchanged |
| Placement | fixture assembly still inserts untreated `large_armor_*.SLDPRT`; `(R, t)` unchanged |
| Git | `git check-ignore` reports `/generated/` for untreated and treated siblings |

| Solid | Edges chamfered | Faces | Volume m³ | Ratio |
| --- | --- | --- | --- | --- |
| `large_armor_block` | 12 | 6 → 26 | 15.625 → 15.588167 | 0.997643 |
| `large_armor_slope` | 9 | 5 → 20 | 7.8125 → 7.784304 | 0.996391 |
| `large_armor_corner` | 6 | 4 → 14 | 2.604167 → 2.584630 | 0.992498 |
| `large_armor_corner_inv` | 9 (3 notch edges skipped) | 7 → 20 | 13.020833 → 12.993208 | 0.997878 |

Every treated part stayed inside the untreated envelope and the cell envelope. Volume decreased and stayed above `EDGE_TREATMENT_MIN_VOLUME_RATIO` 0.85. Face count increased. InvCorner’s notch edges are live-concave; a local chamfer of those edges returns None, so they are not treated.

## S2C-10.3.1 treated assembly selection

Optional assemble selection consumes treated siblings only when requested. Default assemble still inserts untreated `{geometry_id}.SLDPRT`.

| Selection | Insert name |
| --- | --- |
| Default / `--edge-treatment off` | `{geometry_id}.SLDPRT` |
| `--edge-treatment chamfer` | `{geometry_id}_chamfer.SLDPRT` |

Ordinary evidence:

| Check | Result |
| --- | --- |
| Fixture placements default | 24 untreated filenames; geometry_id / names / `(R, t)` / appearance unchanged |
| Explicit chamfer placements | 24 `{geometry_id}_chamfer.SLDPRT`; same IR identity, names, transforms, appearance |
| Missing treated siblings | `MissingCanonicalPartError` even when untreated files exist; no fallback |
| Operator argv | `<blueprint.sbc>` untreated; `<blueprint.sbc> --edge-treatment chamfer` treated; unknown flags fail closed |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |

Live SW 2026 `RevisionNumber` 34.3.2 (`SE2CAD_GENERATED_ROOT=generated`):

| Check | Result |
| --- | --- |
| Attach | Running instance; `started_application` False; document count 0 before and after |
| Treated fixture assembly | `generated/se2cad-test1.SLDASM` save/reopen: 24 components; 9/12/2/1 geometry IDs; each `part_filename` `{geometry_id}_chamfer.SLDPRT`; IR `ArrayData` exact; names match `component_name_from_block` with no `_chamfer`; default instance RGB |
| Untreated assemble after | Same identity overwritten; 24 untreated `{geometry_id}.SLDPRT` |
| Untreated `{geometry_id}.SLDPRT` | SHA-256 unchanged after treated generate and treated assemble |
| Operator documents | Not closed. `C:\SE2CAD-generated\` not written |

## S2C-2.1.1 catalog evidence

Authoritative catalog: `src/se2cad/catalog/large_grid_armor.json`. Loader: `src/se2cad/catalog/`. Public entrypoints `load_default_catalog()`, `DefinitionCatalog.lookup(subtype_id)`, and `LARGE_GRID_CELL_PITCH_MM`.

Local Space Engineers evidence used to author the four entries (not a runtime dependency):

- Install root resolved from the operator Steam library: `/home/ken/.local/share/Steam/steamapps/common/SpaceEngineers` (same path as `~/.steam/steam/steamapps/common/SpaceEngineers`). Steam appid `244850`, buildid `24675677`, last updated 2026-09-05 19:38:41 UTC.
- `Content/Data/CubeBlocks/CubeBlocks_Armor.sbc` (426778 bytes, mtime 2026-09-05). Each of the four subtype IDs occurs once in `Content/Data/CubeBlocks/`.
- `Content/Data/Configuration.sbc` records `<CubeSizes Large="2.5" Small="0.5" />`.

| SubtypeId | TypeId | CubeSize | Size | BlockTopology | CubeTopology |
| --- | --- | --- | --- | --- | --- |
| `LargeBlockArmorBlock` | `CubeBlock` | `Large` | 1×1×1 | `Cube` | `Box` |
| `LargeBlockArmorSlope` | `CubeBlock` | `Large` | 1×1×1 | `Cube` | `Slope` |
| `LargeBlockArmorCorner` | `CubeBlock` | `Large` | 1×1×1 | `Cube` | `Corner` |
| `LargeBlockArmorCornerInv` | `CubeBlock` | `Large` | 1×1×1 | `Cube` | `InvCorner` |

Internet / published-source corroboration (not a substitute for the local evidence):

- Keen published `Configuration.sbc` still has `CubeSizes Large="2.5"`.
- Keen ModAPI `MyCubeTopology` includes `Box`, `Slope`, `Corner`, and `InvCorner`.
- Official wiki CubeBlock definition documents `BlockTopology` `Cube` (armor) versus `TriangleMesh`, and the same `CubeTopology` tokens.

SE2CAD engineering decisions recorded in the catalog, not as Keen facts:

- `geometry_id`: `large_armor_block`, `large_armor_slope`, `large_armor_corner`, `large_armor_corner_inv`
- `recipe_kind`: `native_procedural` (architecture vocabulary; no solid is implemented here)
- `support_status`: `supported`
- `LARGE_GRID_CELL_PITCH_MM = 2500` (architecture-established millimetre form of Keen `Large="2.5"` metres)

Acceptance fixture resolution: all 24 parsed blocks resolve. Geometry-ID counts match subtype counts: `large_armor_block` 9, `large_armor_slope` 12, `large_armor_corner` 2, `large_armor_corner_inv` 1. Those counts live in tests, not catalog code.

## S2C-3.1.1 coordinate evidence

**Local Space Engineers evidence** (install root `/home/ken/.local/share/Steam/steamapps/common/SpaceEngineers`, Steam appid `244850`, buildid `24675677`, last updated 2026-09-05):

- Current `Bin64/VRage.Math.xml` documents `Quaternion.GetForward` as `(0,0,-1)`, `GetRight` as `(1,0,0)`, and `GetUp` as `(0,1,0)`.
- Same file still documents `Base6Directions.LeftDirections` as “Pre-calculated left directions for given forward (index / 6) and up (index % 6)” and `MyBlockOrientation.TransformDirection` with the published summaries.
- Current `Bin64/VRage.Math.dll` contains `IntDirections`, `LeftDirections`, `CreateFromForwardUp`, `GetMatrix`, `MyBlockOrientation`, and `CreateWorld`. The 36-byte `LeftDirections` table at file offset 389746 is exactly the published Keen table.
- Current `Bin64/VRage.Game.xml` still exports `IMyCubeGrid.GridIntegerToWorld` / `WorldToGridInteger`.
- Current `Bin64/Sandbox.Game.dll` still contains `GridIntegerToWorld`, `WorldToGridInteger`, `GridSizeHalf` (6), and `GridSizeHalfVector` (3).

**Internet / Keen published-source corroboration** (not a substitute for the local evidence):

- `Vector3` / `Vector3I`: Forward `(0,0,-1)`, Backward `(0,0,1)`, Left `(-1,0,0)`, Right `(1,0,0)`, Up `(0,1,0)`, Down `(0,-1,0)`.
- `Base6Directions.GetDirection` lookup tables independently recover those vectors. `IsValidBlockOrientation` is orthogonality (24 legal pairs).
- `MyBlockOrientation.GetMatrix` calls `Matrix.CreateWorld(Zero, Forward, Up)`.
- `CreateWorld` / `CreateFromForwardUp`: `Backward = -Forward`, `Right = Up × Backward = Forward × Up`.
- `GridIntegerToWorld`: `gridCoords * GridSize` then world-matrix transform. `WorldToGridInteger`: `Round(local / GridSize)`. AABB: `[Min * GridSize − GridSizeHalf, Max * GridSize + GridSizeHalf]`.

**SE2CAD engineering choices** (not Keen facts):

- Canonical local block frame: +X Right, +Y Up, +Z Backward (identity Forward/Up = identity rotation).
- Column-vector algebra `v_world = R v_local`; columns of `R` are Right, Up, Backward. This is the transpose of VRage/XNA row storage of the same basis.
- Units millimetres; 1×1×1 translation `Min * LARGE_GRID_CELL_PITCH_MM` with no half-cell add.
- Integer 3×3 + millimetre translation rather than a homogeneous 4×4 or Euler angles.

No axis or handedness question remained unresolved. No human-architect convention confirmation was required.

Acceptance fixture IR: 24 instances. Geometry-ID counts match catalog resolution. Representative positions: `(0,0,0)→(0,0,0)`, `(1,0,0)→(2500,0,0)`, `(0,0,1)→(0,0,2500)`, `(0,0,-1)→(0,0,-2500)`, `(5,2,-2)→(12500,5000,-5000)` mm.

## S2C-4.1.1 geometry evidence

**Observed Space Engineers facts** (topology tokens and constructive vertex signs). Distinct from SE2CAD construction vocabulary.

This session could not re-open a local Space Engineers install. Steam `libraryfolders.vdf` on this machine lists no apps; `CubeBlocks_Armor.sbc` and `Sandbox.Game.dll` were not present. Subtype → `CubeTopology` tokens therefore rest on the QUALIFIED S2C-2.1.1 local-definition record (install root `/home/ken/.local/share/Steam/steamapps/common/SpaceEngineers`, Steam appid `244850`, buildid `24675677`, `Content/Data/CubeBlocks/CubeBlocks_Armor.sbc` mtime 2026-09-05): `Box`, `Slope`, `Corner`, `InvCorner`; all 1×1×1; `BlockTopology` `Cube`.

Solid vertex signs come from Keen published `MyCubeGridDefinitions` topology edge tables (`GetTopologyInfo`), not from extracted FBX/MWM meshes:

- Keen `MyCubeTopology` enum order is `Box`, `Slope`, `Corner`, `InvCorner`, then later shapes. `GetTopologyInfo` indexes `m_tileTable[(int)topology]`.
- Current official wiki and Keen ModAPI still list those four tokens and still export `GetTopologyInfo`.
- Edge points are cell-local ±1 cube corners about the cell center. Axes match the qualified SE frame: +X Right, +Y Up, +Z Backward.
- **Box:** eight corners; six full faces.
- **Slope:** six vertices; full faces Forward and Down; sloped quad from the Forward-Up edge `(*, +1, -1)` to the Backward-Down edge `(*, -1, +1)`; identity solid `Y + Z <= 0` in those signs.
- **Corner:** tetrahedron of `(+1,+1,-1)`, `(+1,-1,-1)`, `(-1,-1,-1)`, `(+1,-1,+1)`; right-angle cube corner is Right-Down-Forward `(+1,-1,-1)`; orthogonal triangles on Right, Down, Forward.
- **InvCorner:** the other seven cube corners; full faces Up, Left, Backward; missing cube corner is the same Right-Down-Forward vertex; constructive complement of Corner.

Internet / published-source corroboration (not a substitute for the topology tables): official CubeBlock definition wiki (`CubeTopology` tokens; Side list is a texture-panel order, not the solid); Keen ModAPI `MyCubeGridDefinitions.GetTopologyInfo`.

**SE2CAD engineering choices** (not Keen facts):

- Scale topology signs by `LARGE_GRID_CELL_PITCH_MM / 2` so vertices are integer millimetres in the qualified canonical local frame.
- Construction kinds: axis-aligned box; YZ right triangle extruded along X; tetrahedron; box minus that tetrahedron.
- Shared expected AABB is the cell envelope `[-half, +half]³`. Distinction is vertex set, volume, and construction kind, not a smaller AABB.
- `volume_times_6_mm3` as the exact integer closed-mesh volume. For half-extent `h`: Box `48 h³`, Slope `24 h³`, Corner `8 h³`, InvCorner `40 h³`.
- Part locator unbound. No extra insert offset.

No Corner/InvCorner evidence gap required a stop. The shapes are CubeTopology constructive tables, not proprietary mesh extracts.

## S2C-4.2.1 environment and API evidence

Inspection-only. No SolidWorks session was started. No part documents were written.

**Qualified contracts already sufficient for geometry.** `part_locator` is `None` on all four records. Recipes already specify `axis_aligned_box`, `right_triangular_prism` (YZ triangle extruded on X), `tetrahedron`, and `box_minus_tetrahedron`. `CANONICAL_LOCAL_FRAME` is +X Right, +Y Up, +Z Backward, origin at cell center, millimetres, envelope `±LARGE_GRID_CELL_PITCH_MM/2`. A later backend must consume that frame; it must not invent a second one.

**This host cannot run SolidWorks.** Observed 2026-09-07 on `kenix` (Linux Mint 22.1 / Ubuntu noble, kernel 6.8.0-138-generic, Python 3.12.3):

| Check | Result |
| --- | --- |
| `SLDWORKS` / `wine` / SolidWorks binaries | Not on `PATH`. No Wine prefix. No `~/.wine` SolidWorks tree. |
| Environment | No `SOLID*`, `SLD*`, `SWX*`, `WIN32*`, or `WINE*` variables. |
| Python COM | `win32com` and `pythoncom` are not installed. `pyproject.toml` has no runtime dependencies. |
| Local VMs | User-session `virsh list --all` is empty. `virt-manager` is running. `VBoxManage list vms` is empty. No `.qcow2`/`.vdi`/`.vmdk` under the operator home. |
| Remoting | SSH config has only `github-homelab`. No Windows hostname, SMB/CIFS mount, or SolidWorks listener. Local listeners are DNS/CUPS plus libvirt DNS on `192.168.122.1`. |
| mDNS | Printer, AV, and Cast devices only. No SolidWorks or Windows workstation advertisement. |

Official SolidWorks 2026 client products are Windows 10/11 64-bit ([system requirements](https://www.solidworks.com/support/system-requirements)). There is no supported Linux or Wine runtime.

**Official 2026 API can construct these four solids natively** (help pages exist; several are JS-rendered so method remarks were taken from the 2026 method titles plus older published API behavior):

| Need | Official 2026 API |
| --- | --- |
| New part | `ISldWorks.INewDocument2` / `NewDocument` |
| Box / prism | `IFeatureManager.FeatureExtrusion2` after a sketch |
| Temporary box body | `IModeler.CreateBodyFromBox3` |
| Faces → body | `IModeler.ICreateBodyFromFaces3` |
| Persist a body | `IPartDoc.CreateFeatureFromBody3` |
| Boolean cut (InvCorner) | `IBody2.Operations2` (current help still documents this path) |
| Save | `IModelDoc.SaveAs3` |
| Envelope | `IPartDoc.GetPartBox` |
| Volume / CoM | `ISldWorks.GetMassProperties2` / `IMassProperty` |
| Body inventory | `IPartDoc.GetBodies2` (`swBodyType_e`; `IComponent2.GetBodies2` is obsolete in 2026, superseded by `GetBodies3`) |

COM entry is `SldWorks.Application` (version-independent) or a versioned `SldWorks.Application.N`. Geometry methods take metres, not millimetres. Document Manager API is file/metadata only; it cannot create FeatureManager solids and needs a subscription license key. It is not a substitute for a live SolidWorks session.

Smallest backend that can satisfy the unit, **after** the human decisions: a Windows-only COM adapter behind a CAD-neutral boundary; FeatureManager extrusions for box and slope; tetrahedron by `CreateBodyFromFaces3` or equivalent native loft/bound-from-recipe vertices; InvCorner as box minus that tetrahedron; validate one solid body, envelope, volume, origin, then `SaveAs3` + reopen; bind `part_locator` only after a successful save. No Keen mesh import. No new coordinate frame. Ordinary tests stay free of SolidWorks.

That design was **not** implemented. Choosing it, or any alternative, is the human decision this unit is blocked on.

**Decision required now (one contract, several coupled choices):**

1. Permanent home of generated canonical `.SLDPRT` (in-tree vs generated local cache vs caller-supplied directory). Binding `part_locator` is in this unit’s scope.
2. Linux → Windows SolidWorks 2026 invocation (none exists on this host).
3. Configuration of SolidWorks executable/template paths and any execution endpoint.
4. Automation architecture: in-process Windows COM vs a new remoting/worker stack vs operator-run scripts vs Document Manager (rejected for geometry).
5. Whether `pywin32` or another remoting dependency may be added. That is a new runtime technology relative to the current stdlib-only package.

**Why required now.** S2C-4.2.1 is the first unit that must materialize SolidWorks documents. The recipes are qualified. There is no configured SolidWorks environment, no output-location policy, and no authorized dependency or remoting design. Implementing any of those to “make the unit work” would silently settle architecture.

**Viable alternatives and consequences:**

| Alternative | Consequence |
| --- | --- |
| A. Human supplies a Windows SolidWorks 2026 host and an invocation/config contract; parts written to a designated generated directory; optional Windows-only COM extra; locators bound after save | Smallest design that can still become QUALIFIED. Adds an explicit Windows worker/dependency. Does not invent remoting if the worker runs on the SolidWorks machine. |
| B. Commit generated `.SLDPRT` in-tree after a human licensing/publication decision | Makes lookup simple and offline. Conflicts with the still-open location question and ADR-004 residual redistribution review. Agent must not commit them. |
| C. Mock-only adapter on Linux, leave locators unbound, mark DEV-COMPLETE | Allowed by the plan’s development-evidence bar, but does not produce the four parts, cannot QUALIFY, and still forces an adapter-shape and output-path choice. Rejected here because those choices are the open decisions. |
| D. Document Manager or mesh import | Document Manager cannot author these solids. Mesh import violates the native-recipe and Keen-asset boundaries. |
| E. Wine, DCOM-to-an-unknown-LAN-host, or a new RPC/gRPC worker invented in this unit | Unsupported or a substantial undeclared technology. No endpoint exists to discover. |

**Recommendation.** Adopt A: keep Linux tests stdlib-only; add a Windows-only COM adapter behind the existing CAD-neutral boundary; generate into a local cache (the repo already gitignores `/generated/` and `/out/`); configure the SolidWorks session and output root by environment or an uncommitted local config, not a CLI (CLI shape remains open); do not invent remoting in this unit — run the worker on the machine that has SolidWorks 2026; treat in-tree publication of `.SLDPRT` as a later human decision. Resume S2C-4.2.1 after that contract is written into STATE.

The human architect adopted A on 2026-09-07. Implementation followed that contract. Live typelib inspection and a real SolidWorks 2026 run remain outstanding for QUALIFIED.

## S2C-4.2.1 implementation evidence

Human decisions recorded in ADR-003 and the architecture documents named in the 2026-09-07 implementation session. Backend package: `src/se2cad/solidworks/`.

| Topic | Contract implemented |
| --- | --- |
| Package boundary | COM/pywin32 only in `com_session.py`, `com_construct.py`, `com_validate.py`, `generate.py`. Imported lazily from `generate_canonical_parts`. Top-level `se2cad` does not import the backend. |
| Configuration | `SE2CAD_GENERATED_ROOT` or uncommitted `se2cad.local.json`. Optional `SE2CAD_SOLIDWORKS_PART_TEMPLATE`. No machine path in catalog JSON. |
| Artifact names | `large_armor_block.SLDPRT`, `large_armor_slope.SLDPRT`, `large_armor_corner.SLDPRT`, `large_armor_corner_inv.SLDPRT` |
| Locator | `LogicalPartIdentity` vs runtime `BoundPartLocator`. Bind only after generate/validate/save/reopen. Library records stay `part_locator=None`. |
| Units | `mm_to_metres` is `/ 1000`. Recipes stay millimetres. API lengths metres. Local length tolerance `1e-6` m; CoM `1e-3` m. Not S2C-6.1.1. |
| Construction | Box and slope: `FeatureExtrusion2` mid-plane. Corner and InvCorner: same cell box, then one FeatureManager through-all `FeatureCut4` on a 3-point reference plane through the qualified hypotenuse vertices. Corner keeps the apex half-space; InvCorner keeps the complement. |
| Pipeline without SE/SDK | `resolve_recipes_from_blueprint` on `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc` resolves 24 IR blocks and the four recipes. Proven on Linux and in the Windows integration run. |

**API evidence used for COM calls** (official 2026 pages exist but are JS-rendered; signatures from those titles plus static/CodeStack sources). Live typelib was not inspected.

| Method | Evidence |
| --- | --- |
| `SldWorks.Application` / `gencache.EnsureDispatch` | Long-standing COM ProgID; 2026 client is Windows-only |
| `GetUserPreferenceStringValue(swDefaultTemplatePart)` + `NewDocument` | Official/new-document samples; avoids a hardcoded template path |
| `FeatureExtrusion2` (20 args; `swEndCondMidPlane=6`; depths metres) | Official 2026 method page exists; 20-arg VBA samples; `swEndCondMidPlane` documented as 6 |
| `SketchManager.CreateCornerRectangle` / `InsertSketch` / `Insert3DSketch` / `CreateLine` | Published FeatureManager sketch samples; 3D-sketch lines use model metres |
| `IModeler.CreateBodyFromBox3` / `CreatePlanarSurface2` | Official 2026 pages exist. **Rejected on live 2026 CDispatch:** RPC_E_SERVERFAULT. Not used for QUALIFIED parts. |
| `InsertRefPlane` coincident×3 (constraint 4; Select2 marks 0,1,2) | Official 2026 `InsertRefPlane` page; live 2026-09-08: returns `Plane1` |
| `FeatureCut4` 27 args; `swEndCondThroughAll=1`; Flip=False; Dir selects half-space | Official 2026 FeatureCut4 page (JS-rendered); published 27-arg list; live 2026-09-08: Flip=True returns None; Dir=True Corner; Dir=False InvCorner |
| `GetBodies2`, `GetPartBox`, `Extension.CreateMassProperty` | Official 2026 validation method pages named in the inspection session |
| `Extension.SaveAs`, `OpenDoc6`, `CloseDoc` | Official save/open/close; save is rejected unless the file exists afterwards |

Windows environment from this session: not available. Python 3.12.3 on Linux Mint 22.1 / kernel 6.8.0-138-generic. `win32com` not installed.

## S2C-4.2.1 Windows live evidence (2026-09-08)

Host: Windows 11 VM. Python 3.14.7 x64. pywin32 312. SolidWorks `RevisionNumber` 34.3.2 (year − 1992 = 2026). `GetActiveObject("SldWorks.Application")` returns `win32com.client.CDispatch`. `win32com.client.constants` has no SolidWorks enums without makepy. `gencache.EnsureDispatch` fails (`GetTypeInfo` / cannot automate makepy).

| Check | Result |
| --- | --- |
| Default part template preference 8 | `C:\ProgramData\SolidWorks\SOLIDWORKS 2026\templates\Part.prtdot` |
| `FeatureExtrusion2` arity | 20–22 args: DISP_E_PARAMNOTOPTIONAL. 23 args: succeeds |
| Right Plane 2D sketch mapping | sketch +X → model −Z; sketch +Y → model +Y; mid-plane extrude along X |
| `IModelDoc2.SaveAs(path)` | succeeds; file exists afterwards |
| `Extension.SaveAs` with Python `None` ExportData | DISP_E_TYPEMISMATCH on argument 4 |
| `IModeler.CreatePlanarSurface2` / `CreateBodyFromBox3` | RPC_E_SERVERFAULT for list, tuple, `array.array`, and VARIANT arrays. `CastTo("IModeler")` cannot EnsureDispatch |
| `InsertProtrusionBlend2` | 18-arg call is accepted; with two 3D sketches still returns None |
| Generated artifacts (gitignored `generated/`) | After QUALIFIED rerun: `large_armor_block.SLDPRT` (58873), `large_armor_slope.SLDPRT` (60010), `large_armor_corner.SLDPRT` (69962), `large_armor_corner_inv.SLDPRT` (75675) |
| Library `part_locator` | still `None` on all four records |

## Quality/security assessment (S2C-11.9.1)

Hypotheses tested after the ASCII transcoder, ordinary tests, live SolidWorks targeted probe, Big Red permissive assemble, remediations, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Arbitrary text named `.fbx` is accepted | Disproven. Classification requires binary magic or UTF-8 ASCII FBX 7.x with a mesh-bearing parse. Random text, truncated files, and header-only ASCII stay unresolved. |
| ASCII support is granted by removing the binary-only check | Disproven. `require_usable_sdk_fbx` accepts ASCII only when `ascii_fbx_conversion_available()` and `validate_ascii_fbx` succeed. Resolver still requires the rest of the S2C-11.8.1 eligibility chain. |
| Hostile / oversized ASCII causes runaway parse | Disproven. 32 MB / 200k nodes / depth 40 / 2M array-value bounds fail closed. |
| Path injection / source-root escape | Disproven. Contained SDK resolve and generated-root `relative_to` checks still apply. Intermediate dest must stay under the generated root. |
| Official SDK FBX is overwritten | Disproven. Normalized output is under `_se2cad_sdk_work/{geometry_id}/`. Convert refuses when dest resolves to the source. Live SHA-256 of Conveyor/Gyro FBX unchanged. |
| Binary FBX is forced through ASCII normalization | Disproven. Binary magic short-circuits to the existing Blender path. Ordinary tests assert the ASCII function is not called. |
| Conversion subprocess argument injection | Disproven. Blender is invoked with an argument list; paths are not interpolated into a shell string. |
| Intermediate cache / temp collision | Verified then remediated. A hung import leaked an exclusive lock on `{id}.stl`. Allocation now exclusive-creates a writable name (`{id}.2.stl` …) and cleanup ignores locked leftovers. |
| Stale intermediate reused as success | Disproven. Blender must write the chosen STL; empty or missing output fails closed. |
| Blender exit 0 hides a script exception | Disproven. Script prints `SE2CAD_BLENDER_SCRIPT_FAILED`, writes `{report}.error.txt`, exits 1; host also treats traceback-after-0 and missing STL as failure. |
| Facet-normal modal / unattended hang | Verified then remediated. Unconditional `normals_make_consistent` on binary Light.FBX hung `LoadFile2` with no visible dialog and a zero `GetPartBox`. Repair is ASCII-only. Conveyor/Gyro (ASCII+repair) and later binary FrontLight (no repair) saved/reopened unattended. No dialog auto-dismiss was added. |
| Malformed STL accepted as success | Disproven. Import/open/save/reopen and envelope assertion still run. Forgotten-scale (~0.0026 m) still fails. |
| Silent filler after support | Disproven. Builder failure still raises. Invalid/unavailable ASCII stays unresolved before support. |
| Multi-cell or Small Grid activated | Disproven. Remaining Big Red fillers are only the five multi-cell identities. Small Grid blueprints still fail at parse. CubeTopology path unchanged. |
| Runtime packaged-catalog mutation | Disproven. Catalog remains 9 entries. Overlay is process-local. |
| Whole-SDK conversion | Disproven. Only demanded unique geometry IDs convert. Nearby ConveyorCap/Duct/Tube/Sorter stems are not opened for Conveyor. |
| Keen-derived artifacts entered git | Disproven. Generated CAD remains gitignored. No `.mwm`, `.fbx`, `.dds`, or `.hkt` added to git. |

Accepted residual risk: the ASCII transcoder is a mesh-preserving FBX 7.x subset, not a full FBX SDK. Operator must point game/SDK roots at a legitimate install; a substituted same-named ASCII/binary FBX would convert. Envelope assertion catches gross scale error, not every mesh-topology defect. Conveyor’s 3.76 m Y extent is allowed by the 6.0 m envelope max and is not forgotten-scale. Existing `{geometry_id}.SLDPRT` files are reused without re-validating provenance. A SolidWorks process that leaked a file handle from a hung import can retain that lock until the process exits; conversion then uses an alternate work name. Concurrent assemblies targeting the same missing filename could both decide to generate. Untracked `tests/test_small_grid.py` remains out of scope.

Not claimed: universal FBX support; arbitrary ASCII `.fbx`; OBJ export; multi-cell or CubeTopology placement; Small Grid; animation/subpart architecture; that derived CAD is redistributable.

## Quality/security assessment (S2C-11.8.1)

Hypotheses tested after the resolver, ordinary tests, live SolidWorks targeted probe, Big Red permissive assemble, remediations, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Malicious SubtypeName becomes a filesystem path | Disproven. Geometry IDs are `vanilla_lg_1x1x1_` plus a snake-case slug. Subtype is never joined onto a root. |
| Game-content or SDK root escape | Disproven. Definition and model paths reject `..`, absolute, and drive forms. `contained_sdk_file` requires `relative_to` the resolved SDK root. |
| Hostile XML grants support | Disproven. Targeted lookup rejects doctype/entity/XInclude and fail-closes malformed target definitions as unresolved. |
| Duplicate SubtypeId is silently picked | Disproven. Duplicate exact matches raise `VanillaLookupError`. |
| Construction, LOD, or interior FBX is selected | Disproven. Exact Model stem only. Construction/LOD tokens in the selected path fail closed. Nearby InteriorModel does not make the primary Model ambiguous. |
| Arbitrary MWM→FBX substitution | Disproven. Only the official `.mwm` suffix is rewritten to the same stem. Other extensions are refused. |
| ASCII FBX is marked supported | Verified then remediated. `Conveyor.FBX` and `Gyroscope.FBX` are ASCII; Blender 5.2 cannot import them. Binary magic `Kaydara FBX Binary` is required before support grant. Those identities remain unresolved. |
| 1.0 m envelope rejected valid small 1×1×1 meshes | Verified then remediated. A ~0.50×0.49×0.19 m imported mesh failed the thruster-era minimum. Minimum is now 0.05 m to catch forgotten millimetre scale (~0.0026 m) without requiring the mesh to fill the cell. |
| Missing STL hid the Blender error | Verified then remediated. Blender 5.2 can exit 0 after a Python `RuntimeError`. The missing-STL error now includes stderr. |
| Runtime bind is persisted into the packaged catalog | Disproven. Catalog JSON is unchanged. Runtime records live in a process overlay. |
| Runtime geometry_id collides with a packaged identity | Disproven. Prefix plus packaged-ID collision check. Different recipes for the same overlay ID fail closed. |
| Supported-builder failure silently uses filler | Disproven. Conveyor first failed closed as a supported-path generation error before the ASCII gate. After the gate it is unknown/filler, not a failed supported builder. |
| Whole-SDK materialization or catalog expansion | Disproven. Only demanded unique geometry IDs generate. Indexing CubeBlocks does not grant support. |
| Keen-derived artifacts were committed | Disproven. Generated CAD remains gitignored. No `.mwm`, `.fbx`, `.dds`, or `.hkt` added to git. |
| Small Grid or multi-cell activated | Disproven. Small Grid blueprints still fail at parse. Multi-cell remaining Big Red identities stay unresolved. |

Accepted residual risk: operator must point game/SDK roots at a legitimate install; a substituted same-named binary FBX would import. Envelope assertion catches gross scale error, not every mesh-topology defect. Imported SolidWorks bodies remain graphics/mesh imports; `chamfer_capable` is false. Existing `{geometry_id}.SLDPRT` files are reused without re-validating provenance. Concurrent assemblies targeting the same missing filename could both decide to generate. Snake-case collisions of two different subtypes fail closed at overlay register. Whole-file malformed CubeBlocks XML cannot recover a subtype from that file. Untracked `tests/test_small_grid.py` remains out of scope.

Not claimed: universal vanilla support; ASCII-FBX conversion; multi-cell or CubeTopology placement; Small Grid; that derived CAD is redistributable.

## Quality/security assessment (S2C-11.7.1)

Hypotheses tested after the one authorized SDK-mesh bind, ordinary tests, live SolidWorks minimal probe, Big Red permissive assemble, remediations, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| SDK root escape / `..` traversal | Disproven. `contained_sdk_file` requires `relative_to` the resolved root and rejects `.` / `..` / absolute / drive stems. Ordinary tests cover traversal. |
| Wrong, LOD, construction, or MWM file is accepted | Disproven. Filename must be `HydrogenThrusterSmall.fbx` case-insensitively. LOD/construction path tokens and `.mwm` fail closed. |
| Catalog stores a machine path or `.fbx` | Disproven. Packaged JSON has subtype/geometry/recipe tokens only. Library `*.py` still forbids a `.fbx` string. Stem has no suffix. |
| Other `sdk_mesh_*` identities become supported | Disproven. `is_authorized_sdk_mesh_entry` matches one subtype/geometry/recipe/support tuple. Other `SDK_MESH_*` still fail closed citing ADR-004. Classification of TriangleMesh remains long-tail. |
| Long-tail leftover honesty was bypassed globally | Disproven. Packaged leftover set is unchanged. `query_exception_records` omits only this supported bind. `conversion_may_report_supported` has a narrow authorized exception. |
| Supported-builder failure silently uses filler | Disproven. Generation raises; `materialize_required_parts` does not catch that into filler. Missing usable `.SLDPRT` after a claimed builder still fails closed. |
| `materialize.py` / `assemble.py` scan an install | Disproven. Those modules do not mention `SE2CAD_SDK_ROOT` or `OriginalContent`. Resolution lives in `sdk_source.py`. |
| Scale or axis was applied twice or left in metres | Verified then remediated. First live import without ×1000 measured ~0.00259 m. Recipe `additional_scale=1000` plus envelope assertion now yields ~2.59 m. Rx +90° is recipe-owned; assembly transforms stayed generic. |
| SolidWorks reopen used a stale tiny leftover | Verified then remediated. `close_named` before import and before reopen; work root is generated `_se2cad_sdk_work/`. |
| Case-sensitive `.fbx` missed the official file | Verified then remediated. On-disk name is `.FBX`; compare is case-insensitive. |
| Keen-derived artifacts were committed | Disproven. Generated CAD remains gitignored. No `.mwm`, `.fbx`, `.dds`, or `.hkt` added to git. |
| Small Grid or later units started | Disproven. No `SmallBlockArmorBlock` catalog entry. No S2C-11.8.x. Next executable unit is none. |
| Temp conversion files leak outside the generated root | Disproven. STL work is under the generated root and `cleanup_work_dir` runs in `finally`. |

Accepted residual risk: operator must point `SE2CAD_SDK_ROOT` at official ModSDK `OriginalContent`; a substituted same-named FBX would import. Envelope assertion catches gross scale error, not every mesh-topology defect. Imported SolidWorks body is a graphics/mesh import, not a native solid; `chamfer_capable` remains false. Concurrent assemblies targeting the same missing filename could both decide to generate. Untracked `tests/test_small_grid.py` remains out of scope.

Not claimed: general SDK-mesh or TriangleMesh support; other thrusters; universal vanilla compatibility; Small Grid; that derived CAD is redistributable.

## Quality/security assessment (S2C-12.4.1)

Hypotheses tested after the identity/filename split, ordinary tests, Big Red live assemble, synthetic spaced-identity live assemble, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Path traversal via identity | Disproven. `../evil` and `..\\evil` become a single-segment derived name. `contained_destination` still rejects `../escape.SLDASM`. Live output stayed under `generated/s2c-12.4.1-probe/`. |
| Absolute Windows path injection | Disproven. `C:\\evil` and `C:evil` derive to a single segment inside the resolved root. |
| UNC path injection | Disproven. `\\\\server\\share` derives to a single segment inside the resolved root. |
| Windows reserved device names | Disproven. `CON`, `PRN`, `AUX`, `NUL`, `COM1`, and `lpt9` receive `+digest` stems. `CON.SLDASM` is not produced. |
| Invalid Windows characters / trailing space or dot | Disproven. Those identities derive; the emitted stem matches `^[A-Za-z0-9][A-Za-z0-9_-]*\\+[0-9a-f]{12}$`. |
| Naive normalization collision | Disproven. `Big Red` → `Big_Red+ffe1ed5b9381.SLDASM`; `Big_Red` → `Big_Red.SLDASM`. |
| Process-randomized digest | Disproven. Digest is `sha256(identity.encode('utf-8')).hexdigest()[:12]`. Repeated derivation matches. |
| Logical identity was rewritten | Disproven. Parse/IR/CLI/`GeneratedAssembly.identity` remain `Big Red`. DisplayName `Kolyma` is unused for the filename. |
| Component or part names changed | Disproven. Permissive fixture still uses `large_armor_block.SLDPRT` / `se2cad_unknown_filler.SLDPRT` and IR component names. Catalog still has eight Large Grid entries. |
| Unrelated assembly overwrite via derived name | Disproven. Derived stems contain `+`, which passthrough stems cannot. `assert_overwrite_is_canonical` still refuses `notes.txt`. |
| Generated-root escape after sanitization | Disproven. Filename derivation never replaces `contained_destination`. Tests still reject separator filenames independently. |
| Existing safe assembly names regress | Disproven. `se2cad-test1`, `se2cad-filler-probe`, `se2cad-ob-probe`, and `se2cad-color1` keep their previous `.SLDASM` names. |
| Policy / materialization / Small Grid changed | Disproven. Big Red remains 136 / 65 / 71 / 0 with 71 fillers. No `SmallBlockArmorBlock` catalog entry. |

No verified finding required remediation.

Accepted residual risk: already-safe identities that differ only by case (`Foo` vs `foo`) can still collide on Windows NTFS; that passthrough behavior is unchanged. A 12-hex SHA-256 prefix is collision-resistant for operator-local names, not a cryptographic identity. SolidWorks `GetTitle` after SaveAs shows the filename stem, not the logical ShipBlueprint identity. Regenerating the same identity overwrites the same `.SLDASM` in the generated root, as before. Untracked `tests/test_small_grid.py` remains out of scope.

Not claimed: universal vanilla compatibility; thruster or other functional CAD; catalog expansion; Small Grid; that every possible ShipBlueprint identity is a pretty filename.

## Quality/security assessment (S2C-12.3.1)

Hypotheses tested after parser-rule change, ordinary tests, Big Red parse/preflight/policy, attempted Big Red assemble, synthetic live SolidWorks assemble, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Every `xsi:type` string is accepted | Disproven. Token must match `^MyObjectBuilder_[A-Za-z][A-Za-z0-9_]*$`. Empty, unprefixed, spaced, URL, and hyphenated values raise `UnsupportedBlueprintError`. |
| Malformed XML becomes accepted | Disproven. DTD/entity/XInclude and unclosed XML still raise `MalformedXmlError`. Ordinary negative suite still passes. |
| Required fields are no longer fail-closed | Disproven. Missing/empty `SubtypeName`, malformed `Min` / orientation / `ColorMaskHSV`, and `SubBlocks` still fail on functional builders. |
| Parser decides catalog support | Disproven. Unknown `MyObjectBuilder_Thrust` parses, then strict refuses and permissive assigns `se2cad_unknown_filler`. Packaged catalog remains eight Large Grid armor identities. |
| Object-builder type becomes CAD identity | Disproven. `geometry_id` comes from subtype catalog lookup or filler. `CanonicalBlock` has no `object_builder_type`. |
| Catalog or recipes were expanded | Disproven. `load_default_catalog()` still has eight entries. `all_library_records()` is still eight. No new recipe for thruster geometry. |
| Small Grid is activated | Disproven. `GridSizeEnum=Small` with a Thrust builder still raises `UnsupportedBlueprintError`. |
| Source order or appearance changed | Disproven. Source indexes remain 0..N-1. Fixture omitted-color defaults unchanged. Big Red explicit `ColorMaskHSV` survives. |
| Filler is assigned to malformed blocks | Disproven. Malformed records never reach policy. |
| Runtime conversion scans the game/SDK install | Disproven. Parser still reads only the operator-selected `.sbc`. No discovery import or install walk. |
| Big Red assembly filename was silently sanitized | Disproven. Assemble failed closed on `'Big Red'`. No identity rewrite was added. |

Verified finding: present-but-empty `xsi:type=""` was treated as omitted because `_xsi_type` used `or` and collapsed `""` to the unprefixed `type` attribute. Remediated by reading explicit attribute presence. Regression: `test_structurally_invalid_xsi_types_are_rejected`. Ordinary suite re-run after the fix: 502 tests, 10 skipped, OK.

Accepted residual risk: a `MyObjectBuilder_CubeBlock` element whose `xsi:type` is a well-formed but non-cube-block builder name (for example a document-level type) is representable if the cube-block field contract is met. That is structural acceptance, not catalog support. Operator parse-error text may include the operator-supplied path. Untracked `tests/test_small_grid.py` remains out of scope.

Not claimed: universal vanilla compatibility; thruster or other functional CAD; catalog expansion; Small Grid; assembly filenames that contain spaces.

## Quality/security assessment (S2C-11.6.1)

Hypotheses tested after demand-driven untreated materialization, ordinary tests, live SolidWorks probe, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Assemble eagerly generates unrelated library parts | Disproven. `demanded_untreated_geometry_ids` is first-seen IR IDs only. Live two-geometry assemble created slope and not corner-inv or any heavy-armor part. |
| Same `geometry_id` is generated more than once in one assembly | Disproven. IDs are uniqued before generate. Two instances of `LargeBlockArmorBlock` produced one `generate_canonical_parts` call. |
| Wrong `geometry_id` maps to another filename | Disproven. Destinations still go through `logical_part_filename` / `artifact_path_for` for library-bound IDs. Unknown IDs fail before path resolution. |
| Writes escape the generated root | Disproven. Paths still use `contained_destination`. Live artifacts stayed under `generated/s2c-11.6.1-probe/`. Tests reject `../` and `sub/`. |
| Supported generation failure silently uses filler | Disproven. `materialize_required_parts` does not catch `SolidWorksComError`. A mocked failure leaves no filler file. Missing usable `.SLDPRT` after a claimed builder raises `MissingCanonicalPartError`. |
| Catalog support decisions were mutated | Disproven. Packaged catalog still has eight supported identities. `leftover_set.json` was not edited. Filler remains absent from catalog entries. |
| Runtime conversion scans the SE/SDK install | Disproven. `materialize.py`, `assemble.py`, `generate.py`, and `placement.py` do not mention `SE2CAD_GAME_ROOT`, `SE2CAD_SDK_ROOT`, `SE2CAD-SE`, or `OriginalContent`, and do not import discovery or leftover stamping. |
| Hidden `LargeRoundArmor_*` aliases are treated as planar geometry | Disproven. Those subtypes are unknown to the packaged catalog. Permissive conversion assigns `se2cad_unknown_filler`, not `large_armor_slope` / corner / inv. Derived IDs have no qualified builder. |
| Existing untreated parts are overwritten when reuse should occur | Disproven. `ensure_untreated_canonical_parts` skips `is_file()` destinations. Ordinary test left `keep-me` bytes unchanged. Live second assemble left the 59252-byte block hash unchanged. |
| Chamfer runs before the untreated base exists, or regenerates the base | Disproven. `materialize_required_parts` ensures untreated first. Chamfer with an existing base called generate only for the treated sibling. Live corner bootstrap created both files; later 75 mm block chamfer reused the untreated block hash. |
| Filler enters the supported library | Disproven. Filler is still a library-only identity, not a catalog entry, and `all_library_records()` still excludes it. |
| S2C-13.1.1 or later M7–M15 work started | Disproven. No Small Grid conversion, symmetry, print-shell, catalog expansion, or new CubeTopology constructions. |
| Proprietary assets or generated CAD were committed | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Fixture SHA-256 unchanged. Generated CAD remains gitignored. |

No verified findings required remediation.

Accepted residual risk: two concurrent assemblies targeting the same missing filename could both decide to generate; this operator-local backend is single-session. A zero-byte or foreign file with the exact canonical name is reused because existence, not content, is the reuse predicate. Historical generic `*_chamfer.SLDPRT` files are still not selected. Untracked `tests/test_small_grid.py` is leftover Small Grid WIP and is not part of this unit.

Not claimed: universal vanilla support; automatic binding of the 64 automatable-in-principle CubeTopology identities; mesh/FBX import; Small Grid conversion.

## Quality/security assessment (S2C-10.4.1)

Hypotheses tested after size-specific naming, demand-driven assemble, capability flag, ordinary tests, live SolidWorks runs, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Distinct chamfer sizes collide on one filename | Disproven. Shared `treated_artifact_key` embeds `chamfer_size_token`. Live 50 mm and 75 mm files have different names, sizes, and SHA-256. |
| Stale generic `*_chamfer.SLDPRT` is reused | Disproven. `is_treated_artifact_filename` rejects the unsized name. `missing_treated_geometry_ids` looks up the size-specific path only. Ordinary test with a generic file present still reports the 50 mm sibling missing. |
| Path / token smuggling into artifact identity | Disproven. Size tokens are produced from a validated finite number, never from a raw path. `contained_destination` still rejects separators and `..`. Tests reject `../…chamfer_50mm.SLDPRT` and `notes_chamfer_50mm.SLDPRT`. |
| Capable generation failure silently uses untreated or another size | Disproven. `generate_canonical_parts` is not caught. A patched generation error propagates `SolidWorksComError` and writes no `*_chamfer_*.SLDPRT`. `require_canonical_part_files` for capable IDs names only the exact treated sibling. |
| Assemble eagerly chamfers the whole library | Disproven. `demanded_treated_geometry_ids` is the IR's capable IDs only. Live 75 mm demand created no heavy-armor 75 mm siblings. Explicit `python -m se2cad.solidworks` still defaults to the original four. |
| Chamfer capability grants catalog support | Disproven. Capability is `LibraryRecord.chamfer_capable`, not catalog `support_status`. Filler is `native_procedural` and `chamfer_capable=False`. Catalog JSON was not given a chamfer field. |
| Component names gain chamfer suffixes or sizes | Disproven. Names remain `component_name_from_block`. Live 75 mm component name has no `_chamfer`. |
| Untreated source parts are modified | Disproven. Treated destinations are size-specific siblings. `part_artifact_path` refuses an untreated filename. Live probe hashed `large_armor_block.SLDPRT` before/after treated work. |
| Writes escape the generated root | Disproven. Destinations still go through `contained_destination`. Live artifacts stayed under `generated/`. |
| S2C-13.1.1 or later M7–M15 work started | Disproven. No Small Grid conversion, symmetry, or print-shell. |
| Proprietary assets or generated CAD were committed | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Fixture SHA-256 unchanged. Generated CAD remains gitignored. |

Verified findings remediated during live evidence:

- Late-bound 34.3.2 `GetDocumentCount` is an int property; calling it raised `TypeError`. The live probe now reads the property.
- A one-block untreated assemble after a treated assemble of a different identity failed reopen name matching (`large_armor_block` vs IR short name). That extra assemble was removed from the live probe. Untreated consumption remains evidenced by the already-qualified `test_treated_assembly_consumes_treated_siblings` in the same live class.
- Fallback reopen component order is not IR order; the live probe matches by `geometry_id`.

Ordinary suite re-run after remediations: 458 tests, 8 skipped, 0.709 s, OK. Isolated live probe re-run: OK, 34.418 s.

Accepted residual risk: historical generic `*_chamfer.SLDPRT` files from S2C-10.2.1/10.3.1 may still exist in a local generated root; they are not selected. Regenerating untreated canonical parts in a later live test changes their bytes; in-probe hash stability is the treatment-safety evidence. `GetDocumentCount` equality does not inspect operator documents from another generated root.

Not claimed: algorithm-version compatibility; that every future imported geometry is chamfer-capable; Small Grid conversion.

## Quality/security assessment (S2C-12.2.1)

Hypotheses tested after the CAD-neutral policy module, filler identity, ordinary tests, live filler-assembly run, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Unknown or unsupported blocks are silently substituted as `large_armor_block` | Disproven. Permissive IR uses `se2cad_unknown_filler`. That identity is absent from the packaged catalog. Filler volume `6000000000` vs armor `93750000000` (`volume_times_6_mm3`). Tests reject armor filename and armor geometry_id. |
| Conversion defaults to permissive | Disproven. `convert_blueprint` and `generate_assembly` default to `ConversionPolicy.STRICT`. Assemble argv without `--policy` is strict. Operator `python -m se2cad.policy` without `--policy` is strict and refuses one unknown (exit 2, `conversion_performed=false`). |
| Blocks can be dropped under either policy | Disproven. Permissive mixed-document test requires `ir.grid.block_count == preflight.block_count == 4` and source indexes `0,1,2,3`. `zip(..., strict=True)` fails closed on length mismatch. Strict refusal raises before IR emission. |
| Filler overwrites a real part filename | Disproven. Canonical names are `se2cad_unknown_filler.SLDPRT` vs `large_armor_block.SLDPRT`. Live assembly used those distinct files. |
| Catalog-unsupported keeps its catalog `geometry_id` and looks supported | Disproven. Permissive assigns filler, `support_status=unsupported`, `recipe_kind=unsupported`, not `large_unsupported_probe`. |
| A produced policy report or assemble without `--policy` hides failures | Disproven. Strict raises `ConversionRefusedError` with unknown/unsupported counts. Assemble main prints that error and exits 2. |
| Policy imports SolidWorks or copies pitch literals | Disproven. Neutrality tests forbid win32com, `.sldprt`, `.mwm`, `se2cad.solidworks`, `se2cad.library`, and `2500` in `se2cad.policy`. Ordinary suite 428 tests, 7 skipped, 0.692 s. |
| Leftover honesty or default generation changed | Disproven. `all_library_records()` remains 8. `canonical_geometry_ids()` remains the original four. Packaged leftover still matches `evaluate_leftover_set`. |
| S2C-13.1.1 or later M7–M15 work started | Disproven. No Small Grid conversion, symmetry, or print-shell. |
| Proprietary assets or generated CAD were added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Fixture SHA-256 unchanged. Generated filler artifacts are gitignored. |

No verified findings required remediation.

Accepted residual risk: `build_canonical_blueprint` remains the catalog-resolve path and still constructs IR for catalog-unsupported entries with their catalog `geometry_id`; assembly and `se2cad.policy` use the new policy and default to strict. The filler library recipe is a native SE2CAD solid so it can be generated; that does not grant `supported` to the original subtype. Operator parse-error text may include the operator-supplied blueprint path, as with preflight. Vacuous empty documents remain `all_supported`. Live qualification used a two-block synthetic probe, not a treated-filler assembly.

Not claimed: real geometry for unknown mods; Small Grid conversion; that leftover evaluation is policy; that default generate now writes the filler part.

## Quality/security assessment (S2C-12.1.1)

Hypotheses tested after the CAD-neutral preflight module, ordinary tests, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Blocks can be silently omitted from the report | Disproven. Compute appends one record per parsed block, including unknown. Mixed-document and fixture tests require `len(blocks) == block_count`. Unknown and unsupported stay in counts. |
| Unknown is aliased to a supported armor type | Disproven. Unknown records have `geometry_id` None and `geometry_support` None. Tests reject `large_armor_block` and reject collapsing unknown into unsupported. |
| Catalog-unsupported is collapsed into unknown | Disproven. Synthetic catalog-unsupported reports `catalog_outcome=unsupported` with its own `geometry_id`. |
| Geometry support follows appearance, or the reverse | Disproven. Supported+explicit, unknown+explicit, and unsupported+default keep independent flags. |
| A produced report or CLI exit 0 means conversion succeeded | Disproven. Result field is `all_supported`, not success. CLI always prints `conversion_performed=false` and exits 0 when a report is produced, including unknown-subtype documents. `build_canonical_blueprint` and assemble were not changed. |
| Diagnostics leak machine or catalog paths | Disproven. Structured result has no `source` path. `repr(report)` for the fixture path contains neither that path nor `C:\`. Operator output for fixture and temp unknown documents does not include those paths. Compute opens no files; `from_path` calls `parse_blueprint` only. |
| Malformed input is diagnosed instead of failing closed | Disproven. Zero-grid, Small Grid, and truncated XML raise the existing parser errors. |
| Preflight imports SolidWorks or writes CAD | Disproven. Neutrality tests forbid win32com, `.sldprt`, `.mwm`, and `se2cad.solidworks` / `se2cad.library` / `se2cad.ir` in compute. Ordinary suite 404 tests, 6 skipped, 0.750 s. |
| S2C-12.2.1 or later M7–M15 work started | Disproven. No filler, strict/permissive conversion policy, Small Grid conversion, symmetry, or print-shell. |
| Proprietary assets or generated CAD were added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. Fixture SHA-256 unchanged. |

No verified findings required remediation.

Accepted residual risk: preflight trusts packaged catalog `support_status`. Leftover honesty remains a catalog/library workflow; leftover identities that are not catalogued report as unknown. Catalog-unsupported identities still convert to IR today with `support_status=unsupported`; refusal and filler are S2C-12.2.1. Operator parse-error text may include the operator-supplied blueprint path, as with statistics. Vacuous `all_supported` is true for zero CubeBlocks.

Not claimed: that preflight converts; that filler exists; that unknown subtypes now assemble; that leftover evaluation is preflight; Small Grid conversion.

## Quality/security assessment (S2C-11.5.1)

Hypotheses tested after leftover metadata, honesty checks, ordinary tests, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Failed generation, unclassified identities, or unsupported recipe kinds can report as supported conversion | Disproven. `conversion_may_report_supported` is False for those leftovers. `assert_leftover_honesty` fails closed when a failed-generation leftover is still catalogued `supported`. Loader rejects `reported_as_supported` true. |
| Residual automatable items were silently dropped | Disproven. Packaged leftover lists `Slope2Base` as `missing_construction`. `stamp_automatable_remainder` does not invent a construction. Coverage claim is `not_universal_vanilla`. |
| Packaged leftover drifts from catalog evaluation | Disproven. `assert_packaged_leftover_matches_catalog` requires equality with `evaluate_leftover_set`. |
| Runtime conversion now requires a game/SDK install | Disproven. Leftover and runtime modules do not import `se2cad.discovery` or mention `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT`. Ordinary suite 385 tests, 6 skipped, 0.617 s with no install. |
| Asset paths can enter leftover metadata | Disproven after remediation. Packaged leftover JSON rejects `.mwm` / paths. `evaluate_leftover_set` now rejects smuggled tokens on record construction. |
| Original four conversion changed | Disproven. Fixture SHA-256 unchanged. All 24 IR blocks remain the original four supported native identities. |
| Universal vanilla support was claimed | Disproven. Coverage claim cannot be anything but `not_universal_vanilla`. README and STATE say coverage is not 100%. |
| S2C-12.1.1 or later M7–M15 work started | Disproven. No preflight, filler, Small Grid conversion, symmetry, or print-shell. |
| Additional SolidWorks parts were generated or committed | Disproven. No live generation this session. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |

One verified finding was remediated: `evaluate_leftover_set` initially recorded caller-supplied subtype/geometry/detail tokens without the packaged JSON asset-path checks. `_record` now rejects smuggled asset and path tokens. Affected leftover tests were re-run; ordinary suite 385 tests, 6 skipped, OK.

Accepted residual risk: leftover honesty is a catalog/library consistency workflow, not M12 preflight. `build_canonical_blueprint` still copies packaged catalog `support_status`. Packaged catalog and leftover currently agree. CubeTopology tokens beyond the evidenced residual `Slope2Base` are not individually inventoried; coverage is explicitly not universal.

Not claimed: 100% vanilla coverage; TriangleMesh construction; Small Grid conversion; that every automatable-class identity can generate; that leftover evaluation is conversion preflight.

## Quality/security assessment (S2C-11.4.1)

Hypotheses tested after topology-stamped recipes, representative generation, ordinary tests, and live 34.3.2 evidence existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Generation overwrites unrelated files | Disproven. `assert_overwrite_is_canonical` still rejects `notes.txt`. New names are only library-owned `{geometry_id}.SLDPRT` / `{geometry_id}_chamfer.SLDPRT`. |
| Writes escape the generated root | Disproven. `contained_destination` still rejects separators and `..`. Live heavy parts are under `C:\Users\ken\Documents\se2cad\generated`. `git check-ignore` reports `/generated/`. |
| Default generate now materializes every library identity | Disproven. `canonical_geometry_ids()` and `python -m se2cad.solidworks` still name the original four. Representative generation is an explicit `geometry_ids` request. |
| Unknown automatable topologies are forced through one construction | Disproven. `recipe_for_topology(..., "Slope2Base")` raises `UnsupportedTopologyError`. Only Box/Slope/Corner/InvCorner have builders. |
| Runtime conversion requires a game/SDK install | Disproven. Library and generate modules do not import `se2cad.discovery`. Ordinary suite 367 tests, 6 skipped, 1.054 s with no install. |
| Selection now grants support | Disproven. `select_catalog_recipes` still never writes `SupportStatus.SUPPORTED`. Packaged heavy support is an authored generation decision. |
| COM leftover documents or operator-doc close | Disproven. Attached session document count was 0 before and 0 after. `started_application` False. |
| Original four conversion changed | Disproven. Fixture SHA-256 unchanged. Live fixture assembly still uses the original four filenames and 9/12/2/1 counts. |
| Proprietary assets or committed CAD | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed `.SLDPRT`. |
| S2C-11.5.1 or later M7–M15 work started | Disproven. No leftover-set workflow, preflight, Small Grid conversion, symmetry, or print-shell. |

No verified findings required remediation.

Accepted residual risk: CubeTopology tokens beyond Box/Slope/Corner/InvCorner remain classified automatable without a construction (S2C-11.5.1 remainder). Default `python -m se2cad.solidworks` does not generate the heavy-armor parts; assemble of a heavy-armor blueprint fails closed until those files exist. Distinct `geometry_id` values produce distinct files even when the solid is identical.

Not claimed: 100% vanilla coverage; TriangleMesh construction; Small Grid conversion; that every automatable-class identity can generate.

## Quality/security assessment (S2C-11.3.1)

Hypotheses tested after selection, packaged recipe-kind updates, ordinary tests, and documentation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Selection silently marks expanded identities `supported` | Disproven. `select_catalog_recipes` never writes `SupportStatus.SUPPORTED`. Expand-then-select of `LargeBlockArmorBlock` stays `unsupported`. Packaged heavy-armor entries are `native_procedural` / `unsupported`. Library `lookup_recipe` still raises `UnknownGeometryError` for those IDs. |
| Long-tail identities can be reported as supported | Disproven. Supported + long-tail fails closed. Exception records set `reported_as_supported` False. TriangleMesh stays `unsupported` / `unsupported`. |
| Geometry classes were collapsed | Disproven. TriangleMesh, missing CubeTopology, unusual `block_topology`, unusual `type_id`, and Small Grid have distinct `ExceptionReason` values. Additional CubeTopology tokens such as `Slope2Base` stay automatable, not TriangleMesh. |
| `sdk_mesh_*` was assigned or Keen CAD was treated as redistributable | Disproven. Classification never returns mesh recipe kinds. Existing `sdk_mesh_direct` fails closed citing ADR-004. Packaged JSON has no `.mwm`, `.fbx`, paths, or mesh references. |
| Provenance is missing observed-vs-decided fields | Disproven. `ProvenanceRecord` carries observed definition, geometry class, decided `recipe_kind` / `support_status`, and notes. Query does not rewrite unselected recipe kinds. |
| Conversion now requires a game/SDK install | Disproven. Catalog selection does not import `se2cad.discovery`. Runtime `se2cad/__init__.py` does not export selection. Acceptance IR still builds from packaged catalog + `bp.sbc`. |
| Original four conversion changed | Disproven. Fixture SHA-256 unchanged. All 24 IR blocks remain the original four supported native identities. |
| S2C-11.4.1 or later M7–M15 work started | Disproven. No library recipes for expanded IDs, no SolidWorks generation, no preflight, Small Grid conversion, symmetry, or print-shell. |
| Proprietary assets added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |

No verified findings required remediation.

Accepted residual risk: CubeTopology tokens beyond the qualified four (for example `Slope2Base`) are classified automatable without a library recipe; S2C-11.4.1 must choose a representative generated subset. Statistics `resolved` still means catalog identity exists, not conversion support (same as S2C-11.2.1). `query_exception_records` inspects existing mesh recipe kinds without the apply-time ADR-004 rejection; the packaged catalog has none.

Not claimed: automated generation; TriangleMesh construction; a live vanilla inventory; that `native_procedural` on expanded identities is conversion support.

## Quality/security assessment (S2C-11.2.1)

Hypotheses tested after schema v2, authoring, packaged expansion, ordinary tests, and remediation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Asset paths or machine paths enter packaged catalog data | Disproven. Packaged JSON has no `/home/`, `C:\`, `.mwm`, `.fbx`, `.dds`, `.hkt`, `Steam`, `SpaceEngineers`, or `game_root`. Loader rejects those markers and path separators in identity strings. Authoring from synthetic discovery XML that contains a Model `.mwm` path does not copy it. |
| Duplicate `geometry_id` or subtype collision | Disproven. Loader and `expand_catalog_identities` reject duplicates. Light and heavy Box identities keep distinct IDs. |
| Schema v1 is silently accepted | Disproven. Loader accepts only `CATALOG_SCHEMA_VERSION` 2. Schema 1 fails closed. Unknown fields still fail. |
| Support claimed without a recipe decision | Disproven. Loader rejects `supported` + `unsupported` recipe kind. Authoring never marks a new identity supported. Packaged expanded entries are `unsupported` and have no library recipe. |
| Conversion now requires a game/SDK install | Disproven. Catalog and runtime packages do not import `se2cad.discovery`. Acceptance IR still builds from packaged catalog + `bp.sbc`. |
| Small Grid was activated | Disproven. Loader rejects `cube_size` other than `Large`. Authoring skips Small Grid identities. `SmallBlockArmorBlock` remains unknown. |
| Original four conversion changed | Disproven. Fixture SHA-256 unchanged. All 24 IR blocks remain the original four supported native identities. |
| Authoring emits a catalog the loader cannot load | Confirmed then remediated. A digit-leading subtype produced `2foo_bar`, which the loader rejects. Expand now runs `checked_geometry_id` before recording. Regression test added. |
| Catalog modules scan an install or write discovery paths | Disproven. `src/se2cad/catalog/` has no `SE2CAD_GAME_ROOT` / `se2cad.discovery` tokens. Serialized authoring output has no source-relative paths. |
| S2C-11.3.1 or later M7–M15 work started | Disproven. No recipe-kind assignment policy, exception records, generation, preflight, Small Grid conversion, symmetry, or print-shell. |
| Proprietary assets added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |

Remediated: invalid derived `geometry_id` fails closed at authoring. Tests re-run after remediation: 338 OK, 5 skipped.

Accepted residual risk: the four heavy-armor identities were recorded as the CubeTopology counterparts of the QUALIFIED S2C-2.1.1 class without a live install this session. A later operator-local discovery run may add more vanilla identities or expose drift. Digit-leading or otherwise non-letter subtypes fail closed; vanilla armor IDs in this catalog start with a letter. Cataloguing an identity as `unsupported` makes `lookup` succeed and IR construction possible; assembly still fails closed because those IDs have no canonical part.

Not claimed: recipe selection; geometry generation; Small Grid conversion; TriangleMesh construction; a live vanilla inventory.

## Quality/security assessment (S2C-10.3.1 QUALIFIED)

Hypotheses tested after live SolidWorks qualification evidence existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Assembly selection was re-implemented | Disproven. No `src/` or `tests/` product edits this session. |
| Operator documents were closed to force live evidence | Disproven. Attach found document count 0. `C:\SE2CAD-generated\` files were left untouched (mtimes unchanged). |
| Live run wrote outside the generated root | Disproven. Artifacts are under repo `generated/`. `git check-ignore` reports the parts and assemblies. |
| Treated assemble silently fell back to untreated parts | Disproven. Live test asserted 24 `{geometry_id}_chamfer.SLDPRT` after save/reopen. |
| Treated assemble overwrote untreated `{geometry_id}.SLDPRT` | Disproven. Live test compared untreated SHA-256 before and after treated generate and treated assemble. |
| Transforms, names, or appearance changed | Disproven. Live comparisons used IR `ArrayData`, `component_name_from_block`, and default RGB. `_chamfer` is not in component names. |
| S2C-11.2.1 or later M7–M15 work started | Disproven. Packaged catalog identities, recipes, and conversion contracts are unchanged. |
| Proprietary assets added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| Leftover documents remained open | Disproven. Document count 0 after the live run. |

No verified product findings required remediation.

Accepted residual risk: attaching to a running SolidWorks instance that already has `large_armor_*.SLDPRT` or `se2cad-test1.SLDASM` open still makes OpenDoc/SaveAs fail for the same filenames in another generated root. This session had zero open documents. Treated assemble of the same blueprint identity overwrites the untreated `.SLDASM` name; untreated parts are not modified. The leftover `generated/live-s2c-1031/` file from an earlier failed attempt remains gitignored local cache.

Not claimed: catalog identity expansion; print-shell; a general CLI.

## Quality/security assessment (S2C-10.3.1)

Hypotheses tested after assembly selection, ordinary tests, and the failed live attach existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Explicit chamfer assemble silently falls back to untreated parts | Disproven. `require_canonical_part_files(..., EDGE_TREATMENT_CHAMFER)` looks up `{geometry_id}_chamfer.SLDPRT` only and raises `MissingCanonicalPartError` when untreated files exist and siblings do not. |
| Treated assemble overwrites untreated `{geometry_id}.SLDPRT` | Disproven. Assemble writes only the identity `.SLDASM`. Part destinations still go through `part_artifact_path`, which refuses a treated name equal to the untreated canonical name. |
| `_chamfer` is baked into catalog or IR identity | Disproven. Parser, catalog JSON, and IR are unchanged. `ComponentPlacement.geometry_id` stays the IR value; `component_name` has no `_chamfer`. |
| Path escape from treated part lookup | Disproven. Lookup uses `part_artifact_path` → `contained_destination`. Filenames are single-segment `{geometry_id}_chamfer.SLDPRT`. |
| Transforms or mates changed | Disproven. Placement copies IR rotation/translation/appearance. `com_assemble.py` still has no mate-creation tokens. Ordinary fixture comparisons remain exact. |
| Default assemble now inserts treated parts | Disproven. Omitted and `EDGE_TREATMENT_OFF` still name `{geometry_id}.SLDPRT`. `generate_assembly` treatment default is `None`. |
| Operator documents were closed to force live evidence | Disproven. `C:\SE2CAD-generated\` parts/assembly and untitled `Part1` were left open. Only two leftover repo-`generated/` documents from the failed run were closed. |
| S2C-11.2.1 or later M7–M15 work started | Disproven. Packaged catalog identities, recipes, and conversion contracts are unchanged. |
| Proprietary assets added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |

No verified product findings required remediation. One ordinary test assertion was tightened so “no fallback” is proved by the missing-sibling diagnostic rather than an empty set.

Accepted residual risk: attaching to a running SolidWorks instance that already has `large_armor_*.SLDPRT` open makes OpenDoc/SaveAs fail for the same filenames in another generated root. That blocked QUALIFIED in this session. Treated assemble of the same blueprint identity overwrites the untreated `.SLDASM` name; untreated parts are not modified.

Not claimed: QUALIFIED live treated assembly; catalog identity expansion; print-shell; a general CLI.

## Quality/security assessment (S2C-10.3.1 sequencing amendment)

Hypotheses tested after the governance/planning amendment documents existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| A tenth milestone was created or M7–M15 was reordered | Disproven. Program still lists exactly nine milestones M7–M15. S2C-10.3.1 is a third M10 unit. |
| S2C-10.1.1 or S2C-10.2.1 qualification was rewritten | Disproven. Both remain QUALIFIED with original evidence, live SolidWorks record, and assessments. |
| S2C-11.1.1 was invalidated or its evidence rewritten | Disproven. Status, session history, discovery evidence, and assessment remain QUALIFIED. |
| S2C-11.2.1 was started or marked other than PLANNED | Disproven. Status is PLANNED, deferred until S2C-10.3.1 is QUALIFIED. Packaged catalog still has the four armor identities. |
| History was rewritten to imply M11 never started | Disproven. STATE current-program text, session history, and S2C-11.1.1 QUALIFIED record remain. |
| S2C-10.3.1 was implemented in this session | Disproven. No `src/` or `tests/` edits. Assemble still has no treated-part selection. |
| The ratchet was given M10-specific logic | Disproven. [SE2CAD_RATCHET.md](../../cursor/SE2CAD_RATCHET.md) still derives the next unit from STATE only. |
| Named opschecks were added | Disproven. S2C-10.3.1 reuses `SE2CAD_SOLIDWORKS_INTEGRATION`. The program still defines none. |
| Planned treated assembly was described as implemented capability | Disproven. README assemble path remains untreated. Architecture uses “when STATE records S2C-10.3.1”. |
| Proprietary assets added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |

No verified findings required remediation.

Accepted residual risk: a later session could misread the out-of-sequence insertion as permission to invent further units. The ratchet still requires STATE authorization for the single next unit.

Not claimed: S2C-10.3.1 implementation; treated assembly selection; any change to QUALIFIED S2C-11.1.1.

## Quality/security assessment (S2C-11.1.1)

Hypotheses tested after discovery, shared local-config, synthetic-tree tests, and the ordinary suite existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Discovery walks an arbitrary disk or the whole install | Disproven. Only `Content/Data/CubeBlocks` and `Data/CubeBlocks` `*.sbc` files under a configured root are read. A root without those directories fails closed. |
| Path escape or symlink-equivalent outside the root is accepted | Disproven. `contained_file` and definition-directory resolution use `relative_to` after `resolve`. Outside paths raise `DiscoveryPathError`. |
| XXE / DTD / XInclude in definition XML is loaded | Disproven. The same marker rejection as the blueprint parser (`<!doctype`, `<!entity`, `xinclude`) fails closed before `ElementTree`. |
| Conversion requires a game/SDK install | Disproven. `parse_blueprint` / `load_default_catalog` / `build_canonical_blueprint` succeed with those env vars unset. `se2cad/__init__.py` and runtime packages do not import `se2cad.discovery`. |
| Machine paths or mesh references enter the packaged catalog | Disproven. Catalog JSON is unchanged (four entries). Discovery records root-relative `source_relative` only. Model/Icon `.mwm`/`.dds` in synthetic XML are not copied into the report. |
| Shared `se2cad.local.json` keys break SolidWorks config | Disproven. `game_root` / `sdk_root` are allowed and ignored by the SolidWorks loader. Unknown keys such as `steam_path` still fail. |
| Ordinary suite attaches to SolidWorks or a real install | Disproven. 309 tests, 4 skipped, 0.996 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset and no game tree. |
| S2C-11.2.1 or later M7–M15 work started | Disproven. Packaged catalog identities, recipes, and conversion contracts are unchanged. |

No verified findings required remediation.

Accepted residual risk: discovery error messages may include the operator-supplied root path (same class as `parse_blueprint`). An operator-local run against a real Space Engineers / ModSDK tree was not performed on this host and is not required for QUALIFIED. Nested files below `CubeBlocks/` are not walked; vanilla files in STATE evidence sit directly in that directory.

Not claimed: catalog expansion; recipe selection; Small Grid conversion; TriangleMesh construction; a live install inventory.

## S2C-11.1.1 discovery evidence

Public entrypoints: `se2cad.discovery.discover_cube_block_definitions`, `load_discovery_config`. Narrow operator entry: `python -m se2cad.discovery`. Not imported by `se2cad/__init__.py`.

| Item | Record |
| --- | --- |
| Config | `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT` override `game_root` / `sdk_root` in `se2cad.local.json`. At least one root required. |
| Trees walked | `{root}/Content/Data/CubeBlocks/*.sbc` and `{root}/Data/CubeBlocks/*.sbc` only |
| Observed fields | `subtype_id`, `type_id`, `cube_size`, `size`, `block_topology`, `cube_topology` (omitted when absent), `source_kind`, `source_relative` |
| Not recorded | `geometry_id`, `recipe_kind`, `support_status`, Model/Icon/mesh paths, absolute machine roots |
| Fail closed | missing/non-directory root; path escape; no CubeBlocks tree; malformed XML; DTD/entity/XInclude; missing identity/size/topology; conflicting observed facts |
| Ordinary suite | 309 tests, 4 skipped, 0.996 s, OK |
| Fixture SHA-256 | `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged |

## S2C-11.5.1 leftover and expansion-regression evidence

Public entrypoints: `se2cad.catalog.evaluate_leftover_set`, `load_default_leftover_set`, `conversion_may_report_supported`, `stamp_automatable_remainder`. Authoritative leftover metadata: `src/se2cad/catalog/leftover_set.json`. Schema: `LEFTOVER_SCHEMA_VERSION` 1. Coverage claim: `not_universal_vanilla`. Runtime lookup remains `load_default_catalog`.

| Group | SubtypeId | geometry_id | topology | leftover kind |
| --- | --- | --- | --- | --- |
| Completed automatable | `LargeBlockArmorBlock` | `large_armor_block` | Box | (none) |
| Completed automatable | `LargeBlockArmorSlope` | `large_armor_slope` | Slope | (none) |
| Completed automatable | `LargeBlockArmorCorner` | `large_armor_corner` | Corner | (none) |
| Completed automatable | `LargeBlockArmorCornerInv` | `large_armor_corner_inv` | InvCorner | (none) |
| Completed automatable | `LargeHeavyBlockArmorBlock` | `large_heavy_block_armor_block` | Box | (none) |
| Completed automatable | `LargeHeavyBlockArmorSlope` | `large_heavy_block_armor_slope` | Slope | (none) |
| Completed automatable | `LargeHeavyBlockArmorCorner` | `large_heavy_block_armor_corner` | Corner | (none) |
| Completed automatable | `LargeHeavyBlockArmorCornerInv` | `large_heavy_block_armor_corner_inv` | InvCorner | (none) |
| Residual automatable | (not catalogued) | (none) | Slope2Base | `missing_construction` |

Packaged long-tail identity leftovers are empty: all eight catalogued identities are CubeTopology-class `CubeBlock` armor with known constructions. Exception states for unclassified identities, unsupported recipe kinds, failed generation, and long-tail TriangleMesh/unusual relationships are queryable from `evaluate_leftover_set` and cannot report as supported. `stamp_automatable_remainder` on the packaged catalog is empty. No additional parts were generated.

Acceptance fixture: all 24 blocks still resolve to the original four supported identities. Fixture SHA-256 unchanged. Runtime modules do not open a game/SDK install. Packaged catalog and leftover JSON forbid asset paths.

Ordinary suite: 385 tests, 6 skipped, 0.617 s, OK.

## S2C-11.4.1 automated generation evidence

Public entrypoints: `se2cad.library.recipe_for_topology`, `representative_automatable_geometry_ids`, `se2cad.solidworks.generate_representative_automatable_parts`. Default `generate_canonical_parts()` still generates the original four.

| Group | SubtypeId | geometry_id | topology | support_status | generated |
| --- | --- | --- | --- | --- | --- |
| Original four | `LargeBlockArmorBlock` | `large_armor_block` | Box | `supported` | default generate |
| Original four | `LargeBlockArmorSlope` | `large_armor_slope` | Slope | `supported` | default generate |
| Original four | `LargeBlockArmorCorner` | `large_armor_corner` | Corner | `supported` | default generate |
| Original four | `LargeBlockArmorCornerInv` | `large_armor_corner_inv` | InvCorner | `supported` | default generate |
| Representative | `LargeHeavyBlockArmorBlock` | `large_heavy_block_armor_block` | Box | `supported` | representative generate |
| Representative | `LargeHeavyBlockArmorSlope` | `large_heavy_block_armor_slope` | Slope | `supported` | representative generate |
| Representative | `LargeHeavyBlockArmorCorner` | `large_heavy_block_armor_corner` | Corner | `supported` | representative generate |
| Representative | `LargeHeavyBlockArmorCornerInv` | `large_heavy_block_armor_corner_inv` | InvCorner | `supported` | representative generate |

Known constructions: Box, Slope, Corner, InvCorner only. `Slope2Base` and other automatable-class tokens fail closed. Runtime lookup remains `load_default_catalog`. No CLI expansion.

Live SW 2026 `RevisionNumber` 34.3.2 (`SE2CAD_GENERATED_ROOT=generated`):

| File | Bytes | Solid bodies | Volume m³ |
| --- | --- | --- | --- |
| `large_heavy_block_armor_block.SLDPRT` | 59061 | 1 | 15.625 |
| `large_heavy_block_armor_slope.SLDPRT` | 60364 | 1 | 7.8125 |
| `large_heavy_block_armor_corner.SLDPRT` | 69837 | 1 | 2.6041667 |
| `large_heavy_block_armor_corner_inv.SLDPRT` | 75092 | 1 | 13.020833 |

Ordinary suite: 367 tests, 6 skipped, 1.054 s, OK. Live integration: 6 tests, OK, 566.041 s. Fixture SHA-256 unchanged.

## S2C-11.3.1 recipe selection evidence

Public entrypoints: `se2cad.catalog.select_catalog_recipes`, `classify_observed`, `query_exception_records`, `provenance_records`. Schema remains `CATALOG_SCHEMA_VERSION` 2. Runtime lookup remains `load_default_catalog`.

| Group | SubtypeId | geometry_id | recipe_kind | support_status | class |
| --- | --- | --- | --- | --- | --- |
| Original four | `LargeBlockArmorBlock` | `large_armor_block` | `native_procedural` | `supported` | automatable |
| Original four | `LargeBlockArmorSlope` | `large_armor_slope` | `native_procedural` | `supported` | automatable |
| Original four | `LargeBlockArmorCorner` | `large_armor_corner` | `native_procedural` | `supported` | automatable |
| Original four | `LargeBlockArmorCornerInv` | `large_armor_corner_inv` | `native_procedural` | `supported` | automatable |
| Expanded | `LargeHeavyBlockArmorBlock` | `large_heavy_block_armor_block` | `native_procedural` | `unsupported` | automatable |
| Expanded | `LargeHeavyBlockArmorSlope` | `large_heavy_block_armor_slope` | `native_procedural` | `unsupported` | automatable |
| Expanded | `LargeHeavyBlockArmorCorner` | `large_heavy_block_armor_corner` | `native_procedural` | `unsupported` | automatable |
| Expanded | `LargeHeavyBlockArmorCornerInv` | `large_heavy_block_armor_corner_inv` | `native_procedural` | `unsupported` | automatable |

Packaged exception set is empty: all eight identities are CubeTopology-class `CubeBlock` armor. Long-tail records are queryable for TriangleMesh and unusual relationships; they are not reported as supported. `sdk_mesh_direct` / `sdk_mesh_manifold` are not assigned.

Acceptance fixture: all 24 blocks still resolve to the original four supported identities. Library recipes remain the four native solids.

## S2C-11.2.1 catalog identity evidence

Authoritative catalog: `src/se2cad/catalog/large_grid_armor.json`. Schema: `CATALOG_SCHEMA_VERSION` 2. Authoring: `se2cad.catalog.expand_catalog_identities`. Runtime lookup remains `load_default_catalog`.

| Group | SubtypeId | geometry_id | recipe_kind | support_status |
| --- | --- | --- | --- | --- |
| Original four | `LargeBlockArmorBlock` | `large_armor_block` | `native_procedural` | `supported` |
| Original four | `LargeBlockArmorSlope` | `large_armor_slope` | `native_procedural` | `supported` |
| Original four | `LargeBlockArmorCorner` | `large_armor_corner` | `native_procedural` | `supported` |
| Original four | `LargeBlockArmorCornerInv` | `large_armor_corner_inv` | `native_procedural` | `supported` |
| Expanded | `LargeHeavyBlockArmorBlock` | `large_heavy_block_armor_block` | `unsupported` | `unsupported` |
| Expanded | `LargeHeavyBlockArmorSlope` | `large_heavy_block_armor_slope` | `unsupported` | `unsupported` |
| Expanded | `LargeHeavyBlockArmorCorner` | `large_heavy_block_armor_corner` | `unsupported` | `unsupported` |
| Expanded | `LargeHeavyBlockArmorCornerInv` | `large_heavy_block_armor_corner_inv` | `unsupported` | `unsupported` |

Observed facts for all eight: `CubeBlock`, `Large`, 1×1×1, `Cube`, and the same `Box` / `Slope` / `Corner` / `InvCorner` tokens as the QUALIFIED S2C-2.1.1 armor class. Heavy-armor identities are the CubeTopology counterparts this unit was prepared to record. No live game/SDK tree was read this session.

SE2CAD decisions: distinct `geometry_id` values; expanded entries stay `unsupported` until S2C-11.3.1. `cube_topology` may be omitted for identities without it. Small Grid is not catalogued.

Acceptance fixture: all 24 blocks still resolve to the original four supported identities. Library recipes remain the four native solids.

## Quality/security assessment (S2C-10.2.1)

Hypotheses tested after sibling naming, ordinary tests, and live 34.3.2 treated/untreated generation existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Treated generation overwrites untreated `large_armor_*.SLDPRT` | Disproven. Destinations are `{geometry_id}_chamfer.SLDPRT`. `part_artifact_path` refuses a treated write whose name equals the untreated canonical name. Live treated write left untreated SHA-256 unchanged. |
| Writes escape the generated root | Disproven. `contained_destination` still rejects separators and `..`. Live treated files are under `C:\Users\ken\Documents\se2cad\generated`. `git check-ignore` reports `/generated/`. |
| Treatment is a new `geometry_id` or catalog identity | Disproven. Locator `geometry_id` is unchanged. Catalog and `lookup_recipe` still have exactly the four IDs. Filename suffix is an artifact token, not a catalog key. |
| Default conversion or placement uses treated parts | Disproven. `generate_canonical_parts` / `__main__` default to `EDGE_TREATMENT_OFF`. `recipe_plan.py`, `pipeline.py`, `assemble.py`, `placement.py`, and `com_construct.py` do not request treatment. Live fixture assembly still inserts untreated filenames. |
| Foreign overwrite | Disproven. `notes_chamfer.SLDPRT` is not a treated artifact name and is refused. |
| Ordinary suite attaches to SolidWorks | Disproven. 283 tests, 4 skipped, 0.396 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| Proprietary assets or fixture rewrite | Disproven. Fixture SHA-256 unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| S2C-11.1.1 or later M7–M15 work started | Disproven. No definition discovery, preflight, Small Grid, symmetry, or print-shell. |

Remediated during live evidence: `swChamferEqualDistance` (16) is a no-op on late-bound 34.3.2; equal setback uses `swChamferDistanceDistance` (2) plus `ForceRebuild3`. InvCorner all-edge chamfer returns None; oblique-face (notch) edges are excluded and the remaining 9 succeed. Ordinary suite re-run after the live remediations: 283 OK, 4 skipped. Treated live test re-run: OK, 43.961 s.

Accepted residual risk: a local CAD chamfer and the CAD-neutral sequential half-spaces differ at vertices (box volume delta about 8e-5 m³) and on InvCorner, where three live-concave notch edges are skipped. Both stay inside the S2C-10.1.1 envelope and volume-ratio bounds. The oblique-face fallback is only used when the full convex set is refused; slope/corner succeed without it.

Not claimed: physical print judgment; fillet; print-shell; TriangleMesh; treated parts used at assembly insert.

## Quality/security assessment (S2C-10.1.1)

Hypotheses tested after the CAD-neutral treatment, recipe/generic-solid tests, and the ordinary suite existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Default conversion applies the treatment | Disproven. `apply_edge_treatment(solid)` and `EDGE_TREATMENT_OFF` return the same mesh. `lookup_recipe` vertices/faces/volume are unchanged after a chamfer request. `generate.py`, `recipe_plan.py`, `pipeline.py`, `assemble.py`, and `com_construct.py` do not mention the treatment API. |
| Treatment is a new block type or `geometry_id` | Disproven. Catalog and `all_library_records()` still have exactly the four IDs. `SolidMesh` has no `geometry_id`. `solid.py` / `treatment.py` do not name the four armor IDs. |
| Applicability is a four-ID allowlist | Disproven. A 2000×1600×1200 mm box with no catalog identity treats all 12 convex edges. An L-prism with no identity classifies one concave edge. |
| Frame drift or a second insert offset | Disproven. Records still use `CANONICAL_LOCAL_FRAME` and `additional_offset_mm=(0,0,0)`. Treated recipe vertices stay inside the cell envelope. Armor-block face interiors remain at `±half_extent`. |
| Keen-mesh import | Disproven. Library neutrality still forbids `.mwm` / `.fbx` / `.dds` / `.hkt` and game-install imports. Treatment uses recipe meshes and explicit test solids only. |
| Open or tiny solids are silently treated | Disproven. A one-face mesh raises `InvalidSolidError`. A 40 mm cube raises `TreatmentError` because the named setback consumes an edge. |
| Slope hypotenuse-side edges are skipped | Confirmed, then remediated. Newell winding on the qualified slope hypotenuse face is inward relative to the vertex centroid, so those two edges were first classified concave. Convexity now orients face normals away from the vertex centroid. The qualified recipe windings were not changed. Slope now treats all 9 prism edges. Regression: `test_slope_treats_every_prism_edge`. |
| Ordinary suite attaches to SolidWorks | Disproven. 267 tests, 3 skipped, 0.343 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| Proprietary assets or fixture rewrite | Disproven. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| S2C-10.2.1 or later M7–M15 work started | Disproven. No treated `.SLDPRT` generation, library expansion, preflight, Small Grid, symmetry, or print-shell. |

Remediated during review: centroid-oriented outward normals for convexity classification; slope 9-edge regression. Ordinary suite re-run: 267 OK, 3 skipped.

Accepted residual risk: sequential chamfer half-spaces coincide with a local edge chamfer on the native recipes and on convex solids. An infinite plane from one convex edge of a deeply concave solid can intersect non-adjacent features; S2C-10.2.1 should use a local CAD chamfer and still satisfy this contract's measurables. Vertex-average centroid can lie outside a severely concave mesh; that would mis-orient convexity. The 50 mm setback is an SE2CAD treatment depth, not a Keen mesh measurement.

Not claimed: treated SolidWorks parts; physical print judgment; fillet; print-shell.

## Quality/security assessment (S2C-9.2.1)

Hypotheses tested after conversion, instance assignment, ordinary tests, and live 34.3.2 runs existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Color is baked into shared canonical parts | Disproven. Part-generation modules have no `ColorMask` / `MaterialPropertyValues`. Live color-assembly write left all four `.SLDPRT` SHA-256 values unchanged. Two explicit colors plus default share `large_armor_block.SLDPRT`. |
| Appearance is applied in a second frame | Disproven. Assignment is `IComponent2.MaterialPropertyValues` on the same inserted component after `Transform2`, before rebuild. Transforms and names still match the qualified IR. |
| Color is silently dropped | Disproven. Readback mismatch raises `AssemblyValidationError`. Default and explicit paths both require a stuck RGB. |
| Conversion lives in parser/catalog/IR | Disproven. Those packages do not import `se2cad.solidworks.appearance`. RGB exists only in the SolidWorks package. |
| Default appearance fails the qualified fixture | Disproven. All 24 omitted fixture blocks convert and live-reopen with default instance RGB. SHA-256 unchanged. |
| Untrusted color payloads reach COM | Disproven. Malformed `ColorMaskHSV` still fails at the parser. Conversion receives already-validated finite floats. |
| Ordinary suite attaches to SolidWorks | Disproven. 251 tests, 3 skipped, 0.271 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| Proprietary assets or fixture rewrite | Disproven. Fixture SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| S2C-10.1.1 or later M7–M15 work started | Disproven. No edge treatment, library expansion, preflight, Small Grid, symmetry, or print-shell. |

Remediated during review: live 34.3.2 quantizes component RGB to 8-bit (`0.45` → `114/255`); writer now writes truncated channels and compares with a one-LSB allowance. Hermetic appearance assertions compare with `rgb_close` rather than exact full-precision tuples. Ordinary suite re-run: 251 OK, 3 skipped. Live suite re-run: 3 OK, 69.481 s.

Accepted residual risk: this host could not re-export `SATURATION_DELTA` / `VALUE_DELTA` from a local `VRage.Game.dll`. Deltas rest on the official wiki citation of `HSVOffsetToHSV`. Some community decompilations list `VALUE_DELTA` as `0.55`; a later local DLL export could change default brightness by 0.10. `SkinSubtypeId` remains unparsed. Material lighting extras (ambient/diffuse/specular/shininess) are SE2CAD choices, not Keen facts.

Not claimed: paint skins; a material library product; print-shell coloring; a general CLI.

## Quality/security assessment (S2C-9.1.1)

Hypotheses tested after parser/IR appearance fields and tests existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Malformed `ColorMaskHSV` is silently replaced by the omitted default | Disproven. Nil, children, extra attributes, missing axes, non-numeric, NaN/Inf, `1e999`, overlong tokens, and `z="oops"` raise `InvalidFieldError` or `MissingRequiredFieldError`. |
| Untrusted float tokens accept `+`, whitespace, underscores, or non-finite values | Disproven. `_parse_float_attr` rejects those forms before or after `float()`. |
| Appearance is folded into `geometry_id` or catalog identity | Disproven. Same subtype / different colors share `large_armor_block`. Different subtypes / same color keep distinct geometry IDs. Catalog JSON and recipes have no color fields. |
| Adding color changed omitted `Min` / `BlockOrientation` defaults | Disproven. Omitted Min remains `(0,0,0)` Forward/Up. Explicit color with omitted Min/orientation still uses those defaults. |
| Fixture identities or transforms changed | Disproven. SHA-256 unchanged. IR acceptance still matches subtype/`Min`/Forward/Up/`geometry_id`/transforms; all 24 fixture blocks are default appearance. |
| SolidWorks appearance was assigned or parts were painted | Disproven. SolidWorks package has no `ColorMaskHSV` / appearance assignment calls. Placement and naming do not encode color. |
| Ordinary suite attaches to SolidWorks | Disproven. 233 tests, 2 skipped, 0.236 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| Proprietary assets or fixture rewrite | Disproven. SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| S2C-9.2.1 or later M7–M15 work started | Disproven. No SolidWorks appearance conversion, edges, library expansion, preflight, Small Grid, symmetry, or print-shell. |

Remediated during review: added regression tests for overlong tokens, overflow `1e999`, and explicit color leaving omitted Min/orientation unchanged. Suite re-run: 233 OK, 2 skipped.

Accepted residual risk: this host could not re-export `ShouldSerializeColorMaskHSV` from a local `VRage.Game.dll`. The omitted vector rests on published Keen source, current ModAPI, and fixture omission. `ColorMaskHSV` is stored as HSV-offset, not converted to RGB. `SkinSubtypeId` remains unparsed. Unknown appearance is not a current parser state.

Not claimed: SolidWorks component appearance; RGB conversion; paint skins; a general CLI.

## Quality/security assessment (S2C-8.1.1)

Hypotheses tested after the name function, placement field, and Name2 writer existed, including after live 34.3.2 rename/reopen. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Path or identifier injection via subtype strings | Disproven. Allowlist `^[A-Za-z][A-Za-z0-9_]*$` rejects `../`, separators, spaces, dots, Unicode, and `foo.SLDPRT`. Tests cover those cases. |
| Same subtype at different cells collides | Disproven. Fixture 24 names are unique. Min and `source_index` both change the encoding. Duplicate identity fails closed. |
| Omitted vs explicit orientation invents two names | Disproven. Same Forward/Up and `source_index` produce the same name. Serialization flags are not encoded. |
| Names include machine paths or `geometry_id` | Disproven. Encoding uses subtype/`Min`/Forward/Up/`source_index` only. Naming source has no `C:`, `/home/`, or `.SLDPRT`. |
| Transforms change while renaming | Disproven. Live reopen still matches all 24 packed IR `ArrayData` values. MateGroup stays empty. |
| Canonical `.SLDPRT` files are renamed | Disproven. Live `GetPathName` basenames remain `large_armor_*.SLDPRT`. Generated directory listing is the four parts plus `se2cad-test1.SLDASM`. |
| Name2 set always sticks | Confirmed false, then remediated. Unselected assignment is a no-op (`large_armor_block-1` remained). Select then set works (`ProbeName2-1`). |
| `swExtRefUpdateCompNames` True allows Name2 | Confirmed false (official remarks + live no-op). Toggle 18 is forced False for insert/save/reopen and restored. |
| Restoring the toggle before SaveAs persists names | Confirmed false, then remediated. Reopen showed filename stems until the toggle stayed False through SaveAs. |
| Ordinary suite attaches to SolidWorks | Disproven. 212 tests, 2 skipped, 0.250 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| Parser/catalog/IR transform/recipe contract changed | Disproven. Parser, catalog JSON, transform engine, and recipe geometry were not modified. |
| Proprietary assets or fixture rewrite | Disproven. SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. `git check-ignore` reports `/generated/`. |
| S2C-9.1.1 or later M7–M15 work started | Disproven. No color, edges, library expansion, preflight, Small Grid, symmetry, or print-shell implementation. |

Remediated: Name2 requires Select; `swExtRefUpdateCompNames` must stay False through SaveAs/reopen. Ordinary suite and live integration re-run after those fixes.

Accepted residual risk: if the process dies after forcing the toggle False and before restore, the operator SolidWorks session may keep `swExtRefUpdateCompNames` False until it is set again. `COMPONENT_NAME_MAX_LENGTH` 80 is an SE2CAD identifier cap; the fixture max name length is 50, so live truncation was not exercised. Name2 get is compared after stripping a numeric `-{instance}` suffix.

Not claimed: a general CLI; color; renaming library geometry identities; publication of generated CAD.

## Quality/security assessment (S2C-7.1.1)

Hypotheses tested after the statistics module and operator entry existed. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Untrusted path is opened as something other than the parser's blueprint read | Disproven. `compute_blueprint_statistics_from_path` calls `parse_blueprint` only. Statistics source has no `open`/`write_text`. |
| Structured result stores the filesystem path | Disproven. `BlueprintStatistics` has identity and count fields only. Fixture-path `repr` test does not contain the path. |
| Unknown subtypes are dropped or given a invented geometry_id | Disproven. Synthetic unknown blocks remain in `block_count` and `subtype_counts`, increment unresolved coverage, and do not appear in `geometry_id_counts`. |
| Unsupported documents are accepted to make counts look complete | Disproven. Zero-grid, Small Grid, and malformed XML raise the same parser errors as direct parse. |
| Pitch literals were copied | Disproven. Statistics source has no `2500`. Millimetre size uses `catalog.large_grid_cell_pitch_mm`. |
| A second identity system was invented | Disproven. Subtype, geometry_id, grid size, and Forward/Up are parser/catalog tokens. |
| Operator entry is a general CLI | Disproven. One positional path; usage-on-wrong-arity; no flags or subcommands. |
| Operator print of the qualified fixture crashes on Windows cp1252 | Confirmed, then remediated. U+E030 in ShipBlueprint `DisplayName` raised `UnicodeEncodeError`. Console write now uses `backslashreplace`. Structured result still stores the exact Unicode. Regression test added. |
| Ordinary suite attaches to SolidWorks | Disproven. 198 tests, 2 skipped, 0.231 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| Parser/catalog/IR/transform/library/SolidWorks product code changed | Disproven. Those trees were not modified. |
| Proprietary assets or fixture rewrite | Disproven. SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` unchanged. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| S2C-8.1.1 or later M7–M15 work started | Disproven. No component naming, color, edges, library expansion, preflight, Small Grid, symmetry, or print-shell implementation. |

Remediated: operator stdout encoding for non-cp1252 blueprint display names. Tests re-run after remediation: 198 OK, 2 skipped.

Accepted residual risk: parser error messages still include the operator-supplied path (existing `parse_blueprint` contract). Occupancy uses unique `Min` cells only and does not expand catalog `Size`. Empty `CubeBlocks` is parseable and reports no invented extents.

Not claimed: conversion of unknown blocks; a general CLI; SolidWorks involvement; any M8–M15 feature.

## Quality/security assessment (M7–M15 program authorization)

Hypotheses tested after drafting the current program and updating governance pointers. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Initial M0–M6 program was treated as still executable | Disproven. Historical PROGRAM/PLAN say they are complete; STATE names M7–M15 as current; next unit is S2C-7.1.1. |
| M0–M6 historical status or evidence was rewritten | Disproven. Initial unit table remains QUALIFIED with original evidence. Session history for S2C-0.1.1 through S2C-6.1.1 is unchanged. |
| An implementation milestone was marked ACTIVE | Disproven. S2C-7.1.1 through S2C-15.4.1 are PLANNED. No product code was started. |
| Approved features were reordered, merged, or duplicated | Disproven. Nine milestones M7–M15 match the authorized sequence, each feature once. |
| Cold-storage items became executable units | Disproven. PROGRAM_M7 exclusions list multi-grid/mechanical, reverse conversion, Blender runtime, general FBX product, completed TriangleMesh library, slicer/physical print, extra backends, GUI/general CLI, and external backlog. M11 classifies TriangleMesh; it does not deliver the class. |
| Named opschecks were added without necessity | Disproven. The program defines none. Live SolidWorks units reuse `SE2CAD_SOLIDWORKS_INTEGRATION`. |
| Ratchet cannot drive the program without chat history | Disproven. Ratchet/rules/onboarding read STATE for the current program, plan, and next unit. Unit detail lives in PLAN_M7. |
| Architecture was silently redesigned | Disproven. ADRs were not rewritten. Architecture notes authorized expansions and keeps IR neutrality, transform placement, pitch constants, asset boundary, and Windows-local COM. |
| Planned features were described as implemented capability | Disproven. STATE and README say M7–M15 are approved, not implemented. Architecture says expansions are not implied until STATE records them. |
| Product code or tests were modified | Disproven. Ordinary suite 176 tests, 2 skipped, OK. No `src/` or `tests/` edits. |
| Broken local documentation links | Disproven. 154 local Markdown/MDC links resolve (Cursor rule paths from workspace root; others from the file). |
| Proprietary assets added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or committed CAD. |
| A follow-on program beyond the nine features was invented | Disproven. Executable scope is exactly M7–M15. |

Remediated during review: sequencing rule clarified so a DEV-COMPLETE SolidWorks unit does not freeze later CAD-neutral units; architecture decision 2 notes a second named Small Grid pitch constant; historical vs current program pointers were added wherever a fresh session would otherwise read only M0–M6.

Accepted residual risk: S2C-11.4.1’s “representative automatable subset” and S2C-13.2.1’s optional operator-authored Small Grid fixture are bounded in the plan but still require judgment in those sessions. Install-path configuration was resolved in S2C-11.1.1 by reusing env / `se2cad.local.json`. Color omitted-field semantics and the print-shell product definition remain stop-and-ask items if evidence or two defensible definitions conflict.

Not claimed: any M7–M15 product implementation; publication; a general CLI.

## Quality/security assessment (S2C-6.1.1)

Hypotheses tested after the unchanged fixture ran through the complete operator path and the reopened assembly was compared to the qualified IR. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Dropped or duplicated blocks | Disproven. Parser, IR, placements, and reopened assembly each have 24 entries; 24 unique `Min` cells. |
| Wrong subtype → geometry mapping | Disproven. All 24 map 9/12/2/1 through catalog, IR, part filenames, and `GetPathName` basenames. |
| Order-dependent placement | Disproven. `source_index` is preserved; every reopened component matches its IR block by index, not by list position after `GetComponents`. |
| Row-major transform packing | Disproven. All 24 reopened axes equal qualified rotation columns. |
| Sign / reflection error | Disproven. Fixture rotations keep determinant `+1`. Negative-Z cells remain negative. |
| Translation scaling or half-cell offset | Disproven. `(1,0,0)` → `(2.5,0,0)` m; origin is `(0,0,0)` m, not `1.25`. All 24 translations are `Min * 2.5` m. |
| Default-orientation drift | Disproven. 15 omitted orientations remain identity Forward/Up. |
| Explicit vs omitted serialization confused | Disproven. The nine explicit pairs match the fixture XML; omitted stay identity. |
| Stale canonical parts or stale assembly reuse | Disproven for this run. Operator path regenerated all four parts, then the assembly; reopen `ArrayData` matched the packed IR exactly. |
| Partial generation accepted as success | Disproven for this run. All four parts validated; assembly requires all four files and exactly 24 matching components. |
| Path substitution | Disproven. Each component path stays under the generated root and the basename equals the IR `geometry_id` filename. |
| Generated files entered Git | Disproven. `/generated/` gitignore; `check-ignore` reports the four parts and `se2cad-test1.SLDASM`. No committed `.sldprt`/`.sldasm`. |
| Fixture changed to make qualification pass | Disproven. SHA-256 unchanged. |
| Space Engineers or ModSDK became a runtime dependency | Disproven. Pipeline uses the repository fixture and packaged catalog only. |
| Loosened tolerances hid orientation bugs | Disproven. Live evidence used exact 16-double equality for all 24 components. Recorded allowance remains `1e-6` m. |
| Documents leaked after failure | Disproven for the successful path. `generate_canonical_parts` and `generate_assembly` still close documents in `finally`. |
| Ordinary suite attaches to SolidWorks | Disproven. 176 tests, 2 skipped, 0.224 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| IR/catalog/recipe/transform contract changed | Disproven. Parser, catalog JSON, IR, transform engine, and recipe geometry were not modified. |

Remediated: none. No verified product defect remained after the live end-to-end run.

Accepted residual risk: if part generation fails after writing a subset of the four files, a later assemble can consume a mix of new and previously generated parts. That failure path was not observed. This session regenerated all four parts immediately before the operator assemble.

Not claimed: publication of generated CAD, binding library `part_locator` into catalog/library records, a general CLI, or a follow-on program. Space Engineers was not launched in this session; the intended SE object is the S2C-1.1.1-confirmed fixture.

## Quality/security assessment (S2C-5.1.1)

Hypotheses tested after live 24-component assembly generation. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Row-major packing used instead of official X/Y/Z axis rows | Disproven. `solidworks_arraydata` writes rotation columns (component axes). Down/Right row-major differs and is rejected by test. Live ArrayData matched columns after save/reopen. |
| Sign inversion or reflection | Disproven. Fixture rotations keep determinant `+1`. Negative-Z translation remains negative (`(0,0,-1)` → `(0,0,-2.5)` m). |
| Translation treated as millimetres or given a half-cell offset | Disproven. Packing uses `mm_to_metres`; `(1,0,0)` → `2.5` m; origin is `(0,0,0)` m, not `1.25`. |
| Wrong part selected for `geometry_id` | Disproven. Each component `GetPathName` basename must equal the IR filename. Counts 9/12/2/1. Unknown geometry IDs fail closed. |
| Duplicate or missing components | Disproven. Insert and reopen both require exactly 24 matches; leftover unmatched IR placements fail. |
| Transform applied in a second frame or with a corrective rotation | Disproven. Packing is `(R.columns, t_m, scale=1)` only. No extra offset or SE reinterpretation. |
| Mates used for placement | Disproven. No `AddMate`/`CreateMate`. Auto-fixed first component is unfixed. Live `GetMates` is None; MateGroup has no children. |
| Save/reopen loses placement | Disproven. Live reopen ArrayData matched the IR pack for identity, translation, Down/Forward, and Down/Right. |
| Machine paths entered authoritative data | Disproven. Catalog JSON unchanged; neutrality test still forbids `/home/`, `C:\`, `.SLDPRT`. Library `part_locator` remains `None`. |
| Generated artifacts entered Git | Disproven. `/generated/` gitignore; `check-ignore` reports the four parts and `se2cad-test1.SLDASM`. |
| Documents leaked after failure | Disproven for the successful path. `generate_assembly_from_ir` closes the assembly and opened parts in `finally`; session exit closes remaining titles. |
| Ordinary suite attaches to SolidWorks | Disproven. 167 tests, 2 skipped, 0.220 s with `SE2CAD_SOLIDWORKS_INTEGRATION` unset. |
| `CreateTransform` is required | Disproven. Live 34.3.2 `CreateTransform` server-faults. Product code writes `Transform2.ArrayData` via `VT_ARRAY\|VT_R8`. |
| Raw Python list is a valid ArrayData write | Disproven. Live list write corrupted translation (`1.15e-311`). Locked to VARIANT R8 tuple. |
| IR/catalog/recipe contract changed | Disproven. Parser, catalog JSON, IR, transform engine, and recipe geometry were not modified. |

Remediated: removed a no-op `try/except: raise` in `insert_placements`; renamed the integration assembly test so a combined live run generates parts before the assembly. Ordinary suite and live integration re-run after that. No remaining verified product defect.

Not claimed: S2C-6.1.1 Space Engineers visual/end-to-end comparison, publication of generated CAD, or binding library `part_locator` into catalog/library records.

## Quality/security assessment (S2C-4.2.1 QUALIFIED Corner/InvCorner)

Hypotheses tested after live four-part generation. Outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Backend special-cases geometry IDs instead of recipe data | Disproven. `com_construct` branches on `SolidKind` only. Cut plane vertices are `tetra.faces[-1]` from the plan; keep-side is the unique unused vertex. |
| Frame or origin drifted | Disproven. Reopen bbox is the qualified cell envelope ±1.25 m; CoM matches recipe-derived expected values. |
| mm/metre conversion inverted or implicit | Disproven. Plans still use `mm_to_metres`; pitch 2500 mm → 2.5 m; volumes match `volume_times_6_mm3 / 6 / 1000³`. |
| Extra solid or sheet bodies accepted | Disproven. Validator requires 1 solid and 0 sheets. Live reopen: 1/0 on all four parts. |
| Surface-only or graphics substitute accepted | Disproven. Sheet count 0; mass volume is the qualified tetrahedron / complement, not zero. |
| Failed or partial files accepted | Disproven. `SaveAs` requires the destination file; locator bind requires generate, validate, save, and reopen. Integration would fail without all four files. |
| Stale ActiveDoc reused | Disproven. Each part calls `NewDocument`. |
| Documents leaked after failure | Disproven for the successful run. `generate_one_canonical_part` closes in `finally`; session exit closes remaining titles. |
| Overwrite of unrelated files | Disproven. Only the four canonical filenames may be overwritten. Destinations stayed under `generated/`. |
| Generated artifacts entered Git | Disproven. `/generated/` gitignore; `check-ignore` reports all four `.SLDPRT`. |
| Ordinary tests attach to the live host | Disproven. 145 tests, 1 skipped, 0.158 s without `SE2CAD_SOLIDWORKS_INTEGRATION`. |
| Workaround introduced a second backend architecture | Disproven. Same Windows-local late-bound pywin32 COM + FeatureManager session. No remoting, no typelib/makepy requirement, no mesh import, no IModeler. |
| IModeler or 3D-sketch loft became viable | Disproven again. Server fault / None return reproduced before the FeatureCut path was chosen. |
| `FeatureCut4` Flip is required to choose the half-space | Disproven. Flip=True returns None; Dir selects the half-space. Locked to Flip=False. |

Remediated: none after the live four-part run. No verified product defect remained.

Not claimed: assembly generation, publication of generated parts, or binding library `part_locator` into catalog/library records.

## Quality/security assessment (S2C-4.2.1 Windows qualification)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| The two ordinary-suite failures mean availability must be forced False | Disproven. Live Windows+pywin32 correctly reports True. The tests assumed a Linux / no-pywin32 runner. |
| `test_solidworks_package_imports_without_pywin32` actually established missing pywin32 | Confirmed false, then remediated. Availability is now simulated; CAD-neutral import still runs on the real host. |
| `test_generate_fails_closed_when_backend_is_unavailable` stays SolidWorks-free on Windows | Confirmed it did not establish unavailability. Remediated by patching `_windows`. |
| `EnsureDispatch` is required to attach | Disproven. Operator `Dispatch` and live `GetActiveObject` attach. EnsureDispatch cannot run makepy. |
| Writes escape the generated root during the live run | Disproven for the two saved parts. Destinations were `generated/large_armor_*.SLDPRT`. |
| Generated parts were committed | Disproven. `/generated/` is gitignored. No `.sldprt` added to the committed tree. |
| Ordinary suite launches SolidWorks | Disproven after remediation. 143 tests, 1 skipped, 0.159 s. |
| Config tests are hermetic against `SE2CAD_SOLIDWORKS_VISIBLE` | Confirmed leak, then remediated. |
| IModeler knit is a viable Corner path on this COM binding | Disproven. Server exception on CreatePlanarSurface2 / CreateBodyFromBox3. |
| All four parts are QUALIFIED | Disproven. Integration still fails on Corner. Two parts are live evidence only. |

Remediated: platform-independent availability tests; generate fail-closed isolation; late-bound attach and constants; `com_get` for CDispatch properties; 23-arg `FeatureExtrusion2`; `SaveAs` / `OpenDoc`; Right-plane slope mapping; config env isolation.

Not remediated: Corner/InvCorner live solids. That remains the QUALIFIED blocker. Choosing a new construction technology (beyond FeatureManager / in-process pywin32 COM) would be an architectural decision and was not taken.

Not claimed: QUALIFIED, assembly generation, or publication of generated parts.

## Quality/security assessment (S2C-4.2.1 implementation)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Writes can escape the configured generated root | Disproven for the path helpers. `contained_destination` rejects `..`, nested segments, and `relative_to` failures. Tests cover separators and escapes. |
| Unrelated files can be overwritten | Disproven. Overwrite is allowed only for the four exact canonical filenames. |
| Machine-specific paths entered the catalog | Disproven. `large_grid_armor.json` unchanged; neutrality test forbids `/home/`, `C:\`, `.SLDPRT`. |
| pywin32 leaks into CAD-neutral imports | Disproven. Parser/catalog/IR/transform/library and backend-neutral modules have no `win32com` imports. `import se2cad` succeeds on Linux. |
| Linux suite became Windows-dependent | Disproven. 129 tests run here; the one integration test skips unless `SE2CAD_SOLIDWORKS_INTEGRATION=1`. |
| mm/m conversion is implicit or inverted | Disproven. `mm_to_metres` is `/ 1000`; pitch 2500 mm → 2.5 m; half-extent 1.25 m. |
| Backend invents a second frame or reinterprets recipes | Disproven for the plan layer. Vertices and faces are recipe values converted coordinate-wise. No corrective rotation. |
| Surface/graphics or multi-body results can pass | Disproven in the validator. Exactly one solid and zero sheet bodies are required. |
| Save can succeed without a file | Disproven. `save_as` checks `destination.is_file()`. |
| Reopen validation can be skipped | Disproven. Locator bind requires generate, validate, save, and reopen. |
| COM exceptions are swallowed | Disproven. Failures are wrapped as `SolidWorksComError` with the original exception chained. |
| Documents stay open after failure | Remediated. Each part uses `try`/`finally` `CloseDoc`. Session exit closes remaining titles. SaveAs retitles the tracked document so close uses the post-save name. |
| Stale ActiveDoc is reused | Disproven. Each part calls `NewDocument`. |
| Game/SDK runtime dependency on Windows | Disproven in code. Pipeline uses the repo fixture and packaged catalog only. |
| Cross-OS remoting was introduced | Disproven. No socket/RPC/SSH/DCOM/service code. |
| Proprietary assets or generated SLDPRT were added | Disproven. No `.sldprt` exists in the tree. Fixture SHA-256 unchanged. |
| A post-success environment probe could fail the run | Confirmed then remediated. `generate_canonical_parts` no longer calls `session_environment_report` after a successful four-part run. |
| Pipeline neutrality test treated exclusionary wording as a scan | Confirmed then remediated. The test now checks imports and path tokens. |

Accepted residual risk: COM argument lists were not proven against a live SolidWorks 2026 typelib. `CreateBodyFromBox3` array layout (center vs base-face) and `Operations2` arity have published variants; validation is intended to fail closed if the live API disagrees. QUALIFIED is not claimed.

Not claimed: SolidWorks part production on this host, QUALIFIED, assembly generation, or publication of generated parts.

## Quality/security assessment (S2C-4.2.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| A SolidWorks 2026 session is already available on this development host | Disproven. No binaries, Wine prefix, COM modules, env vars, VM disk, SSH/Windows host, or SolidWorks listener. Official 2026 clients are Windows-only. |
| Recipes or the canonical frame must be changed to implement this unit | Disproven. The four construction kinds and `CANONICAL_LOCAL_FRAME` are sufficient. The stop is environment and output-location policy, not geometry. |
| Document Manager or mesh import could avoid a live SolidWorks session | Disproven for this unit. Document Manager does not create FeatureManager solids. Keen FBX/MWM import is forbidden. |
| A mock adapter could be added without settling architecture | Disproven as a silent path. Binding locators, choosing COM vs remoting, choosing an output root, and adding `pywin32` are the open decisions. |
| Official 2026 API cannot natively build these four solids | Disproven as a blocker. `FeatureExtrusion2`, `CreateBodyFromBox3`, `ICreateBodyFromFaces3`, `CreateFeatureFromBody3`, `Operations2`, `GetPartBox`, mass-property APIs, `GetBodies2`, and `SaveAs3` exist in the 2026 help set. |
| Implementation leaked past the decision boundary | Disproven. This session changed only this state file. No backend package, dependency, path, or `.sldprt` was added. |
| Parser/catalog/IR/transform/library recipes were modified or S2C-5.1.1 started | Disproven. Those trees were not modified by this session. |

Remediated: none. No product defect was introduced. The unit is BLOCKED, not DEV-COMPLETE.

Accepted residual risk: several 2026 help pages are JavaScript-rendered and did not return full parameter remarks to this session. Method existence is evidenced by official 2026 URLs and titles; exact argument lists must be re-read on a machine that can render those pages, or against a live type library, before any COM call is written. API lengths are metres by long-standing COM convention; that conversion must be proven against a live session, not assumed as millimetres.

Not claimed: SolidWorks part production, a chosen remoting design, in-tree `.SLDPRT` publication, or QUALIFIED.

## Quality/security assessment (S2C-4.1.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Library defines a competing coordinate system | Disproven. `CANONICAL_LOCAL_FRAME` copies `SE_DIRECTION_VECTORS` Right/Up/Backward and `LARGE_GRID_CELL_PITCH_MM`. Origin is cell center. Tests require identity Forward/Up to leave vertices unchanged and a known S2C-3.1.1 rotation to map the Corner right-angle vertex with no extra translation. |
| Axis or sign error in identity Slope/Corner/InvCorner | Disproven against Keen topology edge signs. Slope vertices satisfy `Y+Z <= 0` and omit the Up-Backward cube corners. Corner is the Right-Down-Forward tetrahedron. InvCorner is the cube minus that vertex. |
| A shape that merely resembles SE armor was accepted | Disproven. Recipes are the topology-table solids (vertex signs + construction), not visual approximations. |
| Corner/InvCorner required extracted Keen mesh | Disproven. Both are finite CubeTopology edge tables. No FBX/MWM/mesh data was imported. |
| Bounding-box equality collapses the four solids | Disproven. All four share the cell AABB; vertex sets, face counts, `volume_times_6_mm3`, and `SolidKind` remain distinct. Corner ∪ InvCorner reconstructs the cube volume. |
| Recipes are insufficient for later deterministic construction | Disproven. Each record carries `solid_kind`, exact millimetre vertices, outward faces, and a construction spec (box / YZ prism / tetrahedron / box-minus-tetrahedron). InvCorner reuses the Corner tetrahedron. |
| Pitch or half-extent literals were copied | Disproven. Library source has no `2500` or `1250`. Half-extent is `LARGE_GRID_CELL_PITCH_MM // 2`. |
| Game-install or CAD backend dependency | Disproven. Library imports are stdlib plus catalog constants/model, parser `Direction` tokens, and transform direction vectors. No SolidWorks, COM, Blender, subprocess, SQLite, Steam, or asset paths. Tests pass without a game install. |
| Proprietary assets or machine paths were committed | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or `.sldprt` added. Fixture SHA-256 unchanged. |
| Unknown geometry IDs are aliased or folded | Disproven. Lookup is exact `geometry_id` equality. Tests reject subtype strings, case variants, and padding. |
| Parser/catalog/IR/transform were modified or S2C-4.2.1 started | Disproven. Those trees were not modified. No COM, SLDPRT production, mates, or print-prep. SLDPRT location remains an open question. |
| Unrelated refactoring | Disproven. Changes are the library package, package exports, library architecture contract, README capability text, tests, and this state file. |

Remediated: first face-winding set produced a negative closed-mesh volume (inward cube faces). Faces were corrected so `volume_times_6_mm3` is positive and matches the exact Box/Slope/Corner/InvCorner volumes. A transform-invariant regression test was added. Tests re-run after remediation: 103 OK.

Accepted residual risk: this session could not re-inspect current `Sandbox.Game.dll` topology tables because no local Space Engineers install was present. The first four `MyCubeTopology` entries and their edge tables have been stable since the published Keen source; changing them would break existing worlds. A later backend must apply the S2C-3.1.1 column-vector transform to these local solids and must not invent a second frame. `LibraryRecord` can be constructed directly; the conversion path looks up by catalog `geometry_id`.

Not claimed: SolidWorks part production, in-game visual re-check, or that native recipes settle copyright/redistribution status of later CAD documents ([ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md)).

## Quality/security assessment (S2C-3.1.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Axis swap (X/Y/Z permutation) | Disproven. Direction vectors match local XML and Keen tables. Fixture `(1,0,0)`, `(0,1,0)`, `(0,0,1)` translate on the corresponding millimetre axes only. |
| Sign inversion | Disproven. Negative-Z fixture cells remain negative. `Right × Up = Backward = +Z`. |
| Accidental reflection | Disproven. All 24 legal rotations have determinant `+1`. Derived Left matches the local Keen `LeftDirections` table. |
| Wrong matrix multiply convention | Disproven for the documented contract. `apply((1,0,0))` is Right, `(0,1,0)` is Up, `(0,0,1)` is Backward. |
| Wrong Forward/Up cross-product order | Disproven. Right is `Forward × Up`. Reversing it would make Left and det `−1`; the Keen Left table test would fail. |
| Duplicate orientation mapping | Disproven. 24 legal pairs produce 24 distinct matrices. |
| Invalid orientation silently accepted | Disproven. Same-axis and opposite-axis pairs raise `InvalidOrientationError`. |
| Half-cell translation error | Disproven. `Min=(0,0,0)` maps to `(0,0,0)` mm, not `1250`. No `1250` or `0.5` in transform/IR source. |
| Floating-point drift | Disproven. Rotation and translation use integer arithmetic only. Tests assert `int` entries. |
| Parser/catalog identity loss | Disproven. Acceptance IR keeps exact `subtype_id`, `geometry_id`, `Min`, Forward/Up, and source index. |
| CAD/SolidWorks leakage into IR | Disproven. IR/transform imports are stdlib plus parser/catalog/transform types. No SolidWorks, COM, Blender, or part-file imports. |
| Pitch literal duplicated | Disproven. Transform/IR source has no `2500`. Translation imports `LARGE_GRID_CELL_PITCH_MM`. |
| Mapping based only on stale Internet source | Disproven. Local current XML/DLL tables were inspected first; Keen source was corroboration. |
| Parser/catalog architecture changed or later units started | Disproven. `src/se2cad/parser/` and `src/se2cad/catalog/` were not modified. No solids, SLDPRT, mates, or S2C-4.1.1 library recipes. |
| Unrelated refactoring | Disproven. Changes are IR, transform, tests, package exports, and the architecture contract this unit was required to write. |

Remediated: neutrality tests initially treated “no SolidWorks” docstring prose as type leakage. Tests now check imports, not exclusionary wording. Product code did not change for that finding. Tests re-run after remediation: 85 OK.

Accepted residual risk: `RotationMatrix` is a value type and can be constructed directly; the conversion path always goes through `rotation_from_forward_up`. VRage stores the same basis as rows; a later backend must use this column-vector contract, not silently reuse VRage `Mij` layout.

Not claimed: SolidWorks validation, in-game visual re-check, or multi-cell occupancy transforms.

## Quality/security assessment (S2C-2.1.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Subtype identity is case-folded or whitespace-normalized | Disproven. Lookup is exact `==` on the stored string. Tests reject `largeblockarmorblock`, `LARGEBLOCKARMORBLOCK`, padded, and mixed-case forms. Catalog source has no `casefold` / `lower` / `strip`. |
| Duplicate subtype or geometry IDs are ambiguous | Disproven. Loader rejects duplicate `subtype_id` and duplicate `geometry_id`. |
| Malformed catalog data is silently accepted | Confirmed then remediated. Missing required fields, bad JSON, unknown recipe/support tokens, and non-integer sizes already failed. Extra unknown fields (for example an observed `model` path) were ignored. Loader now rejects unexpected fields; regression test added. |
| Observed Keen facts are stored as SE2CAD decisions | Disproven. JSON and domain types split `observed` from `se2cad`. Geometry IDs are not Keen subtype strings. |
| Machine-specific paths were committed | Disproven. Packaged JSON has no `/home/`, `C:\`, Steam, or Space Engineers paths. Tests assert this. |
| Proprietary asset references were committed | Disproven. Catalog records TypeId/SubtypeId/CubeSize/Size/topologies only. No `.mwm`, `.fbx`, `.dds`, or model paths. Extra-field rejection blocks smuggling a model path into schema v1. |
| Catalog loader opens paths taken from blueprint content | Disproven. Default load uses `importlib.resources` for the packaged file. `load_catalog_file` is an explicit caller-supplied path for tests; parser output is never passed to it. |
| A runtime game-install scan is required | Disproven. Tests pass without reading the Steam tree. Catalog modules do not mention Steam or `Content/Data`. |
| Unnecessary dependency or database was introduced | Disproven. Stdlib `json` only. No SQLite. `pyproject.toml` still has no runtime dependencies. |
| Catalog leaked into transforms/CAD or changed the parser | Disproven. Catalog imports are stdlib plus local catalog types. Parser tree `src/se2cad/parser/` has no catalog types and was not modified. No SolidWorks, COM, matrix, or SLDPRT code. |
| Fixture counts were baked into catalog code | Disproven. Source grep of `src/se2cad/catalog/` found no `24`. |
| Unrelated refactoring or S2C-3.1.1 started | Disproven. No IR, placement transforms, or coordinate-frame work. |

Remediated: reject unexpected catalog JSON fields. Tests re-run after remediation: 58 OK.

Accepted residual risk: `load_catalog_file` will read any file path the caller supplies. That API is for tests and explicit local samples, not the conversion path. Schema v1 is closed; adding a field requires a schema-version change.

Not claimed: SolidWorks validation, Space Engineers runtime validation, or that `native_procedural` geometry exists.

## Quality/security assessment (S2C-1.2.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Malformed or entity-bearing XML is accepted | Disproven. `xml.etree.ElementTree` can expand internal entities when a DOCTYPE is present; the parser rejects `<!DOCTYPE`, `<!ENTITY`, and XInclude markers before parse. Tests cover malformed XML, DOCTYPE/entity, XInclude, and a file-URI entity that must not be read. |
| XML values cause arbitrary file access | Disproven. No XML-derived paths are opened. The only filesystem read is the operator-selected blueprint path. XXE canary file was not read. |
| XML values are executed or passed to a shell | Disproven. Parser imports are stdlib XML/path/typing plus local parser types. No `subprocess`, `os.system`, `eval`, or `exec`. |
| Multiple grids are silently accepted | Disproven. Zero, multiple, and nested `CubeGrid` raise `UnsupportedBlueprintError`. |
| Unknown direction tokens are remapped | Disproven. Unknown tokens and non-orthogonal pairs raise `InvalidFieldError`. |
| Subtype identity is normalized or collapsed | Disproven. Acceptance test requires the four exact subtype strings and counts; parser has no armor-category mapping. |
| Omitted Min/orientation defaults were guessed | Disproven. Defaults were established from local SE resources and published Keen serialization methods before implementation; see omitted-field semantics above. |
| SolidWorks / CAD types leaked into the parser | Disproven. No SolidWorks, COM, matrix, geometry-ID, or catalog types in `src/se2cad`. |
| Proprietary SE assets were added | Disproven. No `.mwm`, `.fbx`, `.dds`, `.hkt`, or game/SDK trees added. Negative fixtures are SE2CAD-authored XML strings. Qualified `bp.sbc` SHA-256 unchanged. |
| Unnecessary dependencies or a CLI were introduced | Disproven. Stdlib only. `pyproject.toml` is packaging metadata with no runtime dependencies. No CLI. |
| Missing path was reported as malformed XML | Confirmed. `parse_blueprint` used `MalformedXmlError` for a non-file path. Remediated to `BlueprintParseError`; regression test added. |
| Multi-block `SubBlocks` were silently ignored | Confirmed. Ordinary extra cube-block metadata (e.g. `BuiltBy`) is ignored; `SubBlocks` / `MultiBlockId` / `MultiBlockDefinition` are unsupported structural forms. Remediated to `UnsupportedBlueprintError`; regression test added. |
| Fixture counts were baked into parser code | Disproven. Source grep of `src/` found no `24` or subtype-count constants. Counts live in tests. |
| Unrelated refactoring or later units started | Disproven. No catalog schema, CAD transforms, or S2C-2.1.1 work. |

Remediated: missing-path error type; reject multi-block cube-block children. Tests re-run after remediation: 32 OK.

Accepted residual risk under the local single-user trust model: the parser reads the whole file into memory and does not impose an arbitrary size cap. A cheap `xinclude` substring rejection can refuse an otherwise-supported document whose text happens to contain that marker.

Not claimed: SolidWorks validation, Space Engineers runtime validation, or that the parser is an Internet-facing XML upload service.

## Quality/security assessment (S2C-0.1.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Architecture mistaken for implemented capability | README and architecture docs state they are design, not capability. Architecture “as of S2C-0.1.1” banners were removed so they cannot become a second live ledger. |
| More than one live-status document | STATE is the only status table. PLAN, PROGRAM, architecture, and fixture spec declare they are not live status. |
| Plan carries live status | No status field or status table in PLAN. Status words there are completion-criteria evidence bars only. |
| Session could select work without STATE | Rules, ratchet, process, onboarding, and PLAN header require STATE-first selection. |
| Ratchet allows multiple units | Ratchet and process require exactly one unit and an explicit stop. |
| Apache-2.0 treated as a Keen-asset license | Rule 30, ADR-004, fixtures README, and gitignore safety-net. |
| Derived CAD assumed redistributable | README, ADR-004, and rule 30 forbid that assumption. |
| Human/AI authority ambiguous | Process and rule 00 list exclusive human authorities, including git publication and licensing. |
| QUALIFIED without evidence | Vocabulary requires named evidence. This unit required none external; qualification is repository inspection. |
| SolidWorks validation claimed without SolidWorks | No SolidWorks unit was executed. Later SW units split DEV-COMPLETE and QUALIFIED. |
| Initial program includes Blender / TriangleMesh / printing | Those appear only as exclusions. No implementation milestones for them. |
| Broken or circular cold-start references | Links rechecked after remediations. Reading order is linear (rules → process → STATE → program → plan → architecture → contract → unit specs). |
| Standard Apache-2.0 appendix text treated as unfinished repository placeholders | Corrected. The appendix example instructions are not incomplete fields. `LICENSE` was pre-existing and was not modified by bootstrap. |
| `native_procedural` authorship treated as settling ownership and project-license status | Corrected in ADR-004. No Keen mesh import is distinct from redistributing extracted Keen geometry; it does not settle copyright, derivative-work, or redistribution status. |

Remediated before QUALIFIED: architecture snapshot banners; Python recorded as if it were an architectural decision; “implements” wording that could read as present capability; fixture name clarified as four subtypes, not four instances; PLAN header forbids selecting work from the plan; contract states README must not run ahead of STATE.

Remediated after QUALIFIED, before first commit: `LICENSE` appendix misdescribed as unfinished placeholders; ADR-004 categorical claim that `native_procedural` armor solids remain SE2CAD-owned under the project license.

Not changed (pre-existing, human-owned): `LICENSE` file content.

## Quality/security assessment (S2C-1.1.1)

Hypotheses tested and outcomes:

| Hypothesis | Outcome |
| --- | --- |
| Proprietary game/SDK assets committed with the fixture | Disproven. Fixture tree contains only `bp.sbc` (XML text, 8967 bytes) and `PROVENANCE.md`. Repository scan found no `.mwm`, `.fbx`, `.dds`, `.hkt`, `.sldprt`, `.sldasm`, textures, or `KeenModSDK` / `SpaceEngineers/Content` trees. |
| Unexpected additional block types | Disproven. 24/24 blocks are `MyObjectBuilder_CubeBlock` with the four allowlisted subtypes. Counts match the operator-stated expected counts, established from the file rather than taken as proof in advance. |
| Malformed or entity-expanding XML stored as a fixture | Disproven for this file. Well-formed XML; no DOCTYPE, entity declarations, non-predefined entity references, or XInclude. This is a storage/inspection finding, not a product-parser guarantee. |
| `bp.sbc` modified, normalized, or rewritten during registration | Disproven. SHA-256 `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31` before inspection, after inspection, and after documentation writes. File remains UTF-8 with CRLF (169 CRLF, 0 lone LF). |
| Unrelated repository changes | Disproven. Git status after this unit: untracked `fixtures/acceptance/` (operator `bp.sbc` plus `PROVENANCE.md`) and the intended STATE update. No `src/`, `tests/`, `tools/`, PLAN, architecture, or language-selection changes. |
| Provenance claims exceed available evidence | Checked. Authorship and “created for SE2CAD acceptance testing” are recorded as operator-stated facts from this unit, not as XML-derived facts. File identity fields are quoted from inspection. No licensing conclusion beyond ADR-004. ShipBlueprint `DisplayName` was recorded as stored (`Kolyma` with U+E030 prefix), not rewritten to `se2cad-test1`. |
| Fixture identity confused with player/ship wrapper name | Observed, not a defect. CubeGrid `DisplayName` and ShipBlueprint `Id` Subtype are `se2cad-test1`. ShipBlueprint `DisplayName` is U+E030 + `Kolyma`. Human confirmation attached to the registered file, not to the wrapper display string. |
| Parser or catalog implementation leaked into this unit | Disproven. Inspection was a temporary command. `src/`, `tests/`, and `tools/` still contain only `.gitkeep`. |

Remediated: none. No verified findings required a code or fixture change.

Not claimed: SolidWorks validation, in-game visual re-check, or that Apache-2.0 licenses the blueprint format or Keen subtype identifiers.
