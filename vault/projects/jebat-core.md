# jebat-core

**Status:** Active — live on VPS, workspace adapted
**Repo:** https://github.com/nusabyte-my/jebat-core
**Live:** https://jebat.online (Cloudflare → nginx → Docker)
**VPS:** root@72.62.254.65

## Stack
Python (FastAPI/uvicorn), Docker, SQLite (prod), Redis, nginx

## Active Roles
- Panglima
- Pembina Aplikasi
- Tukang
- Bendahara
- Hulubalang
- Syahbandar
- Penyemak
- Penganalisis
- Strategi Produk
- Khidmat Pelanggan

## Live Architecture (VPS)

```
jebat.online (Cloudflare → nginx)
├── /webui/   → 127.0.0.1:8787  (jebat-webui container)
├── /api/     → 127.0.0.1:8000  (jebat-api container)
└── /         → 302 /webui/
```

### Running Containers
- `jebat-api` — uvicorn on :8000, SQLite DB, healthy ✅
- `jebat-webui` — python webui server on :8787
- `jebat-redis` — Redis :6379

### Health Check
```
GET http://localhost:8000/api/v1/health
→ {"healthy":true,"database":true,"redis":true}
```

## Key Paths on VPS
- Source: `/root/jebat-core/`
- Prod compose: `/root/jebat-core/deploy/vps/docker-compose.prod.yml`
- Nginx: `/etc/nginx/sites-enabled/jebat.online`
- Data volume: `jebat_data` (Docker volume)

## Other Sites on Same VPS
- cashewcapital.my
- evolveplayboost
- wirasiber.my
- serambitiffin-web
- mailcow (full mail stack)

## Python Core Modules
- `jebat/services/api/jebat_api.py` — FastAPI app
- `jebat/services/webui/` — Web UI server + HTML pages
- `jebat/llm/` — LLM providers, auth, history
- `jebat/core/memory/` — Memory layers
- `jebat/integrations/channels/` — Telegram, Discord, WhatsApp, Slack
- `jebat/features/ultra_loop/` — Ultra loop worker
- `jebat/features/sentinel/` — Sentinel feature

## Next Steps
- [ ] Inspect webui HTML pages (`jebat/services/webui/*.html`)
- [ ] Check live config (`/root/jebat-core/jebat/config/config.yaml`)
- [ ] Review LLM provider setup
