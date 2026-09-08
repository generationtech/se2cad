# Blueprint converter architecture

Responsibility: durable contract for parsing a blueprint into a CAD assembly via IR, catalog, transforms, and the block library. Not a capability claim.

This document is decided design. Whether converter stages exist is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Initial-program units are S2C-1.2.1 through S2C-6.1.1.

Companion decisions: [ADR-002](../adr/ADR-002_INTERMEDIATE_REPRESENTATION.md), [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md). Library side: [BLOCK_LIBRARY_ARCHITECTURE.md](BLOCK_LIBRARY_ARCHITECTURE.md).

## Pipeline

```
bp.sbc → parser → catalog resolve → IR + transform engine → library lookup → CAD backend → SLDASM
```

Responsibilities:

| Stage | Does | Does not |
| --- | --- | --- |
| Parser | Read supported `bp.sbc` safely; extract grid and per-block subtype, position, Forward, Up | Resolve geometry identity; compute CAD transforms; call SolidWorks |
| Definition catalog | Map exact subtype → geometry identity; expose grid pitch from one named constant | Load meshes; contain COM types; scan a game install |
| Transform engine | Compute exact placement from grid coordinate + orientation + pitch | Insert components; apply mates |
| Block library | Return canonical part + reference metadata | Parse blueprints |
| SolidWorks backend | Insert parts by transform; save assembly | Recalculate SE orientation; call Blender; build mate networks for fixed SE placement |

## Intermediate representation

The IR is CAD-neutral. It must be able to represent at least:

- grid identity
- grid size
- block subtype
- block grid coordinate
- forward direction
- up direction
- resolved geometry identity
- canonical transform
- information needed by downstream CAD backends that can be expressed without backend API types

It must not contain SolidWorks COM objects or API structures.

## Definition catalog

The catalog is repository-resident JSON, version-controlled with the code, and loaded by the packaged Python module. It is source-of-truth data, not a runtime database and not a scan of a Space Engineers installation.

Authoritative file: `src/se2cad/catalog/large_grid_armor.json`.
Loader: `se2cad.catalog.load_default_catalog`.
Large Grid cell pitch: `se2cad.catalog.LARGE_GRID_CELL_PITCH_MM` (2500 mm). Application code must use that name, not copy the literal.

Each catalog entry has two groups of fields that must not be collapsed:

| Group | Meaning | Fields |
| --- | --- | --- |
| Observed Space Engineers facts | Tokens taken from installed cube-block definitions | `subtype_id`, `type_id`, `cube_size`, `size` (cell occupancy), `block_topology`, `cube_topology` |
| SE2CAD decisions | Identities and policy owned by this project | `geometry_id`, `recipe_kind`, `support_status` |

`geometry_id` is an SE2CAD identity. It is not a Keen subtype. Distinct subtypes keep distinct geometry IDs.

Lookup is an exact, case-sensitive match of the parser `subtype_id` string. Unknown subtypes fail closed. Duplicate `subtype_id` or `geometry_id` values, unknown `recipe_kind` values, and malformed JSON are rejected at load.

Recipe vocabulary remains `native_procedural`, `sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, and `unsupported`. Naming a recipe is not an implementation of that recipe. The initial four Large Grid armor entries use `native_procedural` only.

The catalog must not store machine-specific paths or proprietary mesh/texture references. The normal conversion path must not open Space Engineers content files to resolve these four subtypes.

## Transforms

Coordinate and orientation transformation is an independent subsystem. It finishes before the SolidWorks backend is invoked.

Public entrypoints: `se2cad.transform.rotation_from_forward_up`, `se2cad.transform.cell_center_mm`, and `se2cad.ir.build_canonical_blueprint`.

Large Grid cell pitch is 2500 mm, from the single catalog/dimensional constant `LARGE_GRID_CELL_PITCH_MM`. Do not copy the literal through converter code.

### Proven Space Engineers direction vectors

These are Space Engineers facts, not SE2CAD inventions. Current local `VRage.Math.xml` documents `Quaternion.GetForward` as `(0,0,-1)`, `GetRight` as `(1,0,0)`, and `GetUp` as `(0,1,0)`. Current local `VRage.Math.dll` still contains `Base6Directions.LeftDirections` as the published 36-entry table. Keen published `Vector3` / `Vector3I` / `Base6Directions` / `MyBlockOrientation` / `Matrix.CreateWorld` corroborate the same mapping.

| Direction | SE vector |
| --- | --- |
| Forward | `(0, 0, -1)` |
| Backward | `(0, 0, 1)` |
| Left | `(-1, 0, 0)` |
| Right | `(1, 0, 0)` |
| Up | `(0, 1, 0)` |
| Down | `(0, -1, 0)` |

The world/grid basis is right-handed: Right × Up = Backward = `+Z`.

Forward + Up define a block orientation. The third axis is the ordinary cross product: **Right = Forward × Up**. That is the same construction as Keen `Matrix.CreateWorld` / `Quaternion.CreateFromForwardUp`, which compute `Right = Up × Backward` with `Backward = -Forward`. `GetCross` is an alias of `GetLeft(up, forward)` and is **not** a reason to reverse that product.

`Base6Directions.IsValidBlockOrientation` accepts a pair iff the two direction vectors are orthogonal. That is **24** legal orientations (6 forwards × 4 perpendicular ups). Same-axis and opposite-axis pairs are invalid and must fail closed.

### Canonical SE2CAD frame

SE2CAD engineering choice, geometry-independent, suitable for all four initial 1×1×1 armor types. Not a SolidWorks-specific decision. The block-library unit authors solids against this frame; it does not define cube/slope/corner geometry here.

| Canonical local axis | Meaning |
| --- | --- |
| +X | block Right |
| +Y | block Up |
| +Z | block Backward (so local −Z is block Forward) |

Identity serialization default Forward/Up therefore produces the identity rotation.

Units are millimetres. Grid/world +X/+Y/+Z are the Space Engineers axes above.

### Origin / cell translation

Keen `GridIntegerToWorld` multiplies the integer cell by grid pitch and applies the grid world matrix, with no half-cell add. `WorldToGridInteger` is `Round(local / GridSize)`. Current local `Sandbox.Game.dll` still exports `GridIntegerToWorld`, `WorldToGridInteger`, `GridSizeHalf`, and `GridSizeHalfVector`. Published AABB construction is `[Min * GridSize − GridSizeHalf, Max * GridSize + GridSizeHalf]`.

Therefore a 1×1×1 block at `Min = (i, j, k)` is **centered** at `(i, j, k) * LARGE_GRID_CELL_PITCH_MM`. `Min = (0, 0, 0)` is centered at the canonical origin. Signs are preserved: negative Z remains negative.

For these 1×1×1 CubeTopology blocks, occupancy is a single cell. Orientation does not change the Min-cell anchor; it only rotates the local frame about that center. Multi-cell occupancy is not generalized here.

### Matrix / vector convention

SE2CAD stores a 3×3 orthonormal **integer** rotation `R` and a millimetre translation `t`.

- Column vectors. `v_world = R v_local`.
- Columns of `R` are the world images of local +X, +Y, +Z: **Right, Up, Backward**.
- Entries are −1, 0, or 1. Composition is ordinary matrix multiply, integer arithmetic only.
- Determinant is `+1` (right-handed, no reflection).
- VRage/XNA stores the same basis vectors as **rows** and uses row-vector multiply `v' = v M`. The physical rotation is the same; the SE2CAD array is the transpose of that VRage 3×3 layout.

