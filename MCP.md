# JEBAT v8.2.1 MCP Integration

JEBAT can act as a local Model Context Protocol (MCP) server from a full workspace checkout. It exposes the tools enabled in that checkout to VS Code, Cursor, Windsurf, JetBrains, and other compatible clients.

The supported entry point is `python ./jebat-mcp`. The npm launcher is for the CLI and does not itself host MCP. Remote MCP deployments must be self-hosted and protected by authentication.

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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JEBAT_PROVIDER` | Provider to use | ollama |
| `JEBAT_MODEL` | Model name | qwen2.5-coder:7b |
| `JEBAT_API_KEY` | API key for cloud providers | - |
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
