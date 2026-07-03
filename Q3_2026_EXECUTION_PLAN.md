# Q3 2026 Execution Plan — User Experience & Scale

**Start Date**: 2026-06-15 (immediately after Q2)  
**Target Completion**: 2026-09-30 (12 weeks, ~60 working days)  
**Team**: Single developer (you) — sequential sprints  
**Philosophy**: Ship working increments. Web UI first, then API hardening, then multi-tenancy.

---

## Sprint Overview

| Sprint | Focus | Weeks | Deliverable |
|--------|-------|-------|-------------|
| **Sprint 1-4** | Web UI (Next.js 14) | 4 | Chat + Memory browser + Agent config + Settings |
| **Sprint 5-6** | REST API Hardening | 2 | JWT auth, rate limiting, OpenAPI docs |
| **Sprint 7-8** | Python SDK | 2 | `pip install jebat-sdk` with async client |
| **Sprint 9-10** | JavaScript SDK | 2 | `npm install @jebat/sdk` with TypeScript |
| **Sprint 11-12** | Multi-Tenancy | 2 | Row-level security, quotas, tenant isolation |

**Total**: 12 weeks (~60 working days)  
**Buffer**: 2 weeks for integration/polish

---

## Explicit DON'T-DO List (Scope Guard)

- ❌ No mobile apps — Q4+
- ❌ No plugin system — Q4+
- ❌ No advanced analytics — Q4
- ❌ No federated learning — 2027
- ❌ No custom WebSocket server — use existing FastAPI WebSocket
- ❌ No separate auth service — JWT in API gateway

---

## Sprint 1-4: Web UI (Next.js 14) — 4 weeks

> **Stack**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Zustand + React Query + WebSocket

### Week 1: Foundation & Chat Interface
**Goal**: Running Next.js app with chat page connected to API

**Tasks**:
1. Create `webui/` directory at repo root
2. `pnpm init` + install: `next@14 react@18 react-dom@18 typescript tailwindcss @radix-ui/* zustand @tanstack/react-query ws`
3. Configure: `tsconfig.json`, `tailwind.config.ts`, `next.config.js`
4. App Router structure: `app/(dashboard)/layout.tsx`, `app/(dashboard)/page.tsx` (chat)
5. API client: `lib/api.ts` — fetch wrapper with auth, WebSocket hook
6. Chat components: `MessageList`, `MessageInput`, `ThinkingIndicator`
7. Connect to `POST /api/v1/chat/completions` (or `/api/v1/chat`)
8. **Verify**: `pnpm dev` → localhost:3000 shows chat, sends message, gets response

### Week 2: Memory Browser & Real-time Updates
**Goal**: Memory page with search + live updates via WebSocket

**Tasks**:
1. Page: `app/(dashboard)/memories/page.tsx`
2. Components: `MemoryTable` (search, filter by layer, pagination), `MemoryDetail` modal
3. Connect: `GET/POST /api/v1/memories`
4. WebSocket: `useWebSocket` hook → subscribe to `memory.created`, `memory.updated`
5. Toast notifications for new memories
6. **Verify**: Create memory via API → appears in browser without refresh

### Week 3: Agent Configuration & Settings
**Goal**: Agent management + system settings pages

**Tasks**:
1. Page: `app/(dashboard)/agents/page.tsx` — list agents, show stats, enable/disable
2. Connect: `GET /api/v1/agents`, `POST /api/v1/agents/:id/execute`
3. Page: `app/(dashboard)/settings/page.tsx` — API keys, model selection, channel config
4. Connect: `GET/PUT /api/v1/settings` (new endpoint)
5. Form components with validation (react-hook-form + zod)
6. **Verify**: Toggle agent → status updates; change model → persists

### Week 4: Polish & Channels Page
**Goal**: Channel config page + responsive polish + deployable build

**Tasks**:
1. Page: `app/(dashboard)/channels/page.tsx` — Telegram/WhatsApp/Discord status, webhook URLs
2. Connect: channel status from `/api/v1/status` or new `/api/v1/channels`
3. Dark mode (next-themes) + responsive breakpoints
4. Error boundaries + loading skeletons
5. Build: `pnpm build` → `pnpm start` → production works
6. Dockerize: Add `webui` service to `docker-compose.yml`
7. **Verify**: Full app works in Docker stack

---

## Sprint 5-6: REST API Hardening — 2 weeks

> **Goal**: Production-ready `/api/v1` with auth, rate limiting, docs

### Week 5: Authentication & Rate Limiting
**Tasks**:
1. Add `jebat.auth` module: JWT creation/validation, API key hashing
2. Dependency: `python-jose[cryptography]`, `slowapi` (rate limiting)
3. Middleware: `auth_middleware.py` — verify JWT or API key on protected routes
4. Rate limiter: `slowapi` + Redis backend — 100 req/min default, configurable per tier
5. Login endpoint: `POST /api/v1/auth/login` → returns JWT (for web UI)
6. API key management: `POST/GET/DELETE /api/v1/api-keys`
7. **Verify**: `curl -H "Authorization: Bearer <token>" /api/v1/memories` works; rate limit triggers 429

### Week 6: OpenAPI Docs & Validation
**Tasks**:
1. FastAPI auto-docs: ensure all models have `example` fields
2. Custom OpenAPI: add security schemes (Bearer, APIKey)
3. Request validation: Pydantic v2 with `ConfigDict(extra='forbid')`
4. Error handling: unified `ErrorResponse` model, exception handlers
5. Health checks: `/api/v1/health` → detailed component status
6. CORS: configurable origins via env
7. **Verify**: `/api/docs` shows complete spec; invalid requests return 422 with details

