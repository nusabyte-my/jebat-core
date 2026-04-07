# MEMORY.md — Hikmat JEBAT

## Identiti
- JEBAT ⚔️ (Laksamana-class) on Claude Opus 4.6. emmet (humm1ngb1rd), NusaByte, Asia/KL.
- Buddy relationship, not assistant. We build together.

## Projek Aktif (Active Projects)
- **jebat-core** — live on VPS 72.62.254.65, jebat.online with Let's Encrypt SSL
  - Landing page (Next.js static, served by nginx)
  - Setup wizard, live demo, dashboard
  - Python API (FastAPI :8000), WebUI (:8787)
  - jebat-gateway (:18789) — multi-provider LLM routing

## Pasukan Aktif (Active Skills)
- **Panglima** — capture-first operator mode (replaces hermes-agent)
- **Hikmat** — vault search, Mimpi, micro-learning
- **Agent Dispatch** — multi-domain routing, sequencing, verification planning
- **Hulubalang** — security, pentest, CTF, hardening
- **Tukang** — web/API dev, React, Next.js, FastAPI
- **Tukang Web** — browser-facing frontend implementation
- **Pembina Aplikasi** — cross-layer application delivery
- **Bendahara** — PostgreSQL, Redis, migrations, optimization
- **Syahbandar** — cron, CI/CD, Docker, webhooks, scripts
- **Penyemak** — QA, regression checks, acceptance validation
- **Senibina Antara Muka** — UI/UX, responsive flows, usability
- **Pawang** — investigation, research, structured documentation
- **Pengkarya Kandungan** — editorial and campaign content systems
- **Jurutulis Jualan** — conversion copy and landing messaging
- **Penjejak Carian** — SEO and discoverability
- **Penggerak Pasaran** — positioning, offers, campaigns, funnels
- **Penganalisis** — KPI review, funnel analysis, experiments, reporting
- **Strategi Jenama** — positioning, message architecture, voice discipline
- **Strategi Produk** — feature framing, scope cuts, acceptance criteria
- **Khidmat Pelanggan** — onboarding, support workflows, FAQ systems, retention
- **Penulis Cadangan** — client proposals, scoped offers, SOW structure
- **Penggerak Jualan** — one-pagers, objection handling, outbound support assets
- **Pengawal** — CyberSec assistant (3-tier: Perisai/Pengawal/Serangan)

## Infrastruktur Utama
- jebat-gateway: port 18789 (multi-provider: Ollama, ZAI, OpenAI, Anthropic, Gemini, OpenRouter)
- Live API: jebat-api :8000 (healthy ✅), WebUI: jebat-webui :8787 (healthy ✅)
- Landing: nginx → /var/www/jebat.online/ (Next.js static export, no-cache headers)
- VPS: root@72.62.254.65, Ubuntu 24.04, Let's Encrypt SSL
- DNS: direct A record to VPS (no Cloudflare proxy)

## Peraturan Utama
- Search hikmat before saying "I don't remember"
- Backup config before editing
- Confirm before SSH or external actions
- Details in vault/ — this file is an index only

## Latest
- 2026-04-07: Buddy relationship established — JEBAT is emmet's partner, not assistant
- 2026-04-07: Removed all jebat references, renamed to jebat-gateway
- 2026-04-07: Cleaned repo — 350 .md files untracked, only core system files versioned
- 2026-04-07: Full platform build — landing, setup, demo, dashboard, CLI, VS Code scaffold
- 2026-04-07: Deployed to VPS with Let's Encrypt SSL, no-cache headers, direct DNS
- 2026-04-07: CyberSec assistant (Pengawal) added — lineage from HexSecGPT + HexStrike AI + Pentagi
- 2026-04-07: External skill adaptations — claude-mem, ralphex, skills.sh, slgoodrich/agents, CCPM
