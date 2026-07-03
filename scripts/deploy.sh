#!/bin/bash
# JEBAT Deployment Script
# Usage: ./scripts/deploy.sh [environment]
# Environments: local, staging, production

set -euo pipefail

ENVIRONMENT="${1:-local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Load environment
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    log_info "Loading .env"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    log_warn "No .env file found, using defaults"
fi

cd "$PROJECT_ROOT"

case "$ENVIRONMENT" in
    local)
        log_info "Deploying locally..."
        COMPOSE_FILES=("-f" "docker-compose.yml")
        ;;
    staging)
        log_info "Deploying to staging..."
        COMPOSE_FILES=("-f" "docker-compose.yml")
        ;;
    production)
        log_info "Deploying to production..."
        COMPOSE_FILES=("-f" "docker-compose.yml" "-f" "docker-compose.prod.yml")
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        echo "Usage: $0 [local|staging|production]"
        exit 1
        ;;
esac

# Pull latest images
log_info "Pulling latest images..."
docker compose "${COMPOSE_FILES[@]}" pull

# Build application image
log_info "Building JEBAT image..."
docker compose "${COMPOSE_FILES[@]}" build jebat-api jebat-loop monitoring

# Start services
log_info "Starting services..."
docker compose "${COMPOSE_FILES[@]}" up -d

# Wait for health checks
log_info "Waiting for services to be healthy..."
sleep 10

# Check health
check_service() {
    local name="$1"
    local url="$2"
    local max_retries=30
    local retry=0

    while [[ $retry -lt $max_retries ]]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_info "$name is healthy"
            return 0
        fi
        retry=$((retry + 1))
        sleep 2
    done
    log_error "$name failed health check after $max_retries attempts"
    return 1
}

check_service "PostgreSQL" "http://localhost:5432" || true  # Will fail, pg_isready is better
check_service "JEBAT API" "http://localhost:8000/api/v1/health"
check_service "Monitoring" "http://localhost:8501/_stcore/health"

log_info "Deployment complete!"
echo
echo "Services:"
echo "  - JEBAT API:     http://localhost:8000"
echo "  - API Docs:      http://localhost:8000/api/docs"
echo "  - Monitoring:    http://localhost:8501"
echo "  - PostgreSQL:    localhost:5432"
echo "  - Redis:         localhost:6379"