# TOOLS.md

## Local Runtime Notes

- Primary workspace: `C:\Users\shaid\Desktop\jebatcore`
- State dir: `~/.jebat-gateway`
- Gateway config: `~/.jebat-gateway/jebat-gateway.json`
- Gateway service port: `18789`

## Model Routing (Jebat Gateway)

- Primary: Google Gemini Flash (`google-gemini-cli/gemini-3-flash-preview`)
- Fallbacks: Gemini Pro → ZAI GLM → Ollama Jebat Agent/Qwen/Llama
- In Claude Code: Claude Opus 4.6 (default), Sonnet 4.6 (1M context) available

## Environment

- OS: Windows 11 Pro
- Shell: bash (via Git Bash / Claude Code)
- Runtime tools: Node.js, Python 3.12/3.13, Go, Docker, PostgreSQL 18
- IDEs: VS Code, Zed, Cursor, Trae, Antigravity

## Working Mode

- `JEBATCore` is the main assistant identity
- Panglima is the primary capture-first operating mode
- Jebat Agent remains a compatibility alias, not a separate core
- Workspace skills are the preferred way to add repeatable behaviors
- Claude Code is the primary interface for this workspace
- External IDEs and clients should use the adapter layer in `adapters/`
- `npx jebatcore install` or `bunx jebatcore install` is the distribution entrypoint for workstation bootstrap
- `vault/OPERATING-SYSTEM.md` is the top-level map of the full operator stack
- Use `validate-workspace.ps1` for a lightweight structural validation pass
- Default operational playbooks live in `vault/playbooks/`
- Example filled artifacts live in `vault/examples/`
- Early client qualification should start from `vault/playbooks/discovery-call.md`
- Commercial scoping and proposal work should use `vault/playbooks/client-proposal.md`
- Sales collateral and outbound support work should use `vault/playbooks/sales-enablement.md`
- Ongoing client cadence and recurring work should use `vault/playbooks/retainer-ops.md`
- End-of-cycle reporting and next-period planning should use `vault/playbooks/monthly-review.md`
- Next-quarter prioritization and roadmap alignment should use `vault/playbooks/quarterly-planning.md`
- Renewal, upsell, and scope renegotiation should use `vault/playbooks/renewal-strategy.md`

## sh4dow.bot — Web Control UI

- **Repo:** https://github.com/nusabyte-my/sh4dow.bot
- **Type:** Single-page frontend control panel (Jebat Gateway-style 3-column layout)
- **Gateway:** `sh4dow-gateway` on port `18789`
- **Primary API:** `https://bot.sh4dow.tech/api` (Ollama endpoint)
- **Providers supported:**
  - Ollama → `https://bot.sh4dow.tech/api`
  - ZAI → `https://api.zai.network/v1`
  - OpenAI → `https://api.openai.com/v1`
  - Anthropic → `https://api.anthropic.com/v1`
  - Google Gemini → `https://generativelanguage.googleapis.com/v1beta`
  - OpenRouter → `https://openrouter.ai/api/v1`
- **Features:** Multi-provider chat, tool call badges, thinking indicator, channel management (Telegram etc.)
- **Design:** Dark theme, IBM Plex Mono + Inter, cyan accent `#00e5ff`
- **Local storage key:** `nexus_api_key`

## jebat.online — Live Platform

- **URL:** https://jebat.online → Cloudflare → nginx → Docker (VPS: 72.62.254.65)
- **API:** http://localhost:8000 (`jebat-api`, healthy ✅)
- **WebUI:** http://localhost:8787 (`jebat-webui`, healthy ✅)
- **Routes:** `/webui/` → :8787 | `/api/` → :8000 | `/` → 302 /webui/
- **WebUI Pages:** dashboard, ai_chat, ai_builder, code_assistant, ai_pentest, analytics, immersive_builder
- **Config:** `/root/jebat-core/jebat/config/config.yaml`
- **Features live:** ultra_loop, ultra_think, sentinel, 5-layer memory, multi-agent

## VPS — 72.62.254.65

- **Access:** `ssh root@72.62.254.65`
- **Source:** `/root/jebat-core/`
- **Prod compose:** `/root/jebat-core/deploy/vps/docker-compose.prod.yml`
- **Nginx:** `/etc/nginx/sites-enabled/jebat.online`
- **Other sites:** cashewcapital.my, evolveplayboost, wirasiber.my, mailcow stack

## Agent Aliases (Jebat Gateway)

- `JEBAT Core` → zai/glm-5
- `JEBAT Builder` → ollama/qwen2.5-coder:7b
- `JEBAT Security` → ollama/hermes-sec-v2
- `JEBAT Research` → standard reasoning model
- `JEBAT Google` → gemini-3.1-pro-preview
- `JEBAT Google Fast` → gemini-3-flash-preview
