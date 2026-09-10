# ADR-001 — Canonical block library

Status: Accepted
Date: 2026-09-07

## Context

A Space Engineers blueprint instances many blocks of a small number of types. Regenerating geometry for every instance would be slow, inconsistent, and would couple the converter to whatever authoring tool produced that instance.

Space Engineers also has more than one geometry class. Simple armor (CubeTopology) can often be expressed as native CAD. Functional and detail blocks (TriangleMesh) may depend on source or model assets.

## Decision

Supported block types resolve to reusable canonical CAD parts plus reference metadata.

The runtime blueprint converter asks the library for the canonical part and its metadata. It does not care how that part was created.

Library-build strategies are architectural vocabulary: `native_procedural`, `sdk_mesh_direct`, `sdk_mesh_manifold`, `hand_authored`, `unsupported`. The initial program covers only `native_procedural` for four Large Grid armor types.

CubeTopology and TriangleMesh must not be forced through one geometry-production mechanism. TriangleMesh recipes are out of initial-program scope.

Blender is not part of parse, catalog lookup, IR, or policy. It may be an optional library-build tool for TriangleMesh parts. When STATE records S2C-11.7.1, demand-driven generation of one authorized `sdk_mesh_direct` identity may invoke that library-build step; that is not a general mesh runtime.

## Consequences

- Converter and library-build are separate processes.
- Placement depends on a shared reference-frame contract (S2C-3.1.1, S2C-4.1.1).
- Native armor parts are SE2CAD-authored solids, not imported Keen meshes.
- Distributing any later Keen-derived parts needs an explicit human licensing decision ([ADR-004](ADR-004_THIRD_PARTY_ASSET_BOUNDARY.md)).
