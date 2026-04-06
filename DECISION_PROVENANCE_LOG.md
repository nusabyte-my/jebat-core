# Decision Provenance Log

## Goal

Track important Jebat decisions with enough provenance to understand why they happened later.

---

## Entry format
- date
- decision
- context
- evidence
- alternatives considered
- outcome
- follow-up

---

## Example

### 2026-03-30 — JEBAT as OpenClaw operating model
- **Decision:** Adapt JEBAT into OpenClaw instead of building a parallel system first
- **Context:** Runtime usefulness was prioritized over website polish
- **Evidence:** OpenClaw already provides sessions, tools, memory hooks, cron, and routing surface
- **Alternatives considered:** Build jebat.online first; keep JEBAT conceptually separate
- **Outcome:** Focus shifted to Hermes, skill adaptation, memory procedures, and external skill vetting
- **Follow-up:** Continue runtime and skill adaptation work

### 2026-03-30 — Expand Jebat into an operable admin system
- **Decision:** Expand Jebat into an operable admin system
- **Context:** The stack had become large enough that docs alone were not sufficient
- **Evidence:** Added admin wrapper, snapshot/rollback helpers, trust tooling, and status helpers
- **Alternatives considered:** Keep everything as disconnected scripts and notes
- **Outcome:** Jebat now has a real operator control surface
- **Follow-up:** Keep wiring high-value routines into admin commands


### 2026-03-30 — Achieve baseline snapshot coverage for all core JEBAT skills
- **Decision:** Achieve baseline snapshot coverage for all core JEBAT skills
- **Context:** Jebat needed rollback anchors before deeper future adaptation
- **Evidence:** All 8 JEBAT skills now have baseline snapshot directories under skill-snapshots/
- **Alternatives considered:** Continue evolving skills without recovery points
- **Outcome:** Core skill stack is now protected by local baseline snapshots
- **Follow-up:** Use snapshot/rollback discipline before future risky changes


### 2026-03-30 — Represent the full core JEBAT skill stack in entity memory
- **Decision:** Represent the full core JEBAT skill stack in entity memory
- **Context:** The system had reached a point where structured retrieval of stack components was valuable
- **Evidence:** All 8 core JEBAT skills now have entity memory files under brain/skills/ with richer notes
- **Alternatives considered:** Leave skill understanding fragmented across skill docs only
- **Outcome:** Jebat can now treat its own core skill stack as structured memory entities
- **Follow-up:** Keep enriching important skill entities as the stack evolves


### 2026-03-30 — Declare JEBAT Foundation v1 complete
- **Decision:** Declare JEBAT Foundation v1 complete
- **Context:** The stack reached a stable internal operating base with memory, governance, admin tooling, and rollback coverage
- **Evidence:** Identity, Hermes, 8 refactored skills, trust pipeline, control panel, baseline snapshots, brain structure, and admin surface are all in place
- **Alternatives considered:** Continue expanding indefinitely without marking a stable phase boundary
- **Outcome:** Foundation work is now recognized as a completed phase with a clear handoff to future phases
- **Follow-up:** Treat subsequent work as next-phase expansion rather than foundation bootstrap


### 2026-03-30 — Activate Phase 2 helper wave 2 in live workflow
- **Decision:** Activate Phase 2 helper wave 2 in live workflow
- **Context:** The second runtime helper wave needed to move from available commands into actual operational use
- **Evidence:** Used consolidation, literature review, task append, remediation append, lifecycle logging, and dashboard regeneration
- **Alternatives considered:** Leave helper wave 2 as dormant tooling
- **Outcome:** Phase 2 runtime helpers now have live operational traces in task, remediation, lifecycle, and dashboard files
- **Follow-up:** Reassess whether another helper wave adds real leverage or just complexity


### 2026-03-30 — Design Jebat as the front control layer for VS Code workflows
- **Decision:** Design Jebat as the front control layer for VS Code workflows
- **Context:** The stack became mature enough to define editor-first bootstrap, dispatch, and post-run behavior
- **Evidence:** Created VS Code bootstrap, dispatch, post-run, stack, and phase-3 integration docs
- **Alternatives considered:** Treat editor usage as ad hoc model invocation without a controlling layer
- **Outcome:** Jebat now has an explicit design for loading before and integrating after downstream LLM workflows in the editor
- **Follow-up:** Implement editor integration only when Phase 2 runtime layer is mature enough


### 2026-03-30 — Begin Phase 3A coding-control integration
- **Decision:** Begin Phase 3A coding-control integration
- **Context:** Jebat is being positioned as the coding-task front controller before downstream editor LLM workflows
- **Evidence:** Created VS Code coding bootstrap/dispatch/memory/post-run docs and coding intake/route/verify/writeback helpers
- **Alternatives considered:** Use downstream coding models ad hoc without a controlling layer
- **Outcome:** Phase 3A now has a concrete architectural and helper foundation
- **Follow-up:** Use coding-control helpers on real tasks and refine dispatch behavior from actual usage

