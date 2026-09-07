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

**C. Print preparation** (consolidated printable geometry) is a possible future process. It is not part of the initial program.

## Established decisions

1. **CAD-neutral IR** between parsing and backends. No SolidWorks COM or API types in the IR.
2. **Independent transform engine.** Placement is fully calculated before the SolidWorks backend runs. Large Grid cell pitch is **2500 mm** and must be one named constant.
3. **Transform placement, not mate reconstruction.** A ship with hundreds or thousands of blocks must not create an equivalent mate network.
4. **Reusable canonical parts** for supported block types. Geometry-strategy names (`native_procedural`, `sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, `unsupported`) are architectural vocabulary. The initial program covers only `native_procedural` for four Large Grid armor types.
5. **Blender is not on the runtime path.** Blender may later be an optional library-build tool for complex TriangleMesh parts. Runtime remains `converter → canonical block library`.
6. **Geometry classes differ.** CubeTopology armor can often be native CAD. TriangleMesh functional/detail blocks may need source/model assets and a different library recipe. Do not force one production mechanism. TriangleMesh is outside the initial program.
7. **SolidWorks is the first backend**, not the only conceivable backend. Do not rename core abstractions to imply SolidWorks exclusivity.

## Initial program scope

Single-grid Large Grid only. Four subtypes: `LargeBlockArmorBlock`, `LargeBlockArmorSlope`, `LargeBlockArmorCorner`, `LargeBlockArmorCornerInv`. See [SE2CAD_PROGRAM.md](../governance/SE2CAD_PROGRAM.md).

## Open questions

Not decided here. Live list: [SE2CAD_STATE.md](../governance/SE2CAD_STATE.md). Technology selection, including implementation language, is a human-architect decision.
