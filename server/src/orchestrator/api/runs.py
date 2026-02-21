import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from orchestrator.auth import require_auth
from orchestrator.database import get_db
from orchestrator.schemas.runs import RunCreate, RunResponse
from orchestrator.services import log_service, run_service

router = APIRouter(prefix="/runs", tags=["runs"], dependencies=[Depends(require_auth)])


@router.get("", response_model=list[RunResponse])
async def list_runs(
    job_id: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await run_service.list_runs(db, job_id=job_id, status=status)


@router.post("", response_model=RunResponse, status_code=201)
async def create_adhoc_run(data: RunCreate, db: AsyncSession = Depends(get_db)):
    return await run_service.create_adhoc_run(db, data)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await run_service.cancel_run(db, run_id)
    if not run:
        raise HTTPException(status_code=400, detail="Run cannot be cancelled")
    return run


@router.get("/{run_id}/logs")
async def get_logs(
    run_id: str,
    after: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    logs = await log_service.get_logs(db, run_id, after_sequence=after)
    return [
        {"stream": log.stream, "line": log.line, "sequence": log.sequence}
        for log in logs
    ]


@router.get("/{run_id}/logs/stream")
async def stream_logs(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await run_service.get_run(db, run_id)
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
