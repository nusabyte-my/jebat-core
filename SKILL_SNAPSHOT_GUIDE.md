# Skill Snapshot Guide

## Goal

Create local snapshots of skill directories before changes.

---

## Use the helper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\skill-snapshot-helper.ps1 \
  -SkillPath .\skills\jebat-researcher \
  -Tag pre-update
```

## Use when
- before refactoring a skill
- before importing or merging external patterns
- before risky edits to a reviewed skill
