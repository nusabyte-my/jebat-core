# JEBAT Future Ops Plan

## Goal

Define the next operations-focused evolution of Jebat after current trust, memory, orchestration, and review foundations.

---

## Priority future ops direction

### 1. Skill lifecycle management
Inspired by:
- `arc-skill-gitops`

Future capabilities:
- snapshot skill state before changes
- maintain local version history for reviewed skills
- support rollback discipline after bad updates
- add pre-change audit checks before adoption

### 2. Reviewed-skill change control
Future capabilities:
- track reviewed skill revisions over time
- compare trust score changes between versions
- detect permission creep and new dependencies
- require re-review for significant changes

### 3. Maintenance automation
Future capabilities:
- wrap daily memory review into regular maintenance
- integrate wrap-up helpers into end-of-session flows
- summarize skill audit state periodically

### 4. Research mode expansion
Inspired by:
- `academic-research`
- `arxiv-search-collector`

Future capabilities:
- richer literature review mode
- curated paper set workflow
- citation-chain exploration procedure

### 5. Privacy-first reasoning provenance
Inspired cautiously by:
- `agent-commons`

Future capabilities:
- internal provenance tracking for decisions
- builder/reviewer audit trail
- local reasoning lineage without external publication by default

---

## Guardrails

Future ops must preserve:
- privacy-first defaults
- local-first preference
- explicit approval for risky writes
- no blind external skill inheritance
- no external reasoning publication by default

---

## Best next operational build targets

1. skill snapshot / rollback helper
2. reviewed-skill delta checker
3. session-end automation refinement
4. internal decision provenance log
