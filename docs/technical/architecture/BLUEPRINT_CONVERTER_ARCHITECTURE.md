# Blueprint converter architecture

Responsibility: durable contract for parsing a blueprint into a CAD assembly via IR, catalog, transforms, and the block library. Not a capability claim.

This document is decided design. Whether converter stages exist is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Initial-program units are S2C-1.2.1 through S2C-6.1.1. Current-program converter expansions are defined in [SE2CAD_PLAN_M7.md](../governance/SE2CAD_PLAN_M7.md) and are not implied by this contract until STATE records them.

Companion decisions: [ADR-002](../adr/ADR-002_INTERMEDIATE_REPRESENTATION.md), [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md). Library side: [BLOCK_LIBRARY_ARCHITECTURE.md](BLOCK_LIBRARY_ARCHITECTURE.md).

## Pipeline

```
bp.sbc → parser → catalog resolve → IR + transform engine → library lookup → CAD backend → SLDASM
```

Responsibilities:

| Stage | Does | Does not |
| --- | --- | --- |
| Parser | Read supported `bp.sbc` safely; extract grid and per-block subtype, position, Forward, Up, and `ColorMaskHSV` appearance | Resolve geometry identity; compute CAD transforms; call SolidWorks |
| Definition catalog | Map exact subtype → geometry identity; expose grid pitch from one named constant | Load meshes; contain COM types; scan a game install |
| Transform engine | Compute exact placement from grid coordinate + orientation + pitch | Insert components; apply mates |
| Block library | Return canonical part + reference metadata | Parse blueprints |
| SolidWorks backend | Insert parts by transform; assign instance appearance; save assembly | Recalculate SE orientation; call Blender; build mate networks for fixed SE placement; paint canonical `.SLDPRT` files |
| Statistics | Derive a CAD-neutral summary from parser + catalog fields | Call SolidWorks; invent identities; drop unresolvable blocks; change conversion policy |
| Component names | Derive a CAD-neutral instance name from existing IR fields | Rename canonical `.SLDPRT` identities; invent a catalog key; change `(R, t)` |

## Statistics

Statistics is a CAD-neutral derived report, not a conversion backend. It reads a parsed blueprint and performs catalog lookup per block. It does not import SolidWorks types and does not require IR construction.

Public entrypoints: `se2cad.statistics.compute_blueprint_statistics`, `compute_blueprint_statistics_from_path`, and `compute_blueprint_statistics_from_xml`. A narrow operator entry is `python -m se2cad.statistics <blueprint.sbc>`.

The result uses existing identities only: ShipBlueprint / CubeGrid names, `GridSize`, parser `subtype_id`, catalog `geometry_id` when lookup succeeds, Forward/Up pairs, unique `Min` cells, and `catalog.large_grid_cell_pitch_mm` (the named Large Grid pitch constant). Unknown subtypes stay in block and subtype counts and are reported as unresolved catalog coverage. They are not assigned a geometry identity and are not omitted to make coverage look complete.

Occupancy is unique `Min` cells versus the inclusive axis-aligned cell bounding box of those cells. Millimetre size is each axis span in cells times the catalog pitch. Multi-cell `Size` occupancy is not generalized here.

Unsupported document shapes fail at the parser, with the same errors as direct parse. Statistics must not invent a second fail-closed policy.

## Component names

Component names are a CAD-neutral derived identifier, not a second `subtype_id` / `geometry_id` scheme. Public entrypoints: `se2cad.component_name`, `component_name_from_block`, and `component_names_from_blocks`.

Encoding: `{subtype_id}_x{X}_y{Y}_z{Z}_{Forward}_{Up}_{source_index}`. Negative `Min` values keep a leading ASCII hyphen (`z-1`). Omitted and explicit identity Forward/Up produce the same name. `geometry_id`, filesystem paths, and orientation-serialization flags are not part of the name.

`subtype_id` must match `^[A-Za-z][A-Za-z0-9_]*$`. Path separators, spaces, dots, and other FeatureManager-reserved characters (`/ \\ : * ? " < > | ^`) are rejected. The requested identifier is at most `COMPONENT_NAME_MAX_LENGTH` (80). If the full encoding is longer, the prefix is truncated and the unique `_{source_index}` suffix is preserved so the name stays traceable to the IR block. A set of names for one assembly must be unique.

The SolidWorks writer applies the name at insertion via `IComponent2.Name2` set (short name). Name2 get returns `{short}-{instance}` for a top-level non-virtual component. Matching after save/reopen compares the short name to the IR-derived name. Canonical part filenames and placement transforms are unchanged.

## Appearance

