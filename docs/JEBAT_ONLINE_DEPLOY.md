# JEBAT Online Deploy

This is the minimal production path for hosting `jebat-core` on `jebat.online`.

## What Was Prepared

- VPS SSH alias on your machine: `~/.ssh/config`
- SSH key already present: `~/.ssh/id_ed25519_jebat`
- helper command: `jebat-vps-ssh`
- production deploy files in `deploy/vps/`
- nginx site template: `deploy/vps/nginx.jebat.online.conf`

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
cp deploy/vps/.env.production.example deploy/vps/.env.production
```

Fill in `deploy/vps/.env.production`, then start:

```bash
bash deploy/vps/bootstrap.sh
```

## Stack

- `jebat-webui` serves on `127.0.0.1:8787`
- `jebat-api` serves on `127.0.0.1:8000`
- `redis` supports runtime caching
- existing VPS `nginx` should front `jebat.online`

## Nginx

Install the provided site config on the VPS:

```bash
cp deploy/vps/nginx.jebat.online.conf /etc/nginx/sites-available/jebat.online
ln -sf /etc/nginx/sites-available/jebat.online /etc/nginx/sites-enabled/jebat.online
nginx -t
systemctl reload nginx
```

## Notes

- This production path uses SQLite first to keep the VPS setup simple.
- The existing root `docker-compose.yml` is heavier and includes monitoring and Postgres. Use it later if needed.
- This VPS already has Nginx listening on `80/443`, so JEBAT should integrate behind Nginx instead of binding those ports directly.
