# 🗡️ JEBAT - The Complete AI Development Ecosystem

**Because warriors remember everything that matters.**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/nusabyte-my/jebat-core)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/status-production%20ready-success.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

---

## 🚀 Quick Start

### Try JEBAT Now (5 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# 2. Quick setup
python setup.py --quick

# 3. Start all services
docker-compose up -d

# 4. Open landing page
start landing.html

# 5. Try the chatbot
python examples/chat/standalone_chatbot.py
```

**That's it!** You're running JEBAT. 🎉

---

## 📖 Table of Contents

- [What is JEBAT?](#what-is-jebat)
- [Features](#features)
- [Installation](#installation)
- [Quick Start Guide](#quick-start-guide)
- [Usage Examples](#usage-examples)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 What is JEBAT?

**JEBAT** is a comprehensive AI-powered development ecosystem featuring:

### 🧠 Ultra-Think Reasoning
6 thinking modes for different tasks:
- **FAST** - Instant responses for simple questions
- **DELIBERATE** - Balanced reasoning for most tasks
- **DEEP** - Complex multi-layered analysis
- **STRATEGIC** - Long-term planning
- **CREATIVE** - Innovative lateral thinking
- **CRITICAL** - Analytical evaluation

### ♾️ Eternal Memory System
5-layer memory architecture:
- **M0** - Sensory buffer (30s)
- **M1** - Episodic memory (24h)
- **M2** - Semantic memory (7d)
- **M3** - Procedural memory (permanent)
- **M4** - Core identity (permanent)

### 🤖 Multi-Agent System
Specialized agents working together:
- Code analysis & generation
- Security review
- Documentation
- Testing & QA
- Research & analysis

### 💬 Multi-Channel Support
Meet users where they are:
- CLI interface
- Telegram bot
- WhatsApp Business
- Discord bot
- Slack integration
- REST API
- Web dashboard

---

## ✨ Features

### Core Systems

| Feature | Status | Description |
|---------|--------|-------------|
| **Ultra-Loop** | ✅ Complete | Continuous 5-phase processing cycle |
| **Ultra-Think** | ✅ Complete | Deep reasoning with 6 modes |
| **Memory System** | ✅ Complete | 5-layer eternal memory |
| **Agent System** | ✅ Complete | Multi-agent orchestration |
| **Decision Engine** | ✅ Complete | Intelligent task routing |
| **Error Recovery** | ✅ Complete | Fault tolerance & auto-recovery |

### Channels & Integration

| Channel | Status | Description |
|---------|--------|-------------|
| **CLI** | ✅ Complete | Command-line interface |
| **Telegram** | ✅ Complete | Telegram bot integration |
| **WhatsApp** | ✅ Complete | WhatsApp Business API |
| **Discord** | ✅ Complete | Discord bot with slash commands |
| **Slack** | ✅ Complete | Slack app integration |
| **REST API** | ✅ Complete | FastAPI with 8 endpoints |
| **Web Dashboard** | ✅ Complete | Real-time monitoring UI |

### Developer Tools

| Tool | Status | Description |
|------|--------|-------------|
| **Python SDK** | ✅ Complete | Async Python client |
| **JavaScript SDK** | ✅ Complete | TypeScript client |
| **Plugin System** | ✅ Complete | Dynamic plugin loading |
| **Multi-Tenancy** | ✅ Complete | SaaS-ready architecture |
| **Analytics** | ✅ Complete | Usage tracking & insights |
| **Knowledge Graph** | ✅ Complete | Graph-based knowledge |

---

## 📦 Installation

### Prerequisites

- **Python** 3.11 or higher
- **Docker** & **Docker Compose** (recommended)
- **PostgreSQL** 16+ with TimescaleDB
- **Redis** 7+

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# Add API keys, tokens, etc.

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Services started:**
- JEBAT API (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Grafana (port 3000)
- Prometheus (port 9090)

### Option 2: Local Installation

```bash
# Clone repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python -m jebat.database.setup --init

# Start API server
python -m uvicorn jebat.services.api.jebat_api:app --reload

