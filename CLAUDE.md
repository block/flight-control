# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flight Control is a distributed control plane for AI agent workloads. It dispatches natural-language tasks across a fleet of worker nodes that run Goose agents, streaming results back in real time. Early prototype, localhost-only via Docker Compose.

## First-Time Setup

```bash
# 1. Create .env from the example
cp .env.example .env

# 2. Generate a Fernet encryption key and set it in .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste the output as ORCH_MASTER_KEY in .env
```

## Build & Dev Commands

```bash
# Docker (full stack)
make run                # build + up in one command
make build              # docker compose build
make up                 # docker compose up -d (server on :8080 + 2 workers)
make down               # docker compose down
make logs               # docker compose logs -f
make scale-workers      # scale to 5 workers

# Local development (3 terminals)
make dev-server         # pip install -e ".[dev]" + uvicorn --reload on :8080
make dev-worker         # pip install -e ".[dev]" + worker poll loop
make dev-ui             # npm install + vite dev server on :3000

# Tests
make test               # pytest in server/ then worker/
cd server && pytest     # server tests only
cd worker && pytest     # worker tests only

# Database migrations
make db-migrate                         # alembic upgrade head
make db-revision msg="description"      # autogenerate migration
```

## Architecture

Three-service monorepo (no npm workspaces/Lerna — each service is independent):

- **`server/`** — Control plane (Python 3.12, FastAPI, SQLAlchemy, Uvicorn). REST API at `/api/v1`, Bearer token auth, Fernet credential encryption. Serves the built UI as a SPA.
- **`worker/`** — Compute node (Python 3.12, httpx). Pull-based: polls server for jobs, runs Goose CLI, streams logs back in batches.
- **`ui/`** — Dashboard (React 18, Vite, Tailwind CSS, React Router v6). Proxies `/api` to server in dev.

### Key design decisions
- **Database-as-queue**: `job_runs` table is the job queue with atomic row-level assignment (no Redis/RabbitMQ)
- **Snapshot on run**: Job config is copied into the run record at trigger time
- **Credential isolation**: Fernet-encrypted at rest, decrypted only at dispatch, delivered in-memory, discarded after run
- **Pull-based workers**: Workers poll over HTTP; no inbound ports required

### Server code layout (`server/src/orchestrator/`)
- `api/` — FastAPI routers (jobs, runs, credentials, workers, schedules, system)
- `models/` — SQLAlchemy ORM (7 tables: job_definitions, job_runs, job_logs, credentials, api_keys, workers, schedules)
- `schemas/` — Pydantic request/response models
- `services/` — Business logic layer
- `auth.py` — Bearer token auth with SHA256-hashed keys
- `encryption.py` — Fernet encrypt/decrypt
- `config.py` — Pydantic settings, all env vars prefixed `ORCH_`

### Worker code layout (`worker/src/orchestrator_worker/`)
- `main.py` — Register → heartbeat → poll loop
- `runner.py` — Job execution orchestration
- `agents/goose.py` — Goose CLI runner (extensible via `agents/base.py`)
- `log_streamer.py` — Batched log delivery
- `config_writer.py` — MCP server config generation

### UI code layout (`ui/src/`)
- `pages/` — Route components (Dashboard, Jobs, JobDetail, RunDetail, Workers, Credentials, NewRun)
- `components/` — LogViewer (SSE streaming), ProviderModelSelect
- `lib/api.js` — Fetch wrapper; `lib/models.js` — Provider/model config

## Environment

- Python 3.12.2 (`.python-version`), Node 20+
- Key env vars: `ORCH_MASTER_KEY` (Fernet key, required), `ORCH_DEFAULT_ADMIN_KEY` (default: "admin"), `ORCH_DATABASE_URL` (default: SQLite)
- OpenAPI docs available at `/docs` when server is running
