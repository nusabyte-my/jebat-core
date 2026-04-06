# Decisions Log — Activated

**Date:** 2026-04-05
**Status:** Accepted

## Decision

vault/decisions is now the active log for all durable operating, architecture, and workflow decisions in the JEBAT workspace.

## Why

Prior sessions captured decisions inline in daily logs. This meant they were lost after Mimpi consolidation. Durable decisions need a permanent home that survives memory compression.

## Rules

- Write a decision file whenever a rule, policy, routing, or architecture choice is made that should survive future sessions
- Filename: `YYYY-MM-DD-short-slug.md`
- Status must be one of: Proposed → Accepted → Superseded
- Reference decision files from MEMORY.md Latest section when relevant

## Impact

- All future durable choices go here, not in daily logs
- Mimpi consolidation should scan vault/decisions and reflect Accepted decisions in the dream file
- MEMORY.md index should link to decisions that are still load-bearing
