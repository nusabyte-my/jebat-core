# Memory Promotion Guide

## Goal

Promote useful notes from daily memory into long-term memory deliberately.

---

## Use the helper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\memory-promote-helper.ps1 \
  -SourceFile .\memory\2026-03-30.md \
  -Text "Hermes was adopted as Jebat's routing layer"
```

## Promote when
- a fact is repeated
- a preference is stable
- a project direction is clear
- a workflow should be reused
- a lesson affects future behavior
- a named entity deserves durable tracking outside daily logs

## Entity memory note
For people, places, tech, ideas, and other named entities, prefer structured entity memory instead of burying everything in daily notes. Use `scripts/entity-memory-helper.ps1` when appropriate.

## Do not promote when
- detail is temporary
- note is redundant
- it belongs only in daily context
