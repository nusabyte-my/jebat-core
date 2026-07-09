# Q2 2026 Execution Plan — Infrastructure & Polish

**Start Date**: 2026-06-15 (today)  
**Target Completion**: 2026-06-30 (2 weeks, ~10 working days)  
**Team**: Single developer (you) — sequential sprints, no parallel tracks  
**Philosophy**: Ship working increments daily. No "research spikes" — build, verify, move on.

---

## Sprint Overview

| Sprint | Focus | Days | Deliverable |
|--------|-------|------|-------------|
| **Sprint 1** | Monitoring Dashboard | 3 | Live metrics UI + FastAPI `/api/v1/metrics` + TimescaleDB |
| **Sprint 2** | Docker Deployment | 2 | `docker-compose.yml` + multi-stage Dockerfile + one-command deploy |
| **Sprint 3** | CI/CD Pipeline | 2 | GitHub Actions: lint → test → build → deploy → monitor |
| **Sprint 4** | WhatsApp Channel | 2 | Business API integration: send/receive, media, groups |
| **Sprint 5** | Discord Channel | 1 | Bot with slash commands, embeds, thread support |

**Total**: 10 working days (2 weeks)  
**Buffer**: 0 days — if a sprint overruns, the next slips. No scope creep.

---

## Explicit DON'T-DO List (Scope Guard)

- ❌ No Grafana/Prometheus — use lightweight stack: **TimescaleDB + FastAPI + React/Streamlit**
- ❌ No ELK/Loki — structured JSON logs to **stdout + file rotation**, search via `grep`/`jq`
- ❌ No Kubernetes — single-host Docker Compose only
- ❌ No Baileys/WhatsApp Web — **WhatsApp Business API only** (official, supported)
- ❌ No self-hosted runner — GitHub Actions hosted runners only
- ❌ No mobile apps, no web UI, no plugin system, no multi-tenancy — **Q3+ only**
- ❌ No comprehensive test expansion — **happy-path integration tests only** for new code

---

## Sprint 1: Monitoring Dashboard (3 days)

### Day 1 — Backend & Storage
**Goal**: FastAPI `/api/v1/metrics` writing to TimescaleDB, polling Ultra-Loop/Ultra-Think/agents/channels

**Tasks**:
1. Add `jebat/monitoring/` package:
   - `models.py` — SQLAlchemy + Timescale hypertable: `SystemMetric(ts, component, metric_name, value, labels_jsonb)`
   - `collector.py` — Background task: every 5s, call `get_stats()` on each subsystem, upsert metrics
   - `api.py` — FastAPI router: `GET /api/v1/metrics?component=&since=&limit=`
2. Wire into `jebat/main.py` (or wherever app lifecycle lives): start collector on startup
3. Add `timescaledb` to `requirements.txt` / `pyproject.toml`
4. **Verify**: `curl localhost:8000/api/v1/metrics` returns JSON with recent data points

**Acceptance**: Metrics persist across restarts; <100ms query latency for last 1 hour

### Day 2 — Frontend (Streamlit for speed)
**Goal**: Live-updating dashboard in <500 lines

**Tasks**:
1. `monitoring/dashboard/` — Streamlit app:
   - Auto-refresh every 2s (`st_autorefresh`)
   - Tabs: System, Ultra-Loop, Ultra-Think, Memory, Agents, Channels
   - Charts: `st.line_chart` / `st.area_chart` (native, zero deps)
   - Tables: `st.dataframe` for current values
2. Config: `MONITORING_API_URL` env var (default `http://localhost:8000`)
3. **Verify**: Open `http://localhost:8501` — see live charts updating

**Acceptance**: Dashboard loads <2s; charts update smoothly; mobile viewport usable

### Day 3 — Polish & Integration
**Goal**: Production-ready monitoring subsystem

**Tasks**:
1. Add health endpoint: `GET /api/v1/health` → `{status, uptime, components{}}`
2. Log rotation: `logging.handlers.RotatingFileHandler` (10MB × 5 files)
3. Structured JSON logs: `python-json-logger` → stdout
4. Update `ROADMAP.md`: check off Monitoring Dashboard items
5. **Verify**: Run full stack (API + collector + dashboard) for 10 min — no leaks, no errors

**Definition of Done**: Dashboard runs standalone via `python -m jebat.monitoring.dashboard`; API serves metrics; data survives container restart

---

## Sprint 2: Docker Deployment (2 days)

### Day 4 — Dockerfile + Compose
**Goal**: Single `docker compose up -d` brings up entire stack

