# JEBAT Control Panel

## Core Views
- `JEBAT_STATUS.md` — full stack status
- `JEBAT_EXEC_SUMMARY.md` — executive snapshot
- `OPS_DASHBOARD.md` — static ops reference
- `OPS_DASHBOARD.generated.md` — generated ops state
- `BRAIN_STATUS.generated.md` — generated brain state

## Core Logs
- `DECISION_PROVENANCE_LOG.md`
- `LIFECYCLE_NOTES.md`
- `memory/YYYY-MM-DD.md`
- `MEMORY.md`

## Control Surface
- `JEBAT_ADMIN.md`
- `JEBAT_ADMIN_COMMANDS.md`
- `scripts/jebat-admin.ps1`

## Key Policies
- `BRAIN_USAGE_POLICY.md`
- `EXTERNAL_SKILL_VETTING.md`
- `TRUST_VERIFICATION.md`
- `SKILL_VETTING_WORKFLOW.md`
- `PROMPT_INJECTION_DEFENSE.md`

## Core Skill Stack
- `skills/jebat-memory-skill/`
- `skills/jebat-consolidation-skill/`
- `skills/jebat-agent-orchestrator/`
- `skills/jebat-analyst/`
- `skills/jebat-researcher/`
- `skills/jebat-cybersecurity/`
- `skills/jebat-hardening/`
- `skills/jebat-pentesting/`

## Admin Priorities
1. keep memory clean
2. keep reviewed-skill state current
3. snapshot before risky changes
4. keep provenance and lifecycle logs alive
5. adapt external skills cautiously
