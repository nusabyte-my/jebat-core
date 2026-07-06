# JEBAT v7.0 — Sovereign AI Platform & Agent Workstation

![Version](https://img.shields.io/badge/version-v7.0.0--stable-10b981?style=flat-square)
![Security](https://img.shields.io/badge/security-audited-06b6d4?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-71717a?style=flat-square)
![Tests](https://img.shields.io/badge/tests-145%2F145--passing-10b981?style=flat-square)
![npm](https://img.shields.io/badge/npm-%40nusabyte%2Fjebat-10b981?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-native-8b5cf6?style=flat-square)
![WebUI](https://img.shields.io/badge/WebUI-Stealth--Dark-030303?style=flat-square&labelColor=030303)

> **Sovereign execution, private memory, and audited intelligence.**

JEBAT is an enterprise-grade self-hosted AI platform and agent workstation. It provides governed local LLM inference, secure cognitive routing, multi-agent swarm orchestration, MCP server integration, an embedded threat reconnaissance toolkit, and a full web interface. Run fully air-gapped on your private network with zero data leakage.

Named after the legendary Malay warrior **Hang Jebat** — loyal, powerful, and unforgettable.

---

## Quick Start

### Option 1: npx (Recommended — Zero Install)

```bash
# Interactive REPL
npx @nusabyte/jebat repl

# One-shot chat
npx @nusabyte/jebat chat "Explain the memory consolidation algorithm"

# Run agent task
npx @nusabyte/jebat agent "Audit all API endpoints in src/services"

# Launch WebUI
npx @nusabyte/jebat webui

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

## Platform Suite — 5 Products, 1 Memory

JEBAT ships as a unified platform with 5 integrated products sharing a persistent memory layer and MCP protocol bus.

| Product | Codename | Description |
|---------|----------|-------------|
| **JEBAT Core** | — | The sovereign AI engine — REPL, chat, agent, memory, MCP |
| **Sahabat** | Companion | Memory keeper, briefing agent, meeting intelligence |
| **Keris** | Sentinel | Autonomous pentest orchestrator with AI analysis |
| **Pandai** | Developer | Skills, tools, code generation, developer suite |
| **Perisai** | Nexus | Multi-channel bot orchestrator (Telegram, Discord, Slack, etc.) |

---

## WebUI — Stealth-Dark Tactical Interface

Launch the full web interface with real-time system metrics, product dashboards, and enterprise UX.

```bash
# Launch WebUI
python -m jebat.services.webui.launch
# → http://localhost:8787

# Or via CLI
jebat webui
```

### WebUI Pages (13)

| Page | Description |
|------|-------------|
| **Dashboard** | System metrics (CPU/RAM/disk), product overview, recent scans |
| **Chat** | Universal AI chat with provider selection |
| **Sahabat** | Companion chat, drag-and-drop transcript upload |
| **Keris** | Security scan form, scan history, severity badges |
| **Pandai** | Skills browser, code tools |
| **Perisai** | Channel management, send/broadcast, channel stats |
| **Control** | Runtime control, provider config |
| **Skills** | Skill browser and management |
| **Agents** | Agent orchestration and status |
| **Channels** | Messaging channel configuration |
| **Setup** | Environment setup wizard |
| **Settings** | Provider selection, preferences, API reference |

### WebUI Enterprise Features (25)

**Backend:**
- Rate limiting (120 req/min per IP)
- CORS tightened (localhost-only)
- CSP headers (Content-Security-Policy, X-Frame-Options, nosniff)
- Request ID tracking (X-Request-ID on every response)
- Audit trail (last 500 requests, `/api/audit`)
- Error pages (404/429/500 styled)
- Health check (`/health`)
- Session check (`/api/session/check`)

**Frontend:**
- Loading progress bar
- Dark/Light theme toggle
- Clickable breadcrumb navigation
- Global search palette (Ctrl+K)
- Keyboard shortcuts overlay (?)
- Toast notification system
- Activity log drawer (Ctrl+L)
- Activity log export (JSON/CSV)
- Confirmation dialogs
- Session timeout (15 min inactivity)
- i18n (English/Bahasa Melayu)
- Copy-to-clipboard
- Focus trap (keyboard accessibility)
- Skeleton loading (shimmer)
- Reduced motion support (prefers-reduced-motion)
- Print-friendly CSS
- Drag-and-drop file upload
- Service worker (offline caching)
- PWA manifest (install as desktop app)
- Favicon + OG meta tags
- Responsive mobile sidebar

### WebUI API Endpoints

```
GET  /health                    Health check
GET  /api/system/metrics        CPU, memory, disk, uptime
GET  /api/audit                 Audit trail (last N requests)
GET  /api/session/check         Session verification
GET  /api/keris/history         Scan history
POST /api/keris/scan            Trigger pentest scan
GET  /api/nexus/channels        List channels
POST /api/nexus/send            Send message
POST /api/nexus/broadcast       Broadcast to all
GET  /api/nexus/stats           Channel statistics
GET  /webui/api/status          Provider/model status
POST /webui/api/chat            Chat with AI
POST /webui/api/runtime         Runtime control
```

---

## Core Commands

### General

| Command | Description |
|---------|-------------|
| `jebat repl` | **Interactive REPL** — streaming, tools, history |
| `jebat chat "prompt"` | One-shot chat with tool calling |
| `jebat agent "task"` | Run one-shot agent with tool-calling |
| `jebat webui` | Launch Stealth-Dark WebUI |
| `jebat status` | System health & provider status |
| `jebat doctor` | Diagnose environment issues |
| `jebat init` | Initialize JEBAT with provider config |

### Configuration & Memory

| Command | Description |
|---------|-------------|
| `jebat config show\|set\|reset\|edit` | Configuration management |
| `jebat memory store\|search\|stats` | 5-layer eternal memory |
| `jebat llm providers\|config\|auth` | LLM provider management |
| `jebat llm best-provider` | Auto-detect best available provider |

### File & Tools

| Command | Description |
|---------|-------------|
| `jebat file read\|write\|patch\|search\|undo\|tree` | Safe file ops with backups |
| `jebat tools list\|inspect` | Inspect all registered tools |
| `jebat skills list\|search\|show` | Tok Guru skills |
| `jebat code "description"` | Generate code from description |

### Platform Suite

| Command | Description |
|---------|-------------|
| `jebat companion chat\|briefing\|meeting\|stats` | Sahabat — companion AI |
| `jebat keris scan\|assess\|history` | Keris — pentest scanner |
| `jebat nexus list\|add\|remove\|send\|broadcast\|health\|stats` | Perisai — multi-channel bot |
| `jebat design search\|get\|download\|upload\|lint\|tags` | DESIGN.md integration |

### Agent Orchestration

| Command | Description |
|---------|-------------|
| `jebat delegate run "task"` | Multi-agent swarm dispatch |
| `jebat loop start\|stop\|status` | Autonomous agent loop |
| `jebat think "question"` | Deep reasoning engine |

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

---

## Keris — Sentinel Security

Autonomous pentest orchestrator with AI-powered analysis.

```bash
# Quick scan
jebat keris scan example.com --profile quick

# Full scan with orchestration
jebat keris scan 192.168.1.0/24 --profile full

# Quick assessment
jebat keris assess example.com

# View history
jebat keris history
```

### Scan Profiles

| Profile | Description |
|---------|-------------|
| `quick` | Port scan + basic vulns (~30s) |
| `standard` | Full port scan + service detection + vulns (~2min) |
| `full` | Comprehensive scan + CVE check + SSL analysis (~5min) |
| `vuln` | Vulnerability-focused scan only |

---

## Perisai — Nexus Multi-Channel

Multi-channel bot orchestrator for Telegram, Discord, Slack, Signal, Matrix, and WhatsApp.

```bash
# List channels
jebat nexus list

# Add a channel
jebat nexus add telegram -123456789 --token "BOT_TOKEN"

# Send a message
jebat nexus send -123456789 "Hello from JEBAT!"

# Broadcast to all channels
jebat nexus broadcast "System update complete"

# Health check
jebat nexus health

# Statistics
jebat nexus stats
```

---

## Sahabat — Companion

AI companion for memory, briefings, and meeting intelligence.

```bash
# Interactive chat
jebat companion chat

# Generate briefing
jebat companion briefing

# Summarize meeting
jebat companion meeting --file transcript.txt --title "Sprint Review"

# Companion stats
jebat companion stats
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

## Technical Comparison

| Capability | JEBAT v7.0 | Commercial SaaS (Claude/GPT) | Ollama WebUI | LM Studio |
| :--- | :---: | :---: | :---: | :---: |
| **Data Residency** | **100% Private / Air-gapped** | Cloud (Third-Party) | Local Only | Local Only |
| **LLM Provider Routing** | **6 Providers (Failover)** | Single Provider | Ollama Only | Local Only |
| **MCP Server** | **Native (8 tools + skills)** | None | Basic API | Local API |
| **Cognitive Profiles** | **7 Thinking Modes (Ultra-Think)** | Standard Chat | Standard Chat | Standard Chat |
| **Security Auditing** | **Autonomous Pentest Suite** | Blocked | None | None |
| **Access Control (RBAC)** | **3-Tier Command Classification** | Muted Policy | Basic Auth | None |
| **Eternal Memory** | **5-Layer Heat-Scored Recall** | Session Limits | No | No |
| **Web Interface** | **Stealth-Dark Tactical (25 features)** | Chat UI | Basic UI | Local UI |
| **Platform Suite** | **5 Products, 1 Memory** | Single Product | None | None |
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
  │   ├── cli/                # Entrypoints (jebat_cli.py v7.0.0)
  │   ├── core/               # Cognitive loops (agent_loop, orchestrator, delegation)
  │   ├── mcp/                # MCP server + skill registry + adapter
  │   ├── services/           # WebUI, MCP protocol, API gateway
  │   │   └── webui/          # Stealth-Dark Tactical WebUI
  │   │       ├── launch.py   # Enterprise launcher (rate limit, CSP, audit)
  │   │       ├── webui_server.py  # FastAPI server + WebSocket
  │   │       └── static/     # SPA shell, 13 partials, CSS theme
  │   ├── features/           # Specialized capability suites
  │   │   ├── companion/      # Sahabat — memory, briefing, meetings
  │   │   ├── sentinel/       # Keris — pentest orchestrator
  │   │   ├── nexus/          # Perisai — multi-channel bot
  │   │   ├── design/         # DESIGN.md integration
  │   │   ├── code_agent/     # Code agent feature
  │   │   ├── ultra_loop/     # Autonomous agent loop
  │   │   └── ultra_think/    # 7-mode reasoning engine
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
