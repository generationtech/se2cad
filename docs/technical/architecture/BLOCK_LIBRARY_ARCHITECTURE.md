# Block library architecture

Responsibility: durable contract for canonical reusable block parts and their metadata. Not a catalog implementation and not a capability claim.

This document is decided design. Whether library code or parts exist is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Initial-program work is S2C-4.1.1 and S2C-4.2.1. Current-program library expansions are defined in [SE2CAD_PLAN_M7.md](../governance/SE2CAD_PLAN_M7.md) and are not implied by this contract until STATE records them.

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

## Optional block-edge treatment

S2C-10.1.1. Public entrypoints: `se2cad.library.apply_edge_treatment`, `solid_from_recipe`, `solid_from_vertices_faces`.

Edge definition is an optional geometry treatment, not a new subtype and not a second `geometry_id`. Default conversion is untreated: `lookup_recipe` still returns the qualified native solid, and `apply_edge_treatment(solid)` / `EDGE_TREATMENT_OFF` returns that mesh unchanged. The canonical local frame, cell envelope used for placement, millimetre pitch, and zero insert offset are unchanged.

When requested (`EDGE_TREATMENT_CHAMFER`), the operation is an equal-setback chamfer of every convex manifold edge of a closed solid. Setback is the named constant `EDGE_TREATMENT_SETBACK_MM` (50 mm) along each incident face. Concave edges are left untreated. Applicability is a mesh property; the treatment modules do not name or allowlist the four initial `geometry_id` values.

Measurable contract when treatment is applied:

| Property | Requirement |
| --- | --- |
| Treatment present | `applied` is true; treated face count increases; every classified convex edge is treated |
| Envelope | Treated solid stays inside the untreated axis-aligned bounds; recipe solids stay inside `CANONICAL_CELL_ENVELOPE`; face interiors of the cell box remain on the placement envelope |
| Volume | Treated volume is strictly smaller than untreated and at least `EDGE_TREATMENT_MIN_VOLUME_RATIO` (0.85) of untreated |
| Untreated identity | Library `geometry_id`, recipe vertices/faces, and catalog entries are unchanged |

The CAD-neutral realization clips by each convex edge's chamfer half-space. That coincides with a local edge chamfer on the native recipes and on convex solids. SolidWorks materialization, when STATE records S2C-10.2.1, is a sibling generated artifact (`{geometry_id}_chamfer.SLDPRT`) produced by a local equal-setback chamfer feature. It is not a new `geometry_id` and must not overwrite untreated `large_armor_*.SLDPRT`. When STATE records S2C-10.3.1, explicit assemble selection (`python -m se2cad.solidworks.assemble <blueprint.sbc> --edge-treatment chamfer`) resolves those siblings. Default assemble still names untreated `{geometry_id}.SLDPRT`. Missing treated artifacts fail closed; they are not replaced by untreated parts. `_chamfer` is an artifact treatment, not part of catalog or IR identity.

Fail closed on an open or non-manifold mesh, a non-positive setback, a setback that consumes a convex edge, a requested treatment that does not decrease volume, or a treated solid that leaves the untreated envelope.

## Library-build definition discovery

When STATE records S2C-11.1.1, operator-local cube-block definition discovery is a library-build evidence tool. It is not a runtime converter stage and is not imported by the public `se2cad` conversion surface.

Public entrypoints: `se2cad.discovery.discover_cube_block_definitions`, `load_discovery_config`. A narrow operator entry is `python -m se2cad.discovery`.

Install roots reuse the established environment / uncommitted `se2cad.local.json` pattern: `SE2CAD_GAME_ROOT` / `SE2CAD_SDK_ROOT` and JSON keys `game_root` / `sdk_root`. The same local file may also hold SolidWorks `generated_root`. Discovery reads only `*.sbc` files under the known relative trees `Content/Data/CubeBlocks` and `Data/CubeBlocks`. It does not walk the rest of an install, does not open `.mwm` / `.fbx` / `.dds` / `.hkt`, and does not copy those assets into the repository.

Each discovered record is an observed identity plus the fields the catalog already models: `subtype_id`, `type_id`, `cube_size`, `size`, `block_topology`, and `cube_topology` when present. Small Grid identities may appear as observed `cube_size` facts. `geometry_id`, `recipe_kind`, and `support_status` are not assigned here. Source paths in the report are root-relative. Runtime lookup remains the packaged catalog.

When STATE records S2C-11.2.1, catalog identity expansion is library-build authoring on those observed facts. Public entrypoints: `se2cad.catalog.expand_catalog_identities`, `geometry_id_for_subtype`. Existing packaged SE2CAD decisions are preserved. New Large Grid identities receive distinct `geometry_id` values and remain `unsupported` until a later recipe decision. Small Grid identities are not written into the packaged catalog. Machine paths and mesh/texture references are not stored.

## Asset boundary

Native armor recipes are SE2CAD-authored constructive geometry. They must not import Keen FBX, MWM, or extracted game meshes.

A future proposal to distribute parts derived from Keen assets requires an explicit human licensing decision. See [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).
