# SE2CAD state

Responsibility: what has actually happened. This is the only authoritative live program-status location.

How status words are used: [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md).
Unit definitions (no live status): [SE2CAD_PLAN.md](SE2CAD_PLAN.md).

## Current program

Initial program: four Large Grid armor subtypes, single grid, SolidWorks assembly via canonical reusable parts. See [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md).

The program is not complete. A single-grid Large Grid blueprint parser, a four-entry Large Grid armor catalog, a CAD-neutral IR, an exact placement transform engine, native-procedural recipes for the four Large Grid armor solids, and a Windows-local SolidWorks backend exist. Generated canonical `.SLDPRT` files are not in the tree. Assembly generation is not implemented.

Public capability text in [README.md](../../../README.md) matches this: assembly conversion is not implemented; live SolidWorks 2026 qualification of the four parts is recorded only here.

## Next executable unit

**S2C-4.2.1 — Produce reusable SolidWorks canonical parts**

DEV-COMPLETE. QUALIFIED is blocked: this Linux host still has no SolidWorks 2026 session. Do not start S2C-5.1.1. Resume S2C-4.2.1 in the Windows VM and run the integration test with `SE2CAD_SOLIDWORKS_INTEGRATION=1`. Skipped integration tests are not qualification evidence.

## Unit status

| Unit | Status | Evidence |
| --- | --- | --- |
| S2C-0.1.1 | QUALIFIED | Bootstrap documents and rules exist; local links resolve; plan has no live status; no M1+ implementation; no proprietary game/SDK assets; distinct assessment recorded below; findings remediated. External validation was not required. |
| S2C-1.1.1 | QUALIFIED | Operator-supplied `bp.sbc` registered unmodified at the specified path; `PROVENANCE.md` present; deterministic inspection recorded below; human architect confirmed this is the intended `se2cad-test1` object; distinct assessment recorded below; no verified findings requiring remediation. |
| S2C-1.2.1 | QUALIFIED | Python parser and tests exist; qualified acceptance fixture extracts expected subtype/position/orientation values; unsafe and unsupported XML is rejected; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-2.1.1 | QUALIFIED | Packaged JSON catalog and loader exist; four Large Grid armor subtypes resolve to distinct SE2CAD geometry IDs; unknown/malformed/duplicate catalog data fails closed; acceptance fixture 24 blocks resolve; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-3.1.1 | QUALIFIED | CAD-neutral IR and integer transform engine exist; 24 fixture blocks convert through parser+catalog; all 24 legal Forward/Up orientations are unique right-handed integer rotations; invalid pairs fail closed; distinct assessment recorded below; no verified findings requiring remediation after test-scan false positives were corrected. External validation was not required. |
| S2C-4.1.1 | QUALIFIED | Library records and four native-procedural recipes exist; catalog geometry IDs resolve 1:1; recipes consume the qualified S2C-3.1.1 frame and `LARGE_GRID_CELL_PITCH_MM`; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-4.2.1 | DEV-COMPLETE | Windows-local backend implemented; human architecture decisions recorded; Linux suite 130 tests OK (1 integration skipped). No live SolidWorks 2026 run. No `.SLDPRT` generated or committed. QUALIFIED remains blocked on Windows VM execution. |
| S2C-5.1.1 | PLANNED | Not started. Do not start until S2C-4.2.1 is QUALIFIED. |
| S2C-6.1.1 | PLANNED | Not started. |

## Session history

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

## Open questions

These are not invitations to decide them inside an unrelated unit.

- CLI / entrypoint shape. S2C-4.2.1 added only `python -m se2cad.solidworks` as a Windows operator entry, not a general CLI.
- How a later unit configures an optional local game or SDK install path when that unit needs it. The Windows SolidWorks path does not.
- Numeric position/orientation tolerances for S2C-6.1.1 (recorded when that unit produces evidence).

Resolved in S2C-4.2.1 and no longer open: generated SLDPRT location (local generated root); Linux-to-Windows invocation (out of scope; operator-managed clones and blueprint copy); SolidWorks configuration for this unit (`SE2CAD_GENERATED_ROOT` / `se2cad.local.json` / optional part-template env); in-process Windows COM vs remoting (COM, no remoting); pywin32 as a Windows-only optional dependency.

## Known blockers

**S2C-4.2.1 QUALIFIED** is blocked because this Linux agent host cannot open SolidWorks 2026. Implementation is DEV-COMPLETE. Qualification requires an operator run inside the Windows VM against the synchronized repository clone:

```
set SE2CAD_GENERATED_ROOT=<local generated directory>
set SE2CAD_SOLIDWORKS_INTEGRATION=1
PYTHONPATH=src python -m unittest tests.test_solidworks_integration -v
```

Skipped integration tests are not qualification evidence. Do not start S2C-5.1.1.

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
| Construction | Box and slope: `FeatureExtrusion2` mid-plane. Corner: recipe faces knitted via `CreatePlanarSurface2` / `CreateTrimmedSheet5` / `CreateBodyFromFaces2`. InvCorner: `CreateBodyFromBox3` minus that tetrahedron via `IBody2.Operations2`. |
| Pipeline without SE/SDK | `resolve_recipes_from_blueprint` on `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc` resolves 24 IR blocks and the four recipes. Proven on Linux. Not yet proven inside the Windows VM. |

**API evidence used for COM calls** (official 2026 pages exist but are JS-rendered; signatures from those titles plus static/CodeStack sources). Live typelib was not inspected.

| Method | Evidence |
| --- | --- |
| `SldWorks.Application` / `gencache.EnsureDispatch` | Long-standing COM ProgID; 2026 client is Windows-only |
| `GetUserPreferenceStringValue(swDefaultTemplatePart)` + `NewDocument` | Official/new-document samples; avoids a hardcoded template path |
| `FeatureExtrusion2` (20 args; `swEndCondMidPlane=6`; depths metres) | Official 2026 method page exists; 20-arg VBA samples; `swEndCondMidPlane` documented as 6 |
| `SketchManager.CreateCornerRectangle` / `InsertSketch` / `Insert3DSketch` / `CreateLine` | Published FeatureManager sketch samples; 3D-sketch lines use model metres |
| `IModeler.CreateBodyFromBox3` (9 doubles: center, axis, size; metres) | Official 2026 page exists; CodeStack create-box-body |
| `IModeler.CreatePlanarSurface2` + `ISurface.CreateTrimmedSheet5` | Official 2026 CreatePlanarSurface2 page; CodeStack multi-extrude (`0.00001` m trim) |
| `IModeler.CreateBodyFromFaces2` | Official 2026 `ICreateBodyFromFaces3` / CreateBodyFromFaces2 pages; CodeStack fill-hole |
| `IBody2.Operations2` + `IPartDoc.CreateFeatureFromBody3` | Official Operations2 page; CADSharp/CreateFeatureFromBody3 samples |
| `GetBodies2`, `GetPartBox`, `Extension.CreateMassProperty` | Official 2026 validation method pages named in the inspection session |
| `Extension.SaveAs`, `OpenDoc6`, `CloseDoc` | Official save/open/close; save is rejected unless the file exists afterwards |

Windows environment from this session: not available. Python 3.12.3 on Linux Mint 22.1 / kernel 6.8.0-138-generic. `win32com` not installed.

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
