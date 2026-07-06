# JEBAT v6.1 — Sovereign AI Platform & Agent Workstation

![Version](https://img.shields.io/badge/version-v6.1.0--stable-10b981?style=flat-square)
![Security](https://img.shields.io/badge/security-audited-06b6d4?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-71717a?style=flat-square)
![Tests](https://img.shields.io/badge/tests-145%2F145--passing-10b981?style=flat-square)
![npm](https://img.shields.io/badge/npm-%40nusabyte%2Fjebat-10b981?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-native-8b5cf6?style=flat-square)

> **Sovereign execution, private memory, and audited intelligence.**

JEBAT is an enterprise-grade self-hosted AI platform and agent workstation. It provides governed local LLM inference, secure cognitive routing, multi-agent swarm orchestration, MCP server integration, and an embedded threat reconnaissance toolkit. Run fully air-gapped on your private network with zero data leakage.

Named after the legendary Malay warrior **Hang Jebat** — loyal, powerful, and unforgettable.

---

## Quick Start

### Option 1: npx (Recommended — Zero Install)

Run JEBAT instantly with no setup. The npm wrapper auto-installs the Python package on first run.

```bash
# Interactive REPL
npx @nusabyte/jebat repl

# One-shot chat
npx @nusabyte/jebat chat "Explain the memory consolidation algorithm"

# Run agent task
npx @nusabyte/jebat agent "Audit all API endpoints in src/services"

# With bun
bunx @nusabyte/jebat repl
```

**Requirements:** Node.js >= 18, Python >= 3.11, pip

### Option 2: Global Install

```bash
# Via npm
npm install -g @nusabyte/jebat
jebat repl

# Via pip directly
pip install jebat
jebat repl
```

### Option 3: Source Build

```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
pip install -e .
jebat repl
```

---

## Core Commands

| Command | Description |
|---------|-------------|
| `jebat repl` | **Interactive REPL** — streaming, tools, history |
| `jebat chat "prompt"` | One-shot chat with tool calling |
| `jebat agent "task"` | Run one-shot agent with tool-calling |
| `jebat config show\|set\|reset\|edit` | Configuration management |
| `jebat file read\|write\|patch\|search\|undo\|tree` | Safe file ops with backups |
| `jebat tools list\|inspect` | Inspect all 89 registered tools |
| `jebat memory store\|search\|stats` | 5-layer eternal memory |
| `jebat mcp connect\|list\|call` | MCP server management |
| `jebat skills list\|search\|show` | Tok Guru skills |
| `jebat delegate run "task"` | Multi-agent swarm dispatch |
| `jebat status` | System health & provider status |

---

## MCP Server Integration

JEBAT ships with a native **Model Context Protocol (MCP) server** that exposes 8 tools to any MCP-compatible IDE or client.

### Running JEBAT as an MCP Server

```bash
# Stdio mode (for IDE integration)
python -m jebat.mcp.server

# HTTP mode
python -m jebat.mcp.server --mode http --port 8787

# Via npx
npx @nusabyte/jebat mcp server
```

### MCP Server Tools

| Tool | Description |
|------|-------------|
| `code.read` | Read and analyze code files |
| `code.write` | Create or modify code files |
| `code.generate` | Generate code from description |
| `code.review` | Review code for issues and best practices |
| `project.scaffold` | Create a new project from template |
| `git.operation` | Perform Git operations (init, add, commit, status, log) |
| `test.run` | Run tests (auto, pytest, jest, unittest) |
| `debug.analyze` | Analyze errors and debug issues |

### MCP Resources

| Resource | Description |
|----------|-------------|
| `jebat://status` | Current JEBAT server status |
| `jebat://capabilities` | Available JEBAT capabilities |

### IDE Configuration

#### Cursor / Windsurf / Zed

Add to your MCP config (`.cursor/mcp.json`, `.windsurf/mcp.json`):

```json
{
  "mcpServers": {
    "jebat": {
      "command": "python",
      "args": ["-m", "jebat.mcp.server"],
      "env": {}
    }
  }
}
```

#### VS Code (via Continue / Cline extension)

```json
{
  "mcpServers": {
    "jebat": {
      "command": "npx",
      "args": ["@nusabyte/jebat", "mcp", "server"]
    }
  }
}
```

#### JetBrains (via MCP Plugin)

Settings > Tools > MCP > Add Server:

```
Command: python -m jebat.mcp.server
Mode: stdio
```

### Connecting to External MCP Servers

```bash
# Connect via stdio
jebat mcp connect --stdio "python -m my_server"

# Connect via HTTP
jebat mcp connect --http http://localhost:8080/mcp

# List connected servers
jebat mcp list

# Call a tool on a connected server
jebat mcp call server tool '{"param": "value"}'
```

### MCP Skill Integration

JEBAT bridges its skill system with MCP. Skills are automatically exposed as MCP tools with the `skill.` prefix.

```bash
# Skills are auto-discovered from ~/.jebat/tokguru/
# Each SKILL.md becomes a tool: skill.<name>

# List available skills
jebat skills list

# Search skills
jebat skills search typescript

# Skills are available via MCP as:
# skill.typescript-expert
# skill.react-developer
# etc.
```

---

## Multi-Agent Orchestration

JEBAT dispatches work to specialized sub-agents:

```bash
# Delegate to a specific agent
jebat delegate run "Audit all API endpoints" --agent tukang --tools terminal,file

# Parallel multi-agent task
jebat delegate run "Security audit + code review" --parallel

# Spawn agent swarms
jebat agent "Analyze this codebase for vulnerabilities, performance issues, and code quality"
```

### Agent Roles

| Agent | Domain |
|-------|--------|
| **Tukang** | Implementation, code, builds |
| **Hulubalang** | Security, pentest, hardening |
| **Pawang** | Research, investigation, docs |
| **Syahbandar** | Ops, automation, deploy |
| **Bendahara** | Database, schema, migrations |
| **Penyemak** | QA, validation, release |

---

## Workstation Integration

JEBAT integrates with major developer workspaces as a native MCP server.

### Supported IDEs

| IDE | Method |
|-----|--------|
| **Cursor** | MCP config in `.cursor/mcp.json` |
| **Windsurf** | MCP config in `.windsurf/mcp.json` |
| **VS Code** | Continue / Cline MCP extension |
| **Zed** | MCP config in `~/.config/zed/settings.json` |
| **JetBrains** | MCP Plugin (Settings > Tools > MCP) |

### IDE Workstation Installer

```bash
# Auto-detect IDE and install context files
npx create-jebatcore detect

# Install for specific IDE
npx create-jebatcore install --ide vscode --mode both

# Token optimization
npx create-jebatcore token-analyze
npx create-jebatcore token-compress
```

---

## Technical Comparison

| Capability | JEBAT v6.1 | Commercial SaaS (Claude/GPT) | Ollama WebUI | LM Studio |
| :--- | :---: | :---: | :---: | :---: |
| **Data Residency** | **100% Private / Air-gapped** | Cloud (Third-Party) | Local Only | Local Only |
| **LLM Provider Routing** | **6 Providers (Failover)** | Single Provider | Ollama Only | Local Only |
| **MCP Server** | **Native (8 tools + skills)** | None | Basic API | Local API |
| **Cognitive Profiles** | **7 Thinking Modes (Ultra-Think)** | Standard Chat | Standard Chat | Standard Chat |
| **Security Auditing** | **Autonomous Pentest Suite** | Blocked | None | None |
| **Access Control (RBAC)** | **3-Tier Command Classification** | Muted Policy | Basic Auth | None |
| **Eternal Memory** | **5-Layer Heat-Scored Recall** | Session Limits | No | No |
| **npx / npm** | **Zero-install wrapper** | N/A | N/A | N/A |

---

## Configuration

Config file: `~/.jebat/config.yaml`

```yaml
llm:
  provider: ollama
  model: qwen2.5-coder:7b
  fallback_providers:
    - openai
    - anthropic
    - openrouter
    - groq
safety:
  default_tier: confirm
  sandbox_restricted: true
mcp:
  server_port: 8787
  enable_stdio: true
agent:
  max_iterations: 10
  stream_tokens: true
```

### Quick Config Commands

```bash
# Show config
jebat config show

# Set value
jebat config set agent.safety_mode confirm

# Edit in $EDITOR
jebat config edit

# Health check
jebat doctor
```

---

## System Architecture

```
jebat-core/
  ├── jebat/                  # Active runtime modules
  │   ├── cli/                # Entrypoints (jebat_cli.py v6.1.0)
  │   ├── core/               # Cognitive loops (agent_loop, orchestrator, delegation)
  │   ├── mcp/                # MCP server + skill registry + adapter
  │   ├── services/           # WebUI, MCP protocol, API gateway
  │   ├── features/           # Specialized capability suites
  │   │   ├── code_agent/     # Code agent feature
  │   │   ├── sentinel/       # Security sentinel
  │   │   ├── ultra_loop/     # Autonomous agent loop
  │   │   ├── ultra_think/    # 7-mode reasoning engine
  │   │   └── ...
  │   ├── cortex/             # Skill recommendation engine
  │   ├── orchestration/      # DAG-based workflow engine
  │   ├── multitenancy/       # Multi-tenant isolation
  │   └── llm/                # Multi-provider cognitive routing
  ├── jebat-npm/              # npx/npm wrapper package
  ├── db/                     # SQLite RAG wiki & memory files
  └── docs/                   # Platform architecture references
```

---

## Safety Classification Tiers

To safeguard target servers, JEBAT categorizes all tool execution into permission tiers:

- **AUTO**: Read-only, safe commands executed without intervention (e.g. `cat`, `grep`).
- **CONFIRM**: Write and modification commands prompting user validation (e.g. `write`, `patch`, `git commit`).
- **DANGEROUS**: Destructive or privilege-escalating commands requiring explicit terminal validation tags (e.g. `rm -rf`, `sudo`).

---

## Platform Support

| OS | Shell | Status |
|----|-------|--------|
| macOS | zsh/fish/bash | Full |
| Linux | bash/zsh/fish | Full |
| Windows | PowerShell/CMD/Git Bash | Full |
| WSL2 | bash | Full |

---

## Documentation

- [Quick Reference](QUICK_REFERENCE.md) — One-page cheat sheet
- [Architecture](ARCHITECTURE.md) — Technical deep dive
- [System Report](SYSTEM_REPORT_COMPLETE.md) — Full system report
- [CLI Agent Status](CLI_AGENT_STATUS.md) — Gap analysis & implementation status
- [Deployment](DEPLOYMENT.md) — Deployment guide
- [Roadmap](ROADMAP.md) — Future plans

---

## License & Organization

Developed and maintained under strict data residency governance by NusaByte.
Licensed under the MIT Open Source License. Built by Shaidan Shaari (humm1ngb1rd).

🗡️ **JEBAT** — *Because warriors remember everything that matters.*
