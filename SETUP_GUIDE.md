# JEBAT Workstation Setup Guide

This guide will help you set up a complete development environment for JEBAT on your Windows laptop, including:
- WSL with Kali Linux
- Docker for containerization
- PostgreSQL and MongoDB databases
- Full-stack development environment

## ⚠️ Prerequisites

1. Windows 10 version 2004+ (Build 19041+) or Windows 11
2. Administrative privileges on your laptop
3. Internet connection for downloading packages
4. At least 8GB RAM (16GB recommended), 20GB+ free disk space

## Step 1: Enable WSL and Install Kali Linux

### 1.1 Enable WSL Virtual Machine Feature

Open PowerShell **as Administrator** and run:

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

### 1.2 Set WSL 2 as Default Version

```powershell
wsl --set-default-version 2
```

### 1.3 Download and Install Kali Linux

1. Open Microsoft Store
2. Search for "Kali Linux"
3. Select "Kali Linux" by Offensive Security
4. Click "Get" or "Install"

### 1.4 Launch Kali Linux and Complete Setup

1. Launch Kali Linux from Start menu
2. Wait for installation to complete
3. Create a UNIX username and password when prompted
4. Update Kali Linux packages:

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.5 Install Essential Tools in Kali

```bash
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ufw \
    fail2ban \
    python3-pip \
    npm
```

## Step 2: Install Docker

### Option 2A: Docker Desktop for Windows (Recommended for beginners)

1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Run the installer
3. During installation:
   - ✅ Enable WSL 2 integration
   - ✅ Use the WSL 2 based engine
   - Select your Kali Linux distro for integration
4. Restart when prompted
5. Launch Docker Desktop and sign in (free account required)

### Option 2B: Docker Engine in Kali Linux (More control)

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker Engine
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker  # Apply group membership immediately
```

Verify installation:
```bash
docker run hello-world
docker --version
docker compose version
```

## Step 3: Set Up Databases

### Option 3A: Using Docker Containers (Recommended for isolation)

Create a `docker-compose.yml` file in your project directory:

```yaml
version: '3.8'

services:
  # PostgreSQL for JEBAT Memory System
  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: jebat-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: jebat
      POSTGRES_USER: jebat_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-jebat_secure_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jebat_user -d jebat"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MongoDB for flexible document storage
  mongodb:
    image: mongo:6
    container_name: jebat-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: jebat_user
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-mongodb_secure_password}
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching and session storage
  redis:
    image: redis:7-alpine
    container_name: jebat-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redis_secure_password}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
```

Then run:
```bash
docker compose up -d
```

Verify databases are running:
```bash
docker compose ps
```

### Option 3B: Direct Installation in Kali Linux

#### PostgreSQL:
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create JEBAT database and user
sudo -u postgres psql -c "CREATE USER jebat_user WITH PASSWORD 'jebat_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE jebat OWNER jebat_user;"
sudo -u postgres psql -d jebat -f /path/to/jebat-online/database/schema.sql
```

#### MongoDB:
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Redis:
```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
# Configure password in /etc/redis/redis.conf if needed
```

## Step 4: Set Up Full-Stack Development Environment

### 4.1 Backend Setup (Node.js)

In your WSL Kali Linux:

```bash
# Install Node.js (LTS version)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version

# Install Yarn (optional but recommended)
npm install -g yarn
```

### 4.2 Frontend Setup

```bash
# Install development tools
sudo apt install -y \
    build-essential \
    python3 \
    make \
    g++

# For Next.js development (will be used in jebat-online)
```

### 4.3 IDE/Editor Recommendations

1. **VS Code** (Recommended):
   - Download: https://code.visualstudio.com/
   - Install WSL extension for seamless Linux development
   - Recommended extensions:
     - ESLint
     - Prettier
     - Tailwind CSS IntelliSense
     - PostgreSQL
     - MongoDB for VS Code
     - Docker

2. **Alternative**: Use Vim/Neovim in Kali Linux with appropriate plugins

### 4.4 Initialize JEBAT Online Frontend

If you haven't already set up the Next.js app:

```bash
# Navigate to your workspace
cd /mnt/c/Users/humm1ngb1rd/Desktop/Jebat Online

# Create Next.js app with TypeScript and Tailwind
npx create-next-app@latest jebat-online --ts --tailwind --app
# Or if you already have it:
cd jebat-online
npm install
```

### 4.5 Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` to set your passwords:
```
POSTGRES_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password
# Add other passwords as needed
```

## Step 5: Verify Complete Setup

### 5.1 Check All Services

