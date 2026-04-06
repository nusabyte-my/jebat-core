# Phase 2 Runtime Plan

## Goal

Move Jebat from a documented and governed internal operating base to a more executable runtime system.

---

## Phase 2 priorities

### 1. Operationalize core skills
Start with:
- jebat-memory-skill
- jebat-agent-orchestrator
- jebat-researcher
- jebat-cybersecurity

### 2. Reduce doc-only gaps
For each priority skill:
- identify what is currently conceptual
- add helper scripts, routines, or repeatable procedures
- connect existing admin tooling where possible

### 3. Strengthen routine execution
Use existing surfaces more actively:
- `jebat-admin.ps1`
- memory helpers
- reviewed-skill governance helpers
- lifecycle/provenance helpers

### 4. Maintain rollback safety
Before any risky skill refactor:
- snapshot first
- log lifecycle change
- preserve a rollback path

---

## Success condition

At the end of Phase 2, core Jebat skills should be closer to executable workflows than pure design docs.
