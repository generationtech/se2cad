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

A conceptual library record should eventually be able to express:

| Field | Purpose |
| --- | --- |
| Canonical geometry identity | Distinct from blueprint subtype |
| Grid size | Large Grid for the initial program |
| Geometry strategy | How the part is produced |
| Reference frame | Origin and axes the transform engine assumes |
| Placement semantics | Any additional insert rules the backend needs |
| Part locator | How to obtain the reusable CAD part |

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

The transform engine and the library must share one origin/axis contract. That contract is written in S2C-4.1.1 and must agree with S2C-3.1.1. Do not invent a second frame inside the SolidWorks backend.

Large Grid cell pitch is 2500 mm, consumed from the single named constant established with the catalog (S2C-2.1.1).

## Asset boundary

Native armor recipes are SE2CAD-authored constructive geometry. They must not import Keen FBX, MWM, or extracted game meshes.

A future proposal to distribute parts derived from Keen assets requires an explicit human licensing decision. See [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).
