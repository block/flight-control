import hashlib
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.config import settings
from orchestrator.database import get_db
from orchestrator.models.api_key import ApiKey
from orchestrator.models.user import User
from orchestrator.models.workspace_member import WorkspaceMember

security = HTTPBearer()

DEFAULT_WORKSPACE_ID = "default"
DEFAULT_ADMIN_USER_ID = "admin"


@dataclass
class AuthContext:
    user: User
    api_key: ApiKey
    workspace_id: str


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def require_auth(
    request: Request,
    creds: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    token = creds.credentials
    workspace_id = request.headers.get("X-Workspace-ID", DEFAULT_WORKSPACE_ID)

    # Resolve API key and user
    if token == settings.default_admin_key:
        api_key = ApiKey(id="default", name="default-admin", role="admin", key_hash="", user_id=DEFAULT_ADMIN_USER_ID)
        # Get or create admin user
        result = await db.execute(select(User).where(User.id == DEFAULT_ADMIN_USER_ID))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=DEFAULT_ADMIN_USER_ID, username="admin", display_name="Admin")
    else:
        key_hash = hash_key(token)
        result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Resolve user from api_key.user_id
        if api_key.user_id:
            result = await db.execute(select(User).where(User.id == api_key.user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=401, detail="User not found for API key")
        else:
            # Legacy key without user_id — treat as admin
            result = await db.execute(select(User).where(User.id == DEFAULT_ADMIN_USER_ID))
            user = result.scalar_one_or_none()
            if not user:
                user = User(id=DEFAULT_ADMIN_USER_ID, username="admin", display_name="Admin")

    # Validate workspace membership
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=403,
            detail=f"Not a member of workspace '{workspace_id}'",
        )

    return AuthContext(user=user, api_key=api_key, workspace_id=workspace_id)


async def require_admin(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    if auth.api_key.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth
