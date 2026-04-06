# Direct Source Inspection Notes

## Scope
Inspected raw `SKILL.md` files for shortlisted external skills.

---

## 1. agent-team-orchestration

### Observations
- strong frontmatter description
- uses references for progressive disclosure
- clear role split: orchestrator / builder / reviewer / ops
- explicit task-state model
- explicit handoff requirements
- explicit review step to prevent quality drift

### Good patterns to copy
- artifact output path must be specified
- handoff message minimum fields
- reviewer role separated from builder role
- orchestrator owns state transitions

### Concerns
- none major from the visible SKILL content
- direct code/scripts were not inspected

### Jebat decision
- keep as **PATTERN ONLY** for now
- high-value orchestration reference

---

## 2. arc-trust-verifier

### Observations
- useful trust dimensions: publisher, version consistency, integrity, dependency chain, community signals
- trust levels are clean and operationally useful
- script-driven design is appealing for eventual automation

### Good patterns to copy
- trust levels: VERIFIED / TRUSTED / UNKNOWN / SUSPICIOUS / UNTRUSTED
- attestation concept
- version-consistency checks
- dependency trust-chain checks

### Concerns
- frontmatter includes fields beyond the minimal skill-creator spec (`user-invocable`, `metadata`)
- likely valid in OpenClaw ecosystem, but not minimal-spec clean
- script source itself not inspected yet

### Jebat decision
- adopt concepts now
- keep external skill verdict at **PATTERN ONLY** until deeper inspection

---

## 3. azhua-skill-vetter

### Observations
- practical red-flag list is strong
- permission-vs-purpose review is useful
- explicit verdict output is immediately reusable
- very pragmatic tone

### Good patterns to copy
- mandatory code review mindset
- red-flag checklist
- risk levels with action guidance
- install verdict report format

### Concerns
- frontmatter contains `version`, which is outside the minimal spec guidance from skill-creator
- some checks are a bit absolute and may need refinement for legitimate advanced skills
- direct source beyond SKILL not inspected

### Jebat decision
- high-value vetting reference
- adapt checklist, but keep nuanced judgment
- verdict remains **PATTERN ONLY**

---

## 4. arc-security-audit

### Observations
- clear value proposition: stack-wide consolidated audit
- good composition idea: scanner + trust + integrity + report
- operational command surface is coherent

### Good patterns to copy
- full-stack audit pass
- per-skill breakdown
- prioritized risk report
- optional trust attestations after clean pass

### Concerns
- frontmatter again uses extra fields (`user-invocable`, `metadata`)
- depends on companion tools/skills not yet inspected here
- useful architecture pattern, but not enough for direct install recommendation yet

### Jebat decision
- adapt as audit architecture
- verdict remains **PATTERN ONLY**

---

## Overall conclusion

The direct source inspection improved confidence in the shortlist.

### Strongest immediate pattern sources
1. agent-team-orchestration
2. azhua-skill-vetter
3. arc-trust-verifier
4. arc-security-audit

### Key takeaway
These skills are more useful as:
- workflow references
- structure patterns
- audit/checklist inspiration

than as blind drop-in imports right now.
