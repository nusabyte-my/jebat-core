# ==================== JEBAT Database — TimescaleDB + pgvector ====================
# Extends the official TimescaleDB image with the pgvector extension
# required for 6-type memory vector similarity search.

FROM timescale/timescaledb-ha:pg16

USER root

# Install build tools, compile pgvector, clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        postgresql-server-dev-16 \
    && cd /tmp && \
    git clone --branch v0.8.0 --depth 1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/pgvector && \
    apt-get purge -y build-essential git postgresql-server-dev-16 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER postgres

# Create mount points for schema files
RUN mkdir -p /schemas /docker-entrypoint-initdb.d

# Copy schema and init scripts (overridden by volume mounts in compose)
COPY schema/ /schemas/
COPY init/ /docker-entrypoint-initdb.d/
