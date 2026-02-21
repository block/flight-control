import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from orchestrator.config import settings

# Ensure data directory exists for SQLite
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.split("///")[-1]
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    # SQLite needs check_same_thread=False
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session
