# Contributing to Flight Control

Thank you for your interest in contributing! This project is in its early stages and we welcome issues, discussions, and pull requests.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose

## Getting Started

### Clone the repo

```bash
git clone https://github.com/block/flight-control.git
cd flight-control
```

### Set up environment

```bash
cp .env.example .env
# Generate a Fernet key and add it to .env:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Run with Docker Compose (easiest)

```bash
docker compose up -d
open http://localhost:8080
```

### Run locally for development

```bash
# Terminal 1: Server
cd server && pip install -e ".[dev]" && uvicorn orchestrator.main:app --reload --port 8080

# Terminal 2: Worker
cd worker && pip install -e ".[dev]" && python -m orchestrator_worker.main

# Terminal 3: UI (hot reload)
cd ui && npm install && npm run dev
```

The UI dev server runs on `http://localhost:5173` and proxies API calls to the server on port 8080.

## Project Structure

```
server/     # Control plane (Python/FastAPI)
worker/     # Compute node (Python + Goose CLI)
ui/         # Dashboard (React/Vite/Tailwind)
```

## Running Tests

```bash
cd server && pytest
cd worker && pytest
```

## Submitting Changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Add tests if applicable
4. Ensure tests pass
5. Open a pull request

## Filing Issues

Use the [bug report template](https://github.com/block/flight-control/issues/new?template=bug-report.md) for bugs. For feature requests or questions, open a regular issue.

## Code of Conduct

This project follows the [Block Open Source Code of Conduct](https://github.com/block/.github/blob/main/CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
