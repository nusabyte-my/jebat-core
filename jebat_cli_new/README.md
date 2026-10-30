# JEBAT CLI v8.5.0

Provider-independent coding-agent console with interactive command discovery,
shared tools, sessions, multi-agent workflows, and MCP integration.

## Install

Requires Python 3.11+; the npm launcher also requires Node.js 18+.

```bash
# Run directly; first use bootstraps the Python runtime
npx @nusabyte/jebat repl

# Or install the launcher
npm install -g @nusabyte/jebat
jebat repl
```

Do not use `pip install jebat`: that name belongs to an unrelated PyPI project.
For bootstrap, source installation, upgrades, and troubleshooting, read the
[complete CLI guide](../docs/CLI_GUIDE.md).

## Use the console

```bash
jebat provider add  # Configure a model provider
jebat repl          # Start the interactive console
jebat --help        # CLI options and subcommands
```

`jebat init` separately scans the workspace and generates `AGENTS.md`.

Type `/` and press **Enter** inside the console. Filter by typing, move with **Up/Down** or **Tab**,
select with **Enter**, and cancel with **Escape**. Commands requiring arguments
remain open for completion. Palette selections and typed commands share the same
execution path.

```text
/provider add                  Configure a model provider
/model                        Select a model
/plan                         Toggle plan-before-execution
/tool list                    Discover shared tools
/agents                       List specialist agents
/delegate debug:Investigate   Delegate a focused task
/diff                         Inspect repository changes
/resume                       Restore a saved session
/yolo off                     Keep staged tool approvals enabled
/exit                         Save when enabled and exit
```

Attach files with `@FILE`, run shell commands with `!COMMAND`, and use `"""` for
multi-line prompts.

## Script and automate

```bash
jebat code "Review the CLI dispatch flow"
jebat --provider openai --model gpt-4.1 code "Review this repository"
jebat --plan code "Refactor the command dispatcher"
jebat --continue
jebat tool list --json
jebat tool call file_tree --args '{"path":".","depth":1}' --json
```

Useful global options include `--print`, `--mode json`, `--tools`, `--no-tools`,
`--skills`, `--session`, `--profile`, `--cwd`, `--no-session`, and `--yolo`.
Keep automatic approvals off for untrusted repositories and production systems.

## Documentation

- [Installation, interactive usage, workflows, and upgrades](../docs/CLI_GUIDE.md)
- [Custom providers](../docs/CUSTOM_PROVIDERS.md)
- [MCP integration](../MCP.md)
- [Agentix solutions](../docs/AGENTIC-SOLUTIONS.md)
- [Load JEBAT startup](../docs/LOAD_JEBAT.md)

## Package layout

| Module | Responsibility |
|--------|----------------|
| `jebat.py` | Canonical CLI entrypoint and active interactive dispatcher |
| `cli.py` | Global argument parsing and automation options |
| `command_palette.py` | Keyboard-first `/` command selection |
| `tool_command.py`, `tool_bridge.py` | Shared-tool discovery and execution |
| `resume.py` | Saved-session selection and restoration |
| `agentix*.py` | Declarative agent solutions and orchestration |
| `mcp*.py` | MCP server and integrations |

## Development

```bash
python -m pip install -e .
python -m pytest tests/test_command_palette.py tests/test_cli_new_entrypoint.py -q
```

Python dependencies are declared in `pyproject.toml`; this is not a stdlib-only
package. A local Ollama installation is optional, not a requirement for all
providers.
