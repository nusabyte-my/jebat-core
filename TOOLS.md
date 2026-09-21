# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## SSH Hosts

### Serambi Tiffin VPS (production)
- **Host:** `root@72.62.254.65`
- **Key:** `~/.ssh/id_ed25519-hostinger` (already in `~/.ssh/config` as Host `72.62.254.65`)
- **Path:** `/var/www/serambitiffin-web`
- **PM2:** `serambi-api` (id 17)
- **Note:** Site is behind Cloudflare (`serambitiffin.my` → Cloudflare IPs). SSH to `.65` may time out from some networks — if so, use alternative path or check VPN/local firewall.

### ALAND
- **Host:** `187.127.204.89` (SSH alias `jebatvps`, key `~/.ssh/id_ed25519-hostinger`)
- **Domain:** `alandfeasi.tech`
- **Webroot:** `/var/www/ALAND/packages/frontend/dist/`
- **Backend:** `/var/www/ALAND/packages/backend/dist/` (pm2 `aland-backend`, port 3001)
- **DB:** PostgreSQL 16 (native, port 5432)

### Erawan QPOS (PRODUCTION)
- **Host:** IPv6 `2a02:4780:5e:20bd::1` (Hostinger)
- **User:** `opsadmin` or `root`
- **SSH alias:** `erawan` (see `~/.ssh/config`)
- **Domain:** `qpos.erawanwellness.com`
- **Note:** IPv4 port 22 is firewalled — IPv6 only. `.65` is legacy/non-prod for Erawan.

### EvolvePlayBoost (prod)
- **Host:** root@72.62.254.65, path `/var/www/evolveplayboost` (git checkout of evolvepayboost-web.git, remote = origin)
- **Backend:** pm2 `evolve-backend` = `npm run server` (tsx server/server.ts) :5001 — MUST start WITHOUT NODE_ENV=production (validateConfig footgun: demands plain STRIPE_SECRET_KEY; .env only has _TEST/_LIVE). ecosystem.config.cjs in repo is a trap for restarts.
- **Frontend:** nginx serves dist/ (build on-box via deploy-to-vps.sh flow: pull → pnpm install → prisma generate → build w/ old-chunk retention → pm2 restart evolve-backend only). NOT behind Cloudflare (direct DNS).
- **nginx vhost:** /etc/nginx/sites-enabled/evolveplayboost — `/uploads/` must keep `^~` (asset regex would otherwise win). DIVERGES from repo nginx/ copy (repo copy is stale/simplified).
- **DB:** local PG `evolveplayboost` (postgres user, localhost:5432). Prisma migrations applied by hand + tracked in _prisma_migrations.
### JEBAT VPS (.206 Mainframe — Production)
- **Host:** `root@72.62.255.206` (SSH alias `72.62.255.206`, `jebat-vps`, key `~/.ssh/id_ed25519-hostinger`)
- **Path:** `/var/www/jebat-core`
- **Services (PM2):** `jebat-api` (:8000), `jebat-webui` (:8787)
- **Local AI:** `llama-server` (:8081, systemd `llama-cpp-jebat`), `ollama` (:11434)
- **Nginx:** `/etc/nginx/sites-available/jebat` -> `/etc/nginx/sites-enabled/jebat`

### Public Gateway (.65 VPS)
- **Host:** `root@72.62.254.65` (Cloudflare-facing reverse proxy & SkillPro/Serambi host)
- **Tunnels:** `jebat-upstream-tunnel.service` forwards :8000 and :8787 to `72.62.255.206`
- **Public URLs:** `https://jebat.online` (Landing), `https://jebat.online/api/` (API), `https://jebat.online/webui/` (WebUI)
