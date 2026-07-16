# JEBAT v8.2.1 — Workstation Integration & MCP Server Guide

This guide covers local IDE integration from a full JEBAT workspace checkout. Start the supported MCP entry point with `python ./jebat-mcp --transport stdio`. The exact tool set comes from the enabled workspace integrations; do not rely on historical tool counts in older material.

The npm launcher starts the JEBAT CLI but does not host MCP. Remote MCP is a self-hosted deployment concern and must sit behind authentication.

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
   - [1. CLI Agent and Registered Tools](#1-cli-agent-and-registered-tools)
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
1. **As an API client**: use your own JEBAT API deployment and credentials.
2. **As an MCP subprocess**: let the IDE start `python ./jebat-mcp --transport stdio` from a local workspace checkout.

### Cursor IDE

#### Option A: Local Stdio MCP Server (Recommended)
Exposes the tools enabled in your local JEBAT workspace to Cursor's Composer or Chat.
1. Open Cursor Settings -> **Features** -> **MCP**.
2. Click **+ Add New MCP Server**.
3. Configure:
   - **Name**: `jebat`
   - **Type**: `command`
    - **Command**: `python3 /absolute/path/to/jebat-mcp`

Alternatively, write this JSON to `.cursor/mcp.json` or `%USERPROFILE%\.cursor\mcp.json`:
```json
{
  "mcpServers": {
    "jebat": {
      "command": "python3",
      "args": ["/absolute/path/to/jebat-mcp"]
    }
  }
}
```

#### Option B: OpenAI-Compatible Provider
1. Open Cursor Settings -> **Models**.
2. Under **OpenAI API Key**, override the base URL:
    - **Base URL**: your deployment's documented OpenAI-compatible endpoint
    - **API Key**: a credential issued by that deployment
3. Use only models advertised by that provider.

---

### VS Code (Cline / Roo Code / Roo Clinic)

If you are using extension wrappers like Cline or Roo Code to build agentic coding setups:
1. Open `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` (or equivalent for Roo Code).
2. Append the JEBAT configuration block:
```json
{
  "mcpServers": {
    "jebat": {
      "command": "python3",
      "args": ["/absolute/path/to/jebat-mcp"],
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
      "command": "python3",
      "args": ["/absolute/path/to/jebat-mcp"]
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
    - **Command / Executable**: `python3`
    - **Arguments**: `/absolute/path/to/jebat-mcp`

---

## 2. Deploying JEBAT as an MCP Server

### CLI Configurations Command

JEBAT ships IDE templates under `ide-configs/`. From the workspace root, start the server with:
```bash
python ./jebat-mcp --print-ide-config
```
This dumps clean, pre-formatted JSON structures for Cursor, VS Code, Zed, Windsurf, and JetBrains.

### Transport Modes

#### 1. Stdio (JSON-RPC 2.0 over Standard Input/Output)
Ideal for local IDE subprocess launches.
```bash
python ./jebat-mcp --transport stdio
```

#### 2. HTTP Server (SSE Transport)
Ideal for remote developer environments or sharing a single server across a workspace.
```bash
python ./jebat-mcp --transport http --host 127.0.0.1 --port 8099
```

#### 3. Remote deployment
Use `infra/vps/vps/docker-compose.mcp.yml` and `infra/vps/vps/nginx.jebat.mcp.conf` as deployment references. Keep the service private or put it behind authentication before accepting remote clients.

---

## 3. The 13 Core Capabilities Guide

### 1. CLI Agent and Registered Tools

JEBAT runs as a command-line agent with registered workspace tools protected by command verification tiers.
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
2. **Acts**: Calls an enabled registered tool.
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
