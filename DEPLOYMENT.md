# JEBAT Deployment Guide

## Prerequisites

- Docker 24+
- Docker Compose 2.20+
- 4GB+ RAM available
- 10GB+ disk space

## Quick Start (Local)

```bash
# 1. Clone and navigate
git clone <repo-url>
cd jebat-core

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Deploy
./scripts/deploy.sh local

# 4. Verify
curl http://localhost:8000/api/v1/health
# Open http://localhost:8501 for monitoring dashboard
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | Database user | `jebat` |
| `POSTGRES_PASSWORD` | Database password | **required** |
| `POSTGRES_DB` | Database name | `jebat` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `MONITORING_API_URL` | Internal API URL for dashboard | `http://localhost:8000` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | - |
| `JEBAT_SECRET_KEY` | JWT signing secret | **required** |

## Production Deployment

### Single Server (Docker Compose)

```bash
# Use production overlay
./scripts/deploy.sh production
```

### With Reverse Proxy (nginx)

Add to nginx config:
```nginx
server {
    listen 80;
    server_name jebat.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /monitoring/ {
        proxy_pass http://localhost:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Kubernetes (Future)

Helm charts planned for Q3 2026.

## Database Migrations

```bash
# Run migrations (if using Alembic)
docker compose exec jebat-api alembic upgrade head

# Or init fresh
docker compose exec jebat-api python -m jebat.database.init
```

## Backup & Restore

### PostgreSQL
```bash
# Backup
docker compose exec postgres pg_dump -U jebat jebat > backup_$(date +%F).sql

# Restore
docker compose exec -T postgres psql -U jebat jebat < backup_2026-06-15.sql
```

### Redis
```bash
# Backup (uses Redis persistence)
docker compose exec redis redis-cli BGSAVE
docker cp jebat-redis:/data/dump.rdb ./redis_backup_$(date +%F).rdb
```

## Monitoring

- **Dashboard**: http://localhost:8501
- **API Health**: http://localhost:8000/api/v1/health
- **Prometheus Metrics**: http://localhost:8000/metrics (if enabled)
- **Logs**: `docker compose logs -f jebat-api`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API unhealthy | Check `docker compose logs jebat-api` |
| DB connection failed | Verify PostgreSQL is healthy: `docker compose logs postgres` |
| Dashboard blank | Verify API is reachable: `curl http://jebat-api:8000/api/v1/monitoring/snapshot` |
| Out of memory | Increase Docker memory limit or reduce container limits |
| Port conflicts | Change ports in docker-compose.yml |

## Rollback

```bash
# Stop current
docker compose down

# Restore previous image tag
docker compose pull jebat-api:previous-tag

# Start
docker compose up -d
```

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Use strong `JEBAT_SECRET_KEY` (32+ random chars)
- [ ] Enable TLS via reverse proxy
- [ ] Restrict PostgreSQL/Redis to internal network only
- [ ] Regular security updates: `docker compose pull && docker compose up -d`
- [ ] Monitor logs for anomalies