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

## Windows-local execution (S2C-4.2.1)

Human-architect decisions recorded 2026-09-07. They refine this ADR; they do not reopen transform placement or CAD neutrality.

- Space Engineers and the Space Engineers ModSDK remain on Linux. They are authoring and verification evidence, not a Windows runtime dependency. Do not require them in the Windows VM.
- SolidWorks 2026 remains in the Windows VM. Any workflow that needs SolidWorks runs locally there as a full SE2CAD pipeline (`bp.sbc` → parser → catalog → IR/transforms → recipe lookup → SolidWorks backend). Windows is not a remote worker.
- Linux and Windows may use separate Git clones of this repository. The operator keeps them synchronized with ordinary Git. SE2CAD does not provide a custom cross-OS sync mechanism.
- Blueprint transfer from Linux to Windows is operator-managed. This program does not automate it and does not introduce SMB, RPC, SSH, DCOM, REST, gRPC, sockets, services, watchers, or job queues for that purpose.
- The SolidWorks backend is Windows-local Python using pywin32 and in-process COM. pywin32 is a Windows-only optional/runtime dependency of that backend. Ordinary Linux development and CAD-neutral tests remain independent of pywin32 and SolidWorks.
- Canonical `.SLDPRT` files are generated artifacts, not authoritative source. Authority is catalog + canonical frame + native recipes + backend implementation. Do not commit or publish generated parts. They live under a configurable local generated root (environment variable and/or uncommitted local config). Do not store machine-specific paths in the catalog.
- A part locator may be bound only after generate, validate, save, and reopen all succeed. Logical artifact identity stays separate from the physical local path.

## Consequences

- Backend units may be DEV-COMPLETE on mocks and still require a real SolidWorks run for QUALIFIED when the unit says so.
- Assembly generation is an insert-and-transform problem, not a constraint-solving problem.
- Canonical parts are produced by the library recipes plus the Windows-local SolidWorks backend (S2C-4.x), not by the assembly writer.
- Print/STL/3MF pipelines are not implied by this backend.
- Importing `se2cad.parser`, `se2cad.catalog`, `se2cad.ir`, `se2cad.transform`, `se2cad.library`, or the top-level `se2cad` package must work on Linux without pywin32.
