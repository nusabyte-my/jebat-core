# JEBAT Import Plan

## Goal

Adapt high-value external OpenClaw skill patterns into Jebat without importing unsafe or bloated behavior.

---

## Current import batch

### 1. agent-team-orchestration
Target:
- strengthen Hermes routing
- improve multi-agent task decomposition
- standardize role and handoff patterns

Planned output:
- orchestration conventions inside JEBAT runtime docs
- better delegation rules in orchestrator skill

### 2. arc-trust-verifier
Target:
- create trust scoring for external skills
- define provenance checks before adoption

Planned output:
- trust-verification procedure
- source review checklist
- import class scoring model

### 3. azhua-skill-vetter
Target:
- improve security-first skill intake
- identify unsafe patterns in external skill packages

Planned output:
- vetting workflow
- red-flag indicators
- structural scoring for skills

### 4. arc-security-audit
Target:
- strengthen JEBAT cybersecurity procedures
- review skill stack and runtime posture systematically

Planned output:
- agent-stack audit checklist
- security review flow for skills and runtime config

### 5. G0DM0D3 (defensive reference only)
Target:
- understand jailbreak and prompt-manipulation patterns
- harden Hermes and Jebat against hostile prompting

Planned output:
- prompt injection defense notes
- red-team test cases
- trust-boundary guidance

---

## Execution order

1. trust + vetting first
2. orchestration second
3. security audit third
4. adversarial prompt defense fourth

Reason:
- safe imports before more imports
- stronger routing before more delegation
- stronger audits before more capabilities

---

## Expected outputs

- `TRUST_VERIFICATION.md`
- `SKILL_VETTING_WORKFLOW.md`
- `ORCHESTRATION_PATTERNS.md`
- `AGENT_STACK_SECURITY_AUDIT.md`
- `PROMPT_INJECTION_DEFENSE.md`
- `REDTEAM_TEST_CASES.md`

---

## Success condition

Jebat becomes:
- better at selecting and reviewing external skills
- better at orchestrating specialist work
- better at auditing its own stack
- harder to manipulate through hostile prompts or unsafe skill imports
