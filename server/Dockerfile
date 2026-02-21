# Stage 1: Build UI
FROM node:20-slim AS ui-builder
WORKDIR /app/ui

# Corporate CA cert + npm registry (optional)
ARG NPM_REGISTRY=""
COPY corp-ca.crt* /tmp/
RUN if [ -f /tmp/corp-ca.crt ]; then \
      apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
      cp /tmp/corp-ca.crt /usr/local/share/ca-certificates/corp.crt && \
      update-ca-certificates && \
      npm config set cafile /etc/ssl/certs/ca-certificates.crt && \
      rm -rf /var/lib/apt/lists/*; \
    fi
RUN if [ -n "$NPM_REGISTRY" ]; then npm config set registry "$NPM_REGISTRY"; fi

COPY ui/package.json ui/package-lock.json* ./
RUN npm install
COPY ui/ ./
RUN npm run build

# Stage 2: Python server
FROM python:3.12-slim
WORKDIR /app

# Corporate CA cert + pip index (optional)
ARG PIP_INDEX_URL=""
ARG PIP_TRUSTED_HOST=""
COPY corp-ca.crt* /tmp/
RUN if [ -f /tmp/corp-ca.crt ]; then \
      cp /tmp/corp-ca.crt /usr/local/share/ca-certificates/corp.crt && \
      update-ca-certificates; \
    fi
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Install Python dependencies
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "sqlalchemy[asyncio]>=2.0.0" \
    "aiosqlite>=0.20.0" \
    "alembic>=1.14.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.6.0" \
    "cryptography>=44.0.0" \
    "croniter>=2.0.0" \
    "sse-starlette>=2.1.0" \
    "python-multipart>=0.0.12"

# Copy server code
COPY server/src/ ./src/
COPY server/alembic/ ./alembic/
COPY server/alembic.ini ./

# Copy built UI
COPY --from=ui-builder /app/ui/dist ./ui/dist

# Create data directory
RUN mkdir -p /app/data

ENV PYTHONPATH=/app/src
ENV ORCH_DATABASE_URL=sqlite+aiosqlite:///./data/orchestrator.db

EXPOSE 8080

CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
