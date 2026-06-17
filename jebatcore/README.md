# JEBATCore — npm MCP Adapter Package

> Node.js MCP client adapter for JEBAT CLI Agent. Bootstraps Python + connects IDEs via MCP.

## Install

```bash
npm install jebatcore
# or run directly:
npx jebat chat "Hello world"
npx jebat mcp serve --transport stdio
```

## Quick Start

### 1. CLI Usage (npx jebat)

```bash
# Chat with JEBAT (auto-bootstraps Python if needed)
npx jebat chat "Explain quantum computing"

# Start MCP server for IDE integration
npx jebat mcp serve --transport stdio

# Start MCP server with Streamable HTTP (MCP 2025-03-26)
npx jebat mcp serve --transport streamable-http --port 8100

# Git operations
npx jebat git status
npx jebat git diff

# YOLO mode (auto-approve all tool calls)
npx jebat chat --yolo "Scan localhost for open ports"
```

### 2. MCP Client (Node.js/IDE integration)

```javascript
const { JebatMCPClient } = require('jebatcore');

// Connect via stdio (IDE spawns JEBAT as subprocess)
const client = new JebatMCPClient({ transport: 'stdio' });
await client.connect();

// List available tools
const tools = await client.listTools();

// Call a tool
const result = await client.callTool('web_search', { query: 'JEBAT CLI agent' });

// Request LLM completion via sampling
const response = await client.createMessage([
  { role: 'user', content: { type: 'text', text: 'What is JEBAT?' } }
], 4096);

await client.disconnect();
```

### 3. HTTP/Streamable HTTP (Remote IDE)

```javascript
// SSE transport (legacy HTTP)
const http = new JebatMCPClient({
  transport: 'http',
  url: 'http://jebat.nusabyte.my:8100/sse'
});

// Streamable HTTP (MCP 2025-03-26 spec)
const streamable = new JebatMCPClient({
  transport: 'streamable-http',
  url: 'http://jebat.nusabyte.my:8100/mcp'
});
```

### 4. Python Bootstrap (CI/CD)

```javascript
const { bootstrap } = require('jebatcore');
const info = bootstrap(); // { python: 'python3', installed: true, version: '0.1.0' }
```

## IDE Configuration

### VS Code (settings.json)
```json
{
  "mcp": {
    "servers": {
      "jebat": {
        "command": "jebat",
        "args": ["mcp", "serve", "--transport", "stdio"]
      }
    }
  }
}
```

### Cursor (.cursor/mcp.json)
```json
{
  "mcpServers": {
    "jebat": {
      "command": "npx",
      "args": ["-y", "jebatcore"]
    }
  }
}
```

### Windsurf / JetBrains
Same pattern — use `npx jebatcore` or `jebat mcp serve --transport stdio`.

## Features

| Feature | Description |
|---------|-------------|
| **MCP Server** | Exposes all JEBAT tools to IDEs via stdio/HTTP/streamable-http |
| **MCP Client** | Connect to JEBAT from Node.js using MCP SDK |
| **Sampling** | IDEs can request LLM completions through JEBAT's 9Router proxy |
| **Progress Tokens** | Real-time feedback during long-running tool calls |
| **Auto Bootstrap** | Automatically installs Python JEBAT package if missing |
| **3 Transports** | stdio (IDEs), SSE (legacy HTTP), Streamable HTTP (MCP 2025-03-26) |

## Architecture

```
IDE (VS Code/Cursor) → MCP SDK → jebatcore (npm) → JEBAT Python CLI
                                                    ↓
                                              9Router (local LLM proxy)
                                                    ↓
                                            Free-tier LLMs (no API keys)
```

## License

MIT — humm1ngb1rd / NusaByte