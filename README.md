# JEBAT Online 🗡️

Self-hosted AI assistant platform with eternal memory, multi-agent orchestration, and integrated cybersecurity capabilities.

## What’s in this workspace

### Core identity
- `IDENTITY.md` — Jebat identity
- `USER.md` — humm1ngb1rd profile
- `MEMORY.md` — long-term curated memory
- `memory/2026-03-29.md` — session notes

### Imported / analyzed source
- `jebat-core/` — cloned source repo from <https://github.com/nusabyte-my/jebat-core.git>

### JEBAT skills for OpenClaw
- `skills/jebat-memory-skill/SKILL.md`
- `skills/jebat-consolidation-skill/SKILL.md`
- `skills/jebat-agent-orchestrator/SKILL.md`
- `skills/jebat-analyst/SKILL.md`
- `skills/jebat-researcher/SKILL.md`
- `skills/jebat-cybersecurity/SKILL.md`
- `skills/jebat-hardening/SKILL.md`
- `skills/jebat-pentesting/SKILL.md`

### Infra
- `database/schema.sql` — TimescaleDB schema
- `docker-compose.yml` — TimescaleDB + Redis stack
- `.env.example` — environment template
- `JEBAT_INTEGRATION_PLAN.md` — roadmap

## Architecture

```text
OpenClaw Gateway
  ├─ Multi-channel messaging
  ├─ Sessions / agents / cron
  └─ Tool execution
        │
        ▼
JEBAT Layer
  ├─ 5-layer memory (M0-M4)
  ├─ Heat-based consolidation
  ├─ Multi-agent orchestration
  ├─ Analyst / Researcher
  └─ Cybersecurity / Hardening / Pentesting
        │
        ▼
TimescaleDB + Redis
```

## Memory model
- **M0 Sensory** — 30s
- **M1 Episodic** — 24h
- **M2 Semantic** — 30d
- **M3 Conceptual** — permanent
- **M4 Procedural** — permanent

Heat score:
- 30% visit frequency
- 25% interaction depth
- 25% recency
- 15% cross-references
- 5% explicit rating

## Recommended stack
- Next.js 14
- TypeScript
- Tailwind CSS
- shadcn/ui
- TimescaleDB
- Redis
- OpenClaw Gateway

## Quick start

### 1. Copy env
```bash
cp .env.example .env
```

### 2. Start infra
```bash
docker compose up -d
```

### 3. Verify database
- PostgreSQL/TimescaleDB on `localhost:5432`
- Redis on `localhost:6379`
- PgAdmin on `localhost:5050` with `--profile dev`

### 4. Next platform step
Initialize the web platform:
```bash
npx create-next-app@latest jebat-online --ts --tailwind --app
```

## Priority implementation order
1. Wire memory skill to real DB
2. Add consolidation cron job
3. Add orchestrator runtime mapping to OpenClaw sessions
4. Build jebat.online frontend
5. Add dashboards and admin tooling
6. Add security workflows and reports

## Security split
- **Cybersecurity**: defensive scanning and audit
- **Hardening**: fix/configure systems securely
- **Pentesting**: authorized offensive validation only

## Notes
- Pentesting requires explicit authorization.
- Hardening changes should be staged and backed up.
- Memory backend is designed for DB-first operation, not plain files.
