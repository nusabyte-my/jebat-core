# 🤖 jebat-agent

> 30-second setup for AI agent workspace with 8 local LLM models (Gemma 4, Qwen2.5, Hermes3, Phi-3), IDE integration, multi-agent orchestration, markdown rendering, and enterprise security.

[![npm version](https://img.shields.io/npm/v/jebat-agent.svg)](https://www.npmjs.com/package/jebat-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/nusabyte-my/jebat-core?style=social)](https://github.com/nusabyte-my/jebat-core)

---

## 🚀 Quick Start

```bash
# Interactive setup wizard
npx jebat-agent

# Quick setup (gateway only)
npx jebat-agent --quick

# Full setup (workspace + skills + models)
npx jebat-agent --full

# Migrate from OpenClaw/Hermes
npx jebat-agent --migrate
```

**Live Demo:** [jebat.online/chat](https://jebat.online/chat/)

---

## 📋 What is Jebat Agent?

Jebat Agent is your unified AI agent workspace. It combines the OpenClaw control plane and Hermes capture-first methodology into one powerful, self-hosted platform.

### Features

| Feature | Description | Command |
|---------|-------------|---------|
| **30-Second Setup** | Full workspace with skills and config | `npx jebat-agent --full` |
| **8 Local LLMs** | Deploy Gemma 4, Qwen2.5, Hermes3, Phi-3, and more | `npx jebat-agent --local-model gemma4` |
| **IDE Integration** | VS Code, Zed, Cursor, Claude Desktop, Gemini CLI | `npx jebat-agent --ide vscode` |
| **Channel Setup** | Telegram, Discord, WhatsApp, Slack | `npx jebat-agent --channel telegram` |
| **Migration** | Automatic OpenClaw/Hermes conversion | `npx jebat-agent --migrate` |
| **Multi-Agent** | 10 core agents + 24 specialists | Via jebat-core |
| **5 Orchestration Modes** | Debate, Consensus, Sequential, Parallel, Hierarchical | Via chat UI |
| **Markdown Rendering** | Tables, code blocks, headers in all responses | Automatic |

---

## 🤖 8 Local LLM Models

Run AI locally with Ollama — no API keys needed:

| Model | Size | Best For |
|-------|------|----------|
| **Gemma 4** | 9.6GB | Best overall (default) |
| **Qwen2.5 14B** | 9GB | Coding & reasoning |
| **Hermes3** | 4.7GB | Complex reasoning |
| **Phi-3** | 2.2GB | Fast responses (default secondary) |
| **Llama 3.1 8B** | 4.9GB | General purpose |
| **Mistral** | 4.4GB | Balanced performance |
| **CodeLlama 7B** | 3.8GB | Code generation |
| **TinyLlama** | 637MB | Lightweight testing |

---

## 🔧 Commands

### Setup

```bash
# Interactive wizard
npx jebat-agent

# Quick setup (gateway only)
npx jebat-agent --quick

# Full setup (workspace + skills)
npx jebat-agent --full

# Migrate from OpenClaw/Hermes
npx jebat-agent --migrate
```

### IDE Integration

```bash
npx jebat-agent --ide vscode    # VS Code / Cursor
npx jebat-agent --ide zed       # Zed editor
npx jebat-agent --ide claude    # Claude Desktop
npx jebat-agent --ide gemini    # Gemini CLI
```

### Channel Setup

```bash
npx jebat-agent --channel telegram   # Telegram bot
npx jebat-agent --channel discord    # Discord bot
npx jebat-agent --channel whatsapp   # WhatsApp Business
npx jebat-agent --channel slack      # Slack app
```

### Management

```bash
# Gateway commands
npx jebat-gateway start      # Start gateway
npx jebat-gateway stop       # Stop gateway
npx jebat-gateway restart    # Restart gateway
npx jebat-gateway status     # Check status
npx jebat-gateway logs       # View logs

# Agent commands
npx jebat-setup health       # Check health
npx jebat-setup skills       # List skills
npx jebat-setup test         # Test agent
npx jebat-setup info         # Show info
```

---

## 📁 Directory Structure

After running setup:

```
~/.jebat/
├── jebat-gateway.json    # Gateway configuration
├── .env                  # Environment variables
└── workspace/
    ├── IDENTITY.md       # Agent identity
    ├── SOUL.md           # Agent personality
    ├── TOOLS.md          # Available tools
    ├── USER.md           # User preferences
    └── skills/
        └── jebat-agent/
            └── SKILL.md  # Agent skill definition
```

---

## ⚙️ Configuration

Gateway config at `~/.jebat/jebat-gateway.json`:

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "auth": {
      "mode": "token",
      "token": "your-token"
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/gemma4:latest",
        "secondary": "ollama/phi3:latest",
        "fallbacks": [
          "ollama/qwen2.5:14b",
          "ollama/hermes3:latest"
        ]
      }
    }
  }
}
```

---

## 🔄 Migration

Migrating from OpenClaw/Hermes?

```bash
npx jebat-agent --migrate
```

This will:
- Convert `~/.openclaw` → `~/.jebat`
- Update all config formats
- Rename skills appropriately
- Preserve your existing setup

---

## 🌐 Ecosystem

Jebat Agent works with **jebat-core** for the full platform experience:

| Package | Purpose | Command |
|---------|---------|---------|
| **jebat-agent** | Setup wizard & local models | `npx jebat-agent` |
| **jebat-core** | Multi-agent orchestration | `npx jebat-core` |

---

## 🌍 Live Demos

| Page | URL |
|------|-----|
| **Landing** | [jebat.online](https://jebat.online) |
| **Chat** | [jebat.online/chat](https://jebat.online/chat/) |
| **Portal** | [jebat.online/portal](https://jebat.online/portal/) |
| **Gelanggang** | [jebat.online/gelanggang](https://jebat.online/gelanggang/) |

---

## 💻 Requirements

- Node.js 18+
- npm/npx
- Python 3.10+ (for gateway server)
- 8GB+ RAM for local models (recommended: 16GB+)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT © NusaByte / JEBATCore

---

<p align="center">
  Built with ❤️ in Malaysia by <a href="https://nusabyte.my">NusaByte</a>
</p>