---

## Sprint 7-8: Python SDK — 2 weeks

> **Package**: `jebat-sdk` on PyPI

### Week 7: Core Client
**Tasks**:
1. Create `sdk/python/` with `pyproject.toml` (hatch/poetry)
2. `src/jebat_sdk/client.py` — `AsyncJebatClient` with `httpx.AsyncClient`
3. Methods: `chat()`, `memories.list()`, `memories.create()`, `agents.list()`, `agents.execute()`
4. Auth: `JebatClient(api_key="...")` or `JebatClient(jwt="...")`
5. Streaming: `async for chunk in client.chat_stream(...):`
6. Retries: `tenacity` with exponential backoff
7. Types: Full Pydantic models for request/response
8. **Verify**: `pip install -e .` → script works against local API

### Week 8: Polish & Publish
**Tasks**:
1. Sync client: `JebatClient` (blocking) for scripts
2. Context manager: `async with JebatClient(...) as client:`
3. Pagination helpers: `client.memories.iter_pages()`
4. README + examples + CHANGELOG
5. GitHub Action: build → test → publish to PyPI on tag
6. Version: `0.1.0`
7. **Verify**: `pip install jebat-sdk` from test PyPI → works

---

## Sprint 9-10: JavaScript/TypeScript SDK — 2 weeks

> **Package**: `@jebat/sdk` on npm

### Week 9: Core Client
**Tasks**:
1. Create `sdk/javascript/` with `package.json` (TypeScript, ES modules)
2. `src/client.ts` — `JebatClient` with `fetch` + `AbortController`
3. Methods mirror Python SDK
4. Streaming: `for await (const chunk of client.chatStream(...))`
5. Zod schemas for runtime validation
6. **Verify**: `npm link` → works in Next.js app

### Week 10: React Hooks & Publish
**Tasks**:
1. React hooks: `useChat()`, `useMemories()`, `useAgents()` (React Query integration)
2. SSR-safe: `createClient()` for server components
3. Bundle size optimization: `esbuild` → ESM + CJS
4. README + examples + docs site (typedoc)
5. GitHub Action: build → test → publish to npm on tag
6. Version: `0.1.0`
7. **Verify**: `npm install @jebat/sdk` → works in fresh Next.js project

---

## Sprint 11-12: Multi-Tenancy — 2 weeks

> **Goal**: Isolated tenants with quotas, row-level security

### Week 11: Database & Middleware
**Tasks**:
1. PostgreSQL RLS policies: `CREATE POLICY tenant_isolation ON memories USING (tenant_id = current_setting('app.current_tenant'))`
2. Migration: add `tenant_id` to all user-facing tables (memories, agents, conversations, api_keys, etc.)
3. Tenant model: `id, name, slug, settings_json, quota_limits_json, created_at`
4. Middleware: extract tenant from JWT claim `tenant_id` or subdomain/header
5. Context variable: `SET LOCAL app.current_tenant = '...'` per request
6. Quota enforcement: middleware checks `memories_used_this_month < quota`
7. **Verify**: Two tenants → cannot see each other's memories; quota blocks overage

### Week 12: Admin API & Polish
**Tasks**:
1. Admin endpoints: `POST/GET/PUT/DELETE /api/v1/admin/tenants` (superuser only)
2. Tenant self-service: `GET/PUT /api/v1/tenant/me` (settings, usage stats)
3. Invitation flow: `POST /api/v1/admin/tenants/:id/invite` → email with signup link
4. Usage dashboard: `/api/v1/admin/usage` — per-tenant metrics
5. Update Web UI: tenant switcher (if multi-tenant mode enabled)
6. **Verify**: Create tenant → invite user → user signs up → isolated data

---

## Daily Ritual (Non-Negotiable)

| Time | Activity |
|------|----------|
| **Start** | `git pull` → `pnpm test` / `pytest -x` |
| **During** | Commit every 60-90 min (conventional commits) |
| **End** | `git push` → CI green → update `tasks/todo.md` + `tasks/lessons.md` |

---

## Success Criteria (Q3 Gate)

| Metric | Target | Verification |
|--------|--------|--------------|
| Web UI | Chat + Memories + Agents + Settings + Channels | Manual E2E in Docker |
| REST API | JWT auth + rate limiting + OpenAPI docs | `/api/docs` complete; 429 on abuse |
| Python SDK | `pip install jebat-sdk` → async/sync clients | Script against local API |
| JS SDK | `npm i @jebat/sdk` → React hooks | Works in Next.js app |
| Multi-tenancy | 2 tenants isolated + quotas enforced | Automated test |

---

## Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Next.js learning curve | Medium | Start with `create-next-app` template; use shadcn/ui blocks |
| WebSocket scaling | Low | Single-process first; Redis pub/sub later |
| RLS performance | Low | Add indexes; `EXPLAIN ANALYZE` |
| SDK API drift | Medium | Generate types from OpenAPI spec (`openapi-typescript`) |

---

## Next Phase (Q4) — Not In Scope

- ✅ Mobile apps (React Native / Flutter)
- ✅ Plugin system (dynamic loading)
- ✅ Advanced analytics (Superset/Metabase)
- ✅ Voice integration (Whisper + TTS)

---

**Status**: READY TO EXECUTE  
**Next Action**: Start Sprint 1 Week 1 — Create `webui/` with Next.js 14 foundation

---

*Generated: 2026-06-15 | Owner: humm1ngb1rd | Review: Daily*