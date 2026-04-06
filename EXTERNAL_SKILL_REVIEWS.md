# External Skill Reviews

## Reviewed sources
- agent-team-orchestration
- arc-trust-verifier
- azhua-skill-vetter
- arc-security-audit

Source set reviewed via clawskills pages on 2026-03-30.
Treat all source descriptions as external/untrusted summaries until source code is inspected directly.

---

## 1. agent-team-orchestration

### Summary
A playbook for multi-agent teams with:
- defined roles
- task states
- handoff protocols
- mandatory review steps

### Why it matters for Jebat
This is a strong fit for Hermes because Jebat needs:
- better decomposition discipline
- clearer handoff rules
- less informal delegation
- stronger verification after subagent work

### Trust/usefulness read
- provenance: moderate
- structure quality: unknown until source is inspected
- tool realism: likely high conceptually
- safety posture: neutral/good from description
- usefulness: high

### Import class
**B** — adapt structure and references

### What to extract
- task-state conventions
- handoff message format
- reviewer/builder separation
- explicit quality gates before completion

### Jebat action
Merge into:
- `ORCHESTRATION_PATTERNS.md`
- `JEBAT_RUNTIME_PROCEDURES.md`
- `skills/jebat-agent-orchestrator/`

---

## 2. arc-trust-verifier

### Summary
Trust assessment workflow for skills based on:
- publisher reputation
- version consistency
- content integrity
- dependency chains
- signed attestations

### Why it matters for Jebat
This is exactly the kind of intake logic Jebat needs before importing external skills.

### Trust/usefulness read
- provenance: moderate
- structure quality: unknown until source inspection
- tool realism: plausible
- safety posture: strong from description
- usefulness: very high

### Import class
**A/B** — adapt ideas and trust model first

### What to extract
- trust score dimensions
- explicit trust levels
- dependency chain concern model
- attestation concept for reviewed skills

### Jebat action
Merge into:
- `TRUST_VERIFICATION.md`
- `EXTERNAL_SKILL_VETTING.md`
- future reviewed-skill manifest

---

## 3. azhua-skill-vetter

### Summary
Skill vetting protocol focused on:
- credential harvesting
- obfuscated code
- unauthorized network calls
- install verdict with report

### Why it matters for Jebat
This sharpens the practical side of trust verification by focusing on concrete red flags.

### Trust/usefulness read
- provenance: moderate
- structure quality: unknown until source inspection
- tool realism: high conceptually
- safety posture: strong from description
- usefulness: very high

### Import class
**A/B** — adapt checklist and red flags

### What to extract
- install verdict categories
- concrete malicious pattern checklist
- permission-vs-purpose review logic
- documented vetting record format

### Jebat action
Merge into:
- `SKILL_VETTING_WORKFLOW.md`
- `EXTERNAL_SKILL_VETTING.md`
- security import process

---

## 4. arc-security-audit

### Summary
Stack-wide audit of installed skills using:
- scanner chain
- trust verification
- binary integrity checks
- prioritized risk report
- optional trust attestations

### Why it matters for Jebat
This is the right pattern for auditing Jebat’s eventual skill stack as it grows.

### Trust/usefulness read
- provenance: moderate
- structure quality: unknown until source inspection
- tool realism: plausible
- safety posture: strong from description
- usefulness: high

### Import class
**B** — adapt security audit flow

### What to extract
- consolidated skill-stack audit pattern
- ranked reporting format
- integrity + trust + scanner combination
- per-skill risk summary

### Jebat action
Merge into:
- `AGENT_STACK_SECURITY_AUDIT.md`
- cybersecurity workflow docs
- future audited-skill registry

---

## Net conclusion

These four are worth adapting as **patterns**.

Best order:
1. arc-trust-verifier
2. azhua-skill-vetter
3. agent-team-orchestration
4. arc-security-audit

Reason:
- safe import discipline first
- delegation quality second
- stack-wide auditing after the intake model exists
