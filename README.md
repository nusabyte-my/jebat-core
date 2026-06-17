# JEBAT v6.1.0 — Sovereign AI Platform & Agent Workstation

![Version](https://img.shields.io/badge/version-v6.1.0--stable-10b981?style=flat-square)
![Security](https://img.shields.io/badge/security-audited-06b6d4?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-71717a?style=flat-square)
![Tests](https://img.shields.io/badge/tests-64%2F64--passing-10b981?style=flat-square)

> **Sovereign execution, private memory, and audited intelligence.**

JEBAT is an enterprise-grade self-hosted AI platform and agent workstation. It provides governed local LLM inference, secure cognitive routing, multi-agent swarm orchestration, and an embedded threat reconnaissance toolkit. Run fully air-gapped on your private network with zero data leakage.

---

## Technical Comparison

| Capability | JEBAT v6.1 | Commercial SaaS (Claude/GPT) | Ollama WebUI | LM Studio |
| :--- | :---: | :---: | :---: | :---: |
| **Data Residency** | **100% Private / Air-gapped** | Cloud (Third-Party) | Local Only | Local Only |
| **LLM Provider Routing** | **6 Providers (Failover)** | Single Provider | Ollama Only | Local Only |
| **Cognitive Profiles** | **7 Thinking Modes (Ultra-Think)** | Standard Chat | Standard Chat | Standard Chat |
| **Security Auditing** | **Autonomous Pentest Suite** | Blocked | None | None |
| **Access Control (RBAC)** | **3-Tier Command Classification** | Muted Policy | Basic Auth | None |
| **Eternal Memory** | **5-Layer Heat-Scored Recall** | Session Limits | No | No |
| **Standard Integration** | **Native MCP Client + Server** | None | Basic API | Local API |

---

## 🔌 Workstation & MCP Server Integration

JEBAT v6.1 features native integration with major developer workspaces (Cursor, VS Code, Zed, Windsurf, JetBrains) as a standard **Model Context Protocol (MCP)** server.

For step-by-step injection configurations and details on executing the **13 core capabilities** (ReAct loop, Ultra-Think reasoning, swarms, sandbox, voice I/O, Playwright, pentesting), please consult:
👉 **[WORKSTATION_MCP_GUIDE.md](file:///d:/Jebat/WORKSTATION_MCP_GUIDE.md)**

---

## 6-Step Operational Onboarding Guide

### Step 1: Secure Installation
Install the platform directly onto your secure environment using python package managers, container arrays, or clean source repositories.

```bash
# Option A: Standard local install via pip
pip install jebat

# Option B: Isolated container build
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
docker compose build
docker compose up -d
```

### Step 2: Credential Hardening
Initialize the encrypted keyring credential manager. JEBAT securely encrypts all local secrets to prevent key leakage.

```bash
# Securely store API keys or connection hosts
jebat auth set openai your-openai-key
jebat auth set anthropic your-anthropic-key
jebat auth set ollama http://localhost:11434
```

### Step 3: Configure the Cognitive Router
Configure the default system runtime variables inside `~/.jebat/config.yaml`. Point JEBAT to local weights or cloud endpoints.

```yaml
llm:
  provider: ollama
  model: qwen2.5-coder:7b
  fallback_providers:
    - openai
    - anthropic
safety:
  default_tier: confirm
  sandbox_restricted: true
```

### Step 4: Run Autonomous Agent Loops
Launch the ReAct (Reasoning and Acting) execution engine. You can execute tasks in single queries or jump into an interactive command shell.

```bash
# Run one-shot queries with tool routing
jebat agent "Verify the repository build config in package.json"

# Launch the interactive streaming REPL shell
jebat chat-repl
```

### Step 5: Orchestrate Agent Swarms
Deconstruct high-level goals into parallel subtasks and delegate them to role-based subagents (Tukang, Hulubalang, Pawang).

```bash
# Dispatch a secure multi-agent task array
jebat delegate run "Audit all API endpoints in src/services" --tools terminal,file
```

### Step 6: Deploy Multi-Channel Adapters
Expose the agent gateway securely to team messaging systems, letting your operations team query logs and dispatch commands.

```bash
# Initialize channel listeners (configured in config.yaml)
jebat social start --channels telegram,slack
```

---

## Subcommand Directory

JEBAT exposes 46 subcommands divided into logical management zones:

| Domain | Commands | Description |
| :--- | :--- | :--- |
| **System** | `status`, `init`, `config`, `doctor`, `optimize` | Manage system health, tune configs, run optimizations |
| **Inference** | `llm-providers`, `llm-config`, `llm-auth`, `free-models`, `cost` | Review provider credentials, fallback paths, live usage budgets |
| **Interaction** | `chat`, `chat-project`, `chat-repl`, `think`, `loop` | Standard chat, project context loading, interactive REPL |
| **Orchestration** | `delegate`, `cron`, `skills`, `tools`, `mcp` | Swarm delegation, task scheduler, skill registries, MCP servers |
| **Operations** | `file`, `exec`, `git`, `wiki`, `session`, `todo` | File modifiers, PTY terminal execution, wiki pages, database indices |
| **Security** | `pentest`, `sandbox`, `safety`, `undo` | Auditing tools, Docker container isolation, rollback backups |

---

## System Architecture

```
jebat-core/
  ├── jebat/                  # Active runtime modules
  │   ├── cli/                # Entrypoints (jebat_cli.py v6.1.0)
  │   ├── core/               # Cognitive loops (agent_loop.py, delegation.py)
  │   ├── features/           # Specialized capability suites
  │   │   ├── pentest/        # TukangBesi — reconnaissance orchestration
  │   │   ├── sandbox/        # Hulubalang — Docker container sandbox
  │   │   └── undo/           # Pawang — backup rollbacks
  │   └── llm/                # Multi-provider HSL cognitive routing
  ├── db/                     # SQLite RAG wiki & memory files
  └── docs/                   # Platform architecture references
```

---

## Safety Classification Tiers

To safeguard target servers, JEBAT categorizes all tool execution into permission tiers:

- **AUTO**: Read-only, safe commands executed without intervention (e.g. `cat`, `grep`).
- **CONFIRM**: Write and modification commands prompting user validation (e.g. `write`, `patch`, `git commit`).
- **DANGEROUS**: Destructive or privilege-escalating commands requiring explicit terminal validation tags (e.g. `rm -rf`, `sudo`).

---

## License & Organization
Developed and maintained under strict data residency governance by NusaByte.
Licensed under the MIT Open Source License. Built by Shaidan Shaari (humm1ngb1rd).
