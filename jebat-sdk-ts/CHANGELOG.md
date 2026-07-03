# Changelog

All notable changes to the JEBAT TypeScript SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-15

### Added
- Initial release of JEBAT TypeScript SDK
- **Sync Client** (`JebatClient`) with full API coverage
- **Async Client** (`AsyncJebatClient`) with full async/await support
- **WebSocket Client** (`JebatWebSocketClient`) for real-time streaming
- **Core HTTP Client** (`HttpClient`) with retry logic
- Complete TypeScript interfaces for all API endpoints:
  - Authentication (login, refresh, logout, API keys)
  - Chat (blocking, SSE streaming, WebSocket)
  - Memories (CRUD, search, layers)
  - Agents (list, execute, capabilities)
  - Channels (Telegram, Discord, WhatsApp)
  - Monitoring (health, status, metrics)
  - Swarm orchestration (execute, plan)
- Retry logic with exponential backoff and jitter
- Rate limiting handling with `Retry-After` support
- Structured exceptions mapping HTTP status codes:
  - `AuthenticationError` (401)
  - `TokenExpiredError` / `TokenInvalidError` (401)
  - `PermissionDeniedError` (403)
  - `NotFoundError` (404)
  - `ValidationError` (422)
  - `RateLimitError` (429) with `retryAfter`
  - `ServerError` (5xx)
  - `TimeoutError` (408)
  - `ConnectionError` (network)
- Zod schemas for runtime validation
- Comprehensive test suite (16 tests passing)
- Dual package exports (ESM + CommonJS)
- Full type definitions (`.d.ts` files)

### SDK Features
- **Sync Client**: `JebatClient` for synchronous code
- **Async Client**: `AsyncJebatClient` with full async/await
- **WebSocket**: `JebatWebSocketClient` for real-time streaming
- **Retry**: Configurable exponential backoff with tenacity
- **Rate Limiting**: Automatic handling with headers
- **Authentication**: JWT (argon2) + API keys
- **Streaming**: SSE and WebSocket chat streaming
- **Type Safety**: Complete type hints with TypeScript 5+ strict mode

### Type Definitions
- Error codes enum (`ErrorCode`)
- Thinking modes, Memory layers, Swarm execution modes
- Pagination, Error details, Timestamp mixins
- Full model types (40+ interfaces)

### CLI & Utilities
- Built-in retry decorator (`withRetry`)
- Pre-configured retry presets (quick, standard, aggressive, rateLimitAware)
- `mapHttpError` for automatic error mapping
- `isRetryableError` for custom retry logic