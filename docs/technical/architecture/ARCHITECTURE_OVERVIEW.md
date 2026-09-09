# SE2CAD architecture overview

Responsibility: durable architectural contract for the system as a whole. Not live program status and not a capability claim.

This document is decided design. Whether any described component exists is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md).

Decisions: [ADR-001](../adr/ADR-001_CANONICAL_BLOCK_LIBRARY.md), [ADR-002](../adr/ADR-002_INTERMEDIATE_REPRESENTATION.md), [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md), [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md).
Process detail: [BLOCK_LIBRARY_ARCHITECTURE.md](BLOCK_LIBRARY_ARCHITECTURE.md), [BLUEPRINT_CONVERTER_ARCHITECTURE.md](BLUEPRINT_CONVERTER_ARCHITECTURE.md).

## Purpose

SE2CAD converts Space Engineers ship blueprints into engineering CAD representations.

Primary intended workflow:

```
Space Engineers bp.sbc
        |
        v
 Blueprint Parser
        |
        v
 Canonical SE2CAD IR
        |
  +-----+------+
  |            |
  v            v
Definition   Transform
 Catalog      Engine
  |            |
  +-----+------+
        |
        v
 Canonical Block Library
        |
        v
 SolidWorks Backend
        |
        v
     SLDASM
```

## Two primary processes

**A. Block library / asset preparation** builds reusable canonical CAD parts and the metadata that describes their frames and placement semantics.

**B. Blueprint converter / assembly generator** parses a blueprint, resolves definitions, computes transforms, instantiates library parts, and writes a SolidWorks assembly.

The runtime converter does not care how a canonical part was created. It asks the library for the part and its reference metadata.

**C. Print preparation** (consolidated printable geometry) was out of the initial program. The current approved program authorizes only automatic print-shell generation (M15), not a general slicer or physical-print pipeline. See [SE2CAD_PROGRAM_M7.md](../governance/SE2CAD_PROGRAM_M7.md).

## Established decisions

1. **CAD-neutral IR** between parsing and backends. No SolidWorks COM or API types in the IR.
2. **Independent transform engine.** Placement is fully calculated before the SolidWorks backend runs. Large Grid cell pitch is **2500 mm** and must be the named constant `LARGE_GRID_CELL_PITCH_MM`. Small Grid, when authorized and implemented, uses a second named constant rather than scattered literals or a forked engine. The proven SE2CAD coordinate/orientation contract is in [BLUEPRINT_CONVERTER_ARCHITECTURE.md](BLUEPRINT_CONVERTER_ARCHITECTURE.md).
3. **Transform placement, not mate reconstruction.** A ship with hundreds or thousands of blocks must not create an equivalent mate network.
4. **Reusable canonical parts** for supported block types. Geometry-strategy names (`native_procedural`, `sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, `unsupported`) are architectural vocabulary. The initial program covers only `native_procedural` for four Large Grid armor types.
5. **Blender is not on the runtime path.** Blender may later be an optional library-build tool for complex TriangleMesh parts. Runtime remains `converter → canonical block library`.
6. **Geometry classes differ.** CubeTopology armor can often be native CAD. TriangleMesh functional/detail blocks may need source/model assets and a different library recipe. Do not force one production mechanism. A completed TriangleMesh library remains cold storage, outside M7–M15 executable scope. M11 may classify and except such blocks.
7. **SolidWorks is the first backend**, not the only conceivable backend. Do not rename core abstractions to imply SolidWorks exclusivity. Core parser, catalog, IR, transforms, library, statistics, component naming, and preflight stay backend-neutral.
8. **OS / tool split.** Space Engineers and the ModSDK stay on Linux as authoring and verification evidence. SolidWorks 2026 stays in the Windows VM. The Windows SolidWorks-backed path operates from a repository clone, an operator-supplied `bp.sbc`, the repository catalog and recipes, Python, pywin32, and SolidWorks 2026. It does not require a Space Engineers install. Linux and Windows may use separate Git clones; the operator synchronizes them. Blueprint transfer is operator-managed. Linux-to-Windows automation and remoting are out of scope. Details: [ADR-003](../adr/ADR-003_SOLIDWORKS_BACKEND.md).
9. **Generated canonical SolidWorks parts** are reproducible artifacts under a configurable local generated root. They are not authoritative source and are not committed or published. Authority is catalog + canonical frame + native recipes + backend implementation. [ADR-004](../adr/ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md) remains the publication boundary.

## Initial program scope

The completed initial program was single-grid Large Grid only, four subtypes: `LargeBlockArmorBlock`, `LargeBlockArmorSlope`, `LargeBlockArmorCorner`, `LargeBlockArmorCornerInv`. See [SE2CAD_PROGRAM.md](../governance/SE2CAD_PROGRAM.md).

## Current approved program

M7–M15 continues the same architecture. Authorized expansions (not implemented by this sentence) are listed in [SE2CAD_PROGRAM_M7.md](../governance/SE2CAD_PROGRAM_M7.md): statistics, component naming, instance appearance, optional block-edge treatment, vanilla library expansion, preflight/unknown-block policy, Small Grid, symmetry detection, and print-shell generation. Whether any of those exist is recorded only in [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). When STATE records S2C-11.1.1, library-build discovery may read an operator-local game/SDK tree; the runtime converter still does not. When STATE records S2C-11.2.1, the packaged catalog may record additional Large Grid identities; unsupported entries are not recipes. When STATE records S2C-11.3.1, those identities may have an explicit recipe kind and a queryable exception record; a recipe kind is not support and is not generation. When STATE records S2C-11.4.1, known CubeTopology constructions can be stamped onto additional geometry IDs and a representative automatable subset can be generated through the existing Windows-local backend. When STATE records S2C-11.5.1, leftover and long-tail records live in repository-owned leftover metadata; failed generation, unclassified identities, and unsupported recipe kinds cannot be reported as supported conversion, residual automatable items stay listed, and coverage is not claimed as universal vanilla. When STATE records S2C-12.1.1, CAD-neutral preflight diagnoses supported, unsupported, and unknown blocks against the packaged catalog without converting or inserting filler. When STATE records S2C-12.2.1, an explicit conversion policy may refuse those blocks (strict, the default) or place the designated filler identity `se2cad_unknown_filler` while preserving original subtype, appearance, and pose (permissive).

Do not fork the pipeline for Small Grid. Do not bake instance appearance into reusable geometry. Do not invent work beyond that program.

## Open questions

Not decided here. Live list: [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Remaining technology-selection items (for example the general CLI shape) stay human-architect decisions.
