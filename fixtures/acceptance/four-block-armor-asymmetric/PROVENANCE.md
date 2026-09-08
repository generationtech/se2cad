# Provenance — four-block-armor-asymmetric

This directory is the initial-program acceptance fixture specified in
[INITIAL_ACCEPTANCE_FIXTURE.md](../../../docs/testing/INITIAL_ACCEPTANCE_FIXTURE.md).
Third-party asset policy: [ADR-004](../../../docs/technical/adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).

## Authorship

The blueprint was manually authored by the human operator in Space Engineers.
It was created specifically for SE2CAD acceptance testing.

This record does not invent a legal personal name. The author is the human
operator who supplied the file for S2C-1.1.1 registration.

## Source identity (from the registered file)

Observed in `bp.sbc`:

- ShipBlueprint `Id` Type = `MyObjectBuilder_ShipBlueprintDefinition`
- ShipBlueprint `Id` Subtype = `se2cad-test1`
- CubeGrid `DisplayName` = `se2cad-test1`
- ShipBlueprint `DisplayName` = U+E030 followed by `Kolyma` (recorded as stored)
- `WorkshopId` = `0`

The human architect confirmed during S2C-1.1.1 that this `bp.sbc` is the
intended human-authored `se2cad-test1` acceptance object.

## Registration

- Repository path: `fixtures/acceptance/four-block-armor-asymmetric/bp.sbc`
- Date of repository registration: 2026-09-07
- SHA-256 of the registered `bp.sbc`:
  `99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31`
- The registered `bp.sbc` is the unmodified human-authored blueprint as
  supplied by the operator. It was not synthesized, rewritten, normalized,
  pretty-printed, or reordered by SE2CAD.

## Intended acceptance purpose

Permanent regression and qualification asset for the initial program:
single-grid Large Grid conversion of four armor subtypes through parser,
catalog, IR/transforms, canonical parts, and SolidWorks assembly.

## Composition (from S2C-1.1.1 inspection)

Single `CubeGrid`. `GridSizeEnum` = `Large`. 24 `CubeBlocks`.
Only these subtype IDs, all present:

| SubtypeName | Count |
| --- | ---: |
| LargeBlockArmorBlock | 9 |
| LargeBlockArmorSlope | 12 |
| LargeBlockArmorCorner | 2 |
| LargeBlockArmorCornerInv | 1 |

No other `SubtypeName` values occur. Every block `xsi:type` is
`MyObjectBuilder_CubeBlock`. Inspection observed no second grid, no
`GridSizeEnum` of `Small`, and no functional or mechanical builder types.

## What is not being committed

This fixture is Space Engineers blueprint structural data (XML) authored
by the operator. It is not a Keen game asset, mesh, FBX, MWM, texture,
HKT, or extracted proprietary geometry. No such files are present beside
`bp.sbc`.

Apache-2.0 applies to SE2CAD-owned code and documentation. It does not
relicense Space Engineers or Keen Software House works. This record does
not settle copyright, derivative-work, or redistribution status beyond
[ADR-004](../../../docs/technical/adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).
