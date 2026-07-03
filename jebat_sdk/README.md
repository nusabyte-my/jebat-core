# JEBAT Python SDK

Official Python SDK for the [JEBAT AI Assistant](https://github.com/humm1ngb1rd/jebat) REST API.

## Features

- **Sync & Async Clients** - Use `JebatClient` for sync or `AsyncJebatClient` for async code
- **Full Type Hints** - Complete Pydantic models for all API responses
- **Auto Retry** - Exponential backoff with configurable retry policies
- **Rate Limiting** - Automatic handling with `Retry-After` support
- **Streaming Support** - SSE and WebSocket streaming for chat
- **Authentication** - JWT tokens, refresh tokens, and API keys
- **Type Safe** - Built with Pydantic v2 for runtime validation

## Installation

```bash
pip install jebat-sdk
```

From source:
```bash
git clone https://github.com/humm1ngb1rd/jebat.git
cd jebat/jebat_sdk
pip install -e .
```

## Quick Start

### Synchronous Client

```python
from jebat_sdk import JebatClient

# Initialize client
client = JebatClient(base_url="http://localhost:8000")

# Login
token = client.login("username", "password")
print(f"Access token: {token.access_token[:20]}...")

# Chat (blocking)
response = client.chat("Hello, JEBAT!", mode="deliberate")
print(response.response)

# Chat with streaming
for chunk in client.chat_stream("Tell me a story"):
    print(chunk.content, end="", flush=True)

# Memories
memories = client.list_memories(query="python", layer="M2_SEMANTIC")
for mem in memories.memories:
    print(f"[{mem.layer}] {mem.content}")

# Agents
agents = client.list_agents()
for agent in agents.agents:
    print(f"{agent.name} ({agent.type}) - {agent.status}")

# API keys
key = client.create_api_key("My App", expires_in_days=30)
print(f"Key: {key.key}")  # Only shown once!

# Swarm execution
result = client.execute_swarm(
    "Build a REST API for user management",
    execution_mode="consensus",
    max_agents=5
)
print(result.result)

client.close()
```

### Async Client

```python
import asyncio
from jebat_sdk import AsyncJebatClient

async def main():
    async with AsyncJebatClient(base_url="http://localhost:8000") as client:
        await client.login("username", "password")

        # Streaming chat
        async for chunk in client.chat_stream("Hello, world!"):
            print(chunk.content, end="", flush=True)

        # Parallel requests
        tasks = [
            client.get_health(),
            client.get_status(),
            client.list_agents(),
        ]
        health, status, agents = await asyncio.gather(*tasks)

asyncio.run(main())
```

### WebSocket Streaming

```python
from jebat_sdk import JebatWebSocketClient

async def websocket_chat():
    async with JebatWebSocketClient(
        ws_url="ws://localhost:8000/ws/chat",
        token=access_token
    ) as ws:
        async for chunk in ws.stream({"message": "Hello!", "mode": "deep"}):
            if chunk.type == "content":
                print(chunk.content, end="", flush=True)
            elif chunk.is_final():
                break
```

## CLI Usage

```bash
# Install with CLI extras
pip install jebat-sdk[cli]

# Login
jebat login username password --url http://localhost:8000

# Chat
jebat chat "Hello JEBAT" --mode deliberate --stream

# List memories
jebat memories --query "python" --layer M2_SEMANTIC

# List agents
jebat agents

# Health check
jebat health

# Swarm execution
jebat swarm "Build a REST API" --mode consensus --max-agents 5

# API key management
jebat apikey_create "My App" --expires 30
jebat apikey_list
```

## Configuration

```python
# Custom base URL
client = JebatClient(base_url="https://api.jebat.example.com")

# Custom timeout
client = JebatClient(timeout=60.0)

# Pre-set token
client = JebatClient(base_url="...", token="your-access-token")

# Custom headers
client = JebatClient(headers={"X-Custom-Header": "value"})

# Connection pooling
client = JebatClient(limits=httpx.Limits(max_connections=50))
```

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `login(username, password)` | `POST /api/v1/auth/login` | Get access/refresh tokens |
| `refresh_token(refresh_token)` | `POST /api/v1/auth/refresh` | Get new access token |
| `logout(refresh_token)` | `POST /api/v1/auth/logout` | Revoke refresh token |

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_api_key(name, expires_in_days)` | `POST /api/v1/auth/api-keys` | Create new key |
| `list_api_keys()` | `GET /api/v1/auth/api-keys` | List user's keys |
| `revoke_api_key(prefix)` | `DELETE /api/v1/auth/api-keys/{prefix}` | Revoke key |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `chat(message, mode, user_id)` | `POST /api/v1/chat` | Blocking chat |
| `chat_stream(message, mode)` | `POST /api/v1/chat` (stream) | SSE streaming |
| `chat_websocket(message, mode)` | `WS /ws/chat` | WebSocket streaming |

Modes: `fast`, `deliberate`, `deep`, `strategic`, `creative`, `critical`

### Memories

| Method | Endpoint | Description |
|--------|----------|-------------|
| `list_memories(query, layer, limit)` | `GET /api/v1/memories` | List/search memories |
| `create_memory(content, user_id, layer)` | `POST /api/v1/memories` | Store memory |
| `search_memories(query, ...)` | `GET /api/v1/memories` | Search memories |

Layers: `M0_IMMEDIATE`, `M1_EPISODIC`, `M2_SEMANTIC`, `M3_PROCEDURAL`, `M4_STRATEGIC`

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `list_agents()` | `GET /api/v1/agents` | List all agents |
| `get_agent(agent_id)` | `GET /api/v1/agents/{id}` | Get agent info |
| `execute_agent(task, agent_id, mode)` | `POST /api/v1/agents/execute` | Execute agent |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_health()` | `GET /api/v1/health` | System health |
| `get_status()` | `GET /api/v1/status` | Detailed status |
| `get_metrics()` | `GET /api/v1/metrics` | System metrics |

### Swarm Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `execute_swarm(description, mode, ...)` | `POST /api/v1/swarm/execute` | Execute task |
| `plan_swarm(description, ...)` | `POST /api/v1/swarm/plan` | Get execution plan |

Modes: `single`, `swarm`, `consensus`

## Error Handling

```python
from jebat_sdk import JebatClient
from jebat_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConnectionError,
)

client = JebatClient()

try:
    response = client.chat("Hello")
except AuthenticationError:
    print("Invalid credentials")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except NotFoundError:
    print("Resource not found")
except ValidationError as e:
    print(f"Validation failed: {e.errors}")
except ServerError:
    print("Server error, try again later")
except ConnectionError:
    print("Cannot connect to server")
```

## Retry Configuration

```python
from jebat_sdk.retry import standard_retry, get_retry_decorator

# Custom retry decorator
custom_retry = get_retry_decorator(
    max_attempts=5,
    min_wait=2.0,
    max_wait=30.0,
    multiplier=2.0,
)

# Or use built-in decorators
from jebat_sdk.retry import quick_retry, standard_retry, aggressive_retry

@standard_retry
def my_api_call():
    return client.chat("Hello")

@aggressive_retry
def critical_operation():
    return client.execute_swarm("Critical task")
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/jebat_sdk

# Lint
ruff check .
black .

# Build
pip build
```

## License

MIT License - see LICENSE file for details.