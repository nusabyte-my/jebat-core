# MEMORY.md

This file is the root memory index for the workspace.

## Current Operating Memory

- This repository should be treated as a JEBAT workspace with `jebat-core/` as the canonical operating center.
- Canonical startup begins from `jebat-core/BOOTSTRAP.md`.
- Codex sessions should also load `CODEX_PROFILE.md`.
- If duplicate docs exist at the root and in `jebat-core/`, prefer the `jebat-core/` copy unless the user explicitly directs otherwise.

## Active Projects

- **jebat-core** — canonical JEBAT operating center, VPS services, multi-agent model. Updated to upstream **v8.2.0** on 2026-07-14 (25 commits); reconciled local LLM provider changes (`llamacpp` + `tokenrouter`/`custom`), fixed upstream-shipped conflict markers in `.env.example` and `Dockerfile`.
- **ALAND (AlandFeasi)** - `C:\Users\shaid\Desktop\nusabyte\ALAND`. Property feasibility study platform. pnpm monorepo (packages/frontend React+Vite+Tailwind, packages/backend Express+tRPC+Drizzle :3001, packages/shared feasibility engine). Reference models: boom.online, land.tech. Active from 2026-05-17. **VPS (current): `187.127.204.89`** (domain `alandfeasi.tech`; **IPv4:22 fail2ban-DROPped from dev box -> ssh/deploy via IPv6 `root@2a02:4780:5e:a100::1`**, key `~/.ssh/id_ed25519-hostinger`), webroot `/var/www/ALAND/packages/frontend/dist`, backend `/var/www/ALAND/packages/backend/dist` (pm2 `aland-backend` :3001), DB PostgreSQL 16 :5432. nginx listens on BOTH 80/443 + `[::]:80/443` (backup `/root/alandfeasi.nginx.bak-20260813`; keep OUT of sites-enabled or `nginx -t` fails). **2026-08-13: HIGH-RISE calculator workbook-exact vs `FS- High Rise (Tower & Podium Car Park) - Version2.xlsx`** - Development (density/plot-ratio/building-area/podium) + GDV + GDC B1-B11 + SUMMARY + Results all editable + parity-locked; engine locked to the cent via `engine-lock.test.ts` (landed GDC 406,279,824.92 / profit -41,812,074.92; HR GDC 193,146,807 / profit 31,895,393.38 / 14.17%). SW cache trap: bump `alandfeasi-vN` in `public/sw.js` per deploy + hard refresh. Deploy: `./deploy_to_vps.ps1` (Windows/pwsh only - .sh unusable on this box). **Legacy host `72.62.254.65` / `aland.nusabyte.cloud` / pm2 `aland-api` DECOMMISSIONED 2026-08-13** (commit `c8195e1`). Trunk-based git: branch off `main`, conventional commits, PR into protected `main`; remote `github.com/nusabyte-my/ALAND-Production.git`. 73 frontend / 59 backend tests green. See `memory/2026-08-13.md`. Older note (2026-07-14): full-number formatting (no K/M/B abbreviations except `LiveSummary.tsx`), GDV/GDC table `whitespace-nowrap`, GitHub Actions disabled (private repo, no billing) - direct-to-`main` workflow. See `memory/2026-07-14.md`.
- **Erawan-QSys** — `C:\Users\shaid\Desktop\nusabyte\Erawan-QSys`. Queue system for massage operations (QPOS). Next.js 14 + NestJS + Prisma/PostgreSQL monorepo. Branch: `erawanwellness`. **PRODUCTION** server (active V2): Hostinger **IPv6 `2a02:4780:5e:20bd::1`** (host `erawanhq`, ssh `-6 -i ~/.ssh/id_ed25519-hostinger opsadmin@...`), domain `qpos.erawanwellness.com`. Legacy `72.62.254.65` NOT production; `72.60.42.163` refused as of 2026-07-14. V2 checkout at `/opt/erawanQPOS-v2` (ports 4001/5501), nginx on 443, repo+pm2 root-owned (sudo git/pm2, `sudo -H -u root env PATH=$PATH pm2 ...`). PM2: `erawan-api-v2` + `erawan-web-v2`. DB: Docker postgres:16 `127.0.0.1:5433` (no local psql — `docker exec -i erawanqpos-postgres-1 psql -U erawan -d erawan_qsys`). Features: multi-guest booking flow (guestIndex on BookingItem), per-item actions, POS with pre-loaded cart, Gantt chart (09:00–22:00, `PX_PER_MIN=4`, block colors black/brown/yellow/red/blue), room status red/amber reserved indicators + countdown, booking sort, commission tracking, payments (cash/card/e-wallet/pending). Receipt branding (Iyara Mayuree) source: `apps/web/lib/receipt-branding.ts`; printed output mirrors modal via `printReceipt()` — thermal-safe float rows, logo 42px, copy bands DUPLICATE/MERCHANT COPY. Queue ranking ENFORCED from `packages/core/src/index.ts` (single source of truth; regression tests `packages/core/src/__tests__/queue.test.ts`). v2.x shipped to prod incl. Gantt complete→blue chain `33efcf1`/`fb2a3f4`/`7ce9c99`. All user passwords: `erawan2026`. See `memory/2026-08-06.md` + `.dream-2026-08-10.md`.
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

## Integration Stack (MCP + Skills)

- Full stack map + configs: `vault/integrations/mcp-skill-stack.md` (captured 2026-08-10).
- **opencode** `~/.config/opencode/opencode.json`: `context7`, `sequential-thinking`, `skills` (FastMCP 4 Skills Provider — venv `~/.config/opencode/venvs/skills-mcp`, server `mcps/skills-mcp/server.py`, 120 skills as `skill://` resources). Backup: `opencode.json.bak.stack-20260810`.
- **jebat runtime** `~/.jebat/config.yaml`: same 3 servers under `mcp:` (context7 needs `Accept: application/json, text/event-stream`; sequential-thinking uses `npx.cmd` + 60s cold-start timeout). Backup: `config.yaml.bak-20260810`. **Live-verified 2026-08-10** via jebat MCPClient: context7=2 tools, sequential-thinking=1 tool, skills=144 resources.
- **Fixes shipped 2026-08-10:** jebat CLI v7.5 crashed on Windows (`UnicodeEncodeError` cp1252 banner) — patched `D:\Jebat\jebat-core\jebat_cli_new\jebat.py` (stdio UTF-8 reconfigure at import); `jebat mcp serve` handshake verified. opencode `jebat` MCP entry now sets `PYTHONUTF8=1` env.
- `worldmonitor` added 2026-08-10, removed same day (user request). `skills` was initially the anthropics `npx skills` CLI, swapped for the gofastmcp FastMCP Skills Provider per user link.
- Reality check: cc-switch = desktop GUI (not MCP), lobehub = MCP client (not server), awesome-mcp-servers + awesome-claude-skills = catalogs (sources, not installs).

## Current Production LLM Topology

- `72.62.254.65` is the public-facing JEBAT node for `jebat.online`.
- `72.62.255.206` is the stronger active `llama.cpp` model host for JEBAT chat.
- The live JEBAT stack on `.65` routes `LLAMA_CPP_HOST` to `.206` instead of using a local `.65` model process.
- `.206` exposes TCP `8081` only to `.65` for this path.
- The `.65 -> .206` remote `llama.cpp` route has been verified through the live OpenAI-compatible JEBAT chat endpoint with `provider: "llamacpp"`.
