# AGENTS.md

## Workspace Identity

This repository should be treated as a JEBAT workspace, with `jebat-core/` as the canonical operating center.

If there is any ambiguity between top-level files and `jebat-core/`, prefer `jebat-core/` unless the user explicitly directs otherwise.

## First Files To Load

At the start of a session in this workspace, load these files in order:

1. `jebat-core/BOOTSTRAP.md`
2. `jebat-core/AGENTS.md`
3. `jebat-core/JEBAT_ASSISTANT_GUIDE.md`
4. `jebat-core/MASTER_INDEX.md`
5. `CODEX_PROFILE.md` when the active assistant is Codex

If the task is specifically about identity, behavior, or operating posture, also consult:

1. `JEBAT_ASSISTANT_GUIDE.md`
2. `JEBAT.md`

## Operating Default

- Treat JEBAT and JEBATCore as the same active system for this repo.
- Default to repo-aware implementation, not generic advice.
- Keep the active context narrow and centered on the relevant `jebat-core/` subsystem.
- Prefer documented JEBAT entrypoints, skills, and vault/checklists before inventing new workflows.

## Source Of Truth

For architecture, startup, and operating behavior:

- `jebat-core/BOOTSTRAP.md`
- `jebat-core/AGENTS.md`
- `jebat-core/JEBAT_ASSISTANT_GUIDE.md`
- `jebat-core/MASTER_INDEX.md`
- `CODEX_PROFILE.md` for Codex-specific session behavior

For implementation work, use the nearest local docs in the affected subtree after the files above.
