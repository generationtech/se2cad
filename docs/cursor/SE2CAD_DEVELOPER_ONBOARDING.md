# SE2CAD developer onboarding

Responsibility: orientation and reading map. This document is not authoritative program state, architecture, or process.

SE2CAD is an early-stage project. Conversion software is not implemented yet. Start with the documents below; do not ingest the entire repository on every session.

## Fresh development session

Read in this order, then stop reading unless the selected unit requires more:

1. `.cursor/rules/` (session constraints)
2. [SE2CAD_ENGINEERING_PROCESS.md](../technical/governance/SE2CAD_ENGINEERING_PROCESS.md) (how work is done)
3. [SE2CAD_STATE.md](../technical/governance/SE2CAD_STATE.md) (what has actually happened; next unit)
4. [SE2CAD_PROGRAM.md](../technical/governance/SE2CAD_PROGRAM.md) (why the initial program exists)
5. [SE2CAD_PLAN.md](../technical/governance/SE2CAD_PLAN.md) (the selected unit's full definition)
6. [ARCHITECTURE_OVERVIEW.md](../technical/architecture/ARCHITECTURE_OVERVIEW.md) (decided architecture)
7. [SE2CAD_REPOSITORY_CONTRACT.md](SE2CAD_REPOSITORY_CONTRACT.md) (layout and invariants)
8. Only those architecture or specification documents the selected unit actually touches

A pasteable one-unit prompt is [SE2CAD_RATCHET.md](SE2CAD_RATCHET.md).

## Authority map

| Need | Document |
| --- | --- |
| How to execute a unit, status words, ratchet, stop rules | [SE2CAD_ENGINEERING_PROCESS.md](../technical/governance/SE2CAD_ENGINEERING_PROCESS.md) |
| Live unit status and next work | [SE2CAD_STATE.md](../technical/governance/SE2CAD_STATE.md) only |
| Initial program objective, exclusions, end state | [SE2CAD_PROGRAM.md](../technical/governance/SE2CAD_PROGRAM.md) |
| Bounded unit definitions (no live status) | [SE2CAD_PLAN.md](../technical/governance/SE2CAD_PLAN.md) |
| Decided system architecture | [ARCHITECTURE_OVERVIEW.md](../technical/architecture/ARCHITECTURE_OVERVIEW.md) |
| Block library contract | [BLOCK_LIBRARY_ARCHITECTURE.md](../technical/architecture/BLOCK_LIBRARY_ARCHITECTURE.md) |
| Converter pipeline contract | [BLUEPRINT_CONVERTER_ARCHITECTURE.md](../technical/architecture/BLUEPRINT_CONVERTER_ARCHITECTURE.md) |
| Individual decisions and rationale | [docs/technical/adr/](../technical/adr/) |
| Fixture definition | [INITIAL_ACCEPTANCE_FIXTURE.md](../testing/INITIAL_ACCEPTANCE_FIXTURE.md) |
| Third-party asset policy | [ADR-004](../technical/adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md) |
| Public project description | [README.md](../../README.md) |

## Public visitors

If you are browsing GitHub and are not executing a development unit, [README.md](../../README.md) is enough. Governance documents are for people changing the repository.
