# 🗡️ JEBAT v8.2 — Sovereign Agent OS & Agent Workstation

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

### Method 3: Source Build (Advanced)
```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
curl -fsSL https://jebat.online/install.sh | bash   # bootstrap the Python core
jebat repl
```
> The npm package is a thin launcher. On first run it downloads and runs the
> bootstrap, which provisions Python, the venv, and the `jebat` launcher in
> `~/.local`. There is no `pip install jebat` package.

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
| `jebat memory store\|search\|stats` | 5-layer eternal memory |
| `jebat status` | System health & provider status |
| `jebat --version` | Show version |
| `jebat --help` | Show help |

---

## 🔧 Configuration

Config file: `~/.jebat/jebat.yaml`

```yaml
agent:
  default_model: "qwen2.5-coder:7b"
  default_provider: "ollama"
  safety_mode: "confirm"
  max_iterations: 10
  stream_tokens: true

llm_providers:
  ollama_host: "http://localhost:11434"
  fallback_providers: ["openrouter", "groq", "openai"]

security:
  enable_guardrails: true
  audit_log: true
```

### Quick Config Commands
```bash
# Show config
npx @nusabyte/jebat config show

# Set value
npx @nusabyte/jebat config set agent.safety_mode confirm

# Edit in $EDITOR
npx @nusabyte/jebat config edit
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  JEBAT Wrapper (this package)                                │
│  • Auto-installs Python package via pip                      │
│  • Forwards CLI arguments                                    │
│  • Handles stdin/stdout for REPL                             │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  JEBAT Python Core (pip install jebat)                       │
│  • ReAct AgentLoop (Think→Act→Observe)                       │
│  • Ultra-Think (7 reasoning modes)                           │
│  • Ultra-Loop (autonomous agent)                             │
│  • 5-Layer Memory (M0→M4 with heat scoring)                  │
│  • 89 Tools (file, git, browser, web, vision, sandbox...)    │
│  • MCP Client + Server                                       │
│  • Multi-Agent Swarms (Tukang/Hulubalang/Pawang)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security & Privacy

- **100% Local** — No data leaves your machine
- **Encrypted Storage** — Fernet (API keys) + Argon2id (passwords)
- **Audit Logging** — All tool executions tracked
- **3-Tier Safety** — auto / confirm / dangerous
- **Sandbox Isolation** — Docker for untrusted code
- **No Telemetry** — Opt-in only

---

## 🤝 MCP Integration

```bash
# Connect to MCP servers
npx @nusabyte/jebat mcp connect --stdio "python -m my_server"
npx @nusabyte/jebat mcp connect --http http://localhost:8080/mcp

# List & call
npx @nusabyte/jebat mcp list
npx @nusabyte/jebat mcp call server tool '{"param": "value"}'
```

---

## 🌍 Platform Support

| OS | Shell | Status |
|----|-------|--------|
| macOS | zsh/fish/bash | ✅ Full |
| Linux | bash/zsh/fish | ✅ Full |
| Windows | PowerShell/CMD/Git Bash | ✅ Full |
| WSL2 | bash | ✅ Full |

---

## 📚 Documentation

- [Full README](https://github.com/nusabyte-my/jebat-core/blob/main/README.md)
- [Architecture](https://github.com/nusabyte-my/jebat-core/blob/main/ARCHITECTURE.md)
- [Quick Reference](https://github.com/nusabyte-my/jebat-core/blob/main/QUICK_REFERENCE.md)
- [Deployment](https://github.com/nusabyte-my/jebat-core/blob/main/DEPLOYMENT.md)
- [Roadmap](https://github.com/nusabyte-my/jebat-core/blob/main/ROADMAP.md)

---

## 🤝 Contributing

```bash
# Clone repo
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core/jebat-npm

# Test locally
npm link
jebat repl
```

---

## 📄 License

**MIT License** — See [LICENSE](../LICENSE) file.

Developed under strict data residency governance by **NusaByte**.\
Built with ❤️ by **Shaidan Shaari (humm1ngb1rd)**.

---

## 🙏 Acknowledgments

- **Python core:** [jebat-core](https://github.com/nusabyte-my/jebat-core)
- **Ollama** — Local LLM inference
- **LangGraph** — Cognitive orchestration
- **Rich / prompt-toolkit** — Terminal interfaces
- **Playwright** — Browser automation

---

## 🗡️ The JEBAT Way

> *"Hang Jebat fought with loyalty and honor. JEBAT remembers with precision and purpose."*

**Your AI. Your Data. Your Legacy.**

🗡️ **JEBAT v8.2** — *Because warriors remember everything that matters.*