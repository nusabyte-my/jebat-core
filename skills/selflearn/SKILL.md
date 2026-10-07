---
name: selflearn
description: Use for JEBAT project recall, AutoMimpi consolidation, SelfLearn evidence analysis, learning-advisor recommendations, reviewer feedback, and searchable learning KB history. Restores project facts without treating memory retention as task competence.
---

# SelfLearn — Remember & Adapt

JEBAT's adaptive learning loop for the IDE. Makes the assistant remember durable facts about the current project and adapt its behavior as the codebase evolves.

## Core Loop

```text
Session start: project_recall; compare project_root with the actual workspace.
During work: project_remember for verified facts; mimpi_record_failure for actual failures.
Handoff: session_learning_commit for a summary and durable key facts.
Review: selflearn_analyze, then learning_advisor for evidence-cited proposals.
Consolidate: mimpi_dream; completed reports are persisted in the existing KB.
Feedback: learning_feedback with explicit reviewer outcome and supporting evidence.
Recall history: learning_kb_search; inspect storage with learning_kb_status.
```

## When to Use

| Trigger | Tool | Why |
|---|---|---|
| Session starts, or project directory changed | `project_recall` | Restore remembered stack, commands, conventions, gotchas |
| You discover something durable (build cmd, convention, env quirk, gotcha, goal) | `project_remember` | Persist it across sessions — no re-discovery next time |
| Meaningful work completed / user asks "what did we learn" | `session_learning_commit`, then `mimpi_dream` when appropriate | Persist facts, consolidate selected project evidence, retain a report |
| User asks to adapt / "how should we work here" | `learning_advisor` / `adapt_environment` | Evidence-backed proposals, not autonomous actions |
| User asks about progress / gaps / skills | `selflearn_analyze` | Memory coverage, retention, clock anomalies; not a task-success score |
| User reviews advice | `learning_feedback` | Record helpful/unhelpful/dismissed with evidence; never infer approval |
| User asks about previous learning | `learning_kb_search` | Project-scoped full-text search of persisted dreams/advice |
| A stored fact is wrong | `project_forget` after approval | Delete only the reviewed fact; age alone is not proof it is false |

## What to Remember

Store facts with `project_remember` when you encounter anything a future session would waste time rediscovering:

- **stack** — frameworks, versions, key dependencies, runtime
- **command** — build/dev/test/deploy commands, ports, exact invocations
- **convention** — naming, folder structure, style rules, commit style
- **environment** — env vars, secrets locations (never the values), tool versions, OS quirks
- **gotcha** — bugs you hit, workarounds, traps
- **goal** — the current mission, priorities, constraints

One concise fact per call. Example:

```
project_remember(fact="React 19 + Vite app; build with `npm run build`",
                 category="stack", importance=0.8)
```

## Dream Cycle (mimpi_dream)

`mimpi_dream` consolidates only the active server project's matching traces. It strengthens eligible memories, prunes weak ones, creates content patterns/generalizations, and stores a scoped report in SQLite. Source identities prevent duplicate generalizations on repeated runs.

- `force=false` respects the consolidation interval; a recent project dream is skipped, including after restart when its KB report exists.
- `force=true` deliberately bypasses that interval. CLI startup additionally requires five sessions and a 24-hour shared-state gate; `/dream` is an explicit manual action.
- `status=partial` means consolidation committed but KB/mirror persistence failed. Do not repeat destructive consolidation blindly or claim it rolled back.
- Advice contains source IDs/timestamps. Review actual evidence before acting. Feedback changes recommendation visibility, never source confidence or permissions.
- Main agent only by default. This advisor is deterministic: no model call or subagent. Necessary external subagents must use the exact main-agent model.

## Behavioral Rules

- **Always recall before claiming** — never assume project state; `project_recall` at session start, or `memory_search` for a specific fact.
- **Remember only durable facts** — one-time details go in the conversation, not memory.
- **Category discipline** — use the exact category enum: stack/command/convention/environment/gotcha/goal/other.
- **Importance calibration** — 0.7+ for stack/commands/gotchas (survive pruning), ~0.5 for conventions, <0.5 for trivia.
- **Never store secrets** — store *where* a secret lives (e.g. "API key in `.env`"), never the secret value.
- **Adapt from evidence** — repeated recorded failures justify checking prerequisites, not inventing a failure probability. Helpful/unhelpful feedback is a reviewer judgment, not measured task success.

## Data Location

Memory traces remain in `~/.jebat/memory/traces.json`. New project writes carry `project:<name>` plus `context.project_root`; explicitly rooted traces from another checkout are excluded. Legacy name-only traces remain visible with a `legacy_unbound_count` caveat; do not silently retag them.

Dream/advice records and reviewer feedback use the existing `~/.jebat/wiki/index.db`, or `JEBAT_WIKI_DIR/index.db`. SQLite tables: `learning_records`, `learning_feedback`, and FTS5 `learning_fts`. Queries and feedback are scoped to the canonical project root. No new database service, vector model, or autogenerated wiki pages.

Use `jebat learning analyze|dream|advise|status|search|feedback` for the same lifecycle locally. See `docs/JEBAT_WORKFLOWS.md#learning-advisor-and-kb` for commands, guarantees, and limits.

## Tool Implementation

Tools: `jebat/tools/automimpi_tools.py`. Engine: `jebat/features/memory/automimpi.py`.
Advisor: `jebat/features/memory/learning_advisor.py`. KB: `jebat/features/wiki/wiki_core.py`.
CLI: `jebat_cli_new/learning_command.py`. MCP resources: `jebat://learning/profile`, `jebat://learning/advisor`, `jebat://kb/learning`.

Verification: `python scripts/check_learning.py` exercises temporary memory/SQLite, real CLI/MCP, project isolation, feedback, restarts, and failure paths without model calls. Always isolate both HOME and USERPROFILE on Windows; never use production memory for tests.
