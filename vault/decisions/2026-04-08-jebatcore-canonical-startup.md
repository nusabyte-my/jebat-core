# JEBATCore Canonical Startup And Precedence

**Date:** 2026-04-08
**Status:** Accepted

## Decision

Treat `jebat-core/` as the canonical operating center for this repository and require session startup to begin from `jebat-core/BOOTSTRAP.md`, then `jebat-core/AGENTS.md`, `jebat-core/JEBAT_ASSISTANT_GUIDE.md`, and `jebat-core/MASTER_INDEX.md`.

## Why

The repository contains duplicated or overlapping top-level documentation, legacy OpenClaw-derived structure, and a dedicated `jebat-core/` subtree that more clearly represents the intended JEBATCore operating model. Without an explicit precedence rule, future sessions can load the wrong context and drift into inconsistent behavior.

## Impact

- root startup behavior now resolves to `jebat-core/` first
- duplicate docs should defer to the `jebat-core/` copy unless the user says otherwise
- future assistants should use the new bootstrap chain before substantial work
- durable project memory should record JEBATCore adaptation as an accepted workspace rule
