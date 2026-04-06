# Reviewed Skill Delta Guide

## Goal

Compare two reviewed-skill manifests and detect material changes.

---

## Use the helper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reviewed-skill-delta-checker.ps1 \
  -OldFile .\reviewed-skills-old.json \
  -NewFile .\reviewed-skills.json
```

## Detects
- newly added reviewed skills
- removed reviewed skills
- score changes
- verdict changes
- trust-class changes

## Use when
- re-reviewing a skill set
- auditing trust changes over time
- checking whether imported patterns need renewed scrutiny
