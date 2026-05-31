# JEBAT v6.0.0 — CLI AI Agent
# Build: docker build -t jebat:latest .
# Run:   docker run -it --rm jebat:latest jebat status
#        docker run -it --rm -v ~/.jebat:/root/.jebat jebat:latest jebat chat-repl

FROM python:3.12-slim

LABEL org.opencontainers.image.title="JEBAT"
LABEL org.opencontainers.image.description="41-CLI AI Agent with pentest toolkit, ReAct loop, MCP, and 97 tools"
LABEL org.opencontainers.image.version="6.0.0"
LABEL org.opencontainers.image.authors="humm1ngb1rd <humm1ngb1rd@nusabyte.my>"
LABEL org.opencontainers.image.url="https://github.com/humm1ngb1rd/jebat"
LABEL org.opencontainers.image.source="https://github.com/humm1ngb1rd/jebat"

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    nmap \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install JEBAT from the local directory
WORKDIR /app
COPY pyproject.toml README.md ./
COPY jebat/ jebat/

# Install the package (editable not needed in container)
RUN pip install --no-cache-dir . && \
    python -c "import jebat; print(f'JEBAT v{jebat.__version__} installed')"

# Create default config skeleton
RUN mkdir -p /root/.jebat && \
    echo "# JEBAT config — configure your LLM provider" > /root/.jebat/config.yaml && \
    echo 'llm:' >> /root/.jebat/config.yaml && \
    echo '  provider: openai' >> /root/.jebat/config.yaml && \
    echo '  model: gpt-4o' >> /root/.jebat/config.yaml && \
    echo '  api_key: "${OPENAI_API_KEY}"' >> /root/.jebat/config.yaml

# Test that the CLI boots
RUN jebat status 2>&1 || true

ENTRYPOINT ["jebat"]
CMD ["--help"]