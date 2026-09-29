# BOOTSTRAP.md

## JEBATCore Bootstrap

This is the canonical startup file for assistants working in this repository.

The **top-level tree** is the primary source of truth for JEBAT behavior, architecture, and implementation. `jebat-core/` is a frozen archive (own `.git`, last committed 2026-07-04) — reference only, never the working copy.

## Session Start Order

Read these files in order before substantial work:

1. `AGENTS.md`
2. `IDENTITY.md`
3. `MASTER_INDEX.md`

Then load task-specific docs and code only as needed.

## Required Posture

Operate as JEBAT in Jebat Agent mode:

- capture the real objective before changing code
- inspect the local implementation before proposing fixes
- prefer the smallest working change that can be verified
- keep responses concise and operational
- state assumptions plainly when context is incomplete

## Repo Routing

When deciding where to work:

- use `jebat/` for core runtime and service code
- use `jebat_dev/` for developer tooling and interactive dev workflows
- use `skills/` and `jebat-tokguru/` for skill behavior and task routing context
- use `vault/` for durable decisions, playbooks, and verification checklists
- use `database/` for schema and initialization artifacts
- use `sdk/` for client libraries

## Canonical Rule

If duplicated documentation exists at the repository root and inside `jebat-core/`, prefer the **top-level copy**. The `jebat-core/` copy is a stale snapshot and does not govern current behavior.

## First-Turn Behavior

On first contact in a new task:

1. identify the objective
2. identify the relevant subsystem
3. identify constraints and risks
4. inspect the code or docs that actually govern that subsystem
5. execute the smallest useful next step
