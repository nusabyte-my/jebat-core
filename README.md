# ⚔️ JEBAT Core — The LLM Ecosystem That Remembers Everything

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/status-production%20ready-success.svg" alt="Status" />
  <img src="https://img.shields.io/badge/next.js-16-black" alt="Next.js" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688" alt="FastAPI" />
</p>

<p align="center">
  <strong>Eternal memory. Multi-agent orchestration. 6 thinking modes. CyberSec assistant.</strong><br />
  <em>Self-hosted, privacy-first. Built by <a href="https://nusabyte.my">NusaByte</a>.</em>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</p>

---

## ⭐ If JEBAT is useful to you, please star this repository!

Your stars help others find this project. Every ⭐ matters.

<p align="center">
  <a href="https://github.com/nusabyte-my/jebat-core">
    <img src="https://img.shields.io/github/stars/nusabyte-my/jebat-core?style=social" alt="Stars" />
  </a>
  &nbsp;
  <a href="https://github.com/nusabyte-my/jebat-core/fork">
    <img src="https://img.shields.io/github/forks/nusabyte-my/jebat-core?style=social" alt="Forks" />
  </a>
</p>

**How to star:**
1. Click the ⭐ **Star** button at the top-right of this page
2. Select **Watch** → **All Activity** to stay updated
3. Share with your team — JEBAT works best with collaborators

---

## 📋 Executive Summary

**JEBAT** is a production-ready, self-hosted AI platform that combines eternal memory, multi-agent orchestration, and autonomous security scanning into a single ecosystem. Built for developers, pentesters, and organizations who need an AI operator that remembers everything, routes work intelligently, and keeps your data private.

