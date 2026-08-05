# JEBATCore — npm MCP Client Adapter

> Node.js MCP client adapter for JEBAT. Use `@nusabyte/jebat` for the supported CLI launcher; use a full workspace checkout and `python ./jebat-mcp` when hosting MCP for an IDE.

## Install

```bash
npm install jebatcore
# Supported CLI launcher:
npx @nusabyte/jebat chat "Hello world"
```

## Quick Start

### 1. CLI Usage (npx jebat)

```bash
# Chat with JEBAT (auto-bootstraps Python if needed)
npx jebat chat "Explain quantum computing"

# Host MCP from a full workspace checkout
python ./jebat-mcp --transport stdio

# Self-host HTTP behind an authenticated reverse proxy
python ./jebat-mcp --transport http --host 127.0.0.1 --port 8099

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

### 3. Self-Hosted HTTP (Remote IDE)

```javascript
// HTTP transport from an authenticated deployment you operate
const http = new JebatMCPClient({
  transport: 'http',
  url: 'https://your-mcp-host.example/mcp'
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
        "command": "python3",
        "args": ["/absolute/path/to/jebat-mcp"]
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
      "command": "python3",
      "args": ["/absolute/path/to/jebat-mcp"]
    }
  }
}
```

### Windsurf / JetBrains
Use `python3 /absolute/path/to/jebat-mcp` for a local stdio server.

## Features

| Feature | Description |
|---------|-------------|
| **MCP Server** | Hosted by a full JEBAT workspace through `jebat-mcp` |
| **MCP Client** | Connect to JEBAT from Node.js using MCP SDK |
| **Sampling** | IDEs can request LLM completions through JEBAT's 9Router free-proxy |
| **Progress Tokens** | Real-time feedback during long-running tool calls |
| **Auto Bootstrap** | Automatically installs Python JEBAT package if missing |
| **Transports** | stdio for local IDEs and self-hosted HTTP for controlled remote access |

## Architecture

```
IDE (VS Code/Cursor) → MCP SDK → jebatcore (npm) → JEBAT Python CLI
                                                    ↓
                                          9Router (free AI proxy)
                                                    ↓
                                            Free-tier LLMs (no API keys)
```

## License

MIT — humm1ngb1rd / NusaByte
