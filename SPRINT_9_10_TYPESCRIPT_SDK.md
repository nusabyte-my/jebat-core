# Q3 2026 Sprint 9-10: JavaScript/TypeScript SDK

## Objective
Create a production-ready TypeScript SDK for the JEBAT REST API that can be installed via `npm install @jebat/sdk`.

## Requirements
- TypeScript 5+ with strict mode
- ESM + CommonJS dual package exports
- Full type definitions for all API responses
- Sync and async patterns (fetch + WebSocket)
- Retry logic with exponential backoff
- WebSocket streaming support
- Comprehensive test coverage (Vitest)
- Published to npm

## Package Structure
```
packages/sdk/
├── package.json
├── tsconfig.json
├── README.md
├── CHANGELOG.md
├── src/
│   ├── index.ts
│   ├── client.ts
│   ├── async-client.ts
│   ├── websocket.ts
│   ├── models/
│   │   ├── index.ts
│   │   ├── auth.ts
│   │   ├── chat.ts
│   │   ├── memories.ts
│   │   ├── agents.ts
│   │   ├── channels.ts
│   │   ├── monitoring.ts
│   │   └── common.ts
│   ├── exceptions.ts
│   ├── retry.ts
│   └── types.ts
├── tests/
│   ├── client.test.ts
│   ├── async-client.test.ts
│   ├── websocket.test.ts
│   ├── models.test.ts
│   └── retry.test.ts
└── dist/ (generated)
```

## Sprint 9: Core Client & Models (Week 1)
- [ ] Project setup with package.json, tsconfig.json
- [ ] TypeScript interfaces for all API endpoints
- [ ] Base client with fetch + AbortController
- [ ] Auth helpers (login, refresh, API keys)
- [ ] Zod schemas for runtime validation

## Sprint 10: Async Client & Streaming (Week 2)
- [ ] Async client with fetch + WebSocket
- [ ] WebSocket support for streaming chat
- [ ] Retry logic with exponential backoff
- [ ] Comprehensive tests (Vitest)
- [ ] npm publishing workflow (GitHub Actions)