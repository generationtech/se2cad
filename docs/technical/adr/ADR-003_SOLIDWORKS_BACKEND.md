# ADR-003 — SolidWorks backend

Status: Accepted
Date: 2026-09-07

## Context

The first shipping CAD target is SolidWorks assemblies (SLDASM) that instance canonical parts (SLDPRT).

SolidWorks mates are useful for mechanical design intent. They are a poor way to reconstruct thousands of already-known Space Engineers block poses. A mate network that size is fragile and unnecessary.

The project name and core abstractions must remain CAD-backend-neutral so a later backend is not a rename of the system.

## Decision

SolidWorks is the first CAD backend, isolated behind an automation boundary.

Generated assemblies place components using calculated IR transforms.

Do not use SolidWorks mates merely to reconstruct fixed Space Engineers block placement.

Core parser, definition resolver, IR, and transform system must not be unnecessarily coupled to SolidWorks. Do not rename the project or those abstractions to imply SolidWorks is the only possible backend.

Blender is not a stage on the runtime path to SolidWorks.

## Consequences

- Backend units may be DEV-COMPLETE on mocks and still require a real SolidWorks run for QUALIFIED when the unit says so.
- Assembly generation is an insert-and-transform problem, not a constraint-solving problem.
- Canonical parts are produced by the library (S2C-4.x), not by the assembly writer.
- Print/STL/3MF pipelines are not implied by this backend.
