import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from orchestrator.auth import AuthContext, require_auth, require_auth_sse
from orchestrator.database import get_db
from orchestrator.schemas.artifacts import ArtifactResponse
from orchestrator.schemas.runs import RunCreate, RunResponse
from orchestrator.services import artifact_service, log_service, run_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunResponse])
async def list_runs(
    job_id: str | None = Query(None),
    status: str | None = Query(None),
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await run_service.list_runs(db, auth.workspace_id, job_id=job_id, status=status)


@router.post("", response_model=RunResponse, status_code=201)
async def create_adhoc_run(
    data: RunCreate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await run_service.create_adhoc_run(db, data, auth.workspace_id)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    run = await run_service.get_run(db, run_id, auth.workspace_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    run_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    run = await run_service.cancel_run(db, run_id, auth.workspace_id)
    if not run:
        raise HTTPException(status_code=400, detail="Run cannot be cancelled")
    return run


@router.get("/{run_id}/artifacts", response_model=list[ArtifactResponse])
async def list_run_artifacts(
    run_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await artifact_service.list_artifacts(db, run_id)


@router.get("/{run_id}/artifacts/{artifact_id}")
async def download_artifact(
    run_id: str,
    artifact_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    artifact = await artifact_service.get_artifact(db, artifact_id)
    if not artifact or artifact.run_id != run_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    data = await artifact_service.read_artifact_data(artifact)
    return Response(
        content=data,
        media_type=artifact.content_type,
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )


@router.get("/{run_id}/logs")
async def get_logs(
    run_id: str,
    after: int = Query(0),
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    logs = await log_service.get_logs(db, run_id, after_sequence=after)
    return [
        {"stream": log.stream, "line": log.line, "sequence": log.sequence}
        for log in logs
    ]


@router.get("/{run_id}/logs/stream")
async def stream_logs(
    run_id: str,
    auth: AuthContext = Depends(require_auth_sse),
    db: AsyncSession = Depends(get_db),
):
    run = await run_service.get_run(db, run_id, auth.workspace_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    queue = log_service.subscribe(run_id)

    async def event_generator():
        try:
            while True:
                try:
                    line = await asyncio.wait_for(queue.get(), timeout=30)
                    yield {
                        "event": "log",
                        "data": json.dumps(
                            {"stream": line.stream, "line": line.line, "sequence": line.sequence}
                        ),
                    }
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
        except asyncio.CancelledError:
            pass
        finally:
            log_service.unsubscribe(run_id, queue)

    return EventSourceResponse(event_generator())