```bash
# Check Docker containers (if using Docker)
docker compose ps

# Or check services directly
sudo systemctl status postgresql mongod redis
# or
service postgresql status
service mongod status
service redis-server status
```

### 5.2 Test Database Connections

#### PostgreSQL:
```bash
psql -h localhost -U jebat_user -d jebat -c "SELECT version();"
```

#### MongoDB:
```bash
mongosh "mongodb://jebat_user:your_mongo_password@localhost:27017/jebat" --eval "db.runCommand({ connectionStatus: 1 })"
```

#### Redis:
```bash
redis-cli -a your_redis_password ping
```

### 5.3 Test Full Stack

```bash
# In jebat-online directory
npm run dev
# Should start Next.js development server on http://localhost:3000
```

## Step 6: Optional Security Enhancements

### 6.1 Configure UFW Firewall (in Kali)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 5432/tcp   # PostgreSQL
sudo ufw allow 27017/tcp  # MongoDB
sudo ufw allow 6379/tcp   # Redis
sudo ufw allow 3000/tcp   # Next.js dev
sudo ufw enable
```

### 6.2 Create SSH Keys for GitHub/GitLab
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add to your GitHub/GitLab account
```

### 6.3 Install Additional Security Tools
```bash
sudo apt install -y \
    lynis \
    rkhunter \
    chkrootkit \
    nmap \
    netcat \
    sqlmap \
    hydra \
    john
```

## Step 7: Maintenance and Updates

### 7.1 Regular Updates
```bash
# Update Kali Linux
sudo apt update && sudo apt full-upgrade -y

# Update Docker (if installed via apt)
sudo apt update && sudo apt upgrade -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Update Node.js
npm install -g n
sudo n lts
```

### 7.2 Backup Strategy
```bash
# Backup PostgreSQL
pg_dump -U jebat_user -d jebat > jebat_backup_$(date +%Y%m%d).sql

# Backup MongoDB
mongodump --username jebat_user --password your_mongo_password --authenticationDatabase admin --out ./mongo_backup_$(date +%Y%m%d)

# Backup Docker volumes (if using docker-compose)
# Consider using volume backup tools or manual copy
```

## Troubleshooting Common Issues

### WSL2 Installation Issues
- Ensure virtualization is enabled in BIOS/UEFI
- Run `bcdedit /set hypervisorlaunchtype auto` in Admin PowerShell then restart

### Docker Desktop WSL Integration Issues
- In Docker Desktop Settings → Resources → WSL Integration, ensure your distro is selected
- Restart Docker Desktop after changes

### Database Connection Refused
- Verify service is running: `systemctl service_name status`
- Check if port is listening: `ss -tlnp | grep port_number`
- Verify firewall isn't blocking: `sudo ufw status`

### Node.js Version Conflicts
- Use nvm (Node Version Manager): `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash`
- Then: `nvm install --lts`

## Recommended Build Specifications

For optimal JEBAT development experience:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8GB | 16GB+ |
| **Storage** | 20GB SSD | 50GB+ SSD |
| **CPU** | 4 cores | 6+ cores |
| **WSL Distro** | Kali Linux | Kali Linux (for security tools) |
| **Docker** | Docker Engine | Docker Desktop (easier setup) |
| **Node.js** | v16 | v18 LTS |
| **Browser** | Any modern | Chrome/Firefox with devtools |

## Next Steps After Setup

1. Familiarize yourself with the JEBAT codebase structure
2. Review `JEBAT_INTEGRATION_PLAN.md` for development roadmap
3. Start implementing features according to the priority order:
   - Wire memory skill to real DB
   - Add consolidation cron job
   - Add orchestrator runtime mapping
   - Build jebat.online frontend
   - Add dashboards and admin tooling
   - Add security workflows and reports

## Useful Commands Cheat Sheet

```bash
# WSL
wsl --list --verbose
wsl --set-default <distro>
wsl --terminate <distro>
wsl --shutdown

# Docker
docker compose up -d
docker compose down
docker compose logs -f
docker system prune  # Clean unused resources

# Database
psql -U jebat_user -d jebat
mongosh "mongodb://localhost:27017/jebat"
redis-cli

# Next.js
npm run dev
npm run build
npm start
```

---

**🔒 Security Note**: Always change default passwords in production environments. Consider using environment variables or a secrets manager for sensitive credentials.

**💡 Pro Tip**: Take snapshots of your WSL filesystem periodically using `wsl --export` to quickly restore to known-good states.

Happy hacking with JEBAT! 🗡️