# AGENTS.md

## Workspace Identity

This repository is the canonical JEBAT workspace. The **top-level tree is the source of truth**: it is what Python imports (`jebat/`, `jebat_cli_new/`), it holds the newest docs, and it is where all active work happens.

`jebat-core/` — an older snapshot of this workspace with its own `.git`, last committed 2026-07-04 — was **removed on 2026-09-30** (archived locally to `.local-backups/`; its git history is the same GitHub repo, `nusabyte-my/jebat-core`). Treat it accordingly:

- Do not recreate `jebat-core/`; do not check out the old snapshot into it.
- References to `jebat-core/` in older docs, scripts, or CI are historical: local paths are dead, while `jebat-core` as a repo name and the VPS `/var/www/jebat-core` deployments remain real.
- The top-level copy of any duplicated doc always wins.

`jebatcore/` (no hyphen) is the npm/JS package — unrelated to the archive.

## First Files To Load

At the start of a session in this workspace, load these files in order:

1. `AGENTS.md` (this file)
2. `BOOTSTRAP.md`
3. `IDENTITY.md`
4. `MASTER_INDEX.md`
5. `MEMORY.md`
6. `DESIGN.md`

If the task is specifically about identity, behavior, or operating posture, also consult:

1. `IDENTITY.md`
2. `SOUL.md`

## Operating Default

- Treat JEBAT and JEBATCore as the same active system for this repo.
- Default to repo-aware implementation, not generic advice.
- Keep the active context narrow and centered on the relevant top-level subsystem (`jebat/`, `jebat_cli_new/`, `skills/`, `vault/`, ...).
- Prefer documented JEBAT entrypoints, skills, design rules, and vault/checklists before inventing new workflows.
- Load the nearest local `AGENTS.md`, `MEMORY.md`, and `DESIGN.md` in the subtree you are changing.

## Source Of Truth

For architecture, startup, and operating behavior:

- `BOOTSTRAP.md`
- `IDENTITY.md`
- `MASTER_INDEX.md`
- `MEMORY.md`
- `DESIGN.md`

For implementation work, use the nearest local docs in the affected subtree after the files above.

Docs inside `jebat-core/` may be consulted for historical context, but they are frozen as of 2026-07-04 and do not govern current behavior.