# Start Ultra-Loop
python -m jebat.ultra_process_runner --loop
```

### Option 3: Development Setup

```bash
# Clone with development dependencies
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Install in editable mode with dev extras
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linters
black jebat/
flake8 jebat/
mypy jebat/
```

---

## 🚀 Quick Start Guide

### 1. Start JEBAT

```bash
# Using Docker (recommended)
docker-compose up -d

# Verify it's running
curl http://localhost:8000/api/v1/health
```

### 2. Try the Chatbot

```bash
# Standalone chatbot (no API needed)
python examples/chat/standalone_chatbot.py

# Interactive chatbot (with API)
python examples/chat/interactive_chatbot.py

# Simple chatbot
python examples/chat/simple_chatbot.py
```

### 3. Use the CLI

```bash
# Show status
python -m jebat.cli.launch status

# Run thinking session
python -m jebat.cli.launch think "What is AI?"

# Store memory
python -m jebat.cli.launch memory store "User prefers Python"

# Search memories
python -m jebat.cli.launch memory search "Python"
```

### 4. Access Web Interfaces

- **Landing Page**: `start landing.html`
- **API Docs**: http://localhost:8000/api/docs
- **Monitoring Dashboard**: `jebat/services/webui/dashboard.html`
- **Grafana**: http://localhost:3000 (admin/admin)

---

## 💻 Usage Examples

### Python SDK

```python
from jebat_sdk import JEBATClient
import asyncio

async def main():
    async with JEBATClient() as client:
        # Chat with JEBAT
        response = await client.chat(
            "What is artificial intelligence?",
            mode="deliberate"
        )
        print(f"Response: {response.response}")
        print(f"Confidence: {response.confidence:.0%}")
        
        # Store a memory
        await client.store_memory(
            "I prefer Python over JavaScript",
            user_id="user123",
            layer="M1_EPISODIC"
        )
        
        # Search memories
        memories = await client.search_memories(
            "Python",
            user_id="user123"
        )
        
        for memory in memories:
            print(f"Memory: {memory.content}")

asyncio.run(main())
```

### REST API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Chat
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is AI?",
    "mode": "deliberate",
    "user_id": "user1"
  }'

# Store memory
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test memory",
    "user_id": "user1"
  }'

# Search memories
curl "http://localhost:8000/api/v1/memories/search?query=test&user_id=user1"
```

### JavaScript/TypeScript

```typescript
import { JEBATClient } from '@jebat/sdk';

const client = new JEBATClient({
  baseURL: 'http://localhost:8000'
});

// Chat
const response = await client.chat('What is AI?', {
  mode: 'deliberate'
});
console.log(response.response);

// Store memory
await client.storeMemory('TypeScript is great', {
  userId: 'user123'
});

// Search
const memories = await client.searchMemories('TypeScript', {
  userId: 'user123'
});
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  JEBAT Ecosystem                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │  Ultra-Loop  │         │  Ultra-Think │             │
│  │  (Continuous │         │  (Deep       │             │
│  │   Processing)│         │   Reasoning) │             │
│  └──────┬───────┘         └──────┬───────┘             │
│         │                        │                      │
│         └───────────┬────────────┘                      │
│                     │                                   │
│  ┌──────────────────┴──────────────────┐               │
│  │         Integration Layer            │               │
│  ├──────────────────────────────────────┤               │
│  │  • Memory Manager (M0-M4 layers)     │               │
│  │  • Cache Manager (HOT/WARM/COLD)     │               │
│  │  • Decision Engine (Routing)         │               │
│  │  • Agent Orchestrator (Multi-agent)  │               │
│  │  • Error Recovery (Fault tolerance)  │               │
│  └──────────────────────────────────────┘               │
│                     │                                   │
│  ┌──────────────────┴──────────────────┐               │
│  │         Storage Layer                │               │
│  ├──────────────────────────────────────┤               │
│  │  • PostgreSQL + TimescaleDB          │               │
│  │  • Redis Cache                       │               │
│  │  • Vector Search (pgvector)          │               │
│  └──────────────────────────────────────┘               │
│                     │                                   │
│  ┌──────────────────┴──────────────────┐               │
│  │         Channels Layer               │               │
│  ├──────────────────────────────────────┤               │
│  │  • CLI • Telegram • WhatsApp         │               │
│  │  • Discord • Slack • REST API        │               │
│  └──────────────────────────────────────┘               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

| Document | Description | Link |
|----------|-------------|------|
| **USAGE_GUIDE.md** | Complete usage guide | [View](USAGE_GUIDE.md) |
| **QUICKSTART_EXAMPLES.md** | 8 working examples | [View](QUICKSTART_EXAMPLES.md) |
| **QUICK_REFERENCE_CARD.md** | One-page cheat sheet | [View](QUICK_REFERENCE_CARD.md) |
| **ARCHITECTURE.md** | System architecture | [View](ARCHITECTURE.md) |
| **DEPLOYMENT_GUIDE.md** | Deployment guide | [View](DEPLOYMENT_GUIDE.md) |
| **IMPLEMENTATION_STATUS_FINAL.md** | Status & chatbot guide | [View](IMPLEMENTATION_STATUS_FINAL.md) |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=jebat --cov-report=html

# Run specific test file
pytest tests/test_full_system.py -v

# Run integration tests
pytest tests/test_integration.py -v
```

