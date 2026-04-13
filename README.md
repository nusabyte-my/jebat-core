# ⚔️ JEBAT — The LLM Ecosystem That Remembers Everything

<p align="center">
  <img src="https://img.shields.io/npm/v/jebat-agent.svg?label=jebat-agent" alt="jebat-agent version" />
  <img src="https://img.shields.io/npm/v/jebat-core.svg?label=jebat-core" alt="jebat-core version" />
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/next.js-16-black" alt="Next.js" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
</p>

<p align="center">
  <strong>Eternal Memory · Multi-Agent Orchestration · Autonomous Security</strong><br />
  <em>Self-hosted, enterprise-ready, privacy-first. Built by <a href="https://nusabyte.my">NusaByte</a>.</em>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-packages">npm Packages</a> •
  <a href="#-jebat-agent">Jebat Agent</a> •
  <a href="#-jebat-core">Jebat Core</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 🚀 Quick Start

### Option 1: Setup Wizard (Recommended)

```bash
# Full setup with workspace, skills, and IDE integration
npx jebat-agent --full

# Quick setup (gateway only)
npx jebat-agent --quick
```

### Option 2: Manual Install

```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
npx jebat-core install
```

### Option 3: Try the Chat

Visit **[jebat.online/chat](https://jebat.online/chat)** or run:

```bash
npx jebat-agent --full
npx jebat-gateway start
```

---

## 📦 npm Packages

JEBAT provides two complementary npm packages:

| Package | Version | Purpose | Command |
|---------|---------|---------|---------|
| **[jebat-agent](https://www.npmjs.com/package/jebat-agent)** | `3.0.0` | Setup wizard, local model deployment, IDE integration | `npx jebat-agent` |
| **[jebat-core](https://www.npmjs.com/package/jebat-core)** | `3.0.0` | Platform core, memory system, skill registry, gateway | `npx jebat-core` |

---

## 🤖 Jebat Agent

**The unified AI agent** combining OpenClaw control plane and Hermes capture-first methodology.

### Installation

```bash
# Interactive setup
npx jebat-agent

# Full workspace setup
npx jebat-agent --full

# IDE integration
npx jebat-agent --ide vscode
npx jebat-agent --ide zed
npx jebat-agent --ide claude

# Channel setup
npx jebat-agent --channel telegram
npx jebat-agent --channel discord

# Local model deployment
npx jebat-agent --local-model qwen2.5
npx jebat-agent --local-model gemma4

# Migration from OpenClaw/Hermes
npx jebat-agent --migrate
```

### Features

| Feature | Description | Command |
|---------|-------------|---------|
| **30-Second Setup** | Full workspace with skills and config | `npx jebat-agent --full` |
| **8 Local LLMs** | Deploy Qwen2.5, Gemma 4, Hermes3, Phi-3, and more | `npx jebat-agent --local-model qwen2.5` |
| **IDE Integration** | VS Code, Zed, Cursor, Claude Desktop, Gemini CLI | `npx jebat-agent --ide vscode` |
| **Channel Setup** | Telegram, Discord, WhatsApp, Slack | `npx jebat-agent --channel telegram` |
| **Migration** | Automatic OpenClaw/Hermes conversion | `npx jebat-agent --migrate` |

### Management Commands

```bash
npx jebat-gateway start      # Start gateway server
npx jebat-gateway status     # Check gateway status
npx jebat-gateway restart    # Restart gateway
npx jebat-gateway logs       # View gateway logs
npx jebat-setup health       # Check agent health
npx jebat-setup skills       # List available skills
npx jebat-setup test         # Test agent connectivity
```

### Supported Local Models

| Model | Size | Provider | Best For |
|-------|------|----------|----------|
| **Qwen2.5 14B** | 9GB | Ollama | Best overall performance |
| **Gemma 4** | 9.6GB | Ollama | Google's latest all-rounder |
| **Hermes3 8B** | 4.7GB | Ollama | Complex reasoning |
| **Phi-3** | 2.2GB | Ollama | Fast responses |
| **Llama 3.1 8B** | 4.9GB | Ollama | General purpose |
| **Mistral** | 4.4GB | Ollama | Balanced performance |
| **CodeLlama 7B** | 3.8GB | Ollama | Code generation |
| **TinyLlama** | 637MB | Ollama | Lightweight testing |

---

## 🏗️ Jebat Core

**The platform backbone** — memory system, skill registry, multi-agent orchestration, and gateway.

### Installation

```bash
# Install JEBAT context to IDEs
npx jebat-core install

# Workspace health check
npx jebat-core doctor

# Check system status
npx jebat-core status

# List installed skills
npx jebat-core skill-list

# Deploy to VPS
npx jebat-core deploy
```

### Core Components

| Component | Description |
|-----------|-------------|
| **Memory System** | 5-layer cognitive stack (M0-M4) with heat-based retention |
| **Skill Registry** | 40+ specialized skills optimized for token efficiency |
| **Agent Orchestration** | Multi-agent routing with Gelanggang arena |
| **CyberSec Suite** | Hulubalang (audit), Pengawal (defense), Perisai (hardening), Serangan (pentest) |
| **Gateway Router** | Provider routing across 5 LLM backends with fallback chains |
| **IDE Context** | Inject JEBAT into any editor (VS Code, Cursor, Zed, JetBrains, Neovim) |

### Agent Registry

| Agent | Role | Provider | Model |
|-------|------|----------|-------|
| **Panglima** | Orchestration | Anthropic | claude-sonnet-4 |
| **Tukang** | Development | Ollama | qwen2.5-coder:7b |
| **Hulubalang** | Security | Ollama | hermes-sec-v2 |
| **Pengawal** | CyberSec | Ollama | hermes-sec-v2 |
| **Pawang** | Research | Anthropic | claude-sonnet-4 |
| **Syahbandar** | Operations | Ollama | qwen2.5-coder:7b |
| **Bendahara** | Database | Ollama | qwen2.5-coder:7b |
| **Hikmat** | Memory | Anthropic | claude-sonnet-4 |
| **Penganalisis** | Analytics | Anthropic | claude-sonnet-4 |
| **Penyemak** | QA | Anthropic | claude-sonnet-4 |

Plus **24+ specialist agents**: Tukang Web, Pembina Aplikasi, Senibina Antara Muka, Penyebar Reka Bentuk, and more.

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     JEBAT Platform v3.0                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Jebat Agent│    │ Jebat Core  │    │   Gelanggang│     │
│  │  (npm)      │    │  (npm)      │    │   (Arena)   │     │
│  │             │    │             │    │             │     │
│  │ • Setup     │◄──►│ • Memory    │◄──►│ • LLM-to-LLM│     │
│  │ • Models    │    │ • Skills    │    │ • Debates   │     │
│  │ • Channels  │    │ • Gateway   │    │ • Patterns  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LLM Providers (5)                       │   │
│  │  Anthropic  ·  OpenAI  ·  Ollama  ·  Gemini  ·  ZAI │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⭐ Features

### Memory System
- **5-Layer Cognitive Stack** (M0-M4) with heat-based retention
- Cross-session continuity and intelligent forgetting
- Semantic recall and vector search

### Multi-Agent Orchestration
- **4 Collaboration Patterns**: Sequential, Parallel, Consensus, Adversarial
- **15+ Message Types** for agent communication
- Cross-provider LLM communication
- Gelanggang (LLM-to-LLM Arena)

### Enterprise Security
- Prompt injection defense
- Command sanitization
- Complete audit trails
- Secrets management

### Performance Optimizations
- **LRUCache** for model responses (40-60% latency reduction)
- **ConnectionPool** for LLM providers (30% faster requests)
- **RequestDeduplicator** (30% cost savings)
- **SmartRouter** for fastest provider routing (25% improvement)

---

## 🌐 Live Demos

| Page | URL | Description |
|------|-----|-------------|
| **Landing** | [jebat.online](https://jebat.online) | Main landing with feature overview |
| **Agent** | [jebat.online/agent](https://jebat.online/agent/) | Dedicated agent documentation |
| **Portal** | [jebat.online/portal](https://jebat.online/portal/) | Enterprise customer portal |
| **Chat** | [jebat.online/chat](https://jebat.online/chat/) | AI chat with 8 local models |
| **Gelanggang** | [jebat.online/gelanggang](https://jebat.online/gelanggang/) | Multi-agent LLM arena |
| **Guides** | [jebat.online/guides](https://jebat.online/guides/) | Setup and usage guides |

---

## 🛣️ Roadmap

### Phase 1: Foundation (Weeks 1-4) ✅
- [x] Performance optimization module
- [x] Model caching integration
- [x] Connection pooling
- [x] Customer portal MVP
- [x] CDN for static assets

### Phase 2: Enterprise (Weeks 5-8)
- [ ] Multi-tenancy architecture
- [ ] Role-based access control
- [ ] Audit trails implementation
- [ ] Agent sandboxing
- [ ] Webhook system

### Phase 3: Customer Experience (Weeks 9-12)
- [ ] Khidmat Pelanggan agent
- [ ] Personalization engine
- [ ] Multi-channel notifications
- [ ] Help center integration
- [ ] Feedback system

### Phase 4: Integration (Weeks 13-16)
- [ ] SSO/SAML integration
- [ ] SIEM integration
- [ ] Custom reports engine
- [ ] REST API v2
- [ ] SDK libraries

### Phase 5: Scale (Weeks 17-20)
- [ ] Auto-scaling
- [ ] Load balancing
- [ ] Distributed tracing
- [ ] Advanced analytics

---

## 📊 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Uptime** | 99.99% | 99.9% |
| **Response Time** | <2s local, <5s cloud | 2.1s avg |
| **Cache Hit Rate** | >70% | 65% |
| **Throughput** | 100+ tasks/s | 47 req/s |
| **Customer NPS** | >50 | — |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ in Malaysia by <a href="https://nusabyte.my">NusaByte</a>
</p>
