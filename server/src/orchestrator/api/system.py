from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.database import get_db
from orchestrator.models.job_run import JobRun
from orchestrator.models.worker import Worker
from orchestrator.schemas.workers import WorkerResponse
from orchestrator.services import worker_service

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/system/workers", response_model=list[WorkerResponse])
async def list_workers(db: AsyncSession = Depends(get_db)):
    return await worker_service.list_workers(db)


@router.get("/system/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    # Count runs by status
    result = await db.execute(
        select(JobRun.status, func.count(JobRun.id)).group_by(JobRun.status)
    )
    run_counts = {row[0]: row[1] for row in result.all()}

    # Ensure stale workers are marked offline before counting
    await worker_service.list_workers(db)

    # Count workers by status
    result = await db.execute(
        select(Worker.status, func.count(Worker.id)).group_by(Worker.status)
    )
    worker_counts = {row[0]: row[1] for row in result.all()}

    return {
        "runs": run_counts,
        "workers": worker_counts,
        "queue_depth": run_counts.get("queued", 0),
    }
