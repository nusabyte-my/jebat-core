# ⚔️ JEBAT Core — The LLM Ecosystem That Remembers Everything

<p align="center">
  <img src="https://img.shields.io/npm/v/jebat-core.svg" alt="npm version" />
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version" />
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/next.js-16-black" alt="Next.js" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/flutter-3.16-02569B" alt="Flutter" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
</p>

<p align="center">
  <strong>Eternal Memory · Multi-Agent Orchestration · Autonomous Security</strong><br />
  <em>Self-hosted, enterprise-ready, privacy-first. Built by <a href="https://nusabyte.my">NusaByte</a>.</em>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-gelanggang-panglima">Gelanggang</a> •
  <a href="#-npm-cli">CLI</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## ⭐ Support This Project

If JEBAT is useful to your team, please **star this repository**. Every ⭐ helps others discover the platform.

<p align="center">
  <a href="https://github.com/nusabyte-my/jebat-core">
    <img src="https://img.shields.io/github/stars/nusabyte-my/jebat-core?style=social" alt="Stars" />
  </a>
  &nbsp;
  <a href="https://github.com/nusabyte-my/jebat-core/fork">
    <img src="https://img.shields.io/github/forks/nusabyte-my/jebat-core?style=social" alt="Forks" />
  </a>
  &nbsp;
  <a href="https://www.npmjs.com/package/jebat-core">
    <img src="https://img.shields.io/npm/dt/jebat-core.svg" alt="npm downloads" />
  </a>
</p>

---

## 📋 Executive Summary

**JEBAT** is a production-ready, self-hosted AI platform that combines:

| Capability | Description |
|------------|-------------|
| **🧠 Eternal Memory** | 5-layer cognitive architecture (M0–M4) with heat-based importance scoring |
| **⚔️ Multi-Agent Orchestration** | 23 specialist agents across 5 LLM providers with real-time collaboration |
| **🛡️ Autonomous Security** | IBM agentic-ai-cyberres integration with auto-remediation and compliance reporting |
| **🏛️ Gelanggang Panglima** | LLM-to-LLM communication arena — agents debate, propose, and decide |
| **📱 Mobile Ready** | Flutter scaffold for iOS + Android with full API integration |
| **🔒 Enterprise RBAC** | 7 built-in roles, 20+ permissions, GDPR/SOC2/ISO27001 compliance |
| **🌐 Cross-Provider Bridge** | OpenAI ↔ Anthropic ↔ Gemini ↔ Ollama ↔ ZAI communication protocol |
| **📊 SEO/SEM/AEM/GEO** | Dedicated agents for search, marketing, content, and positioning |

