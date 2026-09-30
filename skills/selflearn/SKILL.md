---
name: selflearn
description: IDE skill for JEBAT's SelfLearn + autoMimpi system — remembers project context across sessions (stack, commands, conventions, gotchas) and adapts behavior to the environment. Use at the start of a session to restore project memory, when learning something new about the project, at the end of meaningful work to consolidate, and when the user asks about what has been learned or how to adapt.
---

# SelfLearn — Remember & Adapt

JEBAT's adaptive learning loop for the IDE. Makes the assistant remember durable facts about the current project and adapt its behavior as the codebase evolves.

## Core Loop

```
Session start  → project_recall()  → restore context
During work    → project_remember() → capture durable facts
Periodically   → mimpi_dream()     → consolidate + suggestions
On request     → selflearn_analyze() / adapt_environment() → status & adaptation
```

## When to Use

| Trigger | Tool | Why |
|---|---|---|
| Session starts, or project directory changed | `project_recall` | Restore remembered stack, commands, conventions, gotchas |
| You discover something durable (build cmd, convention, env quirk, gotcha, goal) | `project_remember` | Persist it across sessions — no re-discovery next time |
| Meaningful work completed / user asks "what did we learn" | `mimpi_dream` | Consolidate traces, extract patterns, get suggestions |
| User asks to adapt / "how should we work here" | `adapt_environment` | Combine project facts + learning recommendations |
| User asks about progress / gaps / skills | `selflearn_analyze` | Skill levels, knowledge gaps, retention health |
| A stored fact is wrong or stale | `project_forget` | Remove it (then re-remember the corrected fact) |

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

Run `mimpi_dream` after a meaningful block of work or when the user asks about learning. It:

1. Consolidates memories (strengthen important, prune weak)
2. Extracts patterns from recent activity
3. Builds a learning profile (skill level, weak/strong areas, gaps)
4. Produces up to 5 prioritized suggestions with an urgency rating
5. Returns a Laksamana quote (JEBAT's voice)

Use the suggestions to steer the next work block.

## Behavioral Rules

- **Always recall before claiming** — never assume project state; `project_recall` at session start, or `memory_search` for a specific fact.
- **Remember only durable facts** — one-time details go in the conversation, not memory.
- **Category discipline** — use the exact category enum: stack/command/convention/environment/gotcha/goal/other.
- **Importance calibration** — 0.7+ for stack/commands/gotchas (survive pruning), ~0.5 for conventions, <0.5 for trivia.
- **Never store secrets** — store *where* a secret lives (e.g. "API key in `.env`"), never the secret value.
- **Adapt, don't repeat** — when `selflearn_analyze` shows a failing pattern (strategy_success_rates), change approach rather than retrying the same tactic.

## Data Location

Memories persist at `~/.jebat/memory/traces.json` — cross-session, per-machine. Project facts are tagged `project` + `project:<name>`, so one server serves multiple projects without cross-contamination.

## Tool Implementation

Tools live in `jebat/tools/automimpi_tools.py`, registered via `@register_tool` and
exposed by the MCP server (`jebat/features/mcp/mcp_server.py`). The engine is
`jebat/features/memory/automimpi.py` (`AutoMimpi` dream cycle + `SelfLearn` analysis),
backed by `EnhancedMemorySystem` persisting to `~/.jebat/memory/traces.json`.
