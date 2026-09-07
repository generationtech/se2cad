# SE2CAD engineering process

Responsibility: how engineering work is performed — authority, bounded intent, ratchet, verification, status words, and stopping behavior.

Program objective and exclusions: [SE2CAD_PROGRAM.md](SE2CAD_PROGRAM.md).
Unit definitions: [SE2CAD_PLAN.md](SE2CAD_PLAN.md).
Live status: [SE2CAD_STATE.md](SE2CAD_STATE.md) only.

## Authority

The human architect retains exclusive authority over architecture and architectural changes, project scope, technology-selection changes, sequencing or creation/removal of planned units, significant tradeoff acceptance, licensing, publishing or distribution of third-party or derived assets, and git commit, tag, push, release, and deployment.

Within an explicitly authorized bounded unit, an agent may inspect the repository, modify files the unit reasonably requires, add or update tests, run verification, perform a distinct quality/security assessment, remediate verified defects, update durable repository state, and report results.

An agent must not silently change architecture, expand scope because adjacent work appears useful, invent new roadmap units while executing a unit, automatically begin a subsequent unit, commit/tag/push/publish/release unless explicitly asked, claim validation that was not performed, or introduce proprietary third-party assets because SE2CAD is Apache-2.0 licensed.

If correct execution requires an architectural decision or meaningful scope expansion, stop and report.

## Bounded intent

A unit is defined by its engineering objective, not by an arbitrary file list. One coherent change may touch source, tests, documentation, fixtures, and metadata.

Do not create artificially tiny units. Do not execute a unit so large that one fresh session cannot implement, test, assess, remediate, update state, and stop.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| PLANNED | Defined in the plan and not started. |
| ACTIVE | Being executed by the current bounded session. |
| DEV-COMPLETE | Implementation complete, development validation passed, distinct quality/security assessment completed, verified findings remediated. |
| QUALIFIED | DEV-COMPLETE plus any external/application validation the unit explicitly requires, with real evidence. |
| BLOCKED | Cannot execute; the blocker is recorded in STATE. |
| SUPERSEDED | Replaced or absorbed by an explicitly approved plan change. |

DEV-COMPLETE is a legitimate completion state. Do not invent external validation merely to obtain QUALIFIED.

Examples:

- A pure parser unit with no external-validation requirement may become QUALIFIED from deterministic automated tests.
- A SolidWorks automation unit may be DEV-COMPLETE on mocked or unit evidence and remain unqualified until a real SolidWorks run exists if the unit requires that evidence.
- The acceptance fixture may require comparison against the observed Space Engineers object before QUALIFIED.

Never update status prospectively. STATE is the only live status location. The plan must not duplicate live status.

## Ratchet

Execute this sequence once per session, for one unit.

1. **Read repository state.** Establish current truth from STATE, implementation, tests, and the contracts the unit needs.
2. **Select and understand the approved unit.** Take the next executable unit from STATE. Read its full definition in the plan. Confirm prerequisites, boundaries, and completion criteria.
3. **Implement.** Only that bounded objective.
4. **Test / functionally verify.** Produce evidence that the intended behavior exists. Add regression tests as appropriate.
5. **Perform a distinct quality/security assessment.** Change posture after functional work. Search for weaknesses such as unsafe path handling, XML parser hazards, malformed blueprint handling, arbitrary file overwrite, unsafe subprocess or command injection, COM automation misuse, temp-file leakage, proprietary asset leakage, coordinate/orientation edge cases, silent unsupported-block handling, nondeterministic generation, dependency/provenance problems, and tests that assert implementation details without proving behavior. Scale depth to actual risk.
6. **Remediate verified findings and reverify.** Fix established defects. Re-run functional verification. Add regression protection where appropriate.
7. **Update durable repository state.** Update STATE, and any architecture or contracts actually changed by evidence. Record what happened, never what is merely intended.
8. **Stop and report.** Report unit executed, implementation summary, tests/verification and evidence, quality/security findings, remediation, external validation still required, durable state updated, deliberately untouched scope, and the next unit for information only. Then stop. Never automatically start the next unit.

## Verification doctrine

- Prefer tests that prove externally meaningful behavior over tests of incidental structure.
- Treat blueprints, paths, and other user-supplied data as untrusted.
- Distinguish development evidence (unit/integration/mocks) from application evidence (SolidWorks session, observed Space Engineers structure) when a unit names the latter.
- Committed fixtures need provenance. See [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md) and [INITIAL_ACCEPTANCE_FIXTURE.md](../../testing/INITIAL_ACCEPTANCE_FIXTURE.md).

## Reading model

Do not ingest every repository document. Use the order in [SE2CAD_DEVELOPER_ONBOARDING.md](../../cursor/SE2CAD_DEVELOPER_ONBOARDING.md). Paste [SE2CAD_RATCHET.md](../../cursor/SE2CAD_RATCHET.md) to start a fresh session.
