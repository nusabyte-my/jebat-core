# 🚀 JEBAT - Complete Installation Guide

**Everything you need to get JEBAT running**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Installation (Docker)](#quick-installation-docker)
3. [Local Installation](#local-installation)
4. [Development Setup](#development-setup)
5. [Post-Installation](#post-installation)
6. [Troubleshooting](#troubleshooting)

---

## 🛠️ Prerequisites

### Required Software

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Python** | 3.11+ | Core runtime | [python.org](https://python.org) |
| **Docker** | 20.10+ | Containerization | [docker.com](https://docker.com) |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com) |

### Optional (for full features)

| Software | Version | Purpose |
|----------|---------|---------|
| **PostgreSQL** | 16+ | Database (included in Docker) |
| **Redis** | 7+ | Cache (included in Docker) |
| **Node.js** | 18+ | JavaScript SDK |

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Storage** | 10 GB | 20+ GB SSD |
| **OS** | Windows 10 / macOS 11 / Linux | Latest |

---

## ⚡ Quick Installation (Docker - Recommended)

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Minimum configuration needed:**

```bash
# Database (change password!)
DATABASE_URL=postgresql+asyncpg://jebat:your_secure_password@localhost:5432/jebat

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional: API keys for channels
TELEGRAM_BOT_TOKEN=your_token_here
WHATSAPP_ACCESS_TOKEN=your_token_here
DISCORD_BOT_TOKEN=your_token_here
```

### Step 3: Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Wait for services to start (30 seconds)
sleep 30

# Check status
docker-compose ps
```

**Expected output:**

```
NAME                    STATUS         PORTS
jebat-api              Up (healthy)   0.0.0.0:8000->8000/tcp
jebat-loop             Up             0.0.0.0:8001->8001/tcp
postgres               Up (healthy)   0.0.0.0:5432->5432/tcp
redis                  Up             0.0.0.0:6379->6379/tcp
grafana                Up             0.0.0.0:3000->3000/tcp
prometheus             Up             0.0.0.0:9090->9090/tcp
```

### Step 4: Verify Installation

```bash
# Test API health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status": "healthy", "version": "2.0.0"}
```

### Step 5: Access Web Interfaces

- **Landing Page**: Open `landing.html` in browser
- **API Docs**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## 💻 Local Installation (Without Docker)

### Step 1: Install Python Dependencies

```bash
# Clone repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install Database

#### Option A: PostgreSQL (Recommended)

```bash
# Install PostgreSQL 16+ with TimescaleDB
# Windows: Download from https://www.timescale.com/install
# macOS:
brew install timescaledb

# Create database
createdb jebat

# Initialize schema
python -m jebat.database.setup --init
```

#### Option B: SQLite (Development Only)

```bash
# SQLite is included with Python
# Update .env:
DATABASE_URL=sqlite+aiosqlite:///jebat.db
```

### Step 3: Install Redis

```bash
# Windows: Download from https://github.com/microsoftarchive/redis
# macOS:
brew install redis

# Start Redis
redis-server

# Test connection
redis-cli ping
# Expected: PONG
```

### Step 4: Configure Environment

```bash
# Copy and edit .env
cp .env.example .env

# Update database URL
# PostgreSQL:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jebat

# Or SQLite:
DATABASE_URL=sqlite+aiosqlite:///jebat.db
```

### Step 5: Start Services

```bash
# Start API server
python -m uvicorn jebat.services.api.jebat_api:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Ultra-Loop
python -m jebat.ultra_process_runner --loop --cycle-interval 1.0
```

---

## 👨‍💻 Development Setup

### Step 1: Clone & Install

```bash
# Clone repository
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Step 2: Install Development Tools

```bash
# Code formatting
pip install black isort

# Linting
pip install flake8 mypy pylint

# Testing
pip install pytest pytest-cov pytest-asyncio

# Documentation
pip install mkdocs mkdocs-material
```

### Step 3: Configure Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Enable hooks
pre-commit install
```

### Step 4: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=jebat --cov-report=html

# View coverage report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

### Step 5: Code Quality Checks

```bash
# Format code
black jebat/
isort jebat/

# Lint
flake8 jebat/
mypy jebat/

# Run all checks
python -m pytest tests/ -v --cov=jebat
```

---

## 🔧 Post-Installation

### 1. Initialize Database

```bash
# Run database migrations
python -m jebat.database.migrate

# Create default user (if needed)
python -m jebat.database.setup --create-default-user
```

### 2. Test Core Systems

```bash
# Run system tests
python tests/test_full_system.py

# Expected output:
# ✅ All systems operational
```

### 3. Try the Chatbot

```bash
# Standalone chatbot
python examples/chat/standalone_chatbot.py

# Interactive chatbot
python examples/chat/interactive_chatbot.py
```

### 4. Configure Channels (Optional)

#### Telegram Bot

```bash
# Get token from @BotFather on Telegram
# Add to .env:
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Start bot
python -m jebat.integrations.channels.telegram
```

#### Discord Bot

```bash
# Create bot at https://discord.com/developers/applications
# Add to .env:
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN

# Start bot
python -m jebat.integrations.channels.discord
```

### 5. Set Up Monitoring

```bash
# Access Grafana
start http://localhost:3000
# Username: admin
# Password: admin

# Import dashboard
# Go to Dashboards → Import
# Upload: monitoring/grafana-dashboard.json
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Services Won't Start

```bash
# Check Docker is running
docker ps

# Check Docker Compose
docker-compose version

# Restart services
docker-compose down
docker-compose up -d

# View logs
docker-compose logs jebat-api
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL is running
# Docker:
docker-compose ps postgres

# Local:
pg_isready -h localhost -p 5432

# Test connection
psql postgresql://user:pass@localhost:5432/jebat -c "SELECT 1"
```

#### 3. Redis Connection Failed

```bash
# Check Redis is running
# Docker:
docker-compose ps redis

# Local:
redis-cli ping

# Expected: PONG
```

#### 4. Port Already in Use

```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# macOS/Linux:
lsof -i :8000

# Kill process or change port in .env
API_PORT=8001
```

#### 5. Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.11+

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

#### 6. Permission Denied (Linux/macOS)

```bash
# Fix permissions
sudo chown -R $USER:$USER .

# Or run with sudo (not recommended)
sudo python setup.py
```

#### 7. Memory Issues

```bash
# Reduce Docker memory limit
# Edit docker-compose.yml:
services:
  jebat-api:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Getting Help

1. **Check Logs**
   ```bash
   docker-compose logs -f
   ```

2. **Run Diagnostics**
   ```bash
   python -m jebat.cli.launch status
   ```

3. **Check Documentation**
   - [USAGE_GUIDE.md](USAGE_GUIDE.md)
   - [QUICK_REFERENCE_CARD.md](QUICK_REFERENCE_CARD.md)

4. **Open Issue**
   - [GitHub Issues](https://github.com/nusabyte-my/jebat-core/issues)

---

## 📊 Installation Verification Checklist

- [ ] Docker installed and running
- [ ] Repository cloned successfully
- [ ] .env file created and configured
- [ ] Services started (`docker-compose ps`)
- [ ] API health check passed
- [ ] Database initialized
- [ ] Redis connected
- [ ] Chatbot runs successfully
- [ ] Web interfaces accessible
- [ ] Tests passing

---

## 🎯 Next Steps

After successful installation:

1. **Read the Docs**
   - [USAGE_GUIDE.md](USAGE_GUIDE.md) - Complete usage guide
   - [QUICKSTART_EXAMPLES.md](QUICKSTART_EXAMPLES.md) - Working examples

2. **Try Examples**
   ```bash
   python examples/chat/standalone_chatbot.py
   python examples/memory/memory_assistant.py
   ```

3. **Customize**
   - Edit `.env` for your needs
   - Configure channels (Telegram, Discord, etc.)
   - Set up monitoring in Grafana

4. **Deploy to Production**
   - See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Installation Complete!** 🎉

**JEBAT** - *Because warriors remember everything that matters.* 🗡️
