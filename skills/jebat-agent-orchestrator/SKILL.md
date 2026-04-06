---
name: jebat-agent-orchestrator
description: Multi-agent coordination guide for JEBAT on OpenClaw. Use when decomposing complex tasks, selecting specialists, spawning sessions, coordinating councils, routing work between agents, or deciding whether to execute locally versus delegate.
---

# JEBAT Agent Orchestrator

Use this skill to decide **whether to work locally, delegate to one specialist, or coordinate multiple agents**.

## Core workflow
1. decide if the task is simple enough to do directly
2. if not, decompose the task into focused parts
3. choose the lightest useful specialist path
4. spawn or coordinate only when quality or speed actually improves
5. verify specialist output before final delivery
6. persist important decisions to memory

## Primary OpenClaw mappings
- `sessions_spawn` for isolated specialists / ACP
- `sessions_send` for cross-session coordination
- `sessions_yield` when waiting on delegated work
- `subagents` for steering or intervention

## Read references when needed
- `references/delegation-patterns.md` — local vs delegated vs council patterns

## Operational rules
- local-first by default
- no delegation theater
- councils are for real tradeoffs, not routine tasks
- always verify before trusting delegated output
