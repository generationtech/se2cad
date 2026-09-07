# Initial acceptance fixture

Responsibility: definition and expected validation behavior of the four-block vertical-slice fixture. Not live status.

Program use: [SE2CAD_PROGRAM.md](../technical/governance/SE2CAD_PROGRAM.md).
Units: S2C-1.1.1 (register), S2C-1.2.1 (parse), S2C-6.1.1 (qualify).
Provenance policy: [ADR-004](../technical/adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).

Whether the fixture files exist is recorded only in [SE2CAD_STATE.md](../technical/governance/SE2CAD_STATE.md). S2C-1.1.1 adds them.

## Purpose

A deliberately asymmetric, user-created Large Grid Space Engineers object used as the permanent regression and qualification asset for the initial program.

The name “four-block” refers to the four supported subtypes, not to a required instance count. The human-authored object must use all four subtypes; it may contain more than four blocks.

Asymmetry and mixed orientations exist to catch axis swaps, left/right reflections, and pitch-sign errors that a symmetric plus-shaped test would hide.

## Composition

Single grid. Large Grid only.

Allowed subtypes, and only these:

- `LargeBlockArmorBlock`
- `LargeBlockArmorSlope`
- `LargeBlockArmorCorner`
- `LargeBlockArmorCornerInv`

The object must use all four subtypes. Blocks must appear in varied Forward/Up orientations, not a single default pose.

No functional blocks, no subgrids, no mechanical blocks, no Small Grid.

## Repository location

When registered by S2C-1.1.1:

```
fixtures/acceptance/four-block-armor-asymmetric/bp.sbc
fixtures/acceptance/four-block-armor-asymmetric/PROVENANCE.md
```

`PROVENANCE.md` must state that the blueprint is human-authored, identify the author, state that no game/SDK geometry is embedded, and briefly describe the intended object (block counts per subtype are recorded at registration from inspection).

Do not invent a substitute `bp.sbc` if the human-authored file is missing.

## What the fixture is not

- Not a Keen or workshop redistribution problem to be solved by copying game meshes into `fixtures/`.
- Not a print-preparation sample.
- Not a multi-grid or mechanical-joint sample.

## Validation behavior

| Stage | Unit | Expected behavior |
| --- | --- | --- |
| Registration | S2C-1.1.1 | File present; provenance present; inspection lists grid size, subtypes, counts, and that orientations vary. Human confirms identity before QUALIFIED. |
| Parse | S2C-1.2.1 | Parser emits one grid and one record per block: subtype, grid coordinate, Forward, Up. No dropped blocks. |
| Catalog / IR | S2C-2.1.1, S2C-3.1.1 | Each subtype resolves; each block gets a canonical transform. Automated orientation tests may use this fixture plus synthetic poses. |
| End-to-end | S2C-6.1.1 | Assembly block count equals fixture block count. Each component position and orientation matches the IR transform / fixture-derived expected pose within the tolerance recorded in that unit. Comparison uses the four canonical library parts. Fail closed if any unsupported subtype appears. |

SolidWorks and observed Space Engineers comparison are external validation for S2C-6.1.1. They are not required to define the fixture, only to qualify the program end state.

## Tolerances

Numeric position/orientation tolerances are not fixed in this specification. S2C-6.1.1 must record the comparison method and tolerances in STATE when evidence is produced. Do not loosen tolerances to hide orientation defects.