| Metric | Value |
|--------|-------|
| **Agents** | 23 specialist agents + Panglima orchestrator |
| **Skills** | 40+ optimized and enhanced skills |
| **Pages** | 9 static pages (landing, onboarding, demo, dashboard, setup, integrations) |
| **Memory** | 5-layer cognitive architecture (M0-M4) with heat scoring |
| **Thinking** | 6 modes: Fast, Deliberate, Deep, Strategic, Creative, Critical |
| **Security** | Autonomous scanner + auto-fix (IBM agentic-ai-cyberres integration) |
| **Roadmap** | 87% complete (Q2-Q4 2026 shipped, 2027 planned) |
| **Owner** | [humm1ngb1rd](https://nusabyte.my) — [NusaByte](https://nusabyte.my) |
| **Live** | [jebat.online](https://jebat.online) |

### Why JEBAT?

- **Memory that persists** — 5-layer system that remembers what matters across every session
- **Agents that specialize** — 23 specialists routed by Panglima (capture-first orchestration)
- **Security that automates** — Autonomous scanner on every startup with auto-remediation
- **Infrastructure you own** — Self-hosted, no cloud dependency, full data control
- **Dynamic loading** — Agents load based on your intent, with shimmer notifications

---

## 🚀 Quick Start

Get JEBAT running in **5 minutes**:

```bash
# 1. Clone the repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# 2. Install web dependencies
cd apps/web && npm install && cd ../..

# 3. Build the frontend
cd apps/web && npx next build && cd ../..

# 4. Start the backend API
cd apps/api && pip install -r requirements.txt && cd ../..
cd apps/api && python -m services.api.jebat_api &

# 5. Start the gateway (port 18789)
# Configure your OpenClaw gateway per your provider setup

# 6. Serve the frontend
cd apps/web && npm start

# Open http://localhost:3000
```

### One-Command Docker Setup

```bash
# Start everything with Docker Compose
docker compose up -d

# Verify services
docker ps

# Check API health
curl http://localhost:8000/api/v1/health
```

---

## ✨ Features

### 🧠 Eternal Memory System
- **5-Layer Architecture**: Sensory (M0) → Episodic (M1) → Semantic (M2) → Conceptual (M3) → Procedural (M4)
- **Heat-Based Scoring**: 30% frequency + 25% depth + 25% recency + 15% cross-refs + 5% rating
- **Auto-Consolidation**: Memories promote and decay based on importance
- **Cross-Linked Recall**: Semantic search across all layers

### ⚔️ Multi-Agent Orchestration
- **Panglima Mode**: Capture-first operator — understands context before acting
- **23 Specialist Agents**: Each optimized for specific domains
- **Dynamic Loading**: Agents load based on your prompt intent with shimmer notifications
- **Council Workflows**: Multiple agents deliberate for complex decisions

| Agent | Domain | Agent | Domain |
|-------|--------|-------|--------|
| Panglima | Orchestration | Hikmat | Memory |
| Tukang | Development | Hulubalang | Security |
| Pawang | Research | Syahbandar | Operations |
| Bendahara | Database | Penyemak | QA |
| Pengawal | CyberSec | Perisai | Defensive |
| Serangan | Offensive | Penganalisis | Analytics |
| + 12 more specialists | | | |

### 🔒 Autonomous Security Scanner
- **Adapted from IBM's agentic-ai-cyberres** for codebase scanning
- **18 MCP Security Tools** cataloged from awesome-cybersecurity-agentic-ai
- **4-Phase Scan**: Secrets → Code Patterns → Dependencies → Infrastructure
- **Auto-Fix Engine**: Automatically remediates 6 vulnerability types with backups
- **Runs on Startup**: Every JEBAT session begins with a security scan

### 🔥 Ultra-Think Reasoning
| Mode | Use Case |
|------|----------|
| **Fast** | Quick answers for simple questions |
| **Deliberate** | Balanced reasoning for most tasks |
| **Deep** | Complex multi-layered analysis |
| **Strategic** | Long-term planning |
| **Creative** | Innovative lateral thinking |
| **Critical** | Analytical evaluation |

### 📡 Multi-Channel Gateway
- **WhatsApp, Telegram, Discord, Slack, REST API**
- **Session management** and **cron automation**
- **DM pairing** for security
- **Multi-provider LLM routing**: Ollama, ZAI, OpenAI, Anthropic, Gemini, OpenRouter

### 🌐 Web Platform (9 Pages)
| Page | Description |
|------|-------------|
| `/` | Landing page with features, integrations, roadmap |
| `/onboarding/` | 5-step questionnaire (Who → Environment → Experience → Needs → Setup) |
| `/demo/` | Interactive chat with dynamic agent loading + shimmer |
| `/setup/` | 5-step setup wizard (Gateway → Providers → IDEs → Skills → Verify) |
| `/dashboard/` | Live gateway status, memory layers, skill overview |
| `/docs/` | Platform documentation |
| `/integration/agent-town/` | Agent Town × JEBAT integration guide |
| `/integration/custom-agent/` | Bring Your Own Agent guide |
| `/demo/` | Public demo page |

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
│  │ Serangan Autonomous: IBM agentic-ai-cyberres        │    │
│  │ 18 MCP Tools + Auto-Fix Engine + Scan Reports       │    │
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
| **AI/ML** | Ollama · OpenAI · Anthropic · Gemini · OpenRouter · ZAI |
| **DevOps** | Docker Compose · Nginx · Let's Encrypt |
| **CLI** | Node.js (jebat) · Python (devtool) · Rich UI |

---

## 📦 Installation

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Node.js** | ≥ 18.0 | For Next.js frontend and NPX CLI |
| **Python** | ≥ 3.11 | For FastAPI backend and scripts |
| **Docker** | ≥ 24.0 | Optional but recommended |
| **Git** | ≥ 2.40 | For version control |

### Method 1: Git Clone + Manual Setup

```bash
# Clone
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Frontend
cd apps/web && npm install && npx next build && cd ../..

# Backend
cd apps/api && pip install -r requirements.txt && cd ../..

# Start API
cd apps/api && python -m services.api.jebat_api &

# Serve frontend
cd apps/web && npm start
```

### Method 2: Docker Compose (Recommended)

```bash
# Clone
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Copy environment
cp infra/docker/.env.example .env

# Start all services
docker compose up -d

# Verify
docker ps
curl http://localhost:8000/api/v1/health
```

### Method 3: NPX CLI (Quick Install)

```bash
# Install JEBAT context to your IDE
npx @nusabyte/jebat install

# Run workspace health check
npx @nusabyte/jebat doctor

# Check gateway status
npx @nusabyte/jebat status

# Start onboarding wizard
npx @nusabyte/jebat setup
```

### IDE Integration

JEBAT supports automatic context injection into:

| IDE | Command | File Created |
|-----|---------|-------------|
| **VS Code** | `npx @nusabyte/jebat install` | `.github/copilot-instructions.md` |
| **Cursor** | `npx @nusabyte/jebat install` | `.cursorrules` |
| **Zed** | `npx @nusabyte/jebat install` | `.zed/jebat-system-prompt.md` |
| **Trae** | `npx @nusabyte/jebat install` | `.trae/rules/jebat.md` |
| **Antigravity** | `npx @nusabyte/jebat install` | `.antigravity/jebat.md` |
| **Windsurf** | `npx @nusabyte/jebat install` | `.windsurf/jebat.md` |

---

## 💻 Usage

### Web Interface

Open [http://localhost:3000](http://localhost:3000) after starting the frontend.

| Route | Description |
|-------|-------------|
| `/` | Landing page — features, integrations, roadmap |
| `/onboarding/` | Tell us about yourself — we'll configure JEBAT for you |
| `/demo/` | Interactive chat — try all 6 thinking modes |
| `/setup/` | 5-step setup wizard — gateway, providers, IDEs, skills |
| `/dashboard/` | Live status — API health, memory layers, installed skills |

### CLI Commands

```bash
# Setup wizard
npx @nusabyte/jebat setup

# Interactive chat
npx @nusabyte/jebat chat

# Install context to IDEs
npx @nusabyte/jebat install

# Detect installed IDEs
npx @nusabyte/jebat detect

# Workspace health check
npx @nusabyte/jebat doctor

# Gateway + VPS status
npx @nusabyte/jebat status

# List installed skills
npx @nusabyte/jebat skill-list

# Token analysis
echo "some text" | npx @nusabyte/jebat token-analyze

# VPS deployment helper
npx @nusabyte/jebat deploy
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health

# System status
curl http://localhost:8000/api/v1/status

# Chat (OpenAI-compatible)
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, JEBAT", "mode": "deliberate"}'

# Memory CRUD
curl http://localhost:8000/api/v1/memories
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{"content": "User prefers dark mode"}'
```

---

## 🗺️ Roadmap

| Quarter | Theme | Status |
|---------|-------|--------|
| **Q2 2026** | Infrastructure & Polish | ✅ **Complete** — Monitoring, Docker, CI/CD, Channels |
| **Q3 2026** | Web UI, API & Scale | ✅ **Complete** — Next.js, REST API, SDKs, Multi-tenancy |
| **Q4 2026** | Advanced Features & AI | 🔶 **In Progress** — Plugin, Agent Loading, Security Scanner |
| **Q1 2027** | Mobile & Voice | 📋 **Planned** — Flutter app, STT/TTS |
| **Q2 2027** | Enterprise Features | 📋 **Planned** — SSO, RBAC, Audit Logging, Compliance |
| **Q3 2027** | Distributed System | 📋 **Planned** — Multi-instance sync, Federated learning |

**Overall Progress: 87% Complete** — [View Full Roadmap](core/ROADMAP.md)

---

## 🤝 Contributing

We welcome contributions! Here's how to help:

```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/jebat-core.git

# 3. Create a feature branch
git checkout -b feature/amazing-feature

# 4. Make your changes
# 5. Test your changes
cd apps/web && npm run build
cd ../api && python -m pytest  # if tests exist

# 6. Commit with clear message
git commit -m "feat: add amazing feature

- Description of what was added
- Why it was added"

# 7. Push and create Pull Request
git push origin feature/amazing-feature
```

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn
- Keep discussions on-topic

---

## 📊 GitHub Stats

<p align="center">
  <img src="https://img.shields.io/github/repo-size/nusabyte-my/jebat-core" alt="Repo Size" />
  <img src="https://img.shields.io/github/issues/nusabyte-my/jebat-core" alt="Issues" />
  <img src="https://img.shields.io/github/issues-pr/nusabyte-my/jebat-core" alt="Pull Requests" />
  <img src="https://img.shields.io/github/last-commit/nusabyte-my/jebat-core" alt="Last Commit" />
</p>

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
- **geezerrrr** — [agent-town](https://github.com/geezerrrr/agent-town) for RPG task assignment concept
- **Community** — All contributors and users

---

## 📞 Support

- **GitHub Issues**: [Report bugs](https://github.com/nusabyte-my/jebat-core/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/nusabyte-my/jebat-core/discussions)
- **Website**: [jebat.online](https://jebat.online)
- **Owner**: [humm1ngb1rd](https://nusabyte.my) — NusaByte

---

<p align="center">
  <strong>⚔️ JEBAT — Because warriors remember everything that matters.</strong><br />
  <em>Made with ❤️ by <a href="https://nusabyte.my">humm1ngb1rd</a> and NusaByte.</em>
</p>

<p align="center">
  <a href="https://github.com/nusabyte-my/jebat-core">
    ⭐ Star this repo if JEBAT is useful to you!
  </a>
</p>
