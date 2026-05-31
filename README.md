# JEBAT — CLI AI Agent

> *\"Mimpi yang menjadi nyata ketika pejuang melaksanakan.\"*
> Dreams become reality when warriors execute.

JEBAT is a full-featured CLI AI agent built in Python. It combines an LLM-powered
agent loop (ReAct), 97 registered tools, MCP server/client, free-tier AI routing,
and a cybersecurity toolkit — all in one terminal command.

## What Makes JEBAT Different

| Feature | JEBAT | Hermes | Claude Code | Codex | OpenClaw |
|---------|-------|--------|-------------|-------|----------|
| ReAct Agent Loop | Built-in | Built-in | Built-in | Built-in | Built-in |
| Free AI (no API key) | 9Router proxy | No | No | No | No |
| CyberSec toolkit | CVE/Shodan/nmap | No | No | No | No |
| MCP Server + Client | Dual mode | Client only | No | No | Server only |
| Social Media ops | TG/X/Discord | No | No | No | No |
| Sandbox (Docker) | Built-in | Built-in | Built-in | Built-in | No |
| Undo/Rollback | Built-in | Built-in | No | No | No |
| Cost Tracking | Built-in | Built-in | No | No | No |
| Plugin System | Built-in | Built-in | No | No | No |
| Telemetry | Opt-in | Opt-in | No | No | No |

## Quick Start

```bash
# Install from PyPI (recommended)
pip install jebat

# ...or install from source
git clone https://github.com/humm1ngb1rd/jebat.git
cd jebat-core
pip install -e .

# Run the init wizard to configure your LLM provider
jebat init

# Quick chat with any LLM
jebat agent "Explain zero-day exploits"

# Interactive REPL with tool-calling
jebat chat-repl

# One-shot agent task
jebat agent "Scan nusabyte.my for SSL issues"

# List 47+ available tools
jebat tools

# Search the web
jebat search "latest CVE 2026"

# Free models via 9Router
jebat free-models

# File operations
jebat file read README.md
jebat file write /tmp/test.txt "hello world"
jebat file patch /tmp/test.txt "hello" "goodbye"
jebat file search "TODO" --dir src/

# Run shell commands
jebat exec "echo Hello from JEBAT"

# Wiki / knowledge base
jebat wiki create "my-page" "Knowledge is power"
jebat wiki read my-page
jebat wiki search --query "power"

# Delegation and automation
jebat delegate run "Resolve all TODOs in src/" --tools terminal,file
jebat delegate list
jebat cron add "echo daily heartbeat" --every 24h --name "daily-check"
jebat cron list

# Safety and audit
jebat safety audit
jebat safety classify "rm -rf /tmp/logs"

# Session history and cross-session search (FTS5)
jebat session list
jebat session search "delegation OR wiki"

# Shell autocomplete (bash/zsh)
source jebat-core/shell/jebat-completion.bash  # bash
source jebat-core/shell/jebat-completion.zsh   # zsh
```

## 40 CLI Subcommands

| Command | What It Does |
|---------|-------------|
| `status` | Show system status |
| `init` | First-run setup: configure LLM provider and API key |
| `loop` | Ultra-Loop control (iteration limit, mode) |
| `think` | Run thinking session |
| `memory` | Memory operations (read, write, search) |
| `config` | Show configuration |
| `llm-providers` | List supported LLM providers |
| `llm-config` | Show resolved LLM configuration |
| `llm-auth` | Show provider auth status |
| `llm-best-provider` | Show best configured provider |
| `auth` | Credential storage: set, get, delete, list, which (keyring/env/enc) |
| `doctor` | Check LLM/provider health |
| `mode-guide` | Print JEBAT assistant guide path |
| `skills` | Inspect TokGuru skills |
| `chat` | Chat with LLM (one-shot) |
| `chat-project` | Chat with project context |
| `chat-repl` | Interactive REPL with AgentLoop tool-calling |
| `tools` | List and inspect registered tools |
| `file` | File operations: read, write, patch, search, undo |
| `exec` | Run shell commands (foreground or background) |
| `wiki` | Knowledge base: create, read, edit, search pages |
| `delegate` | Spawn subagents for parallel task execution |
| `cron` | Schedule recurring tasks (add, list, run, pause, remove) |
| `safety` | Security: audit log, sandbox, command classification |
| `session` | Session history: list, search past conversations (FTS5) |
| `todo` | Personal task tracking: add, list, update, remove, clear |
| `mcp` | MCP server management (serve, ide-config) |
| `search` | Web search (SearXNG, Google/Bing API) |
| `agent` | One-shot agent task with tool-calling |
| `social` | Social media: send (Telegram/Discord/Twitter), search, timeline |
| `git` | Git operations: status, diff, log, commit, branch |
| `free-models` | List free/cheap AI models via 9Router |
| `cost` | Token cost dashboard and tracking |
| `undo` | Undo file changes (rollback to backup) |
| `tts` | Text-to-speech: edge (free), openai, voices list |
| `telemetry` | Opt-in usage analytics |
| `sandbox` | Docker sandbox for code execution |
| `plugins` | Manage JEBAT plugins |

## Architecture

