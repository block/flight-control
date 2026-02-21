import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.base import new_id
from orchestrator.models.user import User
from orchestrator.models.workspace import Workspace
from orchestrator.models.workspace_member import WorkspaceMember
from orchestrator.schemas.workspace import WorkspaceCreate

logger = logging.getLogger(__name__)


async def ensure_defaults(db: AsyncSession) -> None:
    """Create default workspace + admin user + membership if not present."""
    # Default workspace
    result = await db.execute(select(Workspace).where(Workspace.id == "default"))
    if not result.scalar_one_or_none():
        db.add(Workspace(id="default", name="Default", slug="default", description="Default workspace"))

    # Admin user
    result = await db.execute(select(User).where(User.id == "admin"))
    if not result.scalar_one_or_none():
        db.add(User(id="admin", username="admin", display_name="Admin"))

    await db.flush()

    # Membership
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == "default",
            WorkspaceMember.user_id == "admin",
        )
    )
    if not result.scalar_one_or_none():
        db.add(WorkspaceMember(
            id="admin-default",
            workspace_id="default",
            user_id="admin",
            role="owner",
        ))

    await db.commit()
    logger.info("Default workspace and admin user ensured")


async def list_workspaces(db: AsyncSession, user_id: str) -> list[Workspace]:
    """List workspaces where user is a member."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.name)
    )
    return list(result.scalars().all())


async def create_workspace(
    db: AsyncSession, data: WorkspaceCreate, owner_user_id: str
) -> Workspace:
    workspace = Workspace(
        id=new_id(),
        name=data.name,
        slug=data.slug,
        description=data.description,
    )
    db.add(workspace)
    await db.flush()

    # Creator becomes owner
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_user_id,
        role="owner",
    )
    db.add(membership)
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def get_workspace(db: AsyncSession, workspace_id: str) -> Workspace | None:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def list_members(db: AsyncSession, workspace_id: str) -> list[dict]:
    """List members of a workspace with user info."""
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.created_at)
    )
    members = []
    for row in result.all():
        member = row.WorkspaceMember
        user = row.User
        members.append({
            "id": member.id,
            "workspace_id": member.workspace_id,
            "user_id": member.user_id,
            "role": member.role,
            "username": user.username,
            "display_name": user.display_name,
            "created_at": member.created_at,
        })
    return members
