# ADR-004 — Third-party asset boundary

Status: Accepted
Date: 2026-09-07

## Context

`se2cad` is a public Apache-2.0 repository. Apache-2.0 applies to SE2CAD-owned code and documentation. It does not relicense Space Engineers, Keen Software House, Microsoft, SolidWorks/Dassault, Blender, or other third-party works.

Agents and contributors can mistake "this repo is Apache-2.0" for permission to commit game assets, ModSDK FBX files, or generated derivatives.

User-authored blueprints are useful test fixtures. Game and SDK geometry are not automatically redistributable just because a fixture mentions them.

## Decision

Do not commit:

- Space Engineers game assets
- Keen ModSDK FBX files
- MWM model files
- textures from the game or SDK
- proprietary extracted geometry
- SolidWorks proprietary content not created for SE2CAD
- third-party binaries whose redistributable status is unknown

SE2CAD may contain code and metadata that locates, identifies, parses, or transforms assets from a user's legitimate installation where that is lawful and in scope.

Do not assume derived CAD geometry may be publicly redistributed merely because SE2CAD generated it. Any proposal to distribute canonical CAD representations derived from Keen assets requires an explicit human licensing and provenance decision.

User-authored Space Engineers blueprint fixtures may be committed when provenance is known and recorded. Game/SDK geometry must not be embedded in those fixtures as separate redistributed assets.

If redistribution rights are uncertain, stop and ask the human architect. Do not add the file.

## Consequences

- `.gitignore` may include a safety-net for common proprietary extensions. Ignore rules are not a license.
- Fixture units must include a provenance record.
- Native `native_procedural` armor solids are authored without importing or copying Keen FBX, MWM, or game mesh data. That authorship path is materially different from redistributing extracted Keen geometry. It does not by itself settle copyright, derivative-work, or redistribution status. Public distribution or licensing of canonical CAD geometry remains subject to explicit human provenance and licensing review where relevant.
- Cursor rule `30-third-party-assets.mdc` points here.
