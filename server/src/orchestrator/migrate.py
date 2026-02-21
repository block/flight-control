"""Run Alembic migrations programmatically at app startup."""

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from orchestrator.config import settings

logger = logging.getLogger(__name__)


def _get_alembic_config() -> Config:
    """Build an Alembic Config pointing at the right directory and database URL."""
    # alembic.ini and alembic/ directory live at the server package root
    # In Docker: /app/alembic.ini, /app/alembic/
    # In local dev: server/alembic.ini, server/alembic/
    for candidate in [
        Path("/app/alembic.ini"),  # Docker
        Path(__file__).parent.parent.parent.parent / "alembic.ini",  # local dev (server/alembic.ini)
    ]:
        if candidate.exists():
            cfg = Config(str(candidate))
            break
    else:
        raise FileNotFoundError("Cannot find alembic.ini")

    # Override the database URL with the async-stripped version
    # (Alembic uses synchronous connections, so strip the +aiosqlite driver)
    sync_url = settings.database_url.replace("+aiosqlite", "")
    cfg.set_main_option("sqlalchemy.url", sync_url)

    # Ensure the data directory exists for SQLite
    if sync_url.startswith("sqlite"):
        db_path = sync_url.split("///")[-1]
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    return cfg


def run_migrations() -> None:
    """Run `alembic upgrade head` to apply all pending migrations."""
    cfg = _get_alembic_config()
    logger.info("Running database migrations...")
    command.upgrade(cfg, "head")
    logger.info("Database migrations complete")
