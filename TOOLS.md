# TOOLS.md

## Local Runtime Notes

- Primary workspace: `/home/humm1ngb1rd/Desktop/Jebat Online/`
- Git remote: `https://github.com/nusabyte-my/jebat-core.git`
- State dir: `~/.openclaw`
- Gateway config: `~/.openclaw/openclaw.json`

## LLM Providers

| Provider | Endpoint | Models |
|----------|----------|--------|
| Ollama | `http://localhost:11434` | qwen2.5-coder:7b, hermes-sec-v2 |
| ZAI | `https://api.zai.network/v1` | glm-5, glm-4-plus |
| OpenAI | `https://api.openai.com/v1` | gpt-4o, gpt-4o-mini, o1 |
| Anthropic | `https://api.anthropic.com/v1` | claude-sonnet-4, claude-opus-4 |
| Gemini | `https://generativelanguage.googleapis.com/v1beta` | gemini-2.5-pro, gemini-2.0-flash |
| OpenRouter | `https://openrouter.ai/api/v1` | multi-model |

## Environment

- **OS:** CachyOS (Arch Linux)
- **Shell:** bash, fish
- **Runtime:** Node.js, Python 3.11+, Go, Docker, PostgreSQL 18
- **IDEs:** VS Code, Zed, Cursor

## Working Mode

- JEBAT is the main assistant identity
- Panglima is the primary capture-first operating mode
- Hermes remains a compatibility alias, not a separate core
- Workspace skills are the preferred way to add repeatable behaviors
- Claude Code is the primary interface for this workspace
- External IDEs and clients should use the adapter layer in `adapters/`

## jebat.online — Live Platform

- **URL:** https://jebat.online → nginx → Let's Encrypt SSL
- **Landing:** `/var/www/jebat.online/` (Next.js static export)
- **API:** http://localhost:8000 (`jebat-api`, healthy ✅)
- **WebUI:** http://localhost:8787 (`jebat-webui`, healthy ✅)
- **Gateway:** http://localhost:18789 (`sh4dow-gateway`)
- **Nginx:** `/etc/nginx/sites-enabled/jebat.online`
- **Routes:** `/` → static landing | `/api/` → :8000 | `/webui/` → :8787

## VPS — 72.62.254.65

- **Access:** `ssh root@72.62.254.65`
- **Source:** `/root/jebat-core/`
- **Other sites:** cashewcapital.my, evolveplayboost, wirasiber.my, mailcow stack