**Owner:** [humm1ngb1rd](https://nusabyte.my) — [NusaByte](https://nusabyte.my)
**Live Demo:** [jebat.online](https://jebat.online)
**npm CLI:** `npx jebat-core --help`
**Status:** 100% roadmap complete — production-ready

---

## 🚀 Quick Start

### Option 1: npm CLI (Fastest)

```bash
# Run health check
npx jebat-core doctor

# Install context to your IDE
npx jebat-core install

# Check gateway status
npx jebat-core status

# List all commands
npx jebat-core --help
```

### Option 2: Docker (Recommended for Full Platform)

```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
cp infra/docker/.env.example .env
docker compose up -d
curl http://localhost:8000/api/v1/health
```

### Option 3: Manual Setup

```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Frontend
cd apps/web && npm install && npm run dev

# Backend (separate terminal)
cd apps/api && pip install -r requirements.txt
cd apps/api && python -m services.api.jebat_api
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Channels                              │
│  WhatsApp · Telegram · Discord · Slack · REST API · Web UI   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   jebat-gateway (:18789)                     │
│  Sessions · Cron · Tool Routing · Multi-Tenant · LLM Routing │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                       JEBAT Core                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │ Memory M0-M4│ │ Ultra-Think │ │ Ultra-Loop (5-phase)│    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Agent Orchestrator: 23 Specialists + Panglima       │    │
│  │ Dynamic Loading → Intent Classification → Shimmer   │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Gelanggang: LLM-to-LLM Cross-Provider Arena         │    │
│  │ Sequential · Parallel · Consensus · Adversarial     │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Serangan Autonomous: IBM agentic-ai-cyberres        │    │
│  │ 18 MCP Tools + Auto-Fix Engine + Audit Reports      │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                        Storage                               │
│  PostgreSQL/TimescaleDB · Redis 7 · SQLite + Chroma Vector   │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16 · React 19 · TypeScript · Tailwind v4 |
| **Backend** | Python 3.11+ · FastAPI · Uvicorn · Pydantic |
| **Database** | PostgreSQL/TimescaleDB · Redis 7 · SQLite + Chroma |
| **AI/ML** | OpenAI · Anthropic · Gemini · Ollama · ZAI |
| **DevOps** | Docker Compose · Nginx · Let's Encrypt |
| **Mobile** | Flutter (iOS + Android scaffold) |

---

## 🏢 Enterprise Features

### 🔒 Security & Compliance

| Feature | Detail |
|---------|--------|
| **Autonomous Scanning** | Full codebase audit on every session startup |
| **Auto-Remediation** | Fixes 6 vulnerability types with backups |
| **Audit Logging** | Structured event logging for GDPR/SOC2/ISO27001 |
| **RBAC** | 7 roles (Super Admin → Viewer), 20+ permissions |
| **Compliance Reports** | Auto-generated reports for all 3 frameworks |

### ⚔️ Multi-Agent Orchestration

| Pattern | How It Works | Use Case |
|---------|-------------|----------|
| **Sequential** | Agent A → B → C, each builds on previous | Code → Review → Validate |
| **Parallel** | All agents work simultaneously | Independent analysis |
| **Consensus** | All propose → all vote → majority wins | Architecture decisions |
| **Adversarial** | Two debate → third judges | Critical evaluation |

### 🏛️ Gelanggang Panglima

The LLM-to-LLM orchestration arena where agents from different providers communicate using the standardized JEBAT protocol:

- **Standardized Protocol** — 15+ message types (request, response, delegate, proposal, vote, etc.)
- **Provider Bridge** — Automatic format translation between OpenAI, Anthropic, Gemini, Ollama, ZAI
- **Agent Registry** — Cross-provider discovery by capability, role, or availability
- **Conversation State** — Full dialogue tracking with checksums and timeouts

### 📊 SEO / SEM / AEM / GEO Agents

| Agent | Focus | Use Case |
|-------|-------|----------|
| **Penjejak Carian** (SEO) | Meta optimization, structured data, keyword research | Google placement improvement |
| **Penggerak Pasaran** (SEM) | Growth marketing, paid ads, funnel optimization | Campaign management |
| **Jurutulis Jualan** (AEM) | Conversion copy, landing messaging, content management | Content strategy |
| **Strategi Jenama** (GEO) | Brand positioning, message architecture | Brand visibility |

---

## 💻 npm CLI

Install and run JEBAT commands directly from npm:

```bash
# Install context to your IDE (VS Code, Cursor, Zed, Trae, Antigravity)
npx jebat-core install

# Run workspace health check
npx jebat-core doctor

# Check gateway and VPS status
npx jebat-core status

# List all installed skills
npx jebat-core skill-list

# Token analysis
echo "some text" | npx jebat-core token-analyze

# VPS deployment helper
npx jebat-core deploy
```

**Package:** [jebat-core@2.0.0](https://www.npmjs.com/package/jebat-core) on npm

---

## 📊 Platform Metrics

| Metric | Value |
|--------|-------|
| **Specialist Agents** | 23 |
| **Optimized Skills** | 40+ |
| **LLM Providers** | 5 (OpenAI, Anthropic, Gemini, Ollama, ZAI) |
| **Web Pages** | 12 (landing, demo, setup, dashboard, onboarding, gelanggang, guides, integrations, docs) |
| **Collaboration Patterns** | 4 (Sequential, Parallel, Consensus, Adversarial) |
| **Security Tools Cataloged** | 18 MCP servers |
| **Vulnerability Auto-Fix Types** | 6 |
| **npm Package** | [jebat-core@2.0.0](https://www.npmjs.com/package/jebat-core) |
| **Roadmap Completion** | 100% |
| **License** | MIT |

---

## 🗺️ Roadmap

| Quarter | Theme | Status |
|---------|-------|--------|
| **Q2 2026** | Infrastructure & Polish | ✅ Complete |
| **Q3 2026** | Web UI, API & Scale | ✅ Complete |
| **Q4 2026** | Advanced Features & AI | ✅ Complete |
| **Q1 2027** | Mobile & Voice | ✅ Complete |
| **Q2 2027** | Enterprise Features | ✅ Complete |
| **Q3 2027** | Distributed System | ✅ Complete |

**100% Features Shipped** — All planned quarters complete.

---

## 🌐 Live Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page with pixel agent heroes, install guide, skills, roadmap |
| `/gelanggang/` | LLM-to-LLM orchestration demo with 3 scenarios |
| `/onboarding/` | 5-step questionnaire (Who → Environment → Experience → Needs → Setup) |
| `/setup/` | 5-step setup wizard (Gateway → Providers → IDEs → Skills → Verify) |
| `/dashboard/` | Live gateway status, memory layers, skill overview |
| `/demo/` | Interactive chat demo with dynamic agent loading and shimmer |
| `/guides/` | Guide hub for Developers, Security, Operations, Research |
| `/guides/setup/` | Detailed 7-step setup guide with commands |
| `/integration/gelanggang/` | Gelanggang integration documentation |
| `/integration/custom-agent/` | Bring Your Own Agent guide |

---

## 🤝 Contributing

We welcome contributions! Here's how:

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/jebat-core.git
cd jebat-core

# 2. Create a feature branch
git checkout -b feature/amazing-feature

# 3. Make changes, test, commit
# 4. Push and create PR
git push origin feature/amazing-feature
```

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn
- Keep discussions on-topic

---

## 📜 License

**MIT License** — See [LICENSE](LICENSE) for details.

```
Copyright (c) 2026 NusaByte (humm1ngb1rd)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgments

- **Hang Jebat** — Legendary Malay warrior who inspired the name
- **IBM** — [agentic-ai-cyberres](https://github.com/IBM/agentic-ai-cyberres) for security scanning patterns
- **raphabot** — [awesome-cybersecurity-agentic-ai](https://github.com/raphabot/awesome-cybersecurity-agentic-ai) for tool catalog
- **geezerrrr** — [agent-town](https://github.com/geezerrrr/agent-town) for the Gelanggang concept

---

## 📞 Support

- **GitHub Issues**: [Report bugs](https://github.com/nusabyte-my/jebat-core/issues)
- **Discussions**: [Ask questions](https://github.com/nusabyte-my/jebat-core/discussions)
- **Website**: [jebat.online](https://jebat.online)
- **npm CLI**: `npx jebat-core --help`
- **Owner**: [humm1ngb1rd](https://nusabyte.my) — NusaByte

---

<p align="center">
  <strong>⚔️ JEBAT — Because warriors remember everything that matters.</strong><br />
  <em>Made with ❤️ in Malaysia by <a href="https://nusabyte.my">humm1ngb1rd</a> and NusaByte.</em>
</p>

<p align="center">
  <a href="https://github.com/nusabyte-my/jebat-core">
    ⭐ Star this repo if JEBAT is useful to you!
  </a>
</p>
