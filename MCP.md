# JEBAT MCP Integration (Stateless v2026-07-28)

JEBAT can act as a local Model Context Protocol (MCP) server from a full workspace checkout. It exposes the tools enabled in that checkout to VS Code, Cursor, Windsurf, JetBrains, and other compatible clients.

The supported entry point is `python ./jebat-mcp`. The npm launcher is for the CLI and does not itself host MCP. Remote MCP deployments must be self-hosted and protected by authentication.

The server negotiates MCP protocol versions `2024-11-05`, `2025-03-26`, `2025-06-18`, and `2026-07-28` (stateless). The v2026-07-28 stateless architecture eliminates session bindings — each request is self-contained, enabling horizontal scaling behind standard load balancers. In addition to tools, it exposes workflow resources and governed prompts so an IDE can recover context before acting.

## Quick Setup

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "jebat": {
        "command": "python3",
        "args": ["/absolute/path/to/jebat-mcp"]
      }
    }
  }
}
```

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "jebat": {
        "command": "python3",
        "args": ["/absolute/path/to/jebat-mcp"],
      "env": {}
    }
  }
}
```

### Windsurf

Add to `~/.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "jebat": {
        "command": "python3",
        "args": ["/absolute/path/to/jebat-mcp"],
      "env": {}
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

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

## Available Tools

When connected via MCP, JEBAT exposes the tools registered by the installed workspace. Common capability groups include:

| Tool | Description |
|------|-------------|
| File operations | Read, write, patch, search workspace files |
| Terminal operations | Execute approved shell commands |
| Memory and search | Store, recall, and search workspace context |
| Enabled integrations | Browser, scheduling, and other configured capabilities |

## Context Surfaces

| Surface | URI / name | Purpose |
|---------|------------|---------|
| Resource | `jebat://workflow` | Plan → approve → execute → verify → remember guidance |
| Resource | `jebat://tools` | Current tool names, safety tiers, and timeouts |
| Prompt | `plan-act-verify-remember` | Reusable governed task workflow for IDE agents |

Write-capable tool calls return machine-readable `approval_required` metadata before execution. The IDE can show the exact tool, arguments, and safety tier; approval remains explicit in JEBAT CLI.

## Transport Options

### stdio (default)
```bash
python ./jebat-mcp --transport stdio
```
Best for local IDE connections.

### HTTP (SSE)
```bash
python ./jebat-mcp --transport http --host 127.0.0.1 --port 8099
```
Best for remote connections or multi-user setups.

### Streamable HTTP (Stateless)
```bash
python ./jebat-mcp --transport streamable-http --host 127.0.0.1 --port 8100
```
Uses the single `/mcp` endpoint. Fully stateless as of v2026-07-28 — no session bindings, horizontally scalable behind Nginx/HAProxy. Put it behind an authenticated reverse proxy before allowing network access.

### Multi-Instance Deployment (Production)
```bash
# Run 2-4 instances behind Nginx round-robin on VPS
pm2 start "python ./jebat-mcp --transport streamable-http --port 8100" --name mcp-0
pm2 start "python ./jebat-mcp --transport streamable-http --port 8101" --name mcp-1
pm2 start "python ./jebat-mcp --transport streamable-http --port 8102" --name mcp-2
```
```nginx
# Nginx upstream (no sticky sessions needed — stateless)
upstream jebat_mcp {
    server 127.0.0.1:8100;
    server 127.0.0.1:8101;
    server 127.0.0.1:8102;
}
server {
    location /mcp {
        proxy_pass http://jebat_mcp;
    }
}
```

## Full Sovereign Harness Capabilities

JEBAT MCP operates as an active sovereign harness rather than a passive tool server:

1. **Ghost Database Integration (14 Tools)**:
   - Direct SQL execution (`ghost.sql`), schema inspection (`ghost.schema`), and metrics (`ghost.metrics`).
   - Ephemeral database branching (`ghost.create`, `ghost.fork`) and checkpoint restoration (`ghost.checkpoint.create`, `ghost.checkpoint.restore`) for zero-risk test runs.

2. **Dynamic Live Context Resources**:
   - `jebat://memory/project`: Real-time project facts (stack, conventions, environment, gotchas) from SelfLearn.
   - `jebat://memory/dream`: Consolidated heuristics, learning profile, and suggestions from autoMimpi.
   - `jebat://database/schema`: Active database schema layout and definitions.

3. **Autonomous Agent Execution (`agent_execute`)**:
   - Multi-turn ReAct coding engine powered by Hermes scratchpad (`<thought>`) and Atomic Agents Pydantic validation.
   - Allows IDEs to offload entire multi-step coding/debugging loops to the server in a single call.

4. **Dual-Store Vector Memory (SelfLearn + autoMimpi + Ghost DB)**:
   - Cross-session memory traces in `~/.jebat/memory/traces.json` mirrored to Ghost DB / SQLite-vec for semantic search.

5. **Production Deployment on VPS .206**:
   - Stateless Streamable HTTP endpoint(s) running on ports 8100-8102 under PM2, reverse-proxied via Nginx at `https://jebat.nusabyte.my/mcp`.
   - v2026-07-28: no sticky sessions — round-robin across instances for HA and zero-downtime restarts.

6. **Advisor Tools (Jev-style System One Decisions)**:
   - `advisor_classify`: Classify text into categories with confidence (~100ms)
   - `advisor_verify`: Yes/no claim verification with calibrated probability
   - `advisor_score`: Rate text on a scale with confidence
   - `advisor_decide`: Full multi-question typed decision in one parallel pass
   - Backend: TypeSafe Jev API when `TYPESAFE_API_KEY` is set; local fallback otherwise

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JEBAT_PROVIDER` | Provider to use | ollama |
| `JEBAT_MODEL` | Model name | qwen2.5-coder:7b |
| `JEBAT_API_KEY` | API key for cloud providers | - |
| `TYPESAFE_API_KEY` | TypeSafe Jev API key for advisor tools | - (local fallback) |
| `TYPESAFE_BASE_URL` | TypeSafe API base URL | `https://api.typesafe.ai` |
| `JEBAT_MCP_PORT` | Deployment-defined HTTP port | 8099 |

## Troubleshooting

### Connection refused
1. Ensure the full JEBAT workspace and Python dependencies are installed.
2. Test the local server: `python ./jebat-mcp --transport stdio`

### Tools not showing
1. Check IDE MCP settings
2. Restart IDE after adding config
3. Check JEBAT logs: `~/.jebat/logs/mcp.log`

### Authentication errors
1. Keep remote MCP behind an authenticated reverse proxy.
2. Configure provider credentials only on the server that needs them.
