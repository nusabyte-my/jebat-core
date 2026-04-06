# Agent Stack Security Audit

## Goal

Audit Jebat's operating stack, imported skills, and execution patterns for trust and exposure issues.

---

## Audit surface

### 1. Skill layer
Review:
- skill frontmatter quality
- hidden assumptions
- unsafe examples
- external writes
- authorization boundaries
- permission creep between versions
- integrity of bundled scripts or binaries

### 2. Tool layer
Review:
- risky `exec` usage
- elevated command approval flow
- cross-session messaging behavior
- cron-triggered actions

### 3. Memory layer
Review:
- what gets persisted
- whether sensitive data is over-recorded
- whether long-term memory contains things that should stay ephemeral

### 4. Orchestration layer
Review:
- specialist spawning criteria
- session isolation
- over-delegation risks
- result verification quality

### 5. Security layer
Review:
- defensive vs offensive boundary clarity
- authorization gates for pentest behavior
- remediation tracking

---

## Audit questions

1. Can any skill cause external side effects too easily?
2. Are approval boundaries respected?
3. Are memory writes disciplined?
4. Are external skills vetted before adoption?
5. Can orchestration create confusion or unverified outputs?

---

## Recommended cadence

- after any major new skill import
- after adding new security workflows
- after changing orchestration policy
- periodic review during heartbeat or manual maintenance
