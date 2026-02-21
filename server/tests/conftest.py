import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from orchestrator.models.base import Base
from orchestrator.models.user import User
from orchestrator.models.workspace import Workspace
from orchestrator.models.workspace_member import WorkspaceMember


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite async session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Seed default workspace and admin user for tests
        session.add(Workspace(id="default", name="Default", slug="default"))
        session.add(User(id="admin", username="admin", display_name="Admin"))
        session.add(WorkspaceMember(id="admin-default", workspace_id="default", user_id="admin", role="owner"))
        await session.commit()
        yield session

    await engine.dispose()
