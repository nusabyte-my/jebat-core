# MEMORY.md

This file is the root memory index for the workspace.

## Current Operating Memory

- This repository should be treated as a JEBAT workspace with `jebat-core/` as the canonical operating center.
- Canonical startup begins from `jebat-core/BOOTSTRAP.md`.
- Codex sessions should also load `CODEX_PROFILE.md`.
- If duplicate docs exist at the root and in `jebat-core/`, prefer the `jebat-core/` copy unless the user explicitly directs otherwise.

## Active Projects

- **jebat-core** — canonical JEBAT operating center, VPS services, multi-agent model. Updated to upstream **v8.2.0** on 2026-07-14 (25 commits); reconciled local LLM provider changes (`llamacpp` + `tokenrouter`/`custom`), fixed upstream-shipped conflict markers in `.env.example` and `Dockerfile`.
- **ALAND (AlandFeasi)** — `C:\Users\shaid\Desktop\nusabyte\ALAND`. Property feasibility study platform. pnpm monorepo (client + server + shared + packages). Drizzle ORM. Reference models: boom.online, land.tech. Active from 2026-05-17. VPS deploy at `aland.nusabyte.cloud` (`72.62.254.65`, webroot `/var/www/aland.nusabyte.cloud`, pm2 `aland-api`). 2026-07-14: full-number formatting (no K/M/B abbreviations except `LiveSummary.tsx`), GDV/GDC table `whitespace-nowrap`, `deploy_to_vps.sh` hardened (LF + `chmod -R a+rX`), README VPS doc. GitHub Actions disabled (private repo, no billing) - direct-to-`main` workflow. See `memory/2026-07-14.md`.
- **Erawan-QSys** — `C:\Users\shaid\Desktop\nusabyte\Erawan-QSys`. Queue system for massage operations (QPOS). Next.js 15 + NestJS + Prisma/PostgreSQL monorepo. Branch: `erawanwellness`. **PRODUCTION** server: `72.60.42.163` (NOT `72.62.254.65`), domain `qpos.erawanwellness.com`. V2 checkout at `/opt/erawanQPOS-v2` (ports 4001/5501), nginx on 443. PM2: `erawan-api-v2` (id 7) + `erawan-web-v2` (id 6). Features: multi-guest booking flow (guestIndex on BookingItem), per-item actions, POS with pre-loaded cart, Gantt chart (09:00-22:00 working hours), room status with red occupied indicators + countdown timers, booking sort (pending→cancelled priority), commission tracking, payment (cash/card/e-wallet/pending). V1 legacy at `/opt/erawanQPOS` (ports 4000/5500). v2.1.0 UX overhaul (multi-guest booking, Gantt 09:00–22:00, red room-status, booking sort fix) shipped to prod 2026-07-13. All user passwords: `erawan2026`. See `memory/2026-07-13.md` for latest session log.
- **Serambi Tiffin** — `C:\Users\shaid\Desktop\nusabyte\serambi tiffin - web`. React 19 + Vite frontend, Express/TypeScript backend. Auth hardening applied 2026-05-07.
- **SkillPro** — `C:\Users\shaid\Desktop\nusabyte\SkillPro`. Domain `skillpro.my`. Malaysian freelancer/professional identity platform (v0-bootstrapped). Next.js 16 (App Router, port 4050) + React 19 + Tailwind 4 + shadcn + PostgreSQL (`@vercel/postgres` + `pg`) + NextAuth v5 (beta) + Drizzle-less raw SQL migrations in `db/migrations/` + Vitest. Repo: `github.com/nusabyte-my/SkillPro-WEB` (origin/main clean). Active phases: VPS deployment to 72.62.254.65, escrow + KYC modules already scaffolded under `lib/actions` and `lib/repositories`. See `REFACTOR_PLAN.md` and `DEPLOYMENT_GROWTH_PLAN.md`. Brand: green `#22C55E` + blue `#2563EB` + navy `#0F172A`.
- **Aether Energy** — `C:\Users\shaid\Desktop\Aether-Energy\Aether-energy-web`. AI-powered no-code oil trading platform for institutional traders. React 19 + Vite 7 + Tailwind CSS 4 + Express/TypeScript. pnpm monorepo (client/server/shared). Radix UI, framer-motion, recharts, wouter, zod. Design: "Elemental Precision" — dark slate with amber/gold accents. Registered 2026-06-15.
- **KenariCekal_Workforce** — `C:\Users\shaid\Desktop\nusabyte\KenariCekal_Workforce`. WorkforceOS — enterprise workforce attendance for Malaysian manpower agency (~200 staff, 24/7, two shifts/day, multiple sites). Phone-only GPS geofence (BLE/NFC/WiFi intentionally removed — do not reintroduce). NestJS 10 + TypeORM + PostgreSQL + Redis (backend :3000) / Vanilla JS PWA (served from NestJS, face enrollment + selfie liveness) / Next.js 16.2.9 + AntD 6 + Zustand + Leaflet (dashboard :5580). Phase 1 GPS MVP complete; Phase 2 pilot hardening not started. Build: backend typecheck clean, backend lint broken (ESLint 9 vs legacy .eslintrc.js), dashboard has 34 tsc errors. See `IMPROVEMENT_PLAN.md` for roadmap. Captured 2026-07-06.

## Session Notes

- Daily session records live in `memory/YYYY-MM-DD.md`.
- Dream consolidations live in `memory/.dream-YYYY-MM-DD.md`.

## Durable Decisions

- Architecture and operating decisions live in `jebat-core/vault/decisions/`.
- See `jebat-core/vault/decisions/2026-04-08-jebatcore-canonical-startup.md` for the accepted JEBATCore startup rule.
- See `jebat-core/vault/decisions/2026-04-16-llamacpp-jebat-llm-production-cutover.md` for the production `llama.cpp` cutover, VPS tuning, JEBAT chat preset routing, and the current `.65 -> .206` remote model-host topology.

## Current Production LLM Topology

- `72.62.254.65` is the public-facing JEBAT node for `jebat.online`.
- `72.62.255.206` is the stronger active `llama.cpp` model host for JEBAT chat.
- The live JEBAT stack on `.65` routes `LLAMA_CPP_HOST` to `.206` instead of using a local `.65` model process.
- `.206` exposes TCP `8081` only to `.65` for this path.
- The `.65 -> .206` remote `llama.cpp` route has been verified through the live OpenAI-compatible JEBAT chat endpoint with `provider: "llamacpp"`.