**Files**:
```
Dockerfile                          # Multi-stage: builder → runtime (python:3.11-slim)
docker-compose.yml                  # Services below
.env.example                        # Template for required env vars
```

**Services** (`docker-compose.yml`):
```yaml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment: {POSTGRES_DB: jebat, POSTGRES_USER: jebat, POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}}
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck: ["CMD-SHELL", "pg_isready -U jebat -d jebat"]

  redis:
    image: redis:7-alpine
    healthcheck: ["CMD", "redis-cli", "ping"]

  jebat-api:
    build: .
    command: ["uvicorn", "jebat.main:app", "--host", "0.0.0.0", "--port", "8000"]
    depends_on: [postgres, redis]
    environment: [DATABASE_URL, REDIS_URL, *all JEBAT_* vars]
    ports: ["8000:8000"]
    healthcheck: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]

  jebat-loop:
    build: .
    command: ["python", "-m", "jebat.ultra_loop.runner"]
    depends_on: [postgres, redis]
    environment: [DATABASE_URL, REDIS_URL, *all JEBAT_* vars]
    deploy: {resources: {limits: {cpus: "2", memory: "2G"}}}

  monitoring:
    build: .
    command: ["streamlit", "run", "jebat/monitoring/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    depends_on: [jebat-api]
    ports: ["8501:8501"]
    environment: [MONITORING_API_URL=http://jebat-api:8000]

volumes: {postgres_data:}
```

**Verify**: `docker compose up -d` → all 5 containers healthy → dashboard at `localhost:8501`

### Day 5 — Production Hardening
**Tasks**:
1. `.dockerignore` — exclude `.git`, `__pycache__`, `.pytest_cache`, `*.pyc`, `tests/`, `docs/`, `.env`
2. Non-root user in Dockerfile (`USER 1000:1000`)
3. Read-only root filesystem where possible
4. Resource limits on all services (CPU/memory)
5. `docker-compose.prod.yml` overlay: no port binds except 8000/8501, logging driver `json-file` with max-size
6. **Deploy script**: `scripts/deploy.sh` — pulls latest image, runs migrations, health-checks, rolls back on failure
7. Document: `DEPLOYMENT.md` — one-page guide

**Definition of Done**: Clean deploy on fresh VM in <5 min; `docker compose logs -f` shows structured JSON; `docker compose down -v` + `up` restores state

---

## Sprint 3: CI/CD Pipeline (2 days)

### Day 6 — GitHub Actions Workflow
**File**: `.github/workflows/ci.yml`

```yaml
name: CI/CD
on: {push: {branches: [main]}, pull_request: {branches: [main]}}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv pip install -e .[dev]
      - run: uvx ruff check .
      - run: uvx mypy --strict jebat/

  test:
    runs-on: ubuntu-latest
    services:
      postgres: {image: timescale/timescaledb:latest-pg16, env: {POSTGRES_PASSWORD: test}, ports: [5432:5432], options: > --health-cmd="pg_isready" --health-interval=10s --health-timeout=5s --health-retries=5}
      redis: {image: redis:7-alpine, ports: [6379:6379], options: --health-cmd="redis-cli ping" --health-interval=10s --health-timeout=5s --health-retries=5}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv pip install -e .[test]
      - run: uvx pytest -x -q --tb=short
      - uses: codecov/codecov-action@v4

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: {registry: ghcr.io, username: ${{github.actor}}, password: ${{secrets.GHCR_TOKEN}}}
      - uses: docker/build-push-action@v5
        with: {context: ., push: true, tags: ghcr.io/${{github.repository}}:latest, cache-from: type=gha, cache-to: type=gha,mode=max}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: appleboy/ssh-action@master
        with:
          host: ${{secrets.DEPLOY_HOST}}
          username: ${{secrets.DEPLOY_USER}}
          key: ${{secrets.DEPLOY_KEY}}
          script: |
            cd /opt/jebat
            docker compose pull
            docker compose up -d --remove-orphans
            sleep 10
            curl -f http://localhost:8000/api/v1/health || (docker compose logs --tail=50 && exit 1)
```

