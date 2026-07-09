# JEBAT Unified Coding Agent CLI v6.1+

A unified, provider-first coding-agent CLI built on:
- OpenClaude: provider discovery and controls
- OpenManus: agent reasoning and flows
- Pi: multi-provider AI harness

## Quick Start

```bash
cd D:/Jebat/jebat-core

# Show help
python -m jebat_cli_new --help

# List providers
python -m jebat_cli_new provider list

# Add a provider
python -m jebat_cli_new provider add openai --id work --api-key sk-...

# Use a provider for a one-shot task
python -m jebat_cli_new code --provider work --model gpt-4o-mini "Explain this code"

# Start interactive REPL
python -m jebat_cli_new repl
```

## Commands

| Command | Description |
|---------|-------------|
| `jebat code [prompt]` | Run coding agent (interactive if no prompt) |
| `jebat chat [prompt]` | Run chat agent (alias for code) |
| `jebat provider list` | List configured providers |
| `jebat provider add <kind> --id <id>` | Add a provider |
| `jebat provider use <id>` | Select a provider |
| `jebat agent run [prompt]` | Run agent loop |
| `jebat repl` | Start interactive REPL |

## Provider Kinds

| Kind | API Base | Default Model |
|------|----------|---------------|
| ollama | http://127.0.0.1:11434 | qwen2.5-coder:7b |
| openai | https://api.openai.com/v1 | gpt-4o-mini |
| anthropic | https://api.anthropic.com | claude-sonnet-4-20250514 |
| gemini | https://generativelanguage.googleapis.com/v1beta/openai | gemini-2.5-pro |
| github | https://models.github.ai/inference | openai/gpt-4o-mini |

## Tools (Agent Native)

The agent has built-in tools for coding tasks:

1. `read_file(path, offset=1, limit=200)` — Read file with line numbers
2. `write_file(path, content)` — Write content to file
3. `search_files(pattern, path, target, file_glob, limit)` — Search by glob or grep
4. `terminal(command, timeout=120)` — Execute shell commands
5. `list_dir(path, pattern)` — List directory contents

## Streaming

Built-in streaming support for Ollama and OpenAI-compatible providers.

```python
from jebat_cli_new.stream import ollama_stream, StreamHandler
handler = StreamHandler("ollama", "qwen2.5-coder:7b")
text = handler.stream(ollama_stream("qwen2.5-coder:7b", "Hello"))
```

## Architecture

```
jebat_cli_new/
├── __init__.py          # Package metadata
├── __main__.py          # Module entry point
├── jebat.py             # CLI entrypoint (argparse; console-script: jebat_cli_new.jebat:main)
├── models.py            # Shared data classes
├── providers.py         # Provider registry + factory (OllamaProviderImpl here)
├── provider_openai.py   # OpenAI provider impl
├── provider_anthropic.py # Anthropic provider impl
├── provider_gemini.py   # Gemini provider impl
├── provider_github.py   # GitHub Models provider impl
├── agent.py             # Agent loop with tools
├── runner.py            # Ollama completion helper
├── tools.py             # Native tool definitions
├── slash_commands.py    # Slash commands
├── repl.py              # Interactive REPL
└── ux.py                # Terminal UX
```

## Requirements

- Python 3.11+
- No external dependencies (stdlib only)
- Ollama running locally for Ollama provider
