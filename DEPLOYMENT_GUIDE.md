# 🗡️ JEBAT - Deployment Guide

**Version**: 1.0.0  
**Last Updated**: 2026-02-18  
**Status**: PRODUCTION READY  

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Automated Setup](#automated-setup)
4. [Manual Installation](#manual-installation)
5. [Docker Deployment](#docker-deployment)
6. [Production Deployment](#production-deployment)
7. [Configuration](#configuration)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 5-Minute Setup

```bash
# 1. Clone/navigate to JEBAT directory
cd Dev

# 2. Run automated setup
py setup.py --quick

# 3. Edit .env file with your API keys
notepad .env

# 4. Start services
docker-compose up -d

# 5. Check status
py -m jebat.cli.launch status
```

**Done!** JEBAT is running.

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Runtime |
| **PostgreSQL** | 16+ | Database |
| **Redis** | 7+ | Cache |
| **Git** | Latest | Version control |

### Optional (for Docker)

| Software | Version | Purpose |
|----------|---------|---------|
| **Docker** | 24+ | Containerization |
| **Docker Compose** | 2.0+ | Multi-container |

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disk** | 10 GB | 50+ GB SSD |
| **OS** | Windows 10/11, Linux, macOS | Linux (Ubuntu 22.04+) |

---

## Automated Setup

### Using setup.py

**Interactive Setup**:
```bash
py setup.py
```

**Quick Setup (defaults)**:
```bash
py setup.py --quick
```

**Check Requirements Only**:
```bash
py setup.py --check
```

**Initialize Database Only**:
```bash
py setup.py --init-db
```

### What setup.py Does

1. ✅ Checks Python version
2. ✅ Verifies required packages
3. ✅ Creates `.env` file
4. ✅ Creates config directory
5. ✅ Installs dependencies
6. ✅ Initializes database
7. ✅ Runs basic tests

### Post-Setup Steps

1. **Edit `.env` file**:
   ```bash
   notepad .env
   ```

2. **Add API keys**:
   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   TELEGRAM_BOT_TOKEN=123456:ABCdef...
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

---

## Manual Installation

### Step 1: Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database and user
CREATE DATABASE jebat_db;
CREATE USER jebat WITH PASSWORD 'jebat_password';
GRANT ALL PRIVILEGES ON DATABASE jebat_db TO jebat;

-- Enable extensions
\c jebat_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Step 3: Setup Redis

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### Step 4: Configure Environment

Create `.env` file:
```bash
# Copy example
copy .env.example .env

# Edit with your values
notepad .env
```

### Step 5: Initialize Database

```bash
# Initialize database tables
py -c "from jebat.database.models import init_db; import asyncio; asyncio.run(init_db())"
```

### Step 6: Verify Installation

```bash
# Check status
py -m jebat.cli.launch status

# Test thinking
py -m jebat.cli.launch think "What is AI?"
```

---

## Docker Deployment

### Quick Start with Docker

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Services Started

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| **API** | jebat-api | 8000 | FastAPI gateway |
| **Loop** | jebat-loop | - | Ultra-Loop worker |
| **PostgreSQL** | jebat-postgres | 5432 | Database |
| **Redis** | jebat-redis | 6379 | Cache |
| **Prometheus** | jebat-prometheus | 9090 | Metrics |
| **Grafana** | jebat-grafana | 3000 | Dashboard |

### Access Services

- **JEBAT CLI**: `py -m jebat.cli.launch status`
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Docker Commands

```bash
# View logs
docker-compose logs jebat-api
docker-compose logs -f jebat-loop

# Restart services
docker-compose restart jebat-api

# Rebuild containers
docker-compose build --no-cache

# Clean up
docker-compose down -v  # Removes volumes
```

---

## Production Deployment

### Environment Variables

```env
# Production settings
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=WARNING

# Database (use strong passwords!)
DATABASE_URL=postgresql+asyncpg://jebat:STRONG_PASSWORD@host:5432/jebat_db
REDIS_URL=redis://host:6379/0

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRY=3600
```

### Production Checklist

- [ ] Change all default passwords
- [ ] Set `APP_ENV=production`
- [ ] Disable debug mode
- [ ] Configure HTTPS/TLS
- [ ] Setup firewall rules
- [ ] Configure backup strategy
- [ ] Setup monitoring alerts
- [ ] Test disaster recovery

### Security Hardening

1. **Use secrets management**:
   ```bash
   # Docker secrets
   docker secret create jebat_db_password secret.txt
   ```

2. **Enable HTTPS**:
   ```yaml
   # In docker-compose.yml or reverse proxy
   labels:
     - "traefik.http.routers.jebat.tls=true"
   ```

3. **Restrict network access**:
   ```yaml
   networks:
     jebat-network:
       internal: true  # Only accessible within Docker network
   ```

---

## Configuration

### Environment Variables Reference

```env
# Application
APP_ENV=development|production
APP_DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_URL=redis://host:port/db

# Memory
M0_TTL=30s          # Sensory buffer
M1_TTL=24h          # Episodic
M2_TTL=7d           # Semantic
M3_TTL=90d          # Conceptual

# Agents
MAX_AGENTS=10
AGENT_TIMEOUT=300
MAX_RETRIES=3

# Search
SEARCH_TOP_K=10
RERANK_TOP_K=5
```

### Configuration Files

```
config/
├── settings.yaml      # Main configuration
├── agents.yaml        # Agent configurations
├── channels.yaml      # Channel configurations
└── logging.yaml       # Logging configuration
```

---

## Monitoring

### Prometheus Metrics

Access Prometheus: http://localhost:9090

**Available Metrics**:
- `jebat_loop_cycles_total` - Total Ultra-Loop cycles
- `jebat_loop_success_rate` - Cycle success rate
- `jebat_think_sessions_total` - Total thinking sessions
- `jebat_memory_stored_total` - Memories stored
- `jebat_agent_tasks_total` - Agent tasks executed

### Grafana Dashboards

Access Grafana: http://localhost:3000 (admin/admin)

**Pre-configured Dashboards**:
- System Overview
- Ultra-Loop Performance
- Memory Statistics
- Agent Activity
- Channel Metrics

### Alerts

Configure alerts in Grafana or Prometheus:

```yaml
# Example: High error rate alert
groups:
  - name: jebat-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(jebat_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
```

---

## Troubleshooting

### Common Issues

#### Database Connection Error

**Error**: `could not connect to database`

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### Redis Connection Error

**Error**: `Error connecting to Redis`

**Solution**:
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli ping
```

#### Import Errors

**Error**: `ModuleNotFoundError: No module named '...'`

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Clear Python cache
py -m py_compile jebat/**/*.py
```

#### CLI Not Working

**Error**: `ModuleNotFoundError` when running CLI

**Solution**:
```bash
# Clear __pycache__
Remove-Item -Recurse -Force jebat\__pycache__

# Test imports
py -c "from jebat import MemoryManager; print('OK')"
```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs jebat-api

# Follow logs
docker-compose logs -f jebat-loop

# Last 100 lines
docker-compose logs --tail=100 jebat-api
```

### Health Checks

```bash
# Check container health
docker-compose ps

# Check API health
curl http://localhost:8000/api/v1/health

# Check database
py -c "from jebat.database.models import engine; print('DB OK')"
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U jebat jebat_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U jebat jebat_db < backup.sql
```

### Redis Backup

```bash
# Backup Redis
docker-compose exec redis redis-cli SAVE

# Copy dump file
docker cp jebat-redis:/data/dump.rdb ./redis-backup.rdb
```

### Configuration Backup

```bash
# Backup .env and config
tar -czf jebat-config-backup.tar.gz .env config/
```

---

## Performance Tuning

### Database Optimization

```sql
-- Analyze tables
ANALYZE;

-- Vacuum tables
VACUUM;

-- Reindex
REINDEX DATABASE jebat_db;
```

### Memory Tuning

```env
# Increase connection pool
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Adjust cache TTLs
REDIS_CACHE_TTL=3600
```

### Ultra-Loop Tuning

```env
# Faster cycles (more CPU)
CYCLE_INTERVAL=0.5

# More concurrent agents
MAX_AGENTS=20
```

---

## Support

### Documentation

- **Quick Reference**: QUICK_REFERENCE.md
- **System Report**: SYSTEM_REPORT_COMPLETE.md
- **Roadmap**: ROADMAP.md
- **Master Index**: MASTER_INDEX.md

### Getting Help

1. Check troubleshooting section
2. Review logs
3. Check documentation
4. Open GitHub issue (future)

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: 2026-02-18  
**Status**: PRODUCTION READY  

🗡️ **JEBAT** - *Because warriors remember everything that matters.*
