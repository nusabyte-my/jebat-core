# Fourth Batch External Reviews

## 1. arc-skill-gitops

### Summary
Git-based deployment, snapshot, rollback, and version tracking for skills.

### Strong patterns
- snapshot before update
- rollback discipline
- per-skill version tracking
- pre-deploy checks as a gate
- good fit for future Jebat skill lifecycle management

### Concerns
- modifies skill directories and git state
- rollback/deploy actions can be powerful and disruptive
- frontmatter includes richer ecosystem-specific metadata
- direct script audit still needed before stronger trust

### Jebat decision
- **APPROVE WITH CAUTION** as a pattern source
- best for future managed skill lifecycle and rollback discipline

### Planned Jebat use
- reviewed skill change tracking
- skill snapshot / rollback procedures
- safer external skill update workflow

---

## 2. agent-commons

### Summary
Shared external reasoning network where agents consult, extend, and challenge each other’s reasoning chains.

### Strong patterns
- consult before re-deriving work
- reasoning provenance concept
- extend / challenge structure is intellectually useful

### Concerns
- depends on third-party external service and API key
- encourages external publishing of reasoning
- trust, privacy, and exfiltration risk are much higher
- not aligned with Jebat’s privacy-first local-first bias by default

### Jebat decision
- **PATTERN ONLY**
- useful as a conceptual pattern, not a direct stack fit right now

### Planned Jebat use
- internal provenance and review ideas only
- possibly local/shared reasoning pattern later, not external by default

---

## Net takeaway

`arc-skill-gitops` is a good future operations pattern.
`agent-commons` is interesting conceptually, but clashes with Jebat’s privacy-first local-first default unless adapted very carefully.