Per-instance appearance is CAD-neutral Space Engineers `ColorMaskHSV`, not a second `geometry_id` and not a SolidWorks material. The on-disk field is `ColorMaskHSV` with `x`/`y`/`z` attributes (`SerializableVector3`). XmlSerializer omits the element when it equals `SerializableVector3(0, -1, 0)`; that omitted default is `DEFAULT_COLOR_MASK_HSV` `(0.0, -1.0, 0.0)` (HSV-offset). The parser records `color_serialized` so an explicit default vector is distinct from omission.

`AppearanceSupport` is independently reportable from catalog geometry `SupportStatus`: `default` for the omitted mapping, `explicit` for a serialized payload. Unknown appearance is not a current parser state. Malformed `ColorMaskHSV` fails closed.

RGB conversion and SolidWorks assignment live in the SolidWorks package (`se2cad.solidworks.appearance` and the assembly writer). Parser, catalog, and IR do not produce RGB or COM types. Conversion is Keen `HSVOffsetToHSV` (add published `SATURATION_DELTA` 0.8 and `VALUE_DELTA` 0.45, clamp S/V to `[0, 1]`) then standard HSV-to-RGB. The omitted default becomes display HSV `(0, 0, 0.45)` / RGB `(0.45, 0.45, 0.45)`. The writer assigns that RGB as an `IComponent2.MaterialPropertyValues` instance override at insertion. Two instances of the same `geometry_id` keep one canonical part file and different instance appearances. Canonical part generation stays color-agnostic. Geometry applied and appearance applied are independently reportable on the placed-component result.

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
- information needed by downstream CAD backends that can be expressed without backend API types, including per-instance `ColorMaskHSV` appearance

It must not contain SolidWorks COM objects or API structures. Per-instance appearance must not be stored as a change to reusable geometry identity.

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

The backend package is `se2cad.solidworks`. All pywin32 / COM code stays inside that package and is imported only when a SolidWorks session is requested. Importing `se2cad`, `se2cad.parser`, `se2cad.catalog`, `se2cad.ir`, `se2cad.transform`, `se2cad.library`, or `se2cad.statistics` on Linux must not require pywin32. Requesting the backend where COM, pywin32, or SolidWorks is unavailable is a clear backend-availability failure.

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

Live SolidWorks 2026 late-bound CDispatch (`RevisionNumber` 34.3.2) cannot call `IMathUtility.CreateTransform` (server fault, same class as the rejected IModeler array calls). The working write is `Transform2.ArrayData = VARIANT(VT_ARRAY|VT_R8, tuple-of-16)` after `AddComponent5` of a pre-opened part. A raw Python list corrupts translation. The first inserted component is auto-fixed; `Select(True)` plus `UnfixComponent` clears that Fixed state without adding placement mates. The assembly `MateGroup` folder remains empty. `OpenDoc(path, swDocASSEMBLY=2)` reopens a native `.SLDASM`. After insert, `IComponent2.Name2` is set to the CAD-neutral short name; Name2 get includes the instance suffix. Official Name2 remarks: set fails while `swExtRefUpdateCompNames` (enum 18) is True. Live 34.3.2 also requires `Select` before the Name2 put; an unselected assignment is a silent no-op. The writer forces that toggle False from insert through SaveAs and reopen so the SLDASM stores the alternate names; it then restores the prior toggle. Canonical part filenames are unchanged. After the IR transform is written, the writer sets `IComponent2.MaterialPropertyValues` to the converted instance RGB (nine doubles, RGB in `[0, 1]`, 8-bit truncated to match live 34.3.2 storage). That override is on the assembly component, not on the reusable `.SLDPRT`. Default and explicit `ColorMaskHSV` both receive a converted appearance; omitted fixture color must not fail insertion. Comparison allowance is one 8-bit LSB (`1/255`).

## Initial-program limits

The completed initial program’s converter success path was:

- one grid
- Large Grid
- only the four armor subtypes in [SE2CAD_PROGRAM.md](../governance/SE2CAD_PROGRAM.md)

That path remains the qualified baseline. Fail closed on multiple grids and missing required fields. Do not silently drop blocks.

Unknown-subtype handling, Small Grid, and print-shell generation are authorized only by [SE2CAD_PROGRAM_M7.md](../governance/SE2CAD_PROGRAM_M7.md) and only when STATE records the corresponding units. Until those units exist, unknown subtypes and non-Large grid sizes remain fail-closed. Parser/IR `ColorMaskHSV` is present when STATE records S2C-9.1.1. SolidWorks instance-appearance assignment is present when STATE records S2C-9.2.1.

Blender is not a converter stage. A general print/slicer pipeline is not a converter stage.
