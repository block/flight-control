from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import AuthContext, require_auth
from orchestrator.database import get_db
from orchestrator.schemas.credentials import (
    CredentialCreate,
    CredentialResponse,
    CredentialUpdate,
)
from orchestrator.services import credential_service

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.get("", response_model=list[CredentialResponse])
async def list_credentials(
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await credential_service.list_credentials(db, auth.workspace_id)


@router.post("", response_model=CredentialResponse, status_code=201)
async def create_credential(
    data: CredentialCreate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await credential_service.create_credential(db, data, auth.workspace_id)


@router.put("/{cred_id}", response_model=CredentialResponse)
async def update_credential(
    cred_id: str,
    data: CredentialUpdate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    cred = await credential_service.update_credential(db, cred_id, data, auth.workspace_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


@router.delete("/{cred_id}", status_code=204)
async def delete_credential(
    cred_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    if not await credential_service.delete_credential(db, cred_id, auth.workspace_id):
        raise HTTPException(status_code=404, detail="Credential not found")
