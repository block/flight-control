.PHONY: dev dev-server dev-worker dev-ui build up down logs test

# Development
dev-server:
	cd server && pip install -e ".[dev]" && uvicorn orchestrator.main:app --reload --port 8080

dev-worker:
	cd worker && pip install -e ".[dev]" && python -m orchestrator_worker.main

dev-ui:
	cd ui && npm install && npm run dev

# Docker
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

scale-workers:
	docker compose up -d --scale worker=5

# Database
db-migrate:
	cd server && alembic upgrade head

db-revision:
	cd server && alembic revision --autogenerate -m "$(msg)"

# Test
test:
	cd server && pytest
	cd worker && pytest
