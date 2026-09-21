# JEBAT CLI + MCP Quickwin Audit

## Status: 18/18 COMPLETE

Audit inspired by Jev (TypeSafe AI System One) integration context.
See `docs/JEV_CONTEXT.md` for curated Jev reference, `routers/advisor.py` for Jev-style advisor endpoints.

---

## Phase 1: MCP Enhancements (6/6)

| ID | Feature | File | Verified |
|----|---------|------|----------|
| MQ-3 | Tool annotations (readOnly/destructive hints) | `jebat/features/mcp/mcp_server.py` | 89/89 tools annotated |
| MQ-6 | Git context resources (status + diff) | `jebat/features/mcp/mcp_server.py` | 2 resources: git/status, git/diff |
| MQ-1 | Project onboard prompt | `jebat/features/mcp/mcp_server.py` | prompt: project-onboard |
| MQ-2 | Resource templates with URI variables | `jebat/features/mcp/mcp_server.py` | 2 templates |
| MQ-4 | Wire ProgressManager to long tools | `jebat/features/mcp/mcp_server.py` | Progress in tool calls |
| MQ-5 | Wire SamplingHandler to providers | `jebat/features/mcp/mcp_transport.py` | Wired to provider registry |

## Phase 2: CLI Foundation (3/3)

| ID | Feature | File | Verified |
|----|---------|------|----------|
| CQ-1 | Extract unified theme.py | `jebat_cli_new/theme.py` | 95 color constants, StreamingMarkdown |
| CQ-2 | Streaming markdown renderer | `jebat_cli_new/theme.py` | StreamingMarkdown class |
| CQ-6 | Unified diff preview for file writes | `jebat_cli_new/jebat.py` | render_diff in write_file tool |

## Phase 3: CLI Workflow (5/5)

| ID | Feature | File | Verified |
|----|---------|------|----------|
| CQ-3 | @file reference in input | `jebat_cli_new/jebat.py` | `_expand_file_refs()` |
| CQ-4 | ! shell prefix execution | `jebat_cli_new/jebat.py` | `_run_shell_inline()` |
| CQ-5 | Multi-line input (editor/triple-quote) | `jebat_cli_new/jebat.py` | `_multiline_input()`, `_editor_input()` |
| CQ-10 | /compact that actually works | `jebat_cli_new/jebat.py` | `_compact_messages()` |
| CQ-9 | Session fork/branch + continue flags | `jebat_cli_new/jebat.py` | `-c`, `-s`, `/fork`, `/continue` |

## Phase 4: CLI Polish (4/4)

| ID | Feature | File | Verified |
|----|---------|------|----------|
| CQ-7 | Collapsible tool output | `jebat_cli_new/jebat.py` | `_tool_summary()`, `/details` toggle |
| CQ-8 | Per-turn cost + token display | `jebat_cli_new/jebat.py` | `tok` + `$cost` after each turn |
| CQ-11 | Thinking block rendering | `jebat_cli_new/jebat.py` | `/thinking` toggle, thought_card |
| CQ-12 | Mode-specific visual indicators | `jebat_cli_new/jebat.py` | mode_color, mode_icon in prompt |

---

## New REPL Shortcuts

| Shortcut | Action |
|----------|--------|
| `@file.py` | Inline file content into prompt |
| `!git diff` | Run shell command, inject output |
| `"""` | Enter multi-line input mode |
| `/editor` | Open $EDITOR for long prompts |
| `/details` | Toggle verbose tool output |
| `/thinking` | Toggle LLM thinking blocks |
| `/compact` | Summarize conversation context |
| `/fork` | Branch session into new timeline |
| `/continue` | Resume last saved session |

## New CLI Flags

| Flag | Action |
|------|--------|
| `-c`, `--continue` | Resume last session |
| `-s ID`, `--session ID` | Resume specific session |

## Advisor Router (Jev-style)

New endpoint at `/api/advisor` supporting typed decisions:
- `POST /api/advisor/decide` — System One judgments (Yes/No, Pick One, Score)
- Accepts unstructured text + typed question definitions
- Returns calibrated probabilities, not prose
