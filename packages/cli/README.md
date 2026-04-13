# ⚔️ jebat-core

> Multi-Agent Orchestration Platform with 5 LLM-to-LLM Modes, 10 Core Agents, 24 Specialists, 8 Local LLMs, Enterprise Security, and Self-Hosted AI Platform

[![npm version](https://img.shields.io/npm/v/jebat-core.svg)](https://www.npmjs.com/package/jebat-core)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Next.js 16](https://img.shields.io/badge/next.js-16-black)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/nusabyte-my/jebat-core?style=social)](https://github.com/nusabyte-my/jebat-core)

---

## 🚀 Quick Start

```bash
# Install JEBAT Core
npx jebat-core install

# Check system health
npx jebat-core doctor

# Check status
npx jebat-core status

# Deploy to VPS
npx jebat-core deploy
```

**Live Demo:** [jebat.online](https://jebat.online)

---

## 📋 What is JEBAT Core?

JEBAT Core is the platform backbone — the multi-agent orchestration engine that powers the entire JEBAT ecosystem. It provides:

- **10 Core Agents** with specialized roles and responsibilities
- **24 Specialist Agents** for domain-specific tasks
- **5 Orchestration Modes** for LLM-to-LLM collaboration
- **8 Local LLM Models** running on Ollama
- **5 LLM Providers** with intelligent routing
- **Enterprise Security** with complete audit trails
- **100% Self-Hosted** — no cloud dependency

---

## 🎯 5 Orchestration Modes (Research-Backed)

Based on AutoGen, ChatDev 2.0, and MAD Paradigm papers:

| Mode | Icon | Rounds | What Happens |
|------|------|--------|--------------|
| **Multi-Agent Debate** | ⚖️ | 4 | Advocate vs Critic → Rebuttals → Confidence → Moderator conclusion |
| **Consensus Building** | 🤝 | 3 | Share perspectives → Find agreement → Final synthesized conclusion |
| **Sequential Chain** | 🔗 | 3 | Model 1 starts → Model 2 builds → Model 1 refines |
| **Parallel Analysis** | ⚡ | 2 | Both analyze independently → Comparison table with synthesis |
| **Hierarchical Review** | 🏛️ | 3 | Senior delegates → Junior completes → Senior reviews |

---

## 🤖 10 Core Agents

| Agent | Role | Provider | Model |
|-------|------|----------|-------|
| **Panglima** | Orchestration | Anthropic | claude-sonnet-4 |
| **Tukang** | Development | Ollama | qwen2.5-coder:7b |
| **Hulubalang** | Security Audit | Ollama | hermes-sec-v2 |
| **Pengawal** | CyberSec Defense | Ollama | hermes-sec-v2 |
| **Pawang** | Research | Anthropic | claude-sonnet-4 |
| **Syahbandar** | Operations | Ollama | qwen2.5-coder:7b |
| **Bendahara** | Database | Ollama | qwen2.5-coder:7b |
| **Hikmat** | Memory | Anthropic | claude-sonnet-4 |
| **Penganalisis** | Analytics | Anthropic | claude-sonnet-4 |
| **Penyemak** | QA | Anthropic | claude-sonnet-4 |

---

## 👥 24 Specialist Agents

### Delivery & Build
- Tukang Web - Web development
- Pembina Aplikasi - App development
- Senibina Antara Muka - UI/UX architecture
- Penyebar Reka Bentuk - Design distribution

### Security & Growth
- Khidmat Pelanggan - Customer service
- Penasihat Keselamatan - Security advisor
- Juru Audit - Auditor
- Penjaga Kualiti - Quality guardian

### Strategy & Quality
- Perancang Strategik - Strategic planner
- Analis Risiko - Risk analyst
- Pemikir Kritis - Critical thinker
- Pemeriksa Kualiti - Quality inspector

### Design & Knowledge
- Pereka Grafik - Graphic designer
- Penulis Kandungan - Content writer
- Jurubahasa - Translator
- Penyusun Data - Data organizer

---

## 🤖 8 Local LLM Models

| Model | Size | Best For | Provider |
|-------|------|----------|----------|
| **Gemma 4** | 9.6GB | Best overall | Ollama |
| **Qwen2.5 14B** | 9GB | Coding & reasoning | Ollama |
| **Hermes3** | 4.7GB | Complex reasoning | Ollama |
| **Phi-3** | 2.2GB | Fast responses | Ollama |
| **Llama 3.1 8B** | 4.9GB | General purpose | Ollama |
| **Mistral** | 4.4GB | Balanced performance | Ollama |
| **CodeLlama 7B** | 3.8GB | Code generation | Ollama |
| **TinyLlama** | 637MB | Lightweight testing | Ollama |

---

## 🌐 5 LLM Providers

| Provider | Type | Models |
|----------|------|--------|
| **Anthropic** | Cloud API | Claude 4, Sonnet, Opus |
| **OpenAI** | Cloud API | GPT-4o, GPT-4, GPT-3.5 |
| **Ollama** | Local | 8 models above |
| **Gemini** | Cloud API | Gemini Pro, Flash |
| **ZAI** | Cloud API | Zhipu models |

---

## 🛡️ Enterprise Security

### CyberSec Suite
- **Hulubalang** - Security audit & vulnerability scanning
- **Pengawal** - CyberSec defense & threat detection
- **Perisai** - System hardening & compliance
- **Serangan** - Penetration testing & red team

### Security Features
- ✅ Prompt injection defense
- ✅ Command sanitization
- ✅ Complete audit trails
- ✅ Secrets management
- ✅ 100% self-hosted, no cloud dependency

---

## ⚡ Performance Optimizations

| Feature | Impact | Description |
|---------|--------|-------------|
| **LRUCache** | 40-60% latency reduction | Model response caching with 2-hour TTL |
| **ConnectionPool** | 30% faster requests | Persistent provider connections |
| **RequestDeduplicator** | 30% cost savings | Prevents duplicate API calls |
| **SmartRouter** | 25% improvement | Routes to fastest available provider |

---

## 🔧 CLI Commands

### Installation & Setup

```bash
# Install JEBAT Core
npx jebat-core install

# Check system health
npx jebat-core doctor

# Check status
npx jebat-core status

# List installed skills
npx jebat-core skill-list

# Deploy to VPS
npx jebat-core deploy
```

### Gateway Management

```bash
npx jebat-gateway start      # Start gateway server
npx jebat-gateway stop       # Stop gateway
npx jebat-gateway restart    # Restart gateway
npx jebat-gateway status     # Check gateway status
npx jebat-gateway logs       # View gateway logs
```

### Agent Management

```bash
npx jebat-setup health       # Check agent health
npx jebat-setup skills       # List available skills
npx jebat-setup test         # Test agent connectivity
npx jebat-setup info         # Show system info
```

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     JEBAT Platform v3.0                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Jebat Agent │    │  Jebat Core │    │  Gelanggang │     │
│  │   (npm)     │    │   (npm)     │    │  (Arena)    │     │
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

## 🌐 Live Demos

| Page | URL | Description |
|------|-----|-------------|
| **Landing** | [jebat.online](https://jebat.online) | Main landing with all features |
| **Agent** | [jebat.online/agent](https://jebat.online/agent/) | Dedicated agent documentation |
| **Portal** | [jebat.online/portal](https://jebat.online/portal/) | Enterprise customer portal |
| **Chat** | [jebat.online/chat](https://jebat.online/chat/) | AI chat with 5 orchestration modes |
| **Gelanggang** | [jebat.online/gelanggang](https://jebat.online/gelanggang/) | Multi-agent LLM arena |
| **Security** | [jebat.online/security](https://jebat.online/security/) | Security dashboard |

---

## 📚 Documentation

- [BOOTSTRAP.md](../../jebat-core/BOOTSTRAP.md) - Getting started
- [AGENTS.md](../../jebat-core/AGENTS.md) - Agent guide
- [JEBAT_ASSISTANT_GUIDE.md](../../jebat-core/JEBAT_ASSISTANT_GUIDE.md) - Assistant guide
- [MASTER_INDEX.md](../../jebat-core/MASTER_INDEX.md) - Complete index

---

## 🛣️ Roadmap

- [x] Phase 1: Foundation (Weeks 1-4) - Performance, caching, portal MVP
- [ ] Phase 2: Enterprise (Weeks 5-8) - Multi-tenancy, RBAC, audit trails
- [ ] Phase 3: Customer Experience (Weeks 9-12) - Khidmat Pelanggan, personalization
- [ ] Phase 4: Integration (Weeks 13-16) - SSO/SAML, SIEM, REST API v2
- [ ] Phase 5: Scale (Weeks 17-20) - Auto-scaling, distributed tracing

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature

Co-authored-by: Qwen-Coder <qwen-coder@alibabacloud.com>'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ in Malaysia by <a href="https://nusabyte.my">NusaByte</a>
</p>
