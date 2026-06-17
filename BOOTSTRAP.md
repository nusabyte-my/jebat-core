# BOOTSTRAP.md

## JEBATCore Bootstrap

This is the canonical startup file for assistants working in this repository.

`jebat-core/` is the primary source of truth for JEBAT behavior, architecture, and implementation unless the user explicitly says otherwise.

## Session Start Order

Read these files in order before substantial work:

1. `AGENTS.md`
2. `JEBAT_ASSISTANT_GUIDE.md`
3. `MASTER_INDEX.md`
4. `../CODEX_PROFILE.md` when the active assistant is Codex

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

If duplicated documentation exists at the repository root and inside `jebat-core/`, prefer the `jebat-core/` copy unless the user points to another file.

## First-Turn Behavior

On first contact in a new task:

1. identify the objective
2. identify the relevant subsystem
3. identify constraints and risks
4. inspect the code or docs that actually govern that subsystem
5. execute the smallest useful next step
