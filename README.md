# 🗡️ JEBAT v7.5 — Unified Coding Agent

> Sovereign execution, private memory, and audited intelligence.

JEBAT is a **unified, provider-first coding-agent CLI** that connects to 17+ AI providers with a single tool. It features an interactive REPL, 27 bundled skills, cybersecurity tools, multi-agent orchestration, and eternal memory.

Named after the legendary Malay warrior **Hang Jebat** — loyal, powerful, and unforgettable.

---

## 🚀 Installation

### npm (Recommended)
```bash
# Zero-install — runs immediately
npx @nusabyte/jebat repl

# Or install globally
npm install -g @nusabyte/jebat
jebat repl
```

### pip
```bash
pip install jebat
jebat repl
```

### From Source
```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
pip install -e .
jebat repl
```

### Requirements
- **Node.js** ≥ 18 (for npm method)
- **Python** ≥ 3.11

---

## ⚡ Quick Start

```bash
# Interactive REPL
jebat repl

# One-shot chat
jebat chat "Explain this code"

# Run agent task
jebat agent "Refactor this module"

# Security scan
jebat scan src/

# Scaffold new project
jebat scaffold fastapi my-api
```

---

## 🔌 Providers (17 supported)

| Provider | Models | Cost |
|----------|--------|------|
| **Ollama** | Qwen, Llama, Gemma, DeepSeek | FREE |
| **OpenAI** | GPT-4o, GPT-4.1, o3, o4-mini | $2.5-15/1M |
| **Anthropic** | Claude Opus 4, Sonnet 4, Haiku 3.5 | $3-15/1M |
| **Gemini** | 2.5 Pro, 2.5 Flash, 2.0 Flash | $1.25-5/1M |
| **GitHub** | GPT-4o | FREE |
| **OpenRouter** | 150+ models | Varies |
| **Groq** | Llama 3.3, Mixtral, Gemma | $0.5-0.8/1M |
| **Cerebras** | Llama 3.3 | $0.15-0.6/1M |
| **DeepSeek** | V3, R1 | $0.14-0.28/1M |
| **xAI** | Grok 3, 3 Mini | $3-15/1M |
| **Together** | Llama, DeepSeek | $0.2-0.5/1M |
| **Mistral** | Large, Codestral, Small | $0.25-0.75/1M |
| **SambaNova** | Various | FREE |
| **Novita** | Various | $0.35-0.4/1M |
| **Z.AI** | Various | $1-3/1M |
| **Cloudflare AI** | Various | FREE |

---

## 🎯 REPL Commands

```bash
# Session
/help                    # Show help
/clear                   # Clear screen
/version                 # Show version
/exit                    # Exit

# Providers
/provider add            # Add provider (interactive wizard)
/provider test           # Test all providers
/provider ollama         # Switch provider
/model                   # List models for current provider
/model 3                 # Switch model by number

# Memory
/memory                  # List stored memory
/memory+ key = value     # Store memory
/recall query            # Search memory

# Tasks
/tasks                   # List recent tasks
/search query            # Search task database

# Modes
/mode                    # List modes
/mode security           # Switch to security mode
/brainstorm topic        # Brainstorm

# Skills
/skills                  # List bundled skills
/skill security-pentest  # View skill

# Agent
/swarm "multi-task"      # Multi-agent orchestration
/agents                  # List agent profiles

# Security
/scan src/               # Security scan
/audit                   # Audit dependencies
/pentest                 # Penetration testing
/validate input          # Input validation

# Export
/export                  # Export backup
/export-md               # Export as markdown
/commit msg              # Git commit
```

---

## 🧠 Features

- **8 Operating Modes** — Code, Security, Brainstorm, Review, Debug, DevOps, Research, Fullstack
- **27 Skills** — Auto-loaded from jebat-core/skills/
- **Context Tracking** — Track files, tools, decisions
- **Memory System** — Dual-layer global + per-project memory
- **Multi-Agent** — Swarm orchestration with 7 agent profiles
- **Audit Logging** — SQLite-backed action history
- **Cost Tracking** — Per-session cost estimation
- **Session Persistence** — Save/restore conversations

---

## 🔧 MCP Integration

JEBAT supports MCP for IDE integration (VS Code, Cursor, Windsurf, Claude Desktop).

```json
{
  "mcpServers": {
    "jebat": {
      "command": "npx",
      "args": ["@nusabyte/jebat", "mcp", "serve", "--transport", "stdio"]
    }
  }
}
```

See [MCP.md](./MCP.md) for full documentation.

---

## 📚 Documentation

- [NPM Package](https://www.npmjs.com/package/@nusabyte/jebat)
- [MCP Integration](./MCP.md)
- [Skills](./skills/)
- [Agent Guide](./JEBAT_ASSISTANT_GUIDE.md)

---

## 🏢 Enterprise

- **Zero Data Leakage** — Local inference via Ollama
- **Rate Limiting** — 60 calls/minute
- **Input Validation** — SQL/XSS/injection detection
- **API Key Storage** — Encrypted local storage
- **Audit Trail** — Complete action logging

---

## 📄 License

MIT © [NusaByte](https://nusabyte.cloud) (humm1ngb1rd)