---

## 🤝 Contributing

We welcome contributions! Here's how to help:

### 1. Fork the Repository

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/jebat-core.git
cd jebat-core
```

### 2. Create a Branch

```bash
# Create feature branch
git checkout -b feature/amazing-feature
```

### 3. Make Changes

- Write clean, documented code
- Add tests for new features
- Update documentation
- Follow existing code style

### 4. Test

```bash
# Run tests
pytest tests/

# Run linters
black jebat/
flake8 jebat/
mypy jebat/
```

### 5. Commit

```bash
# Commit with clear message
git add .
git commit -m "feat: add amazing feature

- Description of what was added
- Why it was added
- Any breaking changes"
```

### 6. Push & PR

```bash
# Push to your fork
git push origin feature/amazing-feature

# Create Pull Request on GitHub
```

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn
- Keep discussions on-topic

---

## 📄 License

**MIT License** - See [LICENSE](LICENSE) file for details.

```
Copyright (c) 2026 JEBAT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgments

- **Hang Jebat** - Legendary Malay warrior who inspired the name
- **Community** - All contributors and users
- **Open Source** - Built on amazing open-source projects

---

## 📞 Support

- **GitHub Issues**: [Report bugs](https://github.com/nusabyte-my/jebat-core/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/nusabyte-my/jebat-core/discussions)
- **Documentation**: [Read the docs](USAGE_GUIDE.md)
- **Email**: support@jebat.ai (placeholder)

---

## 🎯 Roadmap

### Q2 2026 ✅ - Infrastructure & Polish
- [x] Monitoring Dashboard
- [x] Enhanced Logging
- [x] Docker Deployment
- [x] CI/CD Pipeline
- [x] WhatsApp Channel
- [x] Discord Channel

### Q3 2026 ✅ - User Experience & Scale
- [x] REST API
- [x] Web Interface
- [x] Python SDK
- [x] JavaScript SDK
- [x] Multi-Tenancy

### Q4 2026 ✅ - Advanced Features
- [x] Plugin System
- [x] Analytics Dashboard
- [x] Knowledge Graph
- [x] Model Fine-Tuning
- [x] Advanced ML

### 2027 (Optional)
- [ ] Mobile apps (iOS/Android)
- [ ] Voice integration
- [ ] Advanced analytics
- [ ] Real-time collaboration

---

## 📊 Stats

![Repo Size](https://img.shields.io/github/repo-size/nusabyte-my/jebat-core)
![Stars](https://img.shields.io/github/stars/nusabyte-my/jebat-core?style=social)
![Forks](https://img.shields.io/github/forks/nusabyte-my/jebat-core?style=social)
![Issues](https://img.shields.io/github/issues/nusabyte-my/jebat-core)
![Pull Requests](https://img.shields.io/github/issues-pr/nusabyte-my/jebat-core)

---

**🗡️ JEBAT** - *Because warriors remember everything that matters.*

Made with ❤️ for developers worldwide.
