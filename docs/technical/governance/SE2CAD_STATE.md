# SE2CAD state

Responsibility: what has actually happened. This is the only authoritative live program-status location.

How status words are used: [SE2CAD_ENGINEERING_PROCESS.md](SE2CAD_ENGINEERING_PROCESS.md).
Unit definitions (no live status): [SE2CAD_PLAN.md](SE2CAD_PLAN.md).

## Current program

Initial program: four Large Grid armor subtypes, single grid, SolidWorks assembly via canonical reusable parts. See [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md).

The program is not complete. A single-grid Large Grid blueprint parser exists. No catalog, IR, transform engine, block library, or SolidWorks backend exists in the tree.

Public capability text in [README.md](../../../README.md) matches this: conversion is not implemented.

## Next executable unit

**S2C-2.1.1 — Catalog for the four Large Grid armor types**

Information only. Do not start it in the same session that completed S2C-1.2.1.

## Unit status

| Unit | Status | Evidence |
| --- | --- | --- |
| S2C-0.1.1 | QUALIFIED | Bootstrap documents and rules exist; local links resolve; plan has no live status; no M1+ implementation; no proprietary game/SDK assets; distinct assessment recorded below; findings remediated. External validation was not required. |
| S2C-1.1.1 | QUALIFIED | Operator-supplied `bp.sbc` registered unmodified at the specified path; `PROVENANCE.md` present; deterministic inspection recorded below; human architect confirmed this is the intended `se2cad-test1` object; distinct assessment recorded below; no verified findings requiring remediation. |
| S2C-1.2.1 | QUALIFIED | Python parser and tests exist; qualified acceptance fixture extracts expected subtype/position/orientation values; unsafe and unsupported XML is rejected; distinct assessment recorded below; findings remediated and tests re-run. External validation was not required. |
| S2C-2.1.1 | PLANNED | Not started. |
| S2C-3.1.1 | PLANNED | Not started. |
| S2C-4.1.1 | PLANNED | Not started. |
| S2C-4.2.1 | PLANNED | Not started. |
| S2C-5.1.1 | PLANNED | Not started. |
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

## Resolved technology selections

These are human-architect technology selections recorded as live decisions. They are not architectural ADRs and were not invented as a new planning artifact.

| Decision | Resolution | Recorded |
| --- | --- | --- |
| Implementation language | Python | S2C-1.2.1. Confirmed by the human architect for this unit. |

## Open questions

These are not invitations to decide them inside an unrelated unit.

- CLI / entrypoint shape.
- Whether canonical SLDPRT documents live in-tree or in a generated local cache.
- How users configure SolidWorks, and optionally a local game or SDK install path, when a unit needs that.
- Numeric position/orientation tolerances for S2C-6.1.1 (recorded when that unit produces evidence).
- Exact Space Engineers Forward/Up basis mapping to the library reference frame (established with evidence in S2C-3.1.1; stop and ask if it cannot be proven).

## Known blockers

None recorded as BLOCKED.

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
