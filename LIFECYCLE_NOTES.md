# Lifecycle Notes

## Goal

Track how Jebat’s stack changes over time so future debugging and rollback decisions are easier.

---

## What to track
- reviewed skills added
- reviewed skills retired
- trust score changes
- procedural changes
- major stack direction changes
- replaced workflows and why they were replaced

---

## Entry format
- date
- object changed
- change type
- reason
- impact
- replacement or rollback path

---

## Example

### 2026-03-30 — Research stack strengthened
- **Object changed:** `jebat-researcher`
- **Change type:** capability expansion
- **Reason:** external review batch validated academic research and arXiv collection patterns
- **Impact:** researcher skill now supports stronger literature-review workflows
- **Replacement / rollback:** revert reference changes or restore from skill snapshot if needed

### 2026-03-30 — jebat-admin.ps1
- **Object changed:** jebat-admin.ps1
- **Change type:** capability expansion
- **Reason:** Added broader admin command coverage for provenance, lifecycle, dashboard, manifest, and memory tasks
- **Impact:** Jebat can now operate more of its own governance and maintenance stack directly
- **Replacement / rollback:** Restore from local snapshot if admin surface changes become unstable


### 2026-03-30 — core JEBAT skills
- **Object changed:** core JEBAT skills
- **Change type:** baseline snapshot
- **Reason:** Created initial local recovery points for all major JEBAT skills
- **Impact:** Future refactors and adaptations now have rollback anchors
- **Replacement / rollback:** Restore from matching baseline snapshot in skill-snapshots/


### 2026-03-30 — JEBAT foundation
- **Object changed:** JEBAT foundation
- **Change type:** milestone
- **Reason:** Reached stable Foundation v1 state
- **Impact:** Future work can proceed from a safer, documented, rollback-capable base
- **Replacement / rollback:** Use baseline skill snapshots and control panel docs if future phases destabilize the stack


### 2026-03-30 — Phase 2 runtime execution
- **Object changed:** Phase 2 runtime execution
- **Change type:** phase activation
- **Reason:** Phase 2 moved from planning into executable helper implementation
- **Impact:** Core runtime skills now have attached helpers and admin-surface commands
- **Replacement / rollback:** Use baseline snapshots and Phase 2 planning docs if refactors need to be unwound


### 2026-03-30 — Phase 2 helper wave 2
- **Object changed:** Phase 2 helper wave 2
- **Change type:** capability expansion
- **Reason:** Added consolidation, literature review, remediation append, and task append helpers and began using them
- **Impact:** Core runtime skills now have broader executable scaffolding and active operational use
- **Replacement / rollback:** Use helper rollback discipline and baseline snapshots if the Phase 2 helper layer needs refactoring


### 2026-03-30 — VS Code integration design
- **Object changed:** VS Code integration design
- **Change type:** phase preparation
- **Reason:** Defined Jebat-first editor workflow architecture
- **Impact:** Future editor integration can proceed from explicit bootstrap/dispatch/post-run rules instead of ad hoc use
- **Replacement / rollback:** Keep VS Code docs as planning artifacts until Phase 3 execution begins

