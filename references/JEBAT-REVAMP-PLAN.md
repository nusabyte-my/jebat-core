# JEBAT CLI Revamp Plan
Goal: Build a clean, powerful, JEBAT-branded coding-agent CLI from the existing jebat-core codebase, with provider portability and parity with OpenCode/Kilocode.

## Scope
- Single unified CLI: `jebat` with subcommands `code`, `chat`, `agent`, `mcp`, `provider`, `project`.
- Providers are first-class: any OpenAI-compatible service, Ollama, Gemini, Anthropic, GitHub Models, etc.
- Agent loop, slash commands, streaming, and tool use built in.
- No references to earlier Jebat iterations in branding.

## Integration Map
- OpenClaude: provider discovery, slash commands, streaming, headless CLI, and VS Code extension patterns.
- OpenManus: agent flows, browser/sandbox tools, MCP server, planning/reasoning prompts.
- Pi: multi-provider AI abstraction, agent-core loop, TUI/terminal UX, coding-agent shrinkwrap.

## Milestones
1. Define new root CLI entrypoint and command tree under `jebat-core`.
2. Unify provider layer into one interface backed by Ollama first, then add others.
3. Port OpenManus-style agent steps with tool definitions.
4. Add OpenClaude-style slash commands and presets.
5. Bring Pi-style streaming and terminal UX.
6. Rebrand docs and CLI text to JEBAT only.
7. Smoke test `jebat code` locally on qwen2.5-coder:7b.
