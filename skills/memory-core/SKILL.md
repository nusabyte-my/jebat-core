---
name: hikmat
description: Memory management for JEBAT — vault search, Mimpi consolidation, micro-learning capture, and session continuity. Use before answering questions about past work, projects, or decisions.
category: jebat-native
tags:
  - memory
  - vault
  - continuity
  - autodream
  - learning
ide_support:
  - claude
author: JEBATCore / NusaByte
version: 2.0.0
---

# Hikmat — Wisdom Skill 🌿

## Shared Core

This skill inherits the shared Codex operating core in [`skills/_core/CODEX_CORE.md`](../_core/CODEX_CORE.md).
Use this skill to add memory-specific behavior on top of that common baseline.

In the Nusantara tradition, **hikmat** is the accumulated wisdom passed down — not just knowledge, but understanding earned through experience. A Pawang carries hikmat; it is what separates mastery from mere knowledge.

JEBAT's hikmat lives in the vault, grows with every session, and is consulted before any claim of ignorance.

## Hikmat Priority

**Never claim ignorance without checking memory first.**

Before saying "I don't know" or "I don't remember" about past work, projects, people, or decisions:
1. Check `MEMORY.md` (index)
2. Check `memory/YYYY-MM-DD.md` for relevant dates
3. Check `vault/projects/` for project-specific context
4. Check `.learnings/` for corrections and discoveries

## Memory Architecture

```
MEMORY.md              ← Index only. <200 lines. Pure pointers.
memory/
  YYYY-MM-DD.md        ← Daily raw log. What happened, what changed.
  .dream-state.json    ← autoDream state tracker
vault/
  projects/            ← One file per active project
  decisions/           ← Architectural decisions + rationale
.learnings/
  corrections.md       ← When emmet corrected me
  LEARNINGS.md         ← Discoveries worth keeping
  ERRORS.md            ← Failed commands / tools
```

## autoDream — When to Consolidate

Check these gates on every session start (read dream-state.json first):

1. **TIME**: ≥24h since `lastDreamAt`?
2. **THROTTLE**: ≥10min since `lastScanAt`?
3. **SESSION**: `sessionsSinceDream` ≥ 5?
4. **USER**: emmet not mid-urgent task?

If all pass → consolidate:
1. **Orient**: read MEMORY.md to know current state
2. **Gather**: grep memory/ and vault/ for new content (don't read everything)
3. **Consolidate**: update vault files with durable knowledge
4. **Prune**: keep MEMORY.md as pure index, remove stale entries
5. **Update**: write dream-state.json with new timestamps and reset sessionsSinceDream

Tell emmet: "🌙 Consolidated N files"

## Micro-Learning Loop (Silent — Every Response)

After EVERY response, silently check:

| Condition | Action |
|-----------|--------|
| emmet corrected something | → `.learnings/corrections.md` |
| A command/tool failed | → `.learnings/ERRORS.md` |
| Discovered something new | → `.learnings/LEARNINGS.md` |
| Made an architectural decision | → `vault/decisions/YYYY-MM-DD-slug.md` |

Format for corrections.md: `| YYYY-MM-DD | what I got wrong | correct approach |`
Format for LEARNINGS.md: `| YYYY-MM-DD | discovery |`

## Writing to Memory

### Daily log (`memory/YYYY-MM-DD.md`)
```markdown
# YYYY-MM-DD

## Session Summary
One paragraph.

## What Happened
- Bullet points of actions taken

## Decisions Made
- Any architectural or strategic decisions

## Open Items
- Things to follow up on
```

### Vault project file
```markdown
# Project Name

**Status:** Active | Paused | Done
**Repo:** URL
**Stack:** key technologies

## What It Is
One paragraph.

## Current State
What's working, what's not.

## Next Steps
- [ ] Concrete next action
```

## Memory Hygiene

- MEMORY.md should never exceed 200 lines — it's an index, not storage
- Daily files accumulate — autoDream distills them into vault every 5+ sessions
- vault/ files are the source of truth for project state
- Delete stale vault entries — outdated info is worse than no info
