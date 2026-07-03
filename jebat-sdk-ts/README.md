# JEBAT TypeScript SDK

Official TypeScript SDK for the [JEBAT AI Assistant](https://github.com/humm1ngb1rd/jebat) REST API.

## Features

- **Sync & Async Clients** - Use `JebatClient` for sync or `AsyncJebatClient` for async code
- **Full Type Definitions** - Complete TypeScript interfaces for all API responses
- **Auto Retry** - Exponential backoff with configurable retry policies
- **Rate Limiting** - Automatic handling with `Retry-After` support
- **WebSocket Streaming** - Real-time chat streaming with auto-reconnect
- **Structured Exceptions** - Typed errors mapping HTTP status codes
- **Zod Schemas** - Runtime validation for all models
- **Type Safe** - Built with TypeScript 5+ strict mode

## Installation

```bash
npm install @jebat/sdk
```

From source:
```bash
git clone https://github.com/humm1ngb1rd/jebat.git
cd jebat/jebat-sdk-ts
npm install
npm run build
```

## Quick Start

### Synchronous Client

```typescript
import { JebatClient } from '@jebat/sdk';

// Initialize client
const client = new JebatClient({ baseUrl: 'http://localhost:8000' });

// Login
const tokens = await client.login('username', 'password');
console.log(`Access token: ${tokens.access_token}`);

// Chat (blocking)
const response = await client.chat('Hello, JEBAT!', { mode: 'deliberate' });
console.log(response.response);

// Memories
const memories = await client.listMemories({ query: 'python', layer: 'M2_SEMANTIC' });
for (const mem of memories.items) {
  console.log(`[${mem.layer}] ${mem.content}`);
}

// Agents
const agents = await client.listAgents();
for (const agent of agents.agents) {
  console.log(`${agent.name} (${agent.type}) - ${agent.status}`);
}

// API keys
const key = await client.createApiKey('My App', 30);
console.log(`Key: ${key.key}`); // Only shown once!

client.close();
```

### Async Client

```typescript
import { AsyncJebatClient } from '@jebat/sdk';

async function main() {
  const client = new AsyncJebatClient({ baseUrl: 'http://localhost:8000' });
  
  try {
    await client.login('username', 'password');
    
    // Streaming chat
    for await (const chunk of client.chatStream('Hello, world!')) {
      process.stdout.write(chunk.content);
    }
    
    // Parallel requests
    const [health, agents] = await Promise.all([
      client.getHealth(),
      client.listAgents(),
    ]);
  } finally {
    await client.close();
  }
}

main();
```

### WebSocket Streaming

```typescript
import { JebatWebSocketClient } from '@jebat/sdk';

async function websocketChat() {
  const ws = new JebatWebSocketClient(
    'ws://localhost:8000/ws/chat',
    accessToken
  );
  
  await ws.connect();
  
  for await (const chunk of ws.stream({ message: 'Hello!', mode: 'deep' })) {
    if (chunk.type === 'content') {
      process.stdout.write(chunk.content);
    } else if (chunk.isFinal()) {
      break;
    }
  }
  
  await ws.disconnect();
}
```

## Configuration

```typescript
// Custom base URL
const client = new JebatClient({ baseUrl: 'https://api.jebat.example.com' });

// Custom timeout
const client = new JebatClient({ baseUrl: '...', timeout: 60000 });

// Custom headers
const client = new JebatClient({ 
  baseUrl: '...', 
  headers: { 'X-Custom-Header': 'value' } 
});

// Custom retry config
const client = new JebatClient({ 
  baseUrl: '...', 
  maxRetries: 5 
});
```

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `login(username, password)` | `POST /api/v1/auth/login` | Get access/refresh tokens |
| `refreshAccessToken(refreshToken)` | `POST /api/v1/auth/refresh` | Get new access token |
| `logout(refreshToken)` | `POST /api/v1/auth/logout` | Revoke refresh token |

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| `createApiKey(name, expiresInDays)` | `POST /api/v1/auth/api-keys` | Create new key |
| `listApiKeys()` | `GET /api/v1/auth/api-keys` | List user's keys |
| `revokeApiKey(prefix)` | `DELETE /api/v1/auth/api-keys/{prefix}` | Revoke key |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `chat(message, options)` | `POST /api/v1/chat` | Blocking chat |
| `chatStream(message, options)` | `POST /api/v1/chat` (stream) | SSE streaming |
| `chatWebSocket(message, mode)` | `WS /ws/chat` | WebSocket streaming |

Modes: `fast`, `deliberate`, `deep`, `strategic`, `creative`, `critical`

### Memories

| Method | Endpoint | Description |
|--------|----------|-------------|
| `listMemories(options)` | `GET /api/v1/memories` | List/search memories |
| `createMemory(content, userId, layer)` | `POST /api/v1/memories` | Store memory |
| `searchMemories(options)` | `GET /api/v1/memories` | Search memories |

Layers: `M0_IMMEDIATE`, `M1_EPISODIC`, `M2_SEMANTIC`, `M3_PROCEDURAL`, `M4_STRATEGIC`

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `listAgents()` | `GET /api/v1/agents` | List all agents |
| `getAgent(agentId)` | `GET /api/v1/agents/{id}` | Get agent info |
| `executeAgent(task, options)` | `POST /api/v1/agents/execute` | Execute agent |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getHealth()` | `GET /api/v1/health` | System health |
| `getStatus()` | `GET /api/v1/status` | Detailed status |
| `getMetrics()` | `GET /api/v1/metrics` | System metrics |

### Swarm Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `executeSwarm(description, options)` | `POST /api/v1/swarm/execute` | Execute task |
| `planSwarm(description, options)` | `POST /api/v1/swarm/plan` | Get execution plan |

Modes: `single`, `swarm`, `consensus`

## Error Handling

```typescript
import { 
  JebatClient, 
  JebatError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
  ConnectionError,
} from '@jebat/sdk';

const client = new JebatClient();

try {
  const response = await client.chat('Hello');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.log('Invalid credentials');
  } else if (error instanceof RateLimitError) {
    console.log(`Rate limited, retry after ${error.retryAfter}s`);
  } else if (error instanceof NotFoundError) {
    console.log('Resource not found');
  } else if (error instanceof ValidationError) {
    console.log(`Validation failed: ${error.errors}`);
  } else if (error instanceof ServerError) {
    console.log('Server error, try again later');
  } else if (error instanceof ConnectionError) {
    console.log('Cannot connect to server');
  }
}
```

## Retry Configuration

```typescript
import { 
  retry, 
  calculateWaitTime, 
  DEFAULT_RETRY_CONFIG, 
  RetryPresets,
  withRetry 
} from '@jebat/sdk';

// Custom retry decorator
const customRetry = (config = {}) => withRetry(fn, { ...DEFAULT_RETRY_CONFIG, ...config });

// Or use built-in presets
import { quickRetry, standardRetry, aggressiveRetry } from '@jebat/sdk';

@standardRetry
async function myApiCall() {
  return client.chat('Hello');
}

@aggressiveRetry
async function criticalOperation() {
  return client.executeSwarm('Critical task');
}
```

## Development

```bash
# Install dev dependencies
npm install

# Run tests
npm test

# Type check
npm run typecheck

# Lint
npm run lint
npm run lint:fix

# Build
npm run build

# Generate docs
npm run docs
```

## License

MIT License - see LICENSE file for details.