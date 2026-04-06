# JEBAT Approved Adaptation Bundle

## Goal

Capture the external patterns Jebat is approved to adapt from the reviewed shortlist.

---

## Approved with caution sources

### 1. agent-team-orchestration
Approved adaptations:
- builder / reviewer split
- orchestrator-owned task state transitions
- explicit handoff minimums
- artifact path discipline
- review gates before completion

Where merged:
- `ORCHESTRATION_PATTERNS.md`
- `skills/jebat-agent-orchestrator/`
- `JEBAT_RUNTIME_PROCEDURES.md`

---

### 2. arc-trust-verifier
Approved adaptations:
- trust scoring dimensions
- trust levels / verdict framing
- version consistency checks
- dependency trust-chain thinking
- attestation concept for reviewed skills

Where merged:
- `TRUST_VERIFICATION.md`
- `SKILL_SCORING_GUIDE.md`
- `REVIEWED_SKILLS_MANIFEST.md`

---

### 3. azhua-skill-vetter
Approved adaptations:
- explicit red-flag checklist
- permission-vs-purpose review logic
- install verdict format
- documented vetting record workflow

Where merged:
- `SKILL_VETTING_WORKFLOW.md`
- `EXTERNAL_SKILL_VETTING.md`
- `scripts/skill-review-template.md`

---

### 4. arc-security-audit
Approved adaptations:
- stack-wide audit framing
- per-skill risk summary
- trust + integrity + scanner composition
- prioritized remediation reporting

Where merged:
- `AGENT_STACK_SECURITY_AUDIT.md`
- `skills/jebat-cybersecurity/`
- future reviewed-skill audit workflow

---

## Not approved for blind import

Even with good scores, these are not approved for:
- blind installation without code/resource audit
- automatic execution of bundled scripts
- inheriting their authority or assumptions wholesale

---

## JEBAT rule

Approved adaptation means:
- copy the good workflow ideas
- translate them into Jebat-native procedures
- keep Jebat’s own safety boundaries intact
