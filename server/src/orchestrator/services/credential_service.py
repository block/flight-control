from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.encryption import encrypt_value
from orchestrator.models.credential import Credential
from orchestrator.schemas.credentials import CredentialCreate, CredentialUpdate


async def list_credentials(db: AsyncSession, workspace_id: str) -> list[Credential]:
    result = await db.execute(
        select(Credential)
        .where(Credential.workspace_id == workspace_id)
        .order_by(Credential.name)
    )
    return list(result.scalars().all())


async def get_credential(db: AsyncSession, cred_id: str, workspace_id: str | None = None) -> Credential | None:
    query = select(Credential).where(Credential.id == cred_id)
    if workspace_id:
        query = query.where(Credential.workspace_id == workspace_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_credential(db: AsyncSession, data: CredentialCreate, workspace_id: str) -> Credential:
    cred = Credential(
        workspace_id=workspace_id,
        name=data.name,
        env_var=data.env_var,
        encrypted_value=encrypt_value(data.value),
        description=data.description,
    )
    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return cred


async def update_credential(
    db: AsyncSession, cred_id: str, data: CredentialUpdate, workspace_id: str
) -> Credential | None:
    cred = await get_credential(db, cred_id, workspace_id)
    if not cred:
        return None
    if data.name is not None:
        cred.name = data.name
    if data.env_var is not None:
        cred.env_var = data.env_var
    if data.value is not None:
        cred.encrypted_value = encrypt_value(data.value)
    if data.description is not None:
        cred.description = data.description
    await db.commit()
    await db.refresh(cred)
    return cred


async def delete_credential(db: AsyncSession, cred_id: str, workspace_id: str) -> bool:
    cred = await get_credential(db, cred_id, workspace_id)
    if not cred:
        return False
    await db.delete(cred)
    await db.commit()
    return True
