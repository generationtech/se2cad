# Fixtures

Committed test data for SE2CAD.

Nothing in this directory may be a Space Engineers game asset, Keen ModSDK file, MWM/texture dump, or other redistribution-uncertain binary. See [ADR-004](../docs/technical/adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).

User-authored blueprints may be added when provenance is recorded. Do not embed game or SDK meshes beside them.

Additional fixtures may be added only by an approved unit, with provenance, and must not embed game or SDK geometry.

## Acceptance fixture (initial program)

Specified in [INITIAL_ACCEPTANCE_FIXTURE.md](../docs/testing/INITIAL_ACCEPTANCE_FIXTURE.md).

Expected tree after S2C-1.1.1. Whether those files exist is recorded in [SE2CAD_STATE.md](../docs/technical/governance/SE2CAD_STATE.md):

```
fixtures/acceptance/four-block-armor-asymmetric/bp.sbc
fixtures/acceptance/four-block-armor-asymmetric/PROVENANCE.md
```

Do not invent a substitute blueprint.
