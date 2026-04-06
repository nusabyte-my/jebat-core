# Skill Rollback Guide

## Goal

Restore a skill directory from a local snapshot.

---

## Use the helper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\skill-rollback-helper.ps1 \
  -SnapshotPath .\skill-snapshots\jebat-researcher-pre-update-20260330-101500 \
  -TargetSkillPath .\skills\jebat-researcher
```

## Use when
- a skill refactor breaks structure
- an external adaptation goes bad
- you need to restore a known-good local state

## Caution
This replaces the target skill directory contents.
Make a fresh snapshot first if you might want to recover the current state.
