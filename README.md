# Flight Control

**A distributed control plane for AI agent workloads.**

Flight Control is an open-source platform for dispatching AI agent tasks across a fleet of worker nodes. You describe work in natural language, the control plane queues it, and workers pull jobs, execute them, and stream results back in real time.

> **Status: Early Prototype.** This project runs on localhost via Docker Compose. It is not yet production-hardened. The architecture is designed for distributed deployment, but today it's a single-host development tool. Contributions and feedback welcome.

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/block/flight-control.git
cd flight-control
cp .env.example .env

# 2. Generate an encryption key and add it to .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste the output as ORCH_MASTER_KEY in .env

# 3. Start everything
docker compose up -d

# 4. Open the dashboard
open http://localhost:8080
```

This starts the control plane (API + UI on port 8080) and 2 workers. Scale the workers:

```bash
docker compose up -d --scale worker=5
```

## What It Does

1. **Store credentials** — Encrypt and save API keys (OpenAI, Anthropic, etc.) in the control plane. They're decrypted only when dispatched to a worker and never written to disk.

2. **Define jobs** — Write a natural language task prompt, pick a model and provider, attach MCP servers and credentials.

3. **Dispatch runs** — Click "Run" or submit an ad-hoc task. The control plane queues it and the next idle worker picks it up.

4. **Watch it execute** — Logs stream to the browser in real time via SSE as the agent works.

## Architecture

```
              ┌────────────────┐
              │  Browser (UI)  │
              └───────┬────────┘
                      │
         ┌────────────▼────────────┐
         │      Control Plane       │
         │  Job Queue · Credentials │
         │  Log Aggregation · API   │
         └──┬───────┬───────┬──────┘
            │       │       │
    ┌───────▼──┐ ┌──▼───┐ ┌▼─────────┐
    │ Worker 1 │ │  W2  │ │ Worker N  │
    │  Goose   │ │ Goose│ │  Goose    │
    └──────────┘ └──────┘ └───────────┘
```

- **Pull-based workers** — Workers poll the control plane for jobs over HTTP. No inbound ports needed. If a machine can make outbound HTTPS requests, it can be a worker.
- **Database-as-queue** — No Redis or RabbitMQ. The `job_runs` table is the queue, with atomic row-level assignment to prevent duplicate execution.
- **Credential isolation** — API keys are Fernet-encrypted at rest, decrypted only at dispatch time, delivered in-memory to the worker, and discarded after the run.
- **Snapshot on run** — Job config is copied into the run record at trigger time. Editing a definition doesn't affect in-flight runs.
- **Agent-agnostic** — Currently runs [Goose](https://github.com/block/goose) agents. The runner interface is designed to support other agent runtimes in the future.

## Project Structure

```
flight-control/
├── docker-compose.yml
├── server/                          # Control plane (Python/FastAPI)
│   ├── Dockerfile
│   └── src/orchestrator/
│       ├── main.py                  # FastAPI app, SPA routing
│       ├── api/                     # REST endpoints
│       ├── models/                  # SQLAlchemy ORM (7 tables)
│       ├── schemas/                 # Pydantic request/response models
│       ├── services/                # Business logic
│       ├── auth.py                  # Bearer token authentication
│       └── encryption.py            # Fernet encrypt/decrypt
├── worker/                          # Compute node (Python)
│   ├── Dockerfile
│   └── src/orchestrator_worker/
│       ├── main.py                  # Register → heartbeat → poll loop
│       ├── runner.py                # Job execution orchestration
│       ├── agents/goose.py          # Goose CLI runner
│       ├── log_streamer.py          # Batched log delivery
│       └── config_writer.py         # MCP server config generation
└── ui/                              # Dashboard (React/Vite/Tailwind)
    └── src/
        ├── pages/                   # Dashboard, Jobs, Runs, Workers, Credentials
        ├── components/              # LogViewer (SSE), ProviderModelSelect
        └── lib/                     # API client, provider/model config
```

## API

All endpoints under `/api/v1`, authenticated with `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/jobs` | Create a job definition |
| `POST` | `/jobs/{id}/run` | Dispatch a run |
| `POST` | `/runs` | Create an ad-hoc run |
| `GET` | `/runs/{id}/logs/stream` | SSE log stream |
| `POST` | `/runs/{id}/cancel` | Cancel a run |
| `POST` | `/credentials` | Store an encrypted credential |
| `GET` | `/system/workers` | List fleet status |
| `GET` | `/health` | Health check |

Full CRUD available for jobs, runs, credentials, and schedules. See the auto-generated OpenAPI docs at `/docs` when the server is running.

## Environment Variables

### Control Plane

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCH_DATABASE_URL` | `sqlite+aiosqlite:///./data/orchestrator.db` | Database connection (SQLite or PostgreSQL) |
| `ORCH_MASTER_KEY` | *(required)* | Fernet key for credential encryption |
| `ORCH_DEFAULT_ADMIN_KEY` | `admin` | Bootstrap API key |

### Workers

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCH_SERVER_URL` | `http://server:8080` | Control plane URL |
| `ORCH_API_KEY` | *(required)* | Bearer token for worker authentication |

### Build Overrides (Corporate Environments)

If you're behind a corporate proxy or need to use internal package mirrors, set these in your `.env` file. They're passed as Docker build args automatically:

| Variable | Description |
|----------|-------------|
| `PIP_INDEX_URL` | Custom PyPI index URL |
| `PIP_TRUSTED_HOST` | Trusted host for pip |
| `NPM_REGISTRY` | Custom npm registry URL |

You can also drop a `corp-ca.crt` file in the project root to inject a corporate CA certificate into the Docker builds. It's already in `.gitignore`.

## Local Development

```bash
# Terminal 1: Server
cd server && pip install -e . && uvicorn orchestrator.main:app --reload --port 8080

# Terminal 2: Worker
cd worker && pip install -e . && python -m orchestrator_worker.main

# Terminal 3: UI (hot reload)
cd ui && npm install && npm run dev
```

## Current Limitations

This is an early prototype. Known limitations:

- **Localhost only** — No TLS, no production database config, default API key is `"admin"`.
- **SQLite by default** — Works for development; PostgreSQL is supported but not the default.
- **Single server** — Log streaming uses an in-memory subscriber dict that doesn't work across multiple server replicas.
- **No database migrations** — Alembic is set up but no migration files exist yet.
- **No auto-scaling** — Workers scale manually via `docker compose --scale`.
- **Cron scheduler not wired** — The schedules table exists but the scheduler isn't running.

## Vision

The long-term goal is a production-grade, cloud-agnostic orchestration platform for AI agents that is:

- **Easy to deploy** — Docker containers wired by environment variables. Run on any platform that supports containers.
- **Easy to scale** — Workers auto-scale based on queue depth. Scale to zero when idle, burst when busy.
- **Easy to secure** — TLS, scoped API keys, encrypted credentials, no inbound ports on workers.
- **Easy to observe** — Prometheus metrics, structured logs, real-time dashboards.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Control Plane | Python 3.12, FastAPI, SQLAlchemy, Uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Dashboard | React 18, Vite, Tailwind CSS |
| Workers | Python 3.12, [Goose](https://github.com/block/goose) CLI |
| Encryption | Fernet (cryptography library) |
| Auth | Bearer API keys (SHA256-hashed) |

## Contributing

This project is in its early stages. Issues, discussions, and pull requests are welcome.

## License

Apache-2.0
