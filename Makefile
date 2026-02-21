.PHONY: dev dev-server dev-worker dev-ui build up run fresh down logs test

# ── Development (local, no Docker) ──────────────────────────────

dev-server: ## Install server deps and start FastAPI with hot-reload on :8080
	cd server && pip install -e ".[dev]" && uvicorn orchestrator.main:app --reload --port 8080

dev-worker: ## Install worker deps and start the worker poll loop
	cd worker && pip install -e ".[dev]" && python -m orchestrator_worker.main

dev-ui: ## Install UI deps and start Vite dev server on :3000
	cd ui && npm install && npm run dev

# ── Docker ───────────────────────────────────────────────────────

build: ## Build Docker images for server and workers
	docker compose build

run: build up ## Rebuild images and start all containers (preserves data)

fresh: ## Wipe volumes/data, rebuild images, and start clean
	docker compose down -v
	$(MAKE) build up

up: ## Start containers (kills any leftover dev server on :8080 first)
	@# Kill leftover dev server on :8080 if present
	@for pid in $$(lsof -i :8080 -t 2>/dev/null); do \
		ps -o comm= -p $$pid 2>/dev/null | grep -q uvicorn && kill $$pid 2>/dev/null && echo "Killed dev server (pid $$pid)"; \
	done; true
	docker compose up -d

down: ## Stop and remove all containers (preserves volumes)
	docker compose down

logs: ## Tail logs from all containers
	docker compose logs -f

scale-workers: ## Scale worker fleet to 5 instances
	docker compose up -d --scale worker=5

# ── Database ─────────────────────────────────────────────────────

db-migrate: ## Run pending Alembic migrations
	cd server && alembic upgrade head

db-revision: ## Auto-generate a new migration (usage: make db-revision msg="description")
	cd server && alembic revision --autogenerate -m "$(msg)"

# ── Test ─────────────────────────────────────────────────────────

test: ## Run pytest for server and worker
	cd server && pytest
	cd worker && pytest
