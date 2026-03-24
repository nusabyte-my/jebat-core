# JEBAT Online Deploy

This is the minimal production path for hosting `jebat-core` on `jebat.online`.

## What Was Prepared

- VPS SSH alias on your machine: `~/.ssh/config`
- SSH key already present: `~/.ssh/id_ed25519_jebat`
- helper command: `jebat-vps-ssh`
- production deploy files in `deploy/vps/`

## Your Public Key

Add this key to the VPS user's `~/.ssh/authorized_keys`:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDHvMQEqlvVCh8zvRmeyqg3CaLLZv+9+0UQcALHhvCmO humm1ngb1rd@jebat
```

## Update SSH Alias

Current alias target:

- host: `72.62.254.65`
- user: `root`

Then connect with:

```bash
jebat-vps-ssh
```

## DNS

Point these DNS records to the VPS:

- `jebat.online`
- `www.jebat.online`

## Server Requirements

Install on the VPS:

- Docker
- Docker Compose plugin
- Git

## Deploy

On the VPS:

```bash
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
cp deploy/vps/.env.production.example .env.production
```

Fill in `.env.production`, then start:

```bash
bash deploy/vps/bootstrap.sh
```

## Stack

- `caddy` terminates HTTPS for `jebat.online`
- `jebat-api` serves the app on internal port `8000`
- `redis` supports runtime caching

## Notes

- This production path uses SQLite first to keep the VPS setup simple.
- The existing root `docker-compose.yml` is heavier and includes monitoring and Postgres. Use it later if needed.
- Caddy will obtain TLS automatically once DNS points to the VPS and ports `80/443` are open.
