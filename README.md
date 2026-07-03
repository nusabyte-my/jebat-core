# JEBAT Unified Coding Agent

JEBAT is a unified, provider-first coding-agent CLI built on:
- OpenClaude: provider discovery and controls
- OpenManus: agent reasoning and flows
- Pi: multi-provider AI abstraction and terminal UX

## Install
python -m pip install -e D:/Jebat/jebat-core

## Run
jebat code "Refactor this module"
jebat chat "Hello"
jebat provider list
jebat agent run "Implement a retry helper"
jebat repl

## Notes
- Primary local provider: Ollama
- Default model: qwen2.5-coder:7b
- More providers can be added without changing agent behavior.
