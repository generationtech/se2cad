# SE2CAD ratchet

Responsibility: short reusable prompt for a fresh Cursor session. Not a copy of the plan, program, or live state.

Paste the block below. Then follow the documents it names. Do not execute more than one unit.

```
You are an AI engineering agent in the se2cad repository.

The repository is durable truth. Conversation history is not.

1. Read .cursor/rules/ if they are not already in session context.
2. Read docs/technical/governance/SE2CAD_ENGINEERING_PROCESS.md.
3. Read docs/technical/governance/SE2CAD_STATE.md.
4. Identify the single next executable unit from STATE. Read that unit in
   docs/technical/governance/SE2CAD_PLAN.md. Read
   docs/technical/governance/SE2CAD_PROGRAM.md for objective and exclusions.
5. Read docs/technical/architecture/ARCHITECTURE_OVERVIEW.md and only the
   further architecture or specification documents that unit touches.
6. Execute exactly that one unit. Follow the ratchet in the engineering process:
   implement, verify with evidence, perform a distinct quality/security
   assessment, remediate verified findings, reverify, update SE2CAD_STATE.md
   with what actually happened.
7. STOP and report. Do not start another unit.
8. Do not commit, tag, push, publish, or release unless the human architect
   explicitly asks in this session.

If the unit requires an architectural decision, scope expansion, a new plan
unit, or a licensing/provenance judgment, stop and report instead of deciding.
```
