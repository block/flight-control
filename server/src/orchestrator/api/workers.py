from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import AuthContext, require_auth
from orchestrator.database import get_db
from orchestrator.schemas.artifacts import ArtifactResponse
from orchestrator.schemas.runs import RunCompleteRequest
from orchestrator.schemas.workers import (
    LogBatchRequest,
    PollResponse,
    WorkerHeartbeatRequest,
    WorkerRegisterRequest,
    WorkerRegisterResponse,
)
from orchestrator.services import artifact_service, log_service, worker_service

router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("/register", response_model=WorkerRegisterResponse, status_code=201)
async def register_worker(
    data: WorkerRegisterRequest,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    worker = await worker_service.register_worker(db, data, auth.workspace_id)
    return WorkerRegisterResponse(id=worker.id, name=worker.name)


@router.post("/heartbeat")
async def worker_heartbeat(
    data: WorkerHeartbeatRequest,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    worker = await worker_service.heartbeat(db, data.worker_id, data.status)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"status": "ok"}


@router.post("/poll", response_model=PollResponse | None)
async def poll_for_job(
    worker_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await worker_service.poll_for_job(db, worker_id)


@router.post("/runs/{run_id}/logs")
async def post_logs(
    run_id: str,
    data: LogBatchRequest,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    count = await log_service.append_logs(db, run_id, data.lines)
    return {"appended": count}


@router.post("/runs/{run_id}/artifacts", response_model=ArtifactResponse, status_code=201)
async def upload_artifact(
    run_id: str,
    file: UploadFile,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    artifact = await artifact_service.save_artifact(
        db,
        run_id=run_id,
        filename=file.filename or "unnamed",
        data=data,
        content_type=file.content_type or "application/octet-stream",
        workspace_id=auth.workspace_id,
    )
    return artifact


@router.post("/runs/{run_id}/complete")
async def complete_run(
    run_id: str,
    data: RunCompleteRequest,
    worker_id: str = "",
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    run = await worker_service.complete_run(
        db, worker_id, run_id, data.status, data.result, data.exit_code
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"status": run.status}
