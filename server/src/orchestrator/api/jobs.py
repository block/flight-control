from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import AuthContext, require_auth
from orchestrator.database import get_db
from orchestrator.schemas.jobs import (
    JobDefinitionCreate,
    JobDefinitionResponse,
    JobDefinitionUpdate,
)
from orchestrator.schemas.runs import RunResponse
from orchestrator.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobDefinitionResponse])
async def list_jobs(
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.list_jobs(db, auth.workspace_id)


@router.post("", response_model=JobDefinitionResponse, status_code=201)
async def create_job(
    data: JobDefinitionCreate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.create_job(db, data, auth.workspace_id)


@router.get("/{job_id}", response_model=JobDefinitionResponse)
async def get_job(
    job_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    job = await job_service.get_job(db, job_id, auth.workspace_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobDefinitionResponse)
async def update_job(
    job_id: str,
    data: JobDefinitionUpdate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    job = await job_service.update_job(db, job_id, data, auth.workspace_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    if not await job_service.delete_job(db, job_id, auth.workspace_id):
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/{job_id}/run", response_model=RunResponse, status_code=201)
async def trigger_run(
    job_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await job_service.trigger_run(db, job_id, auth.workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
