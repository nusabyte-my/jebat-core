# 🗡️ JEBAT Core - AI Platform & Development Assistant

**The Complete AI-Powered Development Ecosystem**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/nusabyte-my/jebat-core)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

---

## 📖 Table of Contents

- [Overview](#overview)
- [Product Family](#product-family)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [JEBAT Platform](#jebat-platform)
- [JEBAT DevAssistant](#jebat-devassistant)
- [AGENTIX Multi-Domain Agent](#agentix-multi-domain-agent)
- [Architecture](#architecture)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**JEBAT** (named after the legendary Malay warrior Hang Jebat) is a comprehensive AI platform featuring:

- **🧠 Ultra-Think Reasoning** - Deep analysis and decision-making
- **♾️ Eternal Memory System** - 5-layer memory with heat-based consolidation
- **🤖 Multi-Agent Orchestration** - Coordinate multiple AI agents
- **💻 Development Assistant** - Code generation, review, and scaffolding
- **🔒 Security Tools** - Penetration testing and vulnerability assessment
- **🌐 Multi-Domain Agent** - Social media, web content, network analysis

### Philosophy

> *"Like Hang Jebat served with loyalty and precision, JEBAT serves your development needs with intelligence and dedication."*

---

## 🏛️ Product Family

| Product | Codename | Description | Status |
|---------|----------|-------------|--------|
| **JEBAT Core** | Hang Jebat | Main AI platform with Ultra-Think & Memory | ✅ Active |
| **JEBAT Dev** | Pandai | Interactive development assistant | ✅ Active |
| **JEBAT Security** | Keris | AI-powered penetration testing | 🔄 Dev |
| **AGENTIX** | Agentix | Multi-domain conversational agent | ✅ Active |
| **JEBAT Companion** | Sahabat | Daily task assistant | 📋 Planned |
| **JEBAT Nexus** | Perisai | Bot orchestrator (OpenClaw-style) | 📋 Planned |

---

## ✨ Features

### JEBAT Core Platform

- **5-Layer Memory System**
  - M0: Sensory Buffer (0-30s)
  - M1: Episodic Memory (hours)
  - M2: Semantic Memory (days-weeks)
  - M3: Conceptual Memory (permanent)
  - M4: Procedural Memory (permanent)

- **Ultra-Think Engine**
  - Deliberate mode (analytical)
  - Creative mode (generative)
  - Critical mode (evaluation)
  - Strategic mode (planning)

- **Ultra-Loop Processing**
  - Continuous execution
  - Context preservation
  - Iterative refinement

- **Sentinel Security**
  - Audit logging
  - Access control
  - Threat detection

### JEBAT DevAssistant

- **Interactive CLI** - REPL-style with Rich UI
- **Code Skills**
  - Code generation & review
  - Project scaffolding
  - Git integration
  - Test running
  - Debug analysis

- **Auto-Completion** - Tab completion with context awareness
- **Rich UI** - Tables, panels, syntax highlighting
- **Slash Commands** - `/help`, `/clear`, `/history`, `/status`

### AGENTIX Multi-Domain Agent

- **Domain Expertise**
  - 📱 Social Media Content
  - 🌐 Web Content Generation
  - 💻 Application Development
  - 🔌 Network Analysis
  - 🔐 Cybersecurity Assessment

- **Mode Switching**
  - Standard Mode (filtered)
  - Unrestricted Mode (full capabilities)
  - Expert Mode (technical deep-dive)
  - Creative Mode (maximum creativity)

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Install dependencies
pip install -r requirements.txt

# Install JEBAT package
pip install -e jebat/

# Install DevAssistant
pip install -e jebat_dev/
```

### Launch Commands

```bash
# JEBAT DevAssistant (Interactive)
python -m jebat_dev.gateway

# JEBAT DevAssistant (Single Command)
python -m jebat_dev.gateway "create a React app"

# AGENTIX Agent
python agentix/agent.py

# Product Selector
python jebat_selector.py
```

---

## 📦 Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Git (for version control)

### Step-by-Step

```bash
# 1. Clone repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Install JEBAT core
pip install -e jebat/

# 5. Install DevAssistant
pip install -e jebat_dev/

# 6. Verify installation
python -m jebat_dev.gateway --help
```

### Dependencies

**Core Requirements:**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.3
pyyaml>=6.0.1
python-dotenv>=1.0.0
rich>=13.7.0
prompt-toolkit>=3.0.43
```

**AI & LLM:**
```
openai>=1.10.0
anthropic>=0.8.1
langchain>=0.1.0
```

**Database:**
```
asyncpg>=0.29.0
redis>=5.0.1
sqlalchemy>=2.0.0
```

---

## 🧠 JEBAT Platform

### Architecture

```
jebat/
├── core/
│   ├── memory/        # 5-layer eternal memory
│   ├── cache/         # 3-tier smart cache
│   ├── decision/      # Decision engine
│   └── agents/        # Agent orchestration
├── features/
│   ├── ultra_loop/    # Continuous processing
│   ├── ultra_think/   # Deep reasoning
│   └── sentinel/      # Security layer
├── services/
│   ├── webui/         # Web interface
│   ├── api/           # REST/WebSocket API
│   └── mcp/           # MCP protocol
├── integrations/
│   ├── channels/      # Messaging channels
│   └── webhooks/      # Webhook system
├── database/          # Database layer
├── skills/            # Skill system
└── config/            # Configuration
```

### Memory System

```python
from jebat.core.memory import MemoryManager

# Initialize memory
memory = MemoryManager()

# Store memory
await memory.store(
    content="User prefers Python development",
    layer="semantic",
    importance=0.8,
)

# Retrieve memories
memories = await memory.search(
    query="programming preferences",
    limit=5,
)

# Consolidate memories
await memory.consolidate()
```

### Ultra-Think

```python
from jebat.features.ultra_think import UltraThink, ThinkingMode

# Initialize
thinker = UltraThink(config={"max_thoughts": 20})

# Deliberate thinking
result = await thinker.think(
    problem="How to optimize database queries?",
    mode=ThinkingMode.DELIBERATE,
    timeout=60.0,
)

print(result.conclusion)
print(result.reasoning_steps)
```

---

## 💻 JEBAT DevAssistant

### Interactive CLI

```bash
# Start interactive mode
python -m jebat_dev.gateway

╔═══════════════════════════════════════════════════════════╗
║   🗡️  JEBAT DevAssistant  v1.0.0                         ║
║   Your Personal Development AI Assistant                  ║
╚═══════════════════════════════════════════════════════════╝

🗡️  create a React chat application
⏳ Thinking...
╭─────────────────────────────────────────────╮
│ ✅ Success                                  │
│ Created: projects/chat                      │
╰─────────────────────────────────────────────╯
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `create` | Create projects/components | `create a React chat app` |
| `scaffold` | Scaffold new project | `scaffold myapp --type python_package` |
| `review` | Review code | `review src/main.py` |
| `generate` | Generate code | `generate a REST API` |
| `ui` | Generate UI | `ui modern login form --framework react` |
| `debug` | Debug errors | `debug "ModuleNotFoundError"` |
| `git` | Git operations | `git commit -m "fix: bug"` |
| `test` | Run tests | `test --framework pytest` |

### Slash Commands

- `/help` - Show detailed help
- `/clear` - Clear screen
- `/history` - Show command history
- `/config` - Show configuration
- `/status` - Show system status
- `/models` - Show available models

### Skills System

**Code Skills:**
```python
# Read file
content = await code_skills.read_file("src/main.py")

# Review code
result = await code_skills.review_code("src/main.py")
print(result.issues)
print(result.suggestions)

# Generate code
code = await code_skills.generate_code(
    description="Flask REST API with JWT",
    language="python",
    path="api/app.py",
)
```

**Project Skills:**
```python
# Scaffold project
success = await project_skills.scaffold(
    name="myapp",
    project_type="python_package",
)
```

**Git Skills:**
```python
# Initialize repo
await git_skills.init("projects/myapp")

# Commit changes
await git_skills.commit(
    path="projects/myapp",
    message="feat: add authentication",
)
```

---

## 🤖 AGENTIX Multi-Domain Agent

### Overview

AGENTIX is a versatile AI agent with specialized capabilities across multiple domains and mode switching.

### Launch

```bash
python agentix/agent.py
```

### Domains

| Domain | Capabilities | Examples |
|--------|-------------|----------|
| **Social Media** | Posts, hashtags, calendars | Twitter, LinkedIn, Instagram |
| **Web Content** | Blogs, landing pages, SEO | Articles, product descriptions |
| **App Dev** | Code, projects, architecture | Python, JS, React apps |
| **Network** | Analysis, diagnostics | Ping, traceroute, scanning |
| **Cybersecurity** | Assessments, pentesting | Vulnerability scans, audits |

### Operating Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `standard` | Default with filtering | General use |
| `unrestricted` | Full capabilities | Research/educational |
| `expert` | Technical deep-dive | Advanced users |
| `creative` | Maximum creativity | Content generation |

### Mode Switching

```bash
🤖 Agentix: /mode unrestricted
⚠️  MODE SWITCH WARNING  ⚠️

You are about to switch to UNRESTRICTED mode.
- Content filters are disabled
- Responses may include sensitive material
- For educational/research purposes
- User assumes full responsibility

Type 'confirm' to proceed or 'cancel' to stay.
```

### Examples

**Social Media:**
```bash
🤖 Agentix: Create a Twitter post about AI trends
✨ AI is revolutionizing how we work and create! 🚀

From automated content to intelligent insights, 
the future is here.

#AI #Innovation #Tech #Future #MachineLearning
```

**Web Content:**
```bash
🤖 Agentix: Generate a blog post about cybersecurity
# Cybersecurity: A Comprehensive Guide

## Introduction
Welcome to our in-depth exploration of cybersecurity...
```

**App Development:**
```bash
🤖 Agentix: Help me build a Python FastAPI app
# Project Structure: fastapi_app

**Language:** Python

**Files:**
  - main.py
  - requirements.txt
  - README.md
  - tests/

**Dependencies:**
  - fastapi
  - uvicorn
  - pydantic
```

**Network Analysis:**
```bash
🤖 Agentix: Analyze network 192.168.1.1
# Network Analysis: 192.168.1.1

**Status:** analysis_complete

**Findings:**
  ✓ Network topology mapped
  ✓ Open ports identified
  ✓ Services enumerated
```

**Cybersecurity:**
```bash
🤖 Agentix: Run security assessment
# Security Assessment: target_system

**Vulnerabilities Found:** 1
  ⚠️ [MEDIUM] Software version may have known vulnerabilities

**Recommendations:**
  • Implement regular patching
  • Enable security monitoring
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    JEBAT Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Gateway    │◄───────►│   Brain      │             │
│  │  (CLI/API)   │         │ (Ultra-Think)│             │
│  └──────────────┘         └──────────────┘             │
│         │                       │                       │
│         ▼                       ▼                       │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Sandbox    │         │   Skills     │             │
│  │  (Safe Exec) │         │ (Dev Tools)  │             │
│  └──────────────┘         └──────────────┘             │
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │        Memory System (5 Layers)              │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Component Flow

```
User Input
    │
    ▼
Gateway (CLI/API)
    │
    ▼
DevBrain (Route & Plan)
    │
    ├─► Ultra-Think (Reasoning)
    ├─► Memory (Context)
    └─► Skills (Execution)
            │
            ├─► Code Skills
            ├─► Project Skills
            ├─► Git Skills
            ├─► Test Skills
            └─► Debug Skills
            │
            ▼
Sandbox (Safe Execution)
    │
    ▼
Response (Rich UI)
```

---

## 📚 Command Reference

### JEBAT DevAssistant

```bash
# Create & Scaffold
jebat create <description>
jebat scaffold <name> --type <python_package|react_app|nodejs_app>

# Code Operations
jebat review <path>
jebat generate <description>

# UI Generation
jebat ui <description> --framework <react|vue|angular>

# Debug
jebat debug "<error>" --file <path>

# Git
jebat git <init|add|commit|status|log|push|pull> --path <path>
jebat git commit --path <path> -m "<message>"

# Tests
jebat test --path <path> --framework <pytest|jest|unittest>
```

### AGENTIX

```bash
# Mode Switching
/mode standard
/mode unrestricted
/mode expert
/mode creative

# General Commands
/help
/clear
/status
/domains

# Domain Examples
"Create a LinkedIn post about AI"
"Generate a blog post about cybersecurity"
"Help me build a React dashboard"
"Analyze network 192.168.1.1"
"Run security assessment on example.com"
```

---

## ⚙️ Configuration

### config.yaml

```yaml
system:
  name: JEBAT
  version: 2.0.0
  debug: false

core:
  memory:
    layers: 5
    consolidation_interval: 3600
  agents:
    max_concurrent: 10

features:
  ultra_think:
    enabled: true
    max_thoughts: 20

services:
  webui:
    port: 8787
  api:
    port: 8080
```

### .env

```bash
# System
JEBAT_DEBUG=false
JEBAT_LOG_LEVEL=INFO

# Ultra-Think
JEBAT_ULTRA_THINK_ENABLED=true
JEBAT_ULTRA_THINK_MAX_THOUGHTS=20

# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Database
JEBAT_DATABASE_URL=sqlite:///jebat.db
```

---

## 📖 API Reference

### Memory API

```python
from jebat.core.memory import MemoryManager

memory = MemoryManager()

# Store
await memory.store(content, layer, importance)

# Search
await memory.search(query, limit, filters)

# Consolidate
await memory.consolidate()

# Get heat scores
await memory.get_heat_scores(layer)
```

### Agent API

```python
from jebat.core.agents import AgentOrchestrator

orchestrator = AgentOrchestrator()

# Create agent
agent = await orchestrator.create_agent(
    agent_type="code_reviewer",
    personality="detail_oriented",
)

# Execute task
result = await orchestrator.execute_task(
    agent_id=agent.id,
    task="Review this code",
)
```

### DevAssistant API

```python
from jebat_dev.brain import DevBrain
from jebat_dev.sandbox import DevSandbox

brain = DevBrain()
sandbox = DevSandbox()
brain.initialize_skills(sandbox)

# Execute task
result = await brain.execute_task(
    task_type="create",
    description="a React app",
    sandbox=sandbox,
)
```

---

## 💡 Examples

### Example 1: Create Full-Stack App

```bash
🗡️  scaffold myapp --type nodejs_app
✅ Scaffolded nodejs_app project: myapp
   Location: projects/myapp

🗡️  generate Express API with JWT authentication
✅ Generated API with authentication

🗡️  ui modern login form --framework react
✅ Generated React UI with Stitch MCP
   Files created:
     - src/components/LoginForm.jsx
     - src/styles/LoginForm.css
```

### Example 2: Code Review & Fix

```bash
🗡️  review src/auth.py
📋 Review complete:
  - Consider adding type hints
  - Add docstrings to public methods
  - 2 TODOs found

🗡️  fix the issues in src/auth.py
✅ Applied fixes:
  - Added type hints
  - Added docstrings
  - Addressed TODOs
```

### Example 3: Security Assessment

```bash
🤖 Agentix: Run security assessment on example.com
# Security Assessment: example.com

**Type:** vulnerability_scan
**Status:** complete

**Vulnerabilities Found:** 2
  ⚠️ [HIGH] Outdated SSL certificate
  ⚠️ [MEDIUM] Missing security headers

**Recommendations:**
  • Renew SSL certificate
  • Implement HSTS header
  • Add CSP header
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone fork
git clone https://github.com/your-username/jebat-core.git
cd jebat-core

# Install dev dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Run tests
pytest tests/

# Run linting
black jebat/
flake8 jebat/
```

### Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write docstrings
- Add tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Hang Jebat** - The legendary Malay warrior who inspired JEBAT
- **OpenClaw** - Architecture inspiration
- **Google Stitch** - MCP integration inspiration
- **Community Contributors** - All who have contributed

---

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/nusabyte-my/jebat-core/wiki)
- **Issues**: [GitHub Issues](https://github.com/nusabyte-my/jebat-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nusabyte-my/jebat-core/discussions)

---

## 🗺️ Roadmap

### Q1 2026 (Current)
- ✅ JEBAT Core Platform
- ✅ JEBAT DevAssistant
- ✅ AGENTIX Multi-Domain Agent
- ✅ Interactive CLI with Rich UI

### Q2 2026
- 🎯 JEBAT Security (Keris) - Alpha
- 🎯 Enhanced Ultra-Think integration
- 🎯 Memory system improvements

### Q3 2026
- 🎯 JEBAT Nexus - Bot framework
- 🎯 Multi-channel deployment
- 🎯 Plugin marketplace

### Q4 2026
- 🎯 All products production-ready
- 🎯 Unified dashboard
- 🎯 Cross-product integration

---

**🗡️ "Like Hang Jebat, we code with honor and precision."**

---

## 📊 Repository Structure

```
jebat-core/
├── jebat/                      # Core Platform
│   ├── core/                   # Memory, Cache, Decision, Agents
│   ├── features/               # Ultra-Loop, Ultra-Think, Sentinel
│   ├── services/               # WebUI, API, MCP
│   ├── integrations/           # Channels, Webhooks
│   ├── database/               # Database layer
│   ├── skills/                 # Skill system
│   └── config/                 # Configuration
│
├── jebat_dev/                  # DevAssistant
│   ├── brain/                  # DevBrain with Ultra-Think
│   ├── gateway/                # Interactive CLI
│   ├── sandbox/                # Safe execution
│   ├── skills/                 # Code, Project, Git, Test, Debug
│   └── integrations/           # Stitch MCP
│
├── agentix/                    # Multi-Domain Agent
│   └── agent.py                # Agent core
│
├── jebat_selector.py           # Product selector
├── requirements.txt            # Dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

---

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Maintained by**: NUSABYTE Team
