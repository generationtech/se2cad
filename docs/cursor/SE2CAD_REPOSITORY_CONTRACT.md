# SE2CAD repository contract

Responsibility: repository layout and structural/semantic invariants. Not live program status.

## Layout

```
.cursor/rules/                 Session constraints (point to docs; not a second governance tree)
docs/cursor/                   Onboarding, this contract, ratchet prompt
docs/technical/architecture/   Durable architectural contracts
docs/technical/governance/     Process, current and historical program/plan, state
docs/technical/adr/            Individual accepted decisions
docs/testing/                  Test and fixture specifications
fixtures/                      Committed test data with recorded provenance
src/                           Implementation
tests/                         Automated tests
tools/                         Maintainer utilities (empty until a unit needs one)
```

Do not add placeholder implementation modules solely to populate `src/`, `tests/`, or `tools/`.

## Document invariants

- [SE2CAD_STATE.md](../technical/governance/SE2CAD_STATE.md) is the only document that may carry live unit status. It names the current program and plan.
- The current plan (presently [SE2CAD_PLAN_M7.md](../technical/governance/SE2CAD_PLAN_M7.md)) defines executable units and must not duplicate live status. [SE2CAD_PLAN.md](../technical/governance/SE2CAD_PLAN.md) is the completed initial-program unit catalog.
- Architecture documents describe decided design. They are not capability claims and must not carry a live implementation ledger.
- The public README may describe user-visible capability. It must not run ahead of evidence in STATE.
- Cursor rules stay short and refer here and to governance documents for detail.

## Engineering invariants

- CAD-neutral IR sits between parsing and CAD backends. IR must not contain SolidWorks COM objects or API structures. See [ADR-002](../technical/adr/ADR-002_INTERMEDIATE_REPRESENTATION.md).
- Transform calculation is a separate subsystem from the SolidWorks backend. Large Grid cell pitch is 2500 mm and must live in one named constant, not be copied through application code.
- Generated assemblies place components by calculated transform. Do not reconstruct fixed Space Engineers placement with a mate network.
- The runtime converter asks the canonical block library for a part and its reference metadata. It does not call Blender. See [ADR-001](../technical/adr/ADR-001_CANONICAL_BLOCK_LIBRARY.md) and [ADR-003](../technical/adr/ADR-003_SOLIDWORKS_BACKEND.md).
- CubeTopology armor and TriangleMesh functional blocks are different geometry classes. Do not force one production mechanism. TriangleMesh work is outside the initial program.
- Core parser, catalog, IR, transforms, library, and statistics stay CAD-backend-neutral. SolidWorks is the first backend, not the name of the core.

## Asset invariants

- This public tree must not contain Space Engineers game assets, Keen ModSDK geometry, MWM/texture dumps, or redistribution-uncertain binaries. See [ADR-004](../technical/adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).
- User-authored blueprint fixtures require a provenance record. Do not embed game/SDK meshes in fixtures.
- Apache-2.0 covers SE2CAD-owned material only.

## Git publication

Commit, tag, push, release, and deployment are human-architect actions. Agents do not perform them unless the human explicitly asks in that session.
