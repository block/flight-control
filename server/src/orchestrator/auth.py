import hashlib

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.config import settings
from orchestrator.database import get_db
from orchestrator.models.api_key import ApiKey

security = HTTPBearer()


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def require_auth(
    creds: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    token = creds.credentials

    # Check default admin key for bootstrapping
    if token == settings.default_admin_key:
        return ApiKey(id="default", name="default-admin", role="admin", key_hash="")

    key_hash = hash_key(token)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


async def require_admin(api_key: ApiKey = Depends(require_auth)) -> ApiKey:
    if api_key.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return api_key
