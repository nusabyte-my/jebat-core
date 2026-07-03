# 🗡️ JEBAT v6.1 — Workstation Integration & MCP Server Guide

Welcome to the official integration guide for **JEBAT v6.1**. This document details how to inject JEBAT's cognitive reasoning, multi-agent swarms, security testing suite, and memory context directly into your developer workstation (Cursor, VS Code, Zed, Windsurf, JetBrains), run it as a standard Model Context Protocol (MCP) server, and utilize all 13 core capabilities.

---

## 📌 Table of Contents
1. [Workstation Injection & IDE Integration](#1-workstation-injection--ide-integration)
   - [Cursor IDE](#cursor-ide)
   - [VS Code (Cline / Roo Code / Roo Clinic)](#vs-code-cline--roo-code--roo-clinic)
   - [Zed Editor](#zed-editor)
   - [Windsurf IDE](#windsurf-ide)
   - [JetBrains IDEs](#jetbrains-ides)
2. [Deploying JEBAT as an MCP Server](#2-deploying-jebat-as-an-mcp-server)
   - [CLI Configurations Command](#cli-configurations-command)
   - [Transport Modes](#transport-modes)
3. [The 13 Core Capabilities Guide](#3-the-13-core-capabilities-guide)
   - [1. CLI Agent (46 Subcommands, 89 Tools)](#1-cli-agent-46-subcommands-89-tools)
   - [2. ReAct Loop (Think→Act→Observe)](#2-react-loop-thinkactobserve)
   - [3. Ultra-Think (7 Reasoning Modes)](#3-ultra-think-7-reasoning-modes)
   - [4. Ultra-Loop (Autonomous Cycles)](#4-ultra-loop-autonomous-cycles)
   - [5. 5-Layer Memory (M0→M4 Heat Consolidation)](#5-5-layer-memory-m0m4-heat-consolidation)
   - [6. MCP Client & Server Hub](#6-mcp-client--server-hub)
   - [7. Pentest Suite (TukangBesi Recon)](#7-pentest-suite-tukangbesi-recon)
   - [8. Docker Sandbox (Hulubalang Isolation)](#8-docker-sandbox-hulubalang-isolation)
   - [9. Multi-Agent Swarms (Role Delegation)](#9-multi-agent-swarms-role-delegation)
   - [10. Voice I/O (Whisper STT + Edge TTS)](#10-voice-io-whisper-stt--edge-tts)
   - [11. GitOps Engine (Codebase Evolution)](#11-gitops-engine-codebase-evolution)
   - [12. Browser Automation (Playwright Vision)](#12-browser-automation-playwright-vision)
   - [13. Full Verification (170 passing tests)](#13-full-verification-170-passing-tests)

---

## 1. Workstation Injection & IDE Integration

You can integrate JEBAT into your workstation in two ways:
1. **As an OpenAI-Compatible API Endpoint**: IDE sends prompt queries to JEBAT's local API server.
2. **As an MCP Server Subprocess**: IDE spawns JEBAT CLI as an MCP subprocess, directly consuming its 89 tools.

### Cursor IDE

#### Option A: Local Stdio MCP Server (Recommended)
Exposes all 89 JEBAT tools (files, git, browser, sandbox, search) directly to Cursor's Composer or Chat.
1. Open Cursor Settings -> **Features** -> **MCP**.
2. Click **+ Add New MCP Server**.
3. Configure:
   - **Name**: `jebat`
   - **Type**: `command`
   - **Command**: `jebat mcp serve --transport stdio`

Alternatively, write this JSON to `.cursor/mcp.json` or `%USERPROFILE%\.cursor\mcp.json`:
```json
{
  "mcpServers": {
    "jebat": {
      "command": "jebat",
      "args": ["mcp", "serve", "--transport", "stdio"]
    }
  }
}
```

#### Option B: OpenAI-Compatible Provider
1. Open Cursor Settings -> **Models**.
2. Under **OpenAI API Key**, override the base URL:
   - **Base URL**: `http://localhost:8000/api/v1`
   - **API Key**: `jebat-local-key`
3. Add custom models: `jebat-pro`, `jebat-fast`, `jebat-deep`.

---

### VS Code (Cline / Roo Code / Roo Clinic)

If you are using extension wrappers like Cline or Roo Code to build agentic coding setups:
1. Open `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` (or equivalent for Roo Code).
2. Append the JEBAT configuration block:
```json
{
  "mcpServers": {
    "jebat": {
      "command": "jebat",
      "args": ["mcp", "serve", "--transport", "stdio"],
      "disabled": false
    }
  }
}
```

---

### Zed Editor

Zed connects natively to JEBAT's OpenAI-compatible endpoint for inline completions and assistant panel chat.

1. Open Zed Settings (`Ctrl + ,` or command palette `open settings`).
2. Add or modify the `ai` block in your `settings.json` file:
```json
{
  "ai": {
    "providers": {
      "jebat": {
        "name": "JEBAT AI",
        "type": "openai-compatible",
        "api_url": "http://localhost:8000/api/v1",
        "api_key": "jebat-local-key",
        "models": {
          "chat": "jebat-pro",
          "completion": "jebat-fast"
        }
      }
    },
    "default_provider": "jebat"
  },
  "features": {
    "inline_completion_provider": "jebat"
  }
}
```

---

### Windsurf IDE

Windsurf uses standard MCP server declarations.
1. Open Windsurf Settings -> **MCP**.
2. Add a new configuration under `~/.codeium/windsurf/mcp.json` or `.windsurf/mcp.json`:
```json
{
  "mcpServers": {
    "jebat": {
      "command": "jebat",
      "args": ["mcp", "serve", "--transport", "stdio"]
    }
  }
}
```

---

### JetBrains IDEs

For PyCharm, WebStorm, or IntelliJ using the JetBrains AI Assistant:
1. Open IDE Settings -> **Tools** -> **AI Assistant** -> **MCP Servers**.
2. Click **+ Add Server** and select **Stdio Command**.
3. Input:
   - **Name**: `jebat`
   - **Command / Executable**: `jebat`
   - **Arguments**: `mcp serve --transport stdio`

---

## 2. Deploying JEBAT as an MCP Server

### CLI Configurations Command

JEBAT makes finding setup configurations easy. From your terminal, execute:
```bash
jebat mcp ide-config
```
This dumps clean, pre-formatted JSON structures for Cursor, VS Code, Zed, Windsurf, and JetBrains.

### Transport Modes

#### 1. Stdio (JSON-RPC 2.0 over Standard Input/Output)
Ideal for local IDE subprocess launches.
```bash
jebat mcp serve --transport stdio
```

#### 2. HTTP Server (SSE Transport)
Ideal for remote developer environments or sharing a single server across a workspace.
```bash
jebat mcp serve --transport http --host 127.0.0.1 --port 8099
```

#### 3. Streamable HTTP (MCP 2025-03-26 Spec)
Optimized transport complying with the latest specification version.
```bash
jebat mcp serve --transport streamable-http --port 8099
```

---

## 3. The 13 Core Capabilities Guide

### 1. CLI Agent (46 Subcommands, 89 Tools)

JEBAT runs as a command-line agent wrapping 89 granular OS tools safely behind command verification tiers.
- **Inspect System Health**: `jebat status`
- **Diagnose Problems**: `jebat doctor`
- **Inspect Registered Tools**: `jebat tools list`

#### Safety Classification Tiers
To protect host filesystems, tools are classified into three safety domains:
- **AUTO**: Runs immediately without prompts (e.g. `cat`, `grep`, `git diff`).
- **CONFIRM**: Prompts the user before executing changes (e.g. `write`, `patch`, `git commit`).
- **DANGEROUS**: Requires active confirmation flags or terminal tag parameters (e.g. `rm -rf`, `sudo`).

---

### 2. ReAct Loop (Think→Act→Observe)

The core cognitive engine uses a Reasoning-and-Acting (ReAct) cycle. For every request, JEBAT:
1. **Thinks**: Explores the problem and designs a solution path.
2. **Acts**: Calls one of the 89 registered tools.
3. **Observes**: Analyzes tool execution stdout/stderr and decides on follow-ups.

Responses are streamed **token-by-token** with active status indicators showing live tool selections.
- Run interactive REPL: `jebat repl`
- Override model in REPL: `/model gemma3:12b`
- Toggle safety tier: `/safety dangerous`

---

### 3. Ultra-Think (7 Reasoning Modes)

JEBAT supports multi-phase reasoning beyond simple chat loops.

| Mode | Target Task | CLI Trigger |
|---|---|---|
| `fast` | One-shot code questions / shell lookups | `jebat think --mode fast "query"` |
| `deliberate` | Refactoring, reviewing syntax issues | `jebat think --mode deliberate "query"` |
| `deep` | Algorithmic logic design, database architecture | `jebat think --mode deep "query"` |
| `strategic` | Architectural patterns, migration guides | `jebat think --mode strategic "query"` |
| `creative` | UI styling themes, branding taglines | `jebat think --mode creative "query"` |
| `critical` | Code review and security checks | `jebat think --mode critical "query"` |
| `adversarial` | Exploiting inputs, verifying firewalls | `jebat think --mode adversarial "query"` |

---

### 4. Ultra-Loop (Autonomous Cycles)

Run JEBAT fully autonomously to solve complex tasks (e.g. fixing broken test suites, downloading assets) without stopping.
- **Start Autonomous Loop**: `jebat loop start`
- **Limit Execution Cycles**: `jebat loop start --max-cycles 15`
- **Status Check**: `jebat loop status`

---

### 5. 5-Layer Memory (M0→M4 Heat Consolidation)

A biologically-inspired memory architecture structured to prevent context loss:
- **M0: Sensory Buffer**: Stream context and immediate prompt inputs.
- **M1: Episodic Memory**: Session dialogue database indexed via SQLite FTS5.
- **M2: Semantic Memory**: Extracted knowledge graphs representing developer preferences.
- **M3: Conceptual Memory**: Crystallized rules, structural paradigms, and templates.
- **M4: Procedural Memory**: Installed TokGuru skills and tool usage guides.

#### Command Patterns:
- **Search Memory**: `jebat memory search "database constraints"`
- **Store Fact**: `jebat memory store "Target PostgreSQL cluster is v16.3"`
- **Consolidate Logs**: `jebat memory consolidate` (Triggers heat consolidation M1 → M2 → M3)

---

### 6. MCP Client & Server Hub

Expose client tools or ingest other servers' capabilities seamlessly.
- **Connect to Third-Party Server**: `jebat mcp connect "npx -y @modelcontextprotocol/server-postgres"`
- **List Ingested Tools**: `jebat mcp list`
- **Invoke Ingested Tool**: `jebat mcp call postgres query '{"sql": "SELECT * FROM users"}'`

---

### 7. Pentest Suite (TukangBesi Recon)

JEBAT includes an autonomous penetration testing workflow to scan codebases or active network endpoints safely.
- **Quick Scan**: `jebat pentest quick --target example.com`
- **Standard Audit**: `jebat pentest standard --target example.com`
- **Full Penetration**: `jebat pentest full --target example.com`
- **Vulnerability Check**: `jebat pentest vuln-scan --target example.com`

*Outputs are cleanly generated into formatted markdown files under `reports/` with actionable mitigation solutions.*

---

### 8. Docker Sandbox (Hulubalang Isolation)

To protect the host environment, untrusted code (especially Python scripts generated mid-loop) executes in isolated containers.
- **Run Script in Sandbox**: `jebat sandbox run script.py`
- **Check Container Health**: `jebat sandbox check`
- **Purge Containers**: `jebat sandbox cleanup`

---

### 9. Multi-Agent Swarms (Role Delegation)

High-level project goals are broken down and dispatched in parallel to specialized roles:
- **Tukang**: Code implementation, builds, and visual web compilation.
- **Hulubalang**: Security validations, audit logs, and container sandboxing.
- **Pawang**: Research operations, wiki indexing, and file undo/rollbacks.

#### Dispatch Command:
```bash
jebat delegate run "Audit endpoints and generate a client library" --tools terminal,file
```

---

### 10. Voice I/O (Whisper STT + Edge TTS)

Engage with JEBAT using spoken audio commands.
- **Transcribe Audio File**: `jebat voice transcribe recording.wav`
- **Speak Text (TTS)**: `jebat voice speak "System diagnostic complete."`
- **Interactive Voice Chat**: `jebat voice chat --model qwen2.5-coder`

---

### 11. GitOps Engine (Codebase Evolution)

JEBAT features a robust Git control layer (8 tools) to commit, diff, and verify changes safely.
- **Status Summary**: `jebat git status`
- **File Blame**: `jebat git blame main.py`
- **Create Commit**: `jebat git commit -m "refactor: optimize DB connections"`

---

### 12. Browser Automation (Playwright Vision)

Orchestrate headful/headless web actions using Playwright (click, type, navigate, scrape) with integrated vision-analysis.
- **Navigate and Screen**: `jebat search "https://news.ycombinator.com" --extract`
- **Run Visual UI Audit**: `jebat agent "Open localhost:8787 and verify the buttons align correctly"`

---

### 13. Full Verification (170 passing tests)

Ensure full framework integrity prior to deployment. JEBAT includes 170 unit and integration tests covering cognitive loops, memory, databases, and tool configurations.

```bash
# Execute full test runner
pytest -v
```

All 170 tests pass successfully on local workspace installations.
