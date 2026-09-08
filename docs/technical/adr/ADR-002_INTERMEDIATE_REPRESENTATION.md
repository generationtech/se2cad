# ADR-002 — Canonical intermediate representation

Status: Accepted
Date: 2026-09-07

## Context

Blueprint XML, definition catalogs, and CAD APIs have different data shapes. Putting SolidWorks types in the parser or transforms would lock the core to one backend and make placement untestable without COM.

Space Engineers placement is a grid coordinate plus Forward and Up. CAD placement is a Euclidean transform. That mapping is a distinct problem from document automation.

## Decision

SE2CAD uses a CAD-neutral intermediate representation between blueprint parsing and CAD backends.

The IR must be able to represent at least:

- grid identity
- grid size
- block subtype
- block grid coordinate
- forward direction
- up direction
- resolved geometry identity
- canonical transform
- information needed by downstream CAD backends, expressed without backend API types

The IR must not contain SolidWorks COM objects or API structures.

Coordinate and orientation transformation is an independent subsystem. It calculates exact placement transforms before the SolidWorks backend is invoked.

Large Grid cell pitch is 2500 mm. That value lives in one named constant. Application code must not scatter the literal.

## Consequences

- Parser, catalog, IR, and transforms can be tested without SolidWorks.
- Additional CAD backends can consume the same IR.
- The SolidWorks backend applies transforms; it does not own SE orientation semantics.
- Exact Forward/Up basis mapping was established with evidence in S2C-3.1.1. The contract lives in [BLUEPRINT_CONVERTER_ARCHITECTURE.md](../architecture/BLUEPRINT_CONVERTER_ARCHITECTURE.md).
