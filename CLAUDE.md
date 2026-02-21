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
- **Workspaces**: All resources (jobs, runs, credentials, workers, schedules) are scoped to a workspace via `workspace_id`. The `X-Workspace-ID` header (default: `"default"`) selects the active workspace. Auth returns an `AuthContext` with user + workspace.

### Server code layout (`server/src/orchestrator/`)
- `api/` — FastAPI routers (jobs, runs, credentials, workers, schedules, system, workspaces)
- `models/` — SQLAlchemy ORM (10 tables: job_definitions, job_runs, job_logs, credentials, api_keys, workers, schedules, artifacts, users, workspaces, workspace_members)
- `schemas/` — Pydantic request/response models
- `services/` — Business logic layer
- `auth.py` — Bearer token auth returning `AuthContext` (user + workspace_id)
- `migrate.py` — Runs Alembic migrations programmatically at startup
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

## Database Migrations (CRITICAL)

**Alembic is the ONLY way to change the database schema.** The server runs `alembic upgrade head` automatically on startup (`migrate.py`). There is NO `Base.metadata.create_all` — do not add one.

### Rules for schema changes

1. **Always create an Alembic migration** for any model change (new table, new column, altered constraint). Use `make db-revision msg="description"` to auto-generate, then review and edit.
2. **Never use `create_all`** — it only creates missing tables and silently ignores column additions, constraint changes, and data backfills. This causes "works on fresh DB, breaks on existing DB" bugs.
3. **Use `batch_alter_table`** for all ALTER TABLE operations — SQLite cannot ALTER columns or DROP constraints directly. Batch mode recreates the table.
4. **Use `naming_convention`** when dropping constraints on SQLite — auto-generated constraint names differ between databases. Pass `naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"}` to `batch_alter_table` so Alembic can find unnamed constraints.
5. **Test migration idempotency** — after `make run`, do `make down && make up` (no `-v`) and verify the server starts cleanly without re-running migrations.
6. **Seed data goes in migrations** (for schema-level seeds like default workspace) or in `ensure_defaults()` (for runtime-level seeds). Migration seeds use raw SQL `INSERT`.

### Alembic env.py
- `render_as_batch=True` is enabled globally for SQLite compatibility
- The database URL is overridden from `ORCH_DATABASE_URL` at runtime (async driver stripped for sync Alembic)

## Testing

When making changes, verify them at multiple levels:

- **Unit tests** — Add unit tests for business logic when valuable (e.g., service functions, routing logic). Run with `cd server && pytest` or `cd worker && pytest`.
- **API tests** — The server is API-first. Test endpoints directly via `curl`, `httpx`, or the OpenAPI docs at `/docs`. API behavior is the source of truth.
- **Browser tests** — Use the `agent-browser` skill to verify UI changes and end-to-end flows through the dashboard.

## Environment

- Python 3.12.2 (`.python-version`), Node 20+
- Key env vars: `ORCH_MASTER_KEY` (Fernet key, required), `ORCH_DEFAULT_ADMIN_KEY` (default: "admin"), `ORCH_DATABASE_URL` (default: SQLite)
- OpenAPI docs available at `/docs` when server is running
