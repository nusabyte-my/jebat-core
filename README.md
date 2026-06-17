# 🗡️ JEBAT v6.1 — Sovereign AI Platform & Agent Workstation

![npm](https://img.shields.io/npm/v/@nusabyte/jebat?style=flat-square&color=10b981&logo=npm)
![bun](https://img.shields.io/badge/bun-compatible-06b6d4?style=flat-square&logo=bun)
![Version](https://img.shields.io/badge/version-v6.1.0--stable-10b981?style=flat-square)
![Security](https://img.shields.io/badge/security-audited-06b6d4?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-71717a?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
![Tests](https://img.shields.io/badge/tests-89%20tools%20registered-10b981?style=flat-square)

> **Sovereign execution, private memory, and audited intelligence.**

JEBAT is an **enterprise-grade self-hosted AI platform and agent workstation**. It provides governed local LLM inference, secure cognitive routing, multi-agent swarm orchestration, embedded threat reconnaissance, and eternal memory — all running fully air-gapped on your private network with **zero data leakage**.

Named after the legendary Malay warrior **Hang Jebat** — loyal, powerful, and unforgettable.

---

## 🔌 Workstation & MCP Server Integration

JEBAT v6.1 features native integration with major developer workspaces (Cursor, VS Code, Zed, Windsurf, JetBrains) as a standard **Model Context Protocol (MCP)** server.

For step-by-step injection configurations and details on executing the **13 core capabilities** (ReAct loop, Ultra-Think reasoning, swarms, sandbox, voice I/O, Playwright, pentesting), please consult:

👉 **[WORKSTATION_MCP_GUIDE.md](WORKSTATION_MCP_GUIDE.md)**

---

## 🚀 Quick Start: Zero-Config Installation

### 🏆 Option 0: npx / bunx (Recommended — Zero Config)

```bash
# Runs immediately — auto-installs Python package on first run
npx @nusabyte/jebat repl

# Or with bun
bunx @nusabyte/jebat repl

# One-shot commands
npx @nusabyte/jebat chat "Explain the memory system"
npx @nusabyte/jebat agent "Audit all API endpoints"
npx @nusabyte/jebat config show
```

### 📦 Other Installation Methods

| Method | Command | Best For |
|--------|---------|----------|
| **pip (Standard)** | `pip install jebat` | Python environments |
| **Docker (Production)** | `docker compose up -d` | Isolated deployments |
| **Source (Development)** | `pip install -e ".[dev]"` | Contributing |
| **npm Global** | `npm install -g @nusabyte/jebat` | Global CLI |
| **Global bun** | `bun install -g @nusabyte/jebat` | Bun users |

---

## 🎯 What Makes JEBAT Different

| Capability | JEBAT v6.1 | Commercial SaaS (Claude/GPT) | Ollama WebUI | LM Studio |
|------------|:---:|:---:|:---:|:---:|
| **Data Residency** | **100% Private / Air-gapped** | Cloud (Third-Party) | Local Only | Local Only |
| **LLM Provider Routing** | **6 Providers (Failover)** | Single Provider | Ollama Only | Local Only |
| **Cognitive Profiles** | **7 Thinking Modes (Ultra-Think)** | Standard Chat | Standard Chat | Standard Chat |
| **Security Auditing** | **Autonomous Pentest Suite** | Blocked | None | None |
| **Access Control (RBAC)** | **3-Tier Command Classification** | Muted Policy | Basic Auth | None |
| **Eternal Memory** | **5-Layer Heat-Scored Recall** | Session Limits | No | No |
| **Standard Integration** | **Native MCP Client + Server** | None | Basic API | Local API |
| **Multi-Agent Swarms** | **Tukang / Hulubalang / Pawang** | No | No | No |
| **Code Execution** | **Docker Sandbox + PTY** | No | No | No |
| **Voice I/O** | **Whisper STT + Edge TTS** | No | No | No |
| **Git Integration** | **Full GitOps (commit, blame, stash)** | No | No | No |
| **Browser Automation** | **Playwright (click, type, vision)** | No | No | No |

---

## 🚀 6-Step Operational Onboarding

### Step 1: Secure Installation

```bash
# Option A: Standard local install via pip (recommended)
pip install jebat

# Option B: Isolated container build (production)
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
docker compose build
docker compose up -d

# Option C: Development install with all extras
pip install -e ".[ml,nlp,server,db,dev,monitoring]"
```

### Step 2: Credential Hardening

Initialize the encrypted keyring credential manager. JEBAT securely encrypts all local secrets to prevent key leakage.

```bash
# Securely store API keys or connection hosts
jebat auth set openai your-openai-key
jebat auth set anthropic your-anthropic-key
jebat auth set ollama http://localhost:11434
jebat auth set github your-github-token
```

### Step 3: Configure the Cognitive Router

Point JEBAT to local weights or cloud endpoints. Configuration lives in `~/.jebat/jebat.yaml`:

```yaml
agent:
  default_model: "qwen2.5-coder:7b"      # Local Ollama model
  default_provider: "ollama"
  safety_mode: "confirm"                  # auto | confirm | dangerous
  max_iterations: 10
  stream_tokens: true
  enable_memory: true

llm_providers:
  ollama_host: "http://localhost:11434"
  openai_base_url: "https://api.openai.com/v1"
  anthropic_base_url: "https://api.anthropic.com"
  openrouter_base_url: "https://openrouter.ai/api/v1"
  fallback_providers: ["openrouter", "groq", "openai", "anthropic"]

security:
  enable_guardrails: true
  audit_log: true
```

### Step 4: Run Autonomous Agent Loops

Launch the ReAct (Reasoning and Acting) execution engine:

```bash
# Run one-shot queries with tool routing
jebat agent "Verify the repository build config in package.json"

# Launch the interactive streaming REPL shell (primary interface)
jebat repl

# Or use the traditional chat interface
jebat chat "Explain the memory consolidation algorithm"
```

### Step 5: Orchestrate Agent Swarms

Deconstruct high-level goals into parallel subtasks and delegate them to role-based subagents:

```bash
# Dispatch a secure multi-agent task array
jebat delegate run "Audit all API endpoints in src/services" --tools terminal,file

# Planning + Execution pattern
jebat orchestrate plan-execute "Refactor authentication module" --planner deepseek-r1 --executor qwen2.5-coder

# Structured debate between two LLMs
jebat orchestrate debate "Should we use GraphQL or REST?" --rounds 3
```

### Step 6: Deploy Multi-Channel Adapters

Expose the agent gateway securely to team messaging systems:

```bash
# Start social media listeners (configured in config.yaml)
jebat social start --channels telegram,slack,discord

# Send messages directly from CLI
jebat social send --channel telegram --chat-id -100123456 --text "Deploy complete"
```

---

## 📋 Subcommand Reference

JEBAT exposes **46 subcommands** divided into logical management zones:

```
jebat --help
```

### System & Configuration
| Command | Description |
|---------|-------------|
| `jebat status` | System health, provider status, tool count |
| `jebat init` | Initialize JEBAT in current directory |
| `jebat config show\|set\|reset\|edit\|path\|init` | Full config management |
| `jebat doctor` | Run diagnostics and health checks |
| `jebat optimize` | Performance tuning and cache optimization |

### Inference & LLM Management
| Command | Description |
|---------|-------------|
| `jebat model list\|info\|select\|recommend\|test\|bench` | Model registry and benchmarking |
| `jebat llm-providers` | List supported providers |
| `jebat llm-config` | Show resolved LLM configuration |
| `jebat llm-auth` | Check provider authentication status |
| `jebat free-models` | List free models via OpenRouter |
| `jebat cost` | Token usage and cost tracking |

### Interaction & Chat
| Command | Description |
|---------|-------------|
| `jebat repl` | **Interactive REPL** (primary interface — streaming, tools, history) |
| `jebat chat "prompt"` | One-shot chat with tool calling |
| `jebat chat-project "prompt"` | Chat with project context auto-loaded |
| `jebat think "question"` | Deep reasoning session (Ultra-Think) |
| `jebat loop start\|stop\|status` | Autonomous Ultra-Loop agent |
| `jebat session search\|list\|export` | Session management & FTS5 search |

### Orchestration & Agent Management
| Command | Description |
|---------|-------------|
| `jebat delegate run "task"` | Spawn subagents for parallel execution |
| `jebat cron add\|list\|remove\|run` | Scheduled task management |
| `jebat skills list\|search\|show\|install` | TokGuru skills registry |
| `jebat tools list\|inspect` | Inspect all 89 registered tools |
| `jebat mcp connect\|list\|tools` | MCP server/client management |
| `jebat orchestrate debate\|plan-execute\|validate` | Multi-LLM patterns |

### Operations & File System
| Command | Description |
|---------|-------------|
| `jebat file read\|write\|patch\|search\|undo\|tree` | Safe file operations with backups |
| `jebat exec "command"` | PTY terminal execution with safety tiers |
| `jebat git status\|diff\|log\|commit\|blame\|stash` | Full GitOps integration |
| `jebat wiki create\|search\|update\|export` | Personal knowledge base (FTS5) |
| `jebat todo add\|list\|update\|remove` | Session task tracking |
| `jebat search "query"` | Web search via SearXNG/Brave/DDG |
| `jebat sandbox run\|check\|cleanup` | Docker sandbox execution |

### Security & Auditing
| Command | Description |
|---------|-------------|
| `jebat pentest quick\|standard\|full\|vuln-scan` | Autonomous security reconnaissance |
| `jebat sandbox` | Docker container isolation |
| `jebat safety check\|configure` | Guardrail pipeline management |
| `jebat undo backup\|list\|rollback\|purge` | File rollback & backup management |
| `jebat auth set\|get\|list\|remove` | Encrypted keyring management |

### Communication & Voice
| Command | Description |
|---------|-------------|
| `jebat voice transcribe\|speak\|chat` | Whisper STT + Edge TTS |
| `jebat social send\|search\|timeline` | Telegram, Discord, Slack, X/Twitter |
| `jebat tts "text"` | Text-to-speech synthesis |

---

## 🤖 The REPL Experience (Primary Interface)

```bash
jebat repl --model qwen2.5-coder:7b --provider ollama --safety confirm
```

**Features:**
- **Token-by-token streaming** display with Rich formatting
- **Slash commands**: `/help`, `/tools`, `/model`, `/provider`, `/safety`, `/clear`, `/history`, `/session`, `/save`, `/exit`
- **Session persistence** via SQLite + FTS5 (searchable history)
- **Multi-model/provider switching** mid-session
- **Tool call visualization** — see each step as it happens
- **Input history** via prompt-toolkit (up/down arrows)
- **Graceful Ctrl+C handling**

**Example Session:**
```
JEBAT — Repo-aware AI Agent
Type /help for commands

> read pyproject.toml
  [thinking...]
  [PendekarFile] Reading pyproject.toml...

1|[project]
2|name = "jebat"
3|version = "6.0.0"
...

> /model gemma3:12b
  Model override: gemma3:12b

> patch pyproject.toml '"pydantic>=2.5.3"' '"pydantic>=2.7.0"'
  [PendekarFile] Patched 1 occurrence in pyproject.toml

> /exit
  Goodbye!
```

---

## 🧠 Ultra-Think: 7 Cognitive Reasoning Modes

JEBAT's **Ultra-Think** engine provides structured reasoning beyond standard chat:

| Mode | Use Case | Description |
|------|----------|-------------|
| `fast` | Quick answers | Single-pass response, minimal tokens |
| `deliberate` | General analysis | Structured breakdown, pros/cons |
| `deep` | Complex problems | Multi-step CoT, assumption checking |
| `strategic` | Architecture decisions | Trade-off matrices, long-term impact |
| `creative` | Ideation | Divergent thinking, alternatives |
| `critical` | Code review / audit | Adversarial review, edge cases |
| `adversarial` | Security testing | Red-team perspective, exploit paths |

```bash
# Use in REPL
/prov thinking deep
> How should we architect the multi-tenant isolation?

# Or one-shot
jebat think --mode deep "Design a rate-limiting strategy for 10K tenants"
```

---

## 🔄 Memory System: 5-Layer Heat Architecture

JEBAT implements a **biologically-inspired memory architecture** with automatic consolidation:

```
┌─────────────────────────────────────────────────────────────┐
│  M0: SENSORY BUFFER (0-30s)                                 │
│  Raw inputs, streaming context, immediate perception        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  M1: EPISODIC MEMORY (minutes-hours)                        │
│  Session conversations, working context, recent interactions │
│  • FTS5 full-text search                                     │
│  • Heat scoring: visit_freq × 0.3 + depth × 0.25 + recency × 0.25 │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  M2: SEMANTIC MEMORY (days-weeks)                           │
│  Facts, entities, relationships, extracted knowledge        │
│  • Entity extraction & linking                               │
│  • Deduplication & merging                                   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  M3: CONCEPTUAL MEMORY (permanent)                          │
│  User preferences, mental models, crystallized expertise    │
│  • Knowledge graph construction                              │
│  • Profile aggregation                                       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  M4: PROCEDURAL MEMORY (permanent)                          │
│  Skills, workflows, learned tool patterns, agent strategies │
│  • TokGuru skill registry integration                        │
│  • Execution templates                                       │
└─────────────────────────────────────────────────────────────┘
```

**CLI Memory Operations:**
```bash
# Store a durable fact
jebat memory store "Client prefers PostgreSQL over MySQL for ACID compliance"

# Search memories (FTS5 + semantic)
jebat memory search "database preferences"

# Get statistics
jebat memory stats

# Memory consolidation (M1→M2→M3)
jebat memory consolidate
```

---

## 🛡️ Safety Classification Tiers

Every tool execution is categorized to protect your infrastructure:

| Tier | Behavior | Examples |
|------|----------|----------|
| **AUTO** | Execute immediately, no prompt | `file_read`, `search_web`, `git_status` |
| **CONFIRM** | Prompt `Y/n` before execution | `file_write`, `file_patch`, `git_commit`, `shell_exec` |
| **DANGEROUS** | Requires explicit `--dangerous` flag | `execute_code`, `process_kill`, `rm -rf` |

```bash
# Set default safety mode
jebat config set agent.safety_mode confirm

# Override per session in REPL
/safety dangerous

# YOLO mode — skip ALL prompts (use with caution!)
jebat repl --yolo
```

---

## 🐳 Docker Deployment (Production)

```yaml
# docker-compose.yml
version: '3.8'
services:
  jebat:
    build: .
    image: jebat:latest
    ports:
      - "8000:8000"      # API server
      - "8789:18789"     # Gateway (if enabled)
      - "8080:8080"      # Web UI (if enabled)
    environment:
      - DATABASE_URL=postgresql://user:***@db:5432/jebat
      - REDIS_URL=redis://redis:6379
      - OLLAMA_HOST=http://ollama:11434
      - JEBAT_CONFIG=/app/config/production.yaml
    volumes:
      - ./data:/app/data
      - ~/.jebat:/root/.jebat
    depends_on:
      - db
      - redis
      - ollama
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=jebat
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollamadata:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  pgdata:
  redisdata:
  ollamadata:
```

```bash
# Deploy
docker compose up -d

# View logs
docker compose logs -f jebat
```

---

## 📦 Installation Methods

### Method 1: pip (Standard)
```bash
# Core installation
pip install jebat

# With optional features
pip install "jebat[ml]"        # ML/Analytics: numpy, pandas, scikit-learn, xgboost
pip install "jebat[nlp]"       # NLP: sentence-transformers, spacy
pip install "jebat[server]"    # FastAPI server: fastapi, uvicorn, streamlit
pip install "jebat[db]"        # Databases: pymongo, redis, alembic
pip install "jebat[dev]"       # Development: pytest, black, mypy
pip install "jebat[all]"       # Everything
```

### Method 2: Docker (Isolated)
```bash
docker pull nusabyte/jebat:latest
docker run -it --rm \
  -v ~/.jebat:/root/.jebat \
  -v $(pwd):/workspace \
  nusabyte/jebat repl
```

### Method 3: Source (Development)
```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
pip install -e ".[dev]"
```

### Method 4: Binary (Future)
```bash
# Coming in Q3 2026
curl -fsSL https://jebat.online/install.sh | bash
```

---

## ⚙️ Configuration Reference

### Primary Config: `~/.jebat/jebat.yaml`

```yaml
version: "6.1.0"
data_dir: "~/.jebat"
config_file: "~/.jebat/jebat.yaml"

agent:
  default_model: ""
  default_provider: ""
  safety_mode: "confirm"
  max_iterations: 10
  context_window: 8192
  min_context_messages: 2
  stream_tokens: true
  enable_memory: true
  enable_search: false
  enable_orchestration: false

llm_providers:
  ollama_host: "http://localhost:11434"
  ollama_timeout: 120
  openai_base_url: "https://api.openai.com/v1"
  anthropic_base_url: "https://api.anthropic.com"
  google_base_url: "https://generativelanguage.googleapis.com"
  groq_base_url: "https://api.groq.com/openai/v1"
  openrouter_base_url: "https://openrouter.ai/api/v1"
  fallback_providers: ["openrouter", "groq", "openai", "anthropic"]
```

### Quick Config Commands
```bash
# Show config
jebat config show

# Set value
jebat config set agent.safety_mode confirm

# Edit in $EDITOR
jebat config edit

# Reset to defaults
jebat config reset
```

---

## 🤝 MCP Integration

JEBAT includes native MCP client + server support:

```bash
# Connect to MCP servers (stdio or HTTP)
jebat mcp connect --stdio "python -m my_mcp_server"
jebat mcp connect --http http://localhost:8080/mcp

# List connected servers
jebat mcp list

# Call MCP tools
jebat mcp call server_name tool_name '{"param": "value"}'
```

**Built-in MCP Servers:**
- File system operations
- Git operations
- Web search
- Database queries
- Custom plugin-provided servers

---

## 🔐 Security & Privacy

- **100% Local** — No data leaves your machine
- **Encrypted Storage** — Fernet (API keys) + Argon2id (passwords)
- **Audit Logging** — All tool executions tracked
- **3-Tier Safety** — auto / confirm / dangerous
- **Sandbox Isolation** — Docker for untrusted code
- **No Telemetry** — Opt-in only

---

## 🧪 Testing & Quality

```bash
# Run all tests
pytest -v

# Run specific test suites
pytest tests/test_orchestration.py -v
pytest tests/test_pentest.py -v
pytest tests/test_memory_integration.py -v

# Coverage report
pytest --cov=jebat --cov-report=html

# Type checking
mypy jebat/

# Linting
ruff check jebat/
black jebat/
```

**Test Status:** 170/170 tests passing • 89 tools registered • Zero critical vulnerabilities

---

## 🏗️ Project Structure

```
jebat-core/
├── jebat/                          # Active runtime modules
│   ├── cli/                        # CLI entrypoints
│   │   ├── __main__.py             # New modular CLI (v2)
│   │   └── commands/               # Command implementations
│   │       ├── repl_cmd.py         # REPL command
│   │       ├── config_cmd.py       # Config management
│   │       ├── file_cmd.py         # File operations
│   │       ├── tools_cmd.py        # Tool registry
│   │       └── ...
│   ├── core/                       # Cognitive loops
│   │   ├── agent_loop.py           # ReAct pattern (Think→Act→Observe)
│   │   ├── agent_runtime.py        # Unified runtime (event bus, dispatcher)
│   │   └── delegation.py           # Subagent spawning
│   ├── features/                   # Specialized capability suites
│   │   ├── repl/                   # Streaming REPL
│   │   ├── fileops/                # Safe file operations
│   │   ├── terminal/               # PTY execution
│   │   ├── browser/                # Playwright automation
│   │   ├── vision/                 # Image analysis
│   │   ├── search/                 # Web search (SearXNG, DDG, Brave)
│   │   ├── mcp/                    # MCP client/server
│   │   ├── ultra_think/            # 7 reasoning modes
│   │   ├── ultra_loop/             # Autonomous agent
│   │   ├── memory_management/      # 5-layer memory
│   │   ├── chat/                   # Persistent conversations
│   │   ├── session/                # Session management
│   │   ├── undo/                   # Backup & rollback
│   │   ├── guardrails/             # Safety pipeline
│   │   ├── sandbox/                # Docker sandbox
│   │   ├── pentest/                # Security reconnaissance
│   │   ├── orchestration/          # Multi-agent patterns
│   │   ├── delegate/               # Subagent spawning
│   │   ├── cron/                   # Scheduled tasks
│   │   ├── plugins/                # Plugin system
│   │   ├── skills/                 # TokGuru skills
│   │   ├── cost_tracking/          # Token telemetry
│   │   ├── git/                    # GitOps tools
│   │   ├── wiki/                   # Personal knowledge base
│   │   ├── voice/                  # Whisper + TTS
│   │   ├── social_media/           # Multi-channel
│   │   ├── image_gen/              # DALL-E + SD
│   │   ├── code_index/             # Repository indexing
│   │   ├── analytics/              # Dashboard metrics
│   │   ├── telemetry/              # OpenTelemetry
│   │   ├── auth/                   # Keyring management
│   │   ├── byok/                   # Bring your own keys
│   │   ├── model_bench/            # Model benchmarking
│   │   └── ...
│   ├── llm/                        # Multi-provider routing
│   ├── tools/                      # Tool registry (89 tools)
│   ├── config/                     # Unified config (pydantic-settings)
│   └── database/                   # SQLite/PostgreSQL models
├── tests/                          # Integration tests
├── docs/                           # Architecture docs
├── vault/                          # Checklists, templates, playbooks
├── scripts/                        # Deployment & utility scripts
├── pyproject.toml                  # Package config
├── requirements.txt                # Core dependencies
└── README.md                       # This file
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
```bash
# 1. Fork & clone
git clone https://github.com/your-username/jebat-core.git
cd jebat-core

# 2. Install dev dependencies
pip install -e ".[dev]"

# 3. Create feature branch
git checkout -b feature/amazing-feature

# 4. Write tests first (TDD)
# 5. Implement feature
# 6. Run tests
pytest -v

# 7. Type check & lint
mypy jebat/
ruff check jebat/

# 8. Commit with conventional messages
git commit -m "feat: add amazing feature"

# 9. Push & create PR
git push origin feature/amazing-feature
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full technical architecture |
| [WORKSTATION_MCP_GUIDE.md](WORKSTATION_MCP_GUIDE.md) | MCP IDE integration guide |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | One-page cheat sheet |
| [CLI_AGENT_STATUS.md](CLI_AGENT_STATUS.md) | Implementation status |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment |
| [ROADMAP.md](ROADMAP.md) | Future plans |

---

## 🗺️ Roadmap Highlights

- **Q3 2026:** Web UI Dashboard (Next.js 14 + Recharts), Plugin Marketplace, Desktop App (Tauri)
- **Q4 2026:** Multi-tenancy (RBAC, resource quotas), Python SDK v2, TypeScript SDK
- **2027:** Agent-to-agent protocol (A2A), Distributed memory sync, Mobile app

See [ROADMAP.md](ROADMAP.md) for full details.

---

## 📄 License

**MIT License** — See [LICENSE](LICENSE) file.

Developed and maintained under strict data residency governance by **NusaByte**.

Built with ❤️ by **Shaidan Shaari (humm1ngb1rd)**.

---

## 🙏 Acknowledgments

JEBAT stands on the shoulders of giants:

- **LangGraph / LangChain** — Cognitive orchestration framework
- **PostgreSQL + pgvector** — Vector similarity search
- **FastAPI / Pydantic** — Modern Python APIs
- **Rich / prompt-toolkit** — Terminal interfaces
- **Playwright** — Browser automation
- **Ollama** — Local LLM inference
- **MemContext, CORE, MemFuse, MemoryCore-Lite** — Memory architecture inspiration
- **Hermes, OpenClaw, Claude Code, Codex** — CLI agent benchmarks

---

---

## 🗡️ The JEBAT Way

> *"Hang Jebat fought with loyalty and honor. JEBAT remembers with precision and purpose."*

Like the legendary warrior:
- **🗡️ Loyal** — Never forgets what you tell it
- **⚔️ Powerful** — Multi-agent coordination for complex tasks
- **🎯 Precise** — Sharp execution with cognitive reasoning
- **🛡️ Honorable** — Privacy-first, self-hosted, your control

**Your AI. Your Data. Your Legacy.**

---

🗡️ **JEBAT v6.1** — *Because warriors remember everything that matters.*

---

**Website:** https://jebat.online  |  **GitHub:** https://github.com/nusabyte-my/jebat-core  |  **npm:** https://www.npmjs.com/package/@nusabyte/jebat  |  **Issues:** https://github.com/nusabyte-my/jebat-core/issues

---

*From developer to developer, by nusabyte.my* ❤️