**Secrets needed** (GitHub repo settings): `GHCR_TOKEN`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY`, `POSTGRES_PASSWORD`, all `JEBAT_*` vars

### Day 7 — Verify Pipeline
**Tasks**:
1. Push to `main` → watch full pipeline
2. Fix any flaky tests / missing deps
3. Add status badge to `README.md`
4. Document: `CI_CD.md` — pipeline diagram, required secrets, manual rollback procedure

**Definition of Done**: Green checkmark on `main`; auto-deploy works; rollback documented and tested

---

## Sprint 4: WhatsApp Channel (2 days)

### Day 8 — WhatsApp Business API Client
**Goal**: Minimal wrapper around Meta's Cloud API

**Files**:
- `jebat/channels/whatsapp.py` — `WhatsAppChannel` class implementing `Channel` interface
- `jebat/channels/__init__.py` — export

**Features**:
- Webhook verification (`GET /webhook/whatsapp` with `hub.challenge`)
- Receive: text, image, document, location, contacts → normalize to `ChannelMessage`
- Send: text, media (upload → send), template messages
- Session management: 24h customer care window tracking
- Error handling: rate limits, expired tokens, webhook retries

**Config** (env):
```
WHATSAPP_VERIFY_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_WEBHOOK_URL=https://yourdomain.com/webhook/whatsapp
```

**Verify**: `curl -X POST` to webhook → message appears in JEBAT logs; `channel.send()` delivers to test number

### Day 9 — Integration & Testing
**Tasks**:
1. Register channel in channel registry / router
2. Add to `docker-compose.yml` (shares `jebat-api` port, separate webhook path)
3. Test end-to-end: user → WhatsApp → JEBAT → reply → WhatsApp
4. Media: send image → receive image → verify download
5. Group chat: basic support (recognize `from` as group JID)
6. Update `ROADMAP.md` — check off WhatsApp items

**Definition of Done**: Full conversation loop works; media round-trips; webhook survives container restart

---

## Sprint 5: Discord Channel (1 day)

### Day 10 — Discord Bot
**Goal**: Slash commands + embed responses + thread support

**Files**:
- `jebat/channels/discord.py` — `DiscordChannel` using `discord.py` (app_commands)

**Features**:
- Slash commands: `/jebat chat <prompt>`, `/jebat memory <query>`, `/jebat status`
- Embed responses: title, description, fields (memory results, agent steps)
- Thread support: create thread per conversation for context
- Server-specific settings: allowed channels, default model, memory scope
- Webhook fallback for long responses (>2000 chars)

**Config** (env):
```
DISCORD_BOT_TOKEN=...
DISCORD_APP_ID=...
DISCORD_PUBLIC_KEY=...  # for interaction verification
```

**Verify**: Invite bot to test server → `/jebat chat hello` → embed response in thread

**Definition of Done**: Bot responds to slash commands; embeds render correctly; threads maintain context; multi-server isolation works

---

## Daily Ritual (Non-Negotiable)

| Time | Activity |
|------|----------|
| **Start of day** | `git pull` → review yesterday's commit → run `pytest -x -q` |
| **During** | Commit every 60-90 min with conventional message (`feat:`, `fix:`, `chore:`) |
| **End of day** | `git push` → verify CI green → update `tasks/todo.md` + `tasks/lessons.md` |

---

## Success Criteria (Q2 Gate)

| Metric | Target | Verification |
|--------|--------|--------------|
| Monitoring dashboard | Live, <2s load, 2s refresh | Manual + `curl` health |
| Docker deploy | `docker compose up -d` → all healthy <3 min | Fresh VM test |
| CI/CD | Green on main, auto-deploy <10 min | GitHub Actions log |
| WhatsApp | Send/receive text + media + groups | Manual E2E test |
| Discord | Slash commands + embeds + threads | Manual E2E test |
| Zero regressions | All existing tests pass | `pytest -x -q` |

---

## Next Phase (Q3) — Not In Scope

- ✅ Web UI (Next.js 14)
- ✅ REST API (OpenAPI, JWT, rate limiting)
- ✅ Python/JS SDKs
- ✅ Multi-tenancy (row-level security)

**Decision point**: After Q2 gate, review velocity and decide Q3 staffing.

---

## Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|------------|
| WhatsApp Business API approval delay | High | Apply **today**; use test number in meantime |
| TimescaleDB migration complexity | Medium | Start with vanilla Postgres + manual hypertable; migrate later |
| Discord.py async conflicts with FastAPI | Low | Run bot in separate process (already in compose) |
| CI/CD secret management | Medium | Use GitHub Environments + required reviewers for `deploy` job |

---

**Status**: READY TO EXECUTE  
**Next Action**: Start Sprint 1 Day 1 — create `jebat/monitoring/` package

---

*Generated: 2026-06-15 | Owner: humm1ngb1rd | Review: Daily standup with self*