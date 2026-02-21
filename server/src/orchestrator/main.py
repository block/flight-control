import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from orchestrator.config import settings
from orchestrator.migrate import run_migrations

logger = logging.getLogger(__name__)

# Resolve UI dist directory
_ui_dir: Path | None = None
for _p in [
    Path(__file__).parent.parent.parent.parent / "ui" / "dist",  # local dev
    Path("/app/ui/dist"),  # Docker
]:
    if _p.exists():
        _ui_dir = _p
        break


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations on startup (creates tables + applies schema changes)
    run_migrations()
    logger.info("Database migrations applied")

    # Ensure default workspace and admin user exist
    from orchestrator.database import async_session
    from orchestrator.services import workspace_service

    async with async_session() as db:
        await workspace_service.ensure_defaults(db)

    # Start scheduler background task
    from orchestrator.services.scheduler import run_scheduler

    scheduler_task = asyncio.create_task(run_scheduler())

    yield

    # Shutdown scheduler
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Flight Control",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
from orchestrator.api import credentials, jobs, runs, schedules, skills, system, workers, workspaces

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(workers.router, prefix="/api/v1")
app.include_router(credentials.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(schedules.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")

# Serve static UI files with SPA fallback
if _ui_dir:
    # Mount static assets (js, css, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(_ui_dir / "assets")), name="assets")

    # SPA catch-all: serve index.html for any non-API, non-asset route
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Try to serve the exact file first (e.g., favicon.ico, robots.txt)
        file_path = _ui_dir / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for client-side routing
        return FileResponse(_ui_dir / "index.html")
