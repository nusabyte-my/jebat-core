# Reviewed Skill Attestation Guide

## Goal

Generate a Jebat-native attestation record for a reviewed external skill.

---

## Use directly
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-reviewed-skill-attestation.ps1 \
  -SkillName "agent-team-orchestration" \
  -Source "https://github.com/openclaw/skills/tree/main/skills/arminnaimi/agent-team-orchestration" \
  -Score 25 \
  -TrustClass "adapt with caution" \
  -Verdict "APPROVE WITH CAUTION"
```

## Use through admin wrapper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 skill-attest \
  -Name "agent-team-orchestration" \
  -Source "https://github.com/openclaw/skills/tree/main/skills/arminnaimi/agent-team-orchestration" \
  -Score 25 \
  -TrustClass "adapt with caution" \
  -Verdict "APPROVE WITH CAUTION"
```
