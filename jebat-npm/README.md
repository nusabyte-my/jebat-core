# JEBAT v8.5.0 — Agent CLI

[![npm version](https://img.shields.io/npm/v/@nusabyte/jebat?style=flat-square&color=10b981)](https://www.npmjs.com/package/@nusabyte/jebat)
[![License](https://img.shields.io/npm/l/@nusabyte/jebat?style=flat-square&color=71717a)](LICENSE)
[![Node](https://img.shields.io/node/v/@nusabyte/jebat?style=flat-square)](https://nodejs.org)

`@nusabyte/jebat` is the npm launcher for JEBAT's provider-independent coding
agent console. It supports interactive command discovery, direct tool execution,
sessions, multi-agent workflows, and MCP integration.

## Requirements

- Node.js 18 or newer
- Python 3.11 or newer with `pip`
- A model provider for inference

The launcher bootstraps the supported Python runtime on first use. It does not
install the unrelated `jebat` package from PyPI.

## Install and run

```bash
# Run without a global launcher installation
npx @nusabyte/jebat --version
npx @nusabyte/jebat repl

# Or install globally
npm install -g @nusabyte/jebat
jebat repl

# Bun is also supported
bunx @nusabyte/jebat repl
```

Upgrade the global launcher with:

```bash
npm install -g @nusabyte/jebat@latest
```

For Linux/macOS bootstrap, source installation, upgrades, and troubleshooting,
see the [complete CLI guide](https://github.com/nusabyte-my/jebat-core/blob/main/docs/CLI_GUIDE.md).

## First run

```bash
jebat provider add
jebat repl
```

To generate an `AGENTS.md` workspace capture separately, run `jebat init`.

Configure or change inference from the console:

```text
/provider add
/provider
/model
```

Provider credentials can be read from an environment variable or JEBAT's auth
store instead of being embedded in the provider configuration. Prefer environment
variables in CI and on shared machines.

## Interactive console

Type `/` and press **Enter** to open the command palette. Type to filter, use **Up/Down** or **Tab**
to select, **Enter** to choose, and **Escape** to cancel. Argument-taking
commands remain open for completion. Palette selections use the same handlers
as typed commands.

| Command | Purpose |
|---------|---------|
| `/help` | Show interactive command help |
| `/plan` | Toggle plan-before-execution |
| `/mode` | List or select operating modes |
| `/provider`, `/model` | Configure inference |
| `/tool list` | Discover shared tools |
| `/agents` | List specialist delegation profiles |
| `/delegate PROFILE:TASK` | Delegate a focused task |
| `/swarm TASK` | Auto-orchestrate a task |
| `/yolo [on\|off]` | Control automatic tool approvals |
| `/diff` | Inspect repository changes |
| `/commit MESSAGE` | Create a Git commit |
| `/resume [ID]` | Select or restore a session |
| `/fork` | Fork the current session |
| `/compact` | Compact conversation context |
| `/exit` | Save when enabled and exit |

Additional input forms:

```text
@src/main.py explain the entrypoint
!git status --short
```

`@FILE` attaches file content. `!COMMAND` runs a shell command and adds its
output to context. Use `"""` or `/editor` for multi-line input.

## Automation

```bash
# One-shot coding task
jebat code "Review the CLI dispatch flow"

# Select a provider and model
jebat --provider openai --model gpt-4.1 code "Review this repository"

# Plan before execution
jebat --plan code "Refactor the command dispatcher"

# Resume work
jebat --continue
jebat --session SESSION_ID

# Discover and invoke shared tools
jebat tool list --json
jebat tool call file_tree --args '{"path":".","depth":1}' --json
```

Useful options include `--print`, `--mode json`, `--tools`, `--no-tools`,
`--skills`, `--profile`, `--cwd`, `--no-session`, and `--yolo`. Run
`jebat --help` for the complete parser surface.

Keep staged approvals enabled for untrusted repositories and production systems.
Remote providers receive the prompts and context sent to them; local execution
does not imply that inference is local.

## MCP

Automatically detect supported IDEs and merge JEBAT's local MCP registration:

```bash
npx --yes @nusabyte/jebat mcp pair

# Kiro only
npx --yes @nusabyte/jebat mcp pair --ide kiro

# Inspect without changing files
npx --yes @nusabyte/jebat mcp pair --list
```

Pairing preserves other settings and MCP servers and backs up existing JSON.
Restart/reconnect the IDE afterward. In Kiro Chat, type `#` and select
`plan-act-verify-remember` to load JEBAT's governed workflow.

Generate IDE configuration with:

```bash
jebat mcp ide-config
```

Run the local stdio server with:

```bash
jebat mcp serve --transport stdio
```

See the [MCP integration guide](https://github.com/nusabyte-my/jebat-core/blob/main/MCP.md)
for client configuration and self-hosted transport security.

## Documentation

- [Installation and CLI usage](https://github.com/nusabyte-my/jebat-core/blob/main/docs/CLI_GUIDE.md)
- [CLI package guide](https://github.com/nusabyte-my/jebat-core/blob/main/jebat_cli_new/README.md)
- [Custom providers](https://github.com/nusabyte-my/jebat-core/blob/main/docs/CUSTOM_PROVIDERS.md)
- [Repository and platform overview](https://github.com/nusabyte-my/jebat-core)

## License

MIT · NusaByte
