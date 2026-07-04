# JEBAT MCP Integration

JEBAT can act as an MCP (Model Context Protocol) server, exposing its tools to IDEs like VS Code, Cursor, Windsurf, and JetBrains.

## Quick Setup

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "jebat": {
        "command": "npx",
        "args": ["@nusabyte/jebat", "mcp", "serve", "--transport", "stdio"]
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
      "command": "npx",
      "args": ["@nusabyte/jebat", "mcp", "serve", "--transport", "stdio"],
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
      "command": "npx",
      "args": ["@nusabyte/jebat", "mcp", "serve", "--transport", "stdio"],
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
      "command": "npx",
      "args": ["@nusabyte/jebat", "mcp", "serve", "--transport", "stdio"]
    }
  }
}
```

## Available Tools

When connected via MCP, JEBAT exposes these tools:

| Tool | Description |
|------|-------------|
| `jebat_code` | Execute code with tool calling |
| `jebat_file` | Read, write, patch, search files |
| `jebat_terminal` | Execute shell commands |
| `jebat_memory` | Store and recall memory |
| `jebat_search` | Search codebase |

## Transport Options

### stdio (default)
```bash
jebat mcp serve --transport stdio
```
Best for local IDE connections.

### HTTP (SSE)
```bash
jebat mcp serve --transport http --port 8099
```
Best for remote connections or multi-user setups.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JEBAT_PROVIDER` | Provider to use | ollama |
| `JEBAT_MODEL` | Model name | qwen2.5-coder:7b |
| `JEBAT_API_KEY` | API key for cloud providers | - |
| `JEBAT_MCP_PORT` | HTTP port for remote access | 8099 |

## Troubleshooting

### Connection refused
1. Ensure JEBAT is installed: `npm install -g @nusabyte/jebat`
2. Test MCP server: `echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | jebat mcp serve`

### Tools not showing
1. Check IDE MCP settings
2. Restart IDE after adding config
3. Check JEBAT logs: `~/.jebat/logs/mcp.log`

### Authentication errors
1. Set API key: `jebat apikey <name>:<key>`
2. Or export: `export JEBAT_API_KEY=your-key`
