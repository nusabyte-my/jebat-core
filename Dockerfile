# ==================== JEBAT v6.1 — Multi-Stage Docker Build ====================
# Stage 1: Builder — install deps, compile wheels
# Stage 2: Runtime — slim image with only runtime deps
# Stage 3: (optional) Can be extended with monitoring sidecars

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for asyncpg, cryptography, numpy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.prod.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

LABEL maintainer="NusaByte <team@nusabyte.dev>" \
      description="JEBAT v6.1 Sovereign AI Platform" \
      version="6.1.0"

# Runtime system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r jebat && useradd -r -g jebat -d /app -s /sbin/nologin jebat

WORKDIR /app

# Copy application source
COPY __init__.py .
COPY pyproject.toml .
COPY config/config_manager.py ./config/
COPY database/schema/ ./database/schema/
COPY database/init/ ./database/init/
COPY scripts/*.py ./scripts/
COPY index.html ./
COPY requirements.prod.txt main.py ./

# Create data directories
RUN mkdir -p /app/data /app/logs /app/.jebat && \
    chown -R jebat:jebat /app

# Expose API, WebUI, MCP ports
EXPOSE 8080 8787 18789

# Health check — hits the API root endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

USER jebat

# Use tini as PID 1 for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default: run the API server. Override in docker-compose for workers.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
