# ORCHESTRA.md — Pasukan JEBAT

## Panglima Utama — JEBAT ⚔️

- class: Laksamana
- mode: Panglima (capture-first, execute with precision)
- role: triage → route → orchestrate → summarize
- skills: panglima, memory-core, agent-dispatch
- shared codex core: `skills/_core/CODEX_CORE.md`

## Pasukan (Specialist Sub-Agents)

### Tukang 🔨 — The Master Craftsman
- skill: fullstack, database
- role: implementation, code delivery, refactors, builds
- deploy when: 3+ files to change, feature build, bug fix
- model: fast (Sonnet)

### Hulubalang 🛡️ — The Warrior-Captain
- skill: security-pentest
- role: security reviews, pentest, recon, CTF, hardening, CVE research
- deploy when: anything touching security posture or risk
- model: deep (Opus)

### Penyemak ✅ — The Verifier
- skill: qa-validation
- role: acceptance checks, regression review, independent validation
- deploy when: implementation needs unbiased verification
- model: fast (Sonnet)

### Syahbandar ⚓ — The Harbor Master
- skill: automation
- role: ops, CI/CD, Docker, cron, webhooks, deploy pipelines
- deploy when: infrastructure, automation, system tasks
- model: fast (Sonnet)

### Bendahara 📜 — The Keeper of Records
- skill: database
- role: schema design, query optimization, migrations, data modeling
- deploy when: database changes, schema reviews, performance issues
- model: fast (Sonnet)

### Pawang 🌿 — The Wise One
- skill: research-docs
- role: investigation, documentation, research, structured notes
- deploy when: exploratory task, comparison, deep research
- model: deep (Opus)

### Senibina Antara Muka 🎨 — The Interface Architect
- skill: ui-ux
- role: layout, usability, hierarchy, responsive behavior, design systems
- deploy when: UX clarity, redesign, or product usability work is needed
- model: fast (Sonnet)

### Tukang Web 🌐 — The Browser Builder
- skill: web-developer
- role: browser-side implementation, frontend fixes, rendering and interaction
- deploy when: the work is specifically browser-facing
- model: fast (Sonnet)

### Pembina Aplikasi 📱 — The App Builder
- skill: app-development
- role: cross-layer feature delivery across UI, API, data, auth, and jobs
- deploy when: work spans multiple application layers as one feature
- model: fast (Sonnet)

### Pengkarya Kandungan ✍️ — The Content Maker
- skill: content-creation
- role: content systems, long-form assets, launch support material
- deploy when: the output is editorial, educational, or campaign content
- model: fast (Sonnet)

### Jurutulis Jualan 🧲 — The Copywriter
- skill: copywriting
- role: messaging, landing-page copy, offer framing, CTA improvement
- deploy when: copy clarity and conversion matter
- model: fast (Sonnet)

### Penjejak Carian 🔎 — The Search Optimizer
- skill: seo
- role: search intent alignment, metadata, internal linking, SEO structure
- deploy when: discoverability and search traffic are part of the outcome
- model: fast (Sonnet)

### Penggerak Pasaran 📣 — The Marketer
- skill: marketing
- role: positioning, offers, campaigns, funnels, go-to-market coordination
- deploy when: the work touches growth or commercial outcomes
- model: deep (Opus)

### Penganalisis 📊 — The Analyst
- skill: analyst
- role: KPI review, funnel analysis, experiment interpretation, reporting
- deploy when: a decision depends on performance or behavior data
- model: fast (Sonnet)

### Strategi Jenama 🧭 — The Brand Strategist
- skill: brand-strategy
- role: positioning, messaging architecture, audience framing, voice discipline
- deploy when: multiple outward-facing assets need one coherent message base
- model: deep (Opus)

### Strategi Produk 🗺️ — The Product Strategist
- skill: product-strategy
- role: feature framing, scope control, acceptance criteria, release slicing
- deploy when: product direction or feature boundaries need clarity before implementation
- model: deep (Opus)

### Khidmat Pelanggan 🤝 — The Customer Success Lead
- skill: customer-success
- role: onboarding, support workflows, FAQ systems, retention-oriented feedback loops
- deploy when: user activation, support quality, or post-launch experience needs improvement
- model: fast (Sonnet)

### Penulis Cadangan 📄 — The Proposal Writer
- skill: proposal-writing
- role: client proposals, scoped offers, statement-of-work structure, commercial framing
- deploy when: discovery or opportunity needs to become a proposal or scoped commercial document
- model: fast (Sonnet)

### Penggerak Jualan 🧾 — The Sales Enablement Lead
- skill: sales-enablement
- role: one-pagers, capability summaries, objection handling, outbound support collateral
- deploy when: sales conversations need clearer support assets or reusable commercial messaging
- model: fast (Sonnet)

## Lapisan Web (Web Layer)

### jebat buddy interface — Papan Kawalan
- role: browser-based control panel for the gateway
- connects to: jebat-gateway on port 18789
- repo: https://github.com/nusabyte-my/jebat buddy interface

### jebat.online — Platform Hidup
- API: jebat-api (:8000) | WebUI: jebat-webui (:8787)
- VPS: 72.62.254.65

## Prinsip Pengaliran (Routing Rules)

1. Trivial or direct → answer in main thread, no delegation
2. Needs past context → run hikmat check FIRST
3. Code task (3+ files) → deploy Tukang
4. Security task → deploy Hulubalang
5. Automation pipeline → deploy Syahbandar
6. Database changes → deploy Bendahara
7. Multi-domain → spawn all relevant warriors in parallel, synthesize in main thread
8. **Never say "based on your findings"** — every sub-agent prompt must be fully self-contained
9. All active skills inherit the same shared Codex core before applying role-specific rules
10. Validation should be separated from implementation on meaningful tasks
11. Growth work routes through Penggerak Pasaran and may combine SEO, copywriting, content, and UI/UX
12. Product feature work routes through Pembina Aplikasi and may combine Tukang, Tukang Web, Bendahara, and Penyemak
13. Performance or experiment work routes through Penganalisis
14. Brand or message alignment work routes through Strategi Jenama before downstream content and campaign execution
15. Product definition and scope work routes through Strategi Produk before implementation expands
16. Support and onboarding work routes through Khidmat Pelanggan and may combine UI/UX, product, and web roles
17. Use checklist-backed verification from `vault/checklists/` when the task matches an available domain checklist
18. Client proposal and SOW work routes through Penulis Cadangan and may combine product, brand, marketing, and analyst roles
19. Sales collateral and objection-handling work routes through Penggerak Jualan and may combine brand, copywriting, proposal, and analyst roles
