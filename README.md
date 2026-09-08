# SE2CAD

SE2CAD is an early-stage project to convert Space Engineers ship blueprints into engineering CAD assemblies.

Intended direction:

```
Space Engineers bp.sbc  →  parse  →  CAD-neutral IR  →  canonical block parts  →  CAD assembly
```

SolidWorks is the initial CAD backend (SLDASM). The architecture keeps parsing, definition resolution, the intermediate representation, and transforms independent of any one CAD API so another backend could be added later.

## Current status

The repository currently contains program definition, architecture, engineering governance, a single-grid Large Grid blueprint parser, and a definition catalog for the four initial Large Grid armor subtypes.

Blueprint conversion is **not implemented**. There is no IR, transform engine, block library, or SolidWorks exporter in this tree yet.

The first executable program is a vertical slice: one Large Grid, one grid, and four armor subtypes (`LargeBlockArmorBlock`, `LargeBlockArmorSlope`, `LargeBlockArmorCorner`, `LargeBlockArmorCornerInv`) placed from a user-authored asymmetric blueprint fixture using reusable native CAD parts.

## License and third-party assets

Apache License 2.0 applies to SE2CAD-owned code and documentation. See [LICENSE](LICENSE).

Apache-2.0 does not relicense Space Engineers, Keen Software House, Microsoft, SolidWorks/Dassault, Blender, or other third-party assets. This project does not distribute Space Engineers or Keen SDK geometry. Derived CAD is not automatically redistributable just because SE2CAD produced it.

## Developers

Start at [docs/cursor/SE2CAD_DEVELOPER_ONBOARDING.md](docs/cursor/SE2CAD_DEVELOPER_ONBOARDING.md). Live program status is only in [docs/technical/governance/SE2CAD_STATE.md](docs/technical/governance/SE2CAD_STATE.md).
