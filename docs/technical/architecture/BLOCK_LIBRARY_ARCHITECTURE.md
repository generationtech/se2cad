# Block library architecture

Responsibility: durable contract for canonical reusable block parts and their metadata. Not a catalog implementation and not a capability claim.

This document is decided design. Whether library code or parts exist is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Initial-program work is S2C-4.1.1 and S2C-4.2.1.

Companion: [ADR-001](../adr/ADR-001_CANONICAL_BLOCK_LIBRARY.md). Converter use of the library: [BLUEPRINT_CONVERTER_ARCHITECTURE.md](BLUEPRINT_CONVERTER_ARCHITECTURE.md).

## Role

The library is the only runtime source of canonical CAD parts and the reference metadata needed to place them.

```
blueprint converter  -->  canonical block library  -->  part + reference metadata
```

Not:

```
blueprint converter  -->  Blender  -->  SolidWorks
```

How a part was authored (native features, later optional mesh prep, or hand modeling) is a library-build concern.

## Record

The initial-program library record (`se2cad.library.LibraryRecord`) expresses:

| Field | Purpose |
| --- | --- |
| Canonical geometry identity | Distinct from blueprint subtype |
| Grid size | Large Grid for the initial program |
| Geometry strategy | How the part is produced |
| Reference frame | Origin and axes the transform engine assumes |
| Placement semantics | Insert at cell center; no extra offset |
| Native solid recipe | Exact constructive geometry for later CAD authoring |
| Part locator | Unbound in authoritative records; a backend may bind a logical identity only after generate / validate / save / reopen |

Strategy vocabulary (not an implementation checklist):

- `native_procedural` — construct CAD solid from SE2CAD recipes
- `sdk_mesh_direct` — later; out of initial program
- `sdk_mesh_manifold` — later; out of initial program
- `hand_authored` — later; out of initial program
- `unsupported` — explicit non-support; do not silently substitute

The initial program covers `native_procedural` only, for:

- `LargeBlockArmorBlock`
- `LargeBlockArmorSlope`
- `LargeBlockArmorCorner`
- `LargeBlockArmorCornerInv`

## Geometry classes

Space Engineers definitions include materially different geometry classes.

- **CubeTopology / simple armor** — reconstruct as native CAD. This is the initial-program path.
- **TriangleMesh / functional and detail blocks** — may resolve through source or model assets and need a different library-build recipe. Out of initial-program scope. Do not force these through the native armor mechanism.

## Reference frames

The transform engine and the library share one origin/axis contract. The converter-side frame, axes, units, origin, handedness, and rotation construction are recorded in [BLUEPRINT_CONVERTER_ARCHITECTURE.md](BLUEPRINT_CONVERTER_ARCHITECTURE.md). This document does not define a second frame.

Public library frame: `se2cad.library.CANONICAL_LOCAL_FRAME`. It reads the qualified S2C-3.1.1 axes from `SE_DIRECTION_VECTORS` and the pitch from `LARGE_GRID_CELL_PITCH_MM`.

| Canonical local axis | Meaning |
| --- | --- |
| +X | block Right |
| +Y | block Up |
| +Z | block Backward (local −Z is block Forward) |

The local origin is the 1×1×1 cell center. Units are millimetres. The cell envelope is the axis-aligned box from `−half` to `+half` on each axis, where `half = LARGE_GRID_CELL_PITCH_MM / 2`. Identity Forward/Up is the identity rotation.

Invariant used by later CAD insertion:

```
canonical solid authored in this local frame
    +
S2C-3.1.1 instance transform (R, t)
    =
correctly placed/oriented block geometry
```

Do not add a half-cell offset at insert time. Do not invent a second frame inside the SolidWorks backend.

Large Grid cell pitch is 2500 mm, consumed from the single named constant established with the catalog (S2C-2.1.1).

## Native armor recipes

Public entrypoints: `se2cad.library.lookup_recipe`, `se2cad.library.lookup_record`, and `se2cad.library.all_library_records`.

Lookup is an exact, case-sensitive match of the catalog `geometry_id`. Unknown identities fail closed. Each of the four initial catalog geometry IDs resolves to exactly one `native_procedural` recipe. Authoritative library records keep `part_locator` unbound. A Windows-local SolidWorks backend may return a bound locator only after the canonical part has been generated, validated, saved, and reopened. That locator’s logical identity is the deterministic `geometry_id` filename (for example `large_armor_block.SLDPRT`). The physical path is runtime-only under the configured generated root and must not be written into catalog JSON. Generated `.SLDPRT` files are not source artifacts and are not committed or published.

Recipes are SE2CAD constructive solids. Vertex signs are the cell-local ±1 cube corners from Keen `MyCubeGridDefinitions` topology edge tables for `Box`, `Slope`, `Corner`, and `InvCorner`. Those signs are Space Engineers topology facts. Scaling them by the catalog half-extent, and the construction vocabulary below, are SE2CAD engineering choices.

| geometry_id | Observed `CubeTopology` | Solid kind | Identity convention |
| --- | --- | --- | --- |
| `large_armor_block` | `Box` | axis-aligned box of the cell envelope | all six faces full |
| `large_armor_slope` | `Slope` | right triangular prism, YZ triangle extruded along X | full faces on Forward and Down; solid is `Y + Z <= 0` |
| `large_armor_corner` | `Corner` | tetrahedron | Right-Down-Forward cube corner; orthogonal triangles on Right, Down, Forward |
| `large_armor_corner_inv` | `InvCorner` | cell box minus that same tetrahedron | full faces on Up, Left, Backward; missing cube corner is Right-Down-Forward |

All four solids have the same expected bounding box as the cell envelope. That does not make them the same solid: vertex sets, face counts, volumes, and construction kinds remain distinct.

Deterministic validation properties stored on each recipe: vertex count, face count, outward-wound `volume_times_6_mm3`, and the exact integer bounding box. Faces are sufficient for later solid construction together with the construction kind.

Placement semantics for these 1×1×1 parts: insert at the cell center with no additional offset. The IR transform is the only placement.

## Asset boundary

Native armor recipes are SE2CAD-authored constructive geometry. They must not import Keen FBX, MWM, or extracted game meshes.

A future proposal to distribute parts derived from Keen assets requires an explicit human licensing decision. See [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).