```
jebat-core/
  jebat/
    cli/            # CLI entry point (jebat_cli.py, 40 subcommands)
    core/           # Agent brain
      agent_loop.py   # ReAct loop (Think → Act → Observe → Think)
      delegation.py   # Sub-agent task delegation
    features/       # Tool modules
      browser/        # Web automation (9 tools)
      cybersec/       # Security toolkit (10 tools: CVE, Shodan, nmap, DNS, SSL)
      cost_tracking/  # Bendahara — token cost tracking (5 tools)
      cron/           # Scheduled tasks (6 tools)
      security/       # 3-tier safety, audit log, sandbox mode
      fileops/        # File operations (6 tools)
      wiki/           # Knowledge base with FTS5 search + RAG injection
      terminal/       # Async terminal executor (foreground/background/PTY)
      session/        # Session persistence + FTS5 cross-session search
      image_gen/      # Image generation (1 tool)
      mcp/            # MCP client + server (5 server tools)
      plugins/        # TukangPlugin — plugin system (6 tools)
      repl/           # Streaming REPL
      sandbox/        # Hulubalang — Docker sandbox (4 tools)
      search/         # Web search (3 tools)
      shell/          # Shell/file/code tools (6 tools)
      social_media/   # Pengacara — TG/X/Discord (8 tools)
      telemetry/      # Pengawas — opt-in analytics (6 tools)
      terminal/       # Terminal execution (2 tools)
      undo/           # Pawang — undo/rollback (5 tools)
      vision/         # Vision analysis (2 tools)
      wiki/           # Knowledge wiki (8 tools)
    llm/            # LLM providers
      providers.py     # Multi-provider routing (OpenAI, Anthropic, Gemini, GLM, etc.)
      ninerouter_provider.py  # 9Router — free AI via localhost:20128 proxy
    tools/          # Global tool registry (ToolDef, TOOL_REGISTRY)
    integrations/   # Channels (Telegram, Discord, Slack, WhatsApp, webhook)
```

## Agent Names (Malaysian Identity)

JEBAT uses Malaysian warrior/role names for its subsystems:

| Agent | Malay Meaning | Module |
|-------|--------------|--------|
| **Tukang** | Craftsman | Shell tools, Plugin system |
| **Hulubalang** | Warrior/Guard | Sandbox (Docker) |
| **Pawang** | Tracker/Shaman | Undo/Rollback |
| **Pengacara** | Advocate/Lawyer | Social Media |
| **Bendahara** | Treasurer | Cost Tracking |
| **Pengawas** | Observer/Supervisor | Telemetry |
| **TokGuru** | Master Teacher | Skills |

## Safety Tiers

Every tool call goes through safety classification:

| Tier | Behaviour |
|------|-----------|
| **auto** | Execute immediately — read-only, low-risk |
| **confirm** | Ask Y/n before execution — sudo, rm, chmod |
| **dangerous** | Requires `--dangerous` flag — rm -rf /, dd, mkfs |

Dangerous commands are blocked in MCP mode (IDE integration) and require explicit
confirmation in CLI mode.

## MCP Integration

JEBAT can act as both MCP **client** (connect to external tool servers) and
MCP **server** (expose its 47 tools to IDEs like VS Code, Cursor, Windsurf).

```bash
# Start MCP server on stdio (for IDE integration)
jebat mcp serve

# Generate IDE config (VS Code, Cursor, Windsurf)
jebat mcp ide-config --ide vscode

# Connect to an external MCP server
jebat mcp connect --transport stdio --command "some-mcp-server"
```

The MCP server exposes all 47 core tools with JSON Schema parameter definitions.
Tool calls dispatch through the JEBAT tool registry with safety tier enforcement.

## 9Router — Free AI

9Router is a local proxy at `localhost:20128/v1` that provides free-tier access
to Claude, Gemini, GLM, and MiniMax models. No API key required.

```bash
jebat free-models          # List available free models
jebat chat "hello"         # Uses 9Router automatically if no paid provider configured
```

3-tier fallback: Primary → Secondary → Tertiary. RTK compression for efficiency.

## CyberSec Toolkit

hummingb1rd's differentiation — JEBAT is the only CLI agent with built-in
security tools:

- **CVE lookup** — search NVD for vulnerabilities
- **Shodan** — discover exposed services on any host
- **nmap** — port scanning (auto, confirm, or dangerous tier)
- **DNS audit** — enumerate DNS records, check delegation
- **SSL/TLS check** — certificate chain, expiry, cipher analysis
- **Security headers** — HSTS, CSP, X-Frame-Options audit
- **Password analysis** — strength scoring, entropy calculation
- **OWASP quick check** — top 10 risk assessment

```bash
jebat agent "Run a security audit on nusabyte.my"
```

## Testing

All tests pass:

| Suite | Result |
|-------|--------|
| CLI smoke tests | 15/15 PASS |
| MCP protocol tests | 9/9 PASS (initialize, tools/list, tools/call, ping, errors) |
| Module imports | 11/11 OK |
| Tool registry | 47 core + 50 module = 97 total |

## Configuration

JEBAT config lives in `~/.jebat/config.yaml` (or `JEBAT_CONFIG` env var):

```yaml
llm:
  provider: openai
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}   # or use 9Router for free

safety:
  default_tier: auto

mcp:
  servers: []

telemetry:
  enabled: false  # opt-in only

sandbox:
  docker_image: python:3.12-slim
  network_restricted: true
  mount_project: true
```

## Project Layout

```
D:\Jebat\jebat-core\
  jebat/                 # Python package
  jebat-core/            # Core docs (AGENTS.md, BOOTSTRAP.md, etc.)
  JEBAT_MIMPI.md         # Project diary — dreams → reality
  MEMORY.md              # Agent memory
  DESIGN.md              # Architecture design rules
```

## License

Private — NusaByte proprietary. Built by humm1ngb1rd (Shaidan Shaari).

---

*\"Kaboosh!\" — humm1ngb1rd's signature. Ghost in the machine.*