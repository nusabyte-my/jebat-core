# Changelog

All notable changes to the JEBAT Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-15

### Added
- Initial release of JEBAT Python SDK
- Synchronous client (`JebatClient`) with full API coverage
- Asynchronous client (`AsyncJebatClient`) with full async/await support
- WebSocket streaming client (`JebatWebSocketClient`) for real-time chat
- Complete Pydantic models for all API endpoints:
  - Authentication (login, refresh, logout, API keys)
  - Chat (blocking, SSE streaming, WebSocket)
  - Memories (CRUD, search, layers)
  - Agents (list, execute, capabilities)
  - Channels (Telegram, Discord, WhatsApp)
  - Monitoring (health, status, metrics)
  - Swarm orchestration (execute, plan)
- Retry logic with exponential backoff (tenacity)
- Rate limiting handling with `Retry-After` support
- Structured exceptions mapping HTTP status codes
- CLI with Typer for common operations
- Full type hints with Pydantic v2 models
- Comprehensive test structure ready

### SDK Features
- **Sync Client**: `JebatClient` for synchronous code
- **Async Client**: `AsyncJebatClient` with full async/await
- **WebSocket**: `JebatWebSocketClient` for real-time streaming
- **CLI**: `jebat` command for common operations
- **Models**: 30+ Pydantic models with full validation
- **Retry**: Configurable exponential backoff with tenacity
- **Rate Limiting**: Automatic handling with headers
- **Authentication**: JWT + API keys with argon2
- **Streaming**: SSE and WebSocket chat streaming
- **Type Safety**: Complete type hints with Pydantic v2

### CLI Commands
- `jebat login` - Authenticate and get tokens
- `jebat chat` - Send chat messages (with --stream)
- `jebat memories` - Search/list memories
- `jebat agents` - List agents
- `jebat health` - Check API health
- `jebat swarm` - Execute swarm tasks
- `jebat apikey_create` / `apikey_list` - API key management