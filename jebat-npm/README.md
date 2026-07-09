# 🗡️ JEBAT v7.5 — Sovereign AI Platform & Agent Workstation

[![npm version](https://img.shields.io/npm/v/@nusabyte/jebat?style=flat-square&color=10b981)](https://www.npmjs.com/package/@nusabyte/jebat)
[![npm downloads](https://img.shields.io/npm/dm/@nusabyte/jebat?style=flat-square&color=06b6d4)](https://www.npmjs.com/package/@nusabyte/jebat)
[![License](https://img.shields.io/npm/l/@nusabyte/jebat?style=flat-square&color=71717a)](LICENSE)
[![Node](https://img.shields.io/node/v/@nusabyte/jebat?style=flat-square)](https://nodejs.org)

> **Sovereign execution, private memory, and audited intelligence.**

JEBAT is an **enterprise-grade self-hosted AI platform and agent workstation**. It provides governed local LLM inference, secure cognitive routing, multi-agent swarm orchestration, embedded threat reconnaissance, and eternal memory — all running fully air-gapped on your private network with **zero data leakage**.

Named after the legendary Malay warrior **Hang Jebat** — loyal, powerful, and unforgettable.

---

## 🚀 Quick Start

### Zero-Config Installation (npx / bunx)

```bash
# Run immediately — auto-installs Python package on first run
npx @nusabyte/jebat repl

# Or with bun
bunx @nusabyte/jebat repl

# One-shot chat
npx @nusabyte/jebat chat "Explain the memory consolidation algorithm"

# Run agent task
npx @nusabyte/jebat agent "Audit all API endpoints in src/services"
```

### Requirements

| Tool | Version | Install |
|------|---------|---------|
| **Node.js** | ≥ 18 | [nodejs.org](https://nodejs.org) |
| **Python** | ≥ 3.11 | [python.org](https://python.org) |
| **pip** | Latest | Included with Python |

---

## 📦 Installation Methods

### Method 1: npx (Recommended — Zero Install)
```bash
npx @nusabyte/jebat repl
```
- Automatically installs Python package via pip on first run
- Always runs latest version
- No global pollution

### Method 2: Global Install
```bash
npm install -g @nusabyte/jebat
# or
bun install -g @nusabyte/jebat

jebat repl
```

### Method 3: Python Direct (Advanced)
```bash
pip install jebat
jebat repl
```

---

## 🎯 Core Commands

| Command | Description |
|---------|-------------|
| `jebat repl` | **Interactive REPL** — streaming, tools, history (primary interface) |
| `jebat chat "prompt"` | One-shot chat with tool calling |
| `jebat agent "task"` | Run one-shot agent with tool-calling |
| `jebat config show\|set\|reset\|edit` | Full configuration management |
| `jebat file read\|write\|patch\|search\|undo\|tree` | Safe file ops with backups |
| `jebat tools list\|inspect` | Inspect all 89 registered tools |

---

## 🔌 REPL Commands (v7.5)

### Session
| Command | Description |
|---------|-------------|
| `/help` | Show categorized help |
| `/clear` | Clear screen |
| `/exit` | Exit session |
| `/banner` | Re-show JEBAT banner |
| `/version` | Show version |

### Providers & Models
| Command | Description |
|---------|-------------|
| `/provider add` | Interactive provider wizard with model browser |
| `/provider remove` | Remove a provider |
| `/provider test` | Test all providers |
| `/provider <id>` | Switch active provider |
| `/model` | Show model catalog for current provider |
| `/model <number\|name>` | Switch model |
| `/providers` | Health-check all providers |
| `/health` | Ping all providers |
| `/ping` | Test provider connectivity |

### Memory
| Command | Description |
|---------|-------------|
| `/memory` | List stored memory |
| `/mem+ <key> = <value>` | Store key/value in memory |
| `/mem` | Show memory entries |
| `/memory+ <key> = <value> <tags>` | Store memory with tags |
| `/recall <query>` | Search memory by query |

### Tasks
| Command | Description |
|---------|-------------|
| `/tasks` | List recent tasks |
| `/task <id>` | Show task details |
| `/agentdb` | Show agent run database |
| `/search <query>` | Search tasks in DB |

### Modes
| Command | Description |
|---------|-------------|
| `/mode` | List/switch operating modes |
| `/mode <name>` | Switch mode (code, security, brainstorm, review, debug, devops, research, fullstack) |
| `/brainstorm <topic>` | Brainstorm on a topic |
| `/scan <path>` | Security scan codebase |
| `/audit <path>` | Audit dependencies |
| `/ports <host>` | Scan open ports |
| `/detect <path>` | Detect frameworks/stack |
| `/scaffold <fw> <name>` | Scaffold new project |
| `/pentest` | Penetration testing checklist |

### Skills
| Command | Description |
|---------|-------------|
| `/skills` | List bundled + installed skills |
| `/skill <name>` | View skill content |

### Info
| Command | Description |
|---------|-------------|
| `/status` | Show agent status |
| `/ctx` | Show session context tracker |
| `/history` | Show session history |
| `/diff` | Show git diff |

### Export
| Command | Description |
|---------|-------------|
| `/export` | Export backup |
| `/export-md` | Export chat as markdown |
| `/commit <msg>` | Git commit with message |

### Agent
| Command | Description |
|---------|-------------|
| `/agents` | List agent profiles |
| `/swarm <task>` | Multi-agent orchestration |
| `/delegate <agent>:<task>` | Delegate to sub-agent |
| `/auth` | Manage auth tokens |
| `/apikey <name>:<key>` | Store API key |

### Security
| Command | Description |
|---------|-------------|
| `/validate <string>` | Validate input for injection |
| `/ratelimit` | Show rate limiter status |

### UI
| Command | Description |
|---------|-------------|
| `/skin` | Switch UI skin |
| `/think` | Toggle think mode |
| `/verbose` | Toggle verbose output |
| `/compact` | Toggle compact mode |
| `/ghost` | Toggle ghost mode (silent) |
| `/plan` | Toggle plan mode |

---

## 🧠 Features

### 17 Providers
- **Local**: Ollama (zero cost)
- **Cloud**: OpenAI, Anthropic, Gemini, GitHub, OpenRouter, Groq, Cerebras, Mistral, Together, DeepSeek, xAI, SambaNova, Novita, Z.AI, Cloudflare AI
- **Custom**: Any OpenAI-compatible endpoint

### 8 Operating Modes
- 💻 **Code** — Default code writing
- 🛡️ **Security** — Security scanning & hardening
- 🧠 **Brainstorm** — Creative thinking
- 🔍 **Review** — Code review
- 🐛 **Debug** — Systematic debugging
- 🚀 **DevOps** — Infrastructure & deployment
- 📚 **Research** — Deep research
- 🌐 **Fullstack** — End-to-end development

### 27 Skills
- Bundled from jebat-core/skills/
- Auto-loaded based on context
- View with `/skills` and `/skill <name>`

### Cybersecurity Tools
- `/scan` — Vulnerability scanning (secrets, SQLi, XSS, command injection)
- `/audit` — Dependency auditing
- `/ports` — Port scanning
- `/pentest` — Penetration testing checklist

### Framework Tools
- `/detect` — Detect frameworks/tech stack
- `/scaffold` — Scaffold new projects (FastAPI, Flask, Express)

### Memory System
- Dual-layer: global + per-project
- Context memory loop (learns from interactions)
- `/recall` — Search memory by query

### Context Tracking
- `/ctx` — Track files read, tools used, decisions
- Auto-updates during agent runs

### Multi-Agent
- `/swarm` — Auto-orchestrate with multiple agents
- `/delegate` — Delegate to specific agent profiles
- 7 agent profiles: coder, reviewer, security, debugger, devops, researcher, planner

### Auth & Security
- `/auth` — Token management
- `/apikey` — API key storage
- Rate limiting (60 calls/minute)
- Input validation

---

## 🔧 MCP Integration

JEBAT supports MCP (Model Context Protocol) for integration with other AI tools.

### MCP Server Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "jebat": {
      "command": "npx",
      "args": ["@nusabyte/jebat", "mcp"]
    }
  }
}
```

### MCP Tools Available

| Tool | Description |
|------|-------------|
| `jebat_code` | Execute code with tool calling |
| `jebat_file` | Read/write/patch files |
| `jebat_search` | Search codebase |
| `jebat_terminal` | Execute shell commands |
| `jebat_memory` | Store/recall memory |

### MCP Environment Variables

| Variable | Description |
|----------|-------------|
| `JEBAT_PROVIDER` | Set provider (ollama, openai, anthropic, etc.) |
| `JEBAT_MODEL` | Set model name |
| `JEBAT_API_KEY` | Set API key |

---

## 📚 Documentation

- [JEBAT CLI Guide](https://github.com/nusabyte-my/jebat-core/blob/master/README.md)
- [MCP Integration](./MCP.md)
- [Contributing](./CONTRIBUTING.md)
- [Changelog](./CHANGELOG.md)

---

## 🏢 Enterprise Features

- **Audit Logging** — SQLite-backed with timestamps, tool usage, latency
- **Cost Tracking** — Per-session cost estimation
- **Session Persistence** — Save/restore conversations
- **Export** — Markdown, JSON, backup formats
- **Ghost Mode** — Silent execution
- **Plan Mode** — Planning before execution

---

## 🔒 Security

- **Zero Data Leakage** — All inference runs locally or via encrypted channels
- **Rate Limiting** — 60 calls/minute default
- **Input Validation** — SQL injection, XSS, command injection detection
- **API Key Storage** — Encrypted local storage
- **Audit Trail** — Complete action logging

---

## 📄 License

MIT © [NusaByte](https://nusabyte.cloud) (humm1ngb1rd)
