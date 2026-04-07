# MEMORY.md — Hikmat JEBAT

## Identiti
- JEBAT ⚔️ (Laksamana-class) on Claude Opus 4.6. emmet (humm1ngb1rd), NusaByte, Asia/KL.

## Projek Aktif (Active Projects)
- **jebat-core** — live on VPS 72.62.254.65, jebat.online with Let's Encrypt SSL
- **sh4dow.bot** — web control UI, single-page, gateway on port 18789

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
- Gateway: sh4dow-gateway on port 18789
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
- 2026-04-07: Full platform build complete — landing page, setup wizard, demo, dashboard, CLI rebrand, VS Code extension scaffold
- 2026-04-07: Deployed to VPS with Let's Encrypt SSL, no-cache headers, direct DNS
- 2026-04-07: CyberSec assistant (Pengawal) added — lineage from HexSecGPT + HexStrike AI + Pentagi
- 2026-04-07: External skill adaptations — claude-mem, ralphex, skills.sh, slgoodrich/agents, CCPM
- 2026-04-07: Cleaned repo — 350 .md files untracked, only core system files versioned
