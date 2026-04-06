# Trust Verification for External Skills

## Goal

Score whether an external skill is trustworthy enough to adapt into Jebat.

---

## Trust dimensions

### 1. Provenance
Check:
- source repo identity
- whether the skill is from an established registry/list
- whether the author history looks coherent
- whether publisher identity and ownership are stable

### 2. Structural quality
Check:
- valid frontmatter
- clear trigger description
- sane file layout
- references/scripts/assets used correctly
- no bloated monolithic prompt dump

### 3. Tool alignment
Check:
- maps to real OpenClaw tools
- no fantasy capabilities
- no hidden elevated assumptions
- no unexplained external side effects

### 4. Safety posture
Check:
- no silent data exfiltration
- no bypass language
- no hidden third-party writes
- no unsafe approval workarounds
- no mismatch between claimed purpose and actual behavior

### 5. Operational usefulness
Check:
- improves Jebat meaningfully
- not redundant with existing skills
- likely to be reused
- adds a real workflow, reference set, or verification layer

### 6. Version and integrity consistency
Check:
- suspicious version jumps
- unexplained capability changes
- changed permissions or dependencies
- integrity concerns for bundled binaries or scripts

---

## Scoring model

Score each 0-5.

- provenance
- structure
- tool realism
- safety
- usefulness

### Decision
- 22-25: strong candidate
- 17-21: adapt with caution
- 12-16: pattern extraction only
- 0-11: reject

---

## Hard fail conditions

Reject immediately if skill:
- instructs bypassing safeguards
- contains covert outbound behavior
- hides destructive commands
- claims authorization where none exists
- blurs defensive and offensive security without boundaries

---

## JEBAT policy

External skills are never trusted just because they are popular.
Trust is earned by:
- clarity
- restraint
- realism
- safety
- practical value
