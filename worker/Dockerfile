FROM python:3.12-slim
WORKDIR /app

# Corporate CA cert (optional)
ARG PIP_INDEX_URL=""
ARG PIP_TRUSTED_HOST=""
ARG NPM_REGISTRY=""
COPY corp-ca.crt* /tmp/
RUN if [ -f /tmp/corp-ca.crt ]; then \
      cp /tmp/corp-ca.crt /usr/local/share/ca-certificates/corp.crt && \
      update-ca-certificates; \
    fi
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Install system deps (bzip2 for goose install, libxcb1 for goose runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bzip2 libxcb1 ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for MCP server npx commands)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
RUN if [ -n "$NPM_REGISTRY" ]; then npm config set registry "$NPM_REGISTRY"; fi

# Install agent-browser + Playwright Chromium (pre-baked to avoid runtime downloads)
RUN npm install -g agent-browser \
    && npx playwright install --with-deps chromium \
    && npx playwright install ffmpeg \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Install Goose (Block's Goose CLI)
RUN CONFIGURE=false curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | CONFIGURE=false bash \
    && ln -sf /root/.local/bin/goose /usr/local/bin/goose

ENV PATH="/root/.local/bin:${PATH}"

# Pre-configure Goose with developer extension enabled
RUN mkdir -p /root/.config/goose && cat > /root/.config/goose/config.yaml <<'GOOSECONF'
extensions:
  developer:
    enabled: true
    type: builtin
    name: developer
    timeout: 300
    bundled: true
  todo:
    enabled: true
    type: platform
    name: todo
    bundled: true
GOOSECONF

# Install Python dependencies
RUN pip install --no-cache-dir \
    "httpx>=0.27.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.6.0"

# Copy worker code
COPY worker/src/ ./src/

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "orchestrator_worker.main"]