A homogeneous 4×4 is not required for this discrete placement: `(R, t)` is the rigid transform a later CAD backend applies.

Solid recipes and the library-side record that agrees with this frame: [BLOCK_LIBRARY_ARCHITECTURE.md](BLOCK_LIBRARY_ARCHITECTURE.md). The SolidWorks backend packs this same `(R, t)` into `IMathTransform.ArrayData` without a second frame.

## SolidWorks backend

First CAD backend, isolated behind a boundary. Core parser, catalog, IR, and transforms must not import SolidWorks types.

The backend package is `se2cad.solidworks`. All pywin32 / COM code stays inside that package and is imported only when a SolidWorks session is requested. Importing `se2cad`, `se2cad.parser`, `se2cad.catalog`, `se2cad.ir`, `se2cad.transform`, or `se2cad.library` on Linux must not require pywin32. Requesting the backend where COM, pywin32, or SolidWorks is unavailable is a clear backend-availability failure.

Execution model (human-architect, S2C-4.2.1): the Windows process runs the needed SE2CAD stages locally. Windows is not a remote worker. Linux-to-Windows remoting is out of scope. See [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md).

API lengths are metres. Recipe millimetres are converted only inside the backend, explicitly. The backend consumes the qualified canonical frame and must not apply a corrective rotation or offset to make a part “look right”.

Generated canonical part files use deterministic names from `geometry_id` (`large_armor_block.SLDPRT`, …) and must stay under the configured generated root. A part locator may be bound only after generate, validate, save, and reopen succeed. The locator’s logical identity is not a Windows absolute path and is not stored in the catalog.

Placement method: apply the calculated transform to each inserted component. Do not reconstruct fixed Space Engineers block placement with mates.

Generated assemblies use deterministic names from the IR identity subtype (`se2cad-test1.SLDASM`) and must stay under the configured generated root. The writer consumes already-generated canonical `.SLDPRT` files; it does not author or substitute parts, and it does not write locators into catalog or library records.

SolidWorks `IMathTransform.ArrayData` is sixteen doubles. Official CreateTransform / ArrayData remarks (still the 2026 method-page contract) store:

- `[0:3]`, `[3:6]`, `[6:9]`: component X, Y, Z axes in parent space
- `[9:12]`: translation in metres
- `[12]`: scale (`1`)
- `[13:16]`: unused

Those axes are the qualified rotation columns (local +X/+Y/+Z in world). Translation is `position_mm / 1000`. No transpose, no corrective rotation, no half-cell offset, no mate network.

Live SolidWorks 2026 late-bound CDispatch (`RevisionNumber` 34.3.2) cannot call `IMathUtility.CreateTransform` (server fault, same class as the rejected IModeler array calls). The working write is `Transform2.ArrayData = VARIANT(VT_ARRAY|VT_R8, tuple-of-16)` after `AddComponent5` of a pre-opened part. A raw Python list corrupts translation. The first inserted component is auto-fixed; `Select(True)` plus `UnfixComponent` clears that Fixed state without adding placement mates. The assembly `MateGroup` folder remains empty. `OpenDoc(path, swDocASSEMBLY=2)` reopens a native `.SLDASM`.

## Initial-program limits

The converter success path for this program is:

- one grid
- Large Grid
- only the four armor subtypes in [SE2CAD_PROGRAM.md](../governance/SE2CAD_PROGRAM.md)

Fail closed on multiple grids, unsupported grid size, missing required fields, or unknown subtypes. Do not silently drop blocks or substitute unsupported types.

Blender is not a converter stage. Print preparation is not a converter stage.
