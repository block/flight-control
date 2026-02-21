from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.config import settings
from orchestrator.encryption import decrypt_value
from orchestrator.models.base import utcnow
from orchestrator.models.credential import Credential
from orchestrator.models.job_run import JobRun
from orchestrator.models.worker import Worker
from orchestrator.schemas.workers import PollResponse, WorkerRegisterRequest


async def register_worker(db: AsyncSession, data: WorkerRegisterRequest) -> Worker:
    worker = Worker(name=data.name, labels=data.labels)
    db.add(worker)
    await db.commit()
    await db.refresh(worker)
    return worker


async def heartbeat(db: AsyncSession, worker_id: str, status: str = "online") -> Worker | None:
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        return None
    worker.last_heartbeat = utcnow()
    worker.status = status
    await db.commit()
    await db.refresh(worker)
    return worker


def labels_match(required_labels: dict | None, worker_labels: dict | None) -> bool:
    """Check if worker labels satisfy required labels (subset match)."""
    if not required_labels:
        return True  # No requirements = any worker can run it
    if not worker_labels:
        return False  # Has requirements but worker has no labels
    # All required labels must be present in worker labels with matching values
    return all(
        worker_labels.get(key) == value
        for key, value in required_labels.items()
    )


async def poll_for_job(db: AsyncSession, worker_id: str) -> PollResponse | None:
    """Atomically assign a queued job to this worker, respecting label constraints."""
    # Get worker's labels first
    worker_result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = worker_result.scalar_one_or_none()
    if not worker:
        return None
    worker_labels = worker.labels or {}

    # Find oldest queued run that matches this worker's labels
    result = await db.execute(
        select(JobRun)
        .where(JobRun.status == "queued")
        .order_by(JobRun.created_at.asc())
    )
    runs = result.scalars().all()
    
    # Find first run whose required_labels match this worker
    run = None
    for candidate in runs:
        if labels_match(candidate.required_labels, worker_labels):
            run = candidate
            break
    
    if not run:
        return None

    # Atomic assign: only update if still queued (prevents race condition)
    assign_result = await db.execute(
        update(JobRun)
        .where(JobRun.id == run.id, JobRun.status == "queued")
        .values(status="assigned", worker_id=worker_id, started_at=utcnow())
    )

    # If another worker already grabbed it, rowcount will be 0
    if assign_result.rowcount == 0:
        return None

    # Update worker status
    await db.execute(
        update(Worker)
        .where(Worker.id == worker_id)
        .values(status="busy", current_run_id=run.id)
    )

    await db.commit()

    # Re-fetch the run to get the updated state
    result = await db.execute(select(JobRun).where(JobRun.id == run.id))
    run = result.scalar_one_or_none()

    # Decrypt credentials
    credentials: dict[str, str] = {}
    if run.credential_ids:
        cred_result = await db.execute(
            select(Credential).where(Credential.name.in_(run.credential_ids))
        )
        for cred in cred_result.scalars().all():
            try:
                credentials[cred.env_var] = decrypt_value(cred.encrypted_value)
            except Exception:
                pass  # Skip failed decryptions

    return PollResponse(
        run_id=run.id,
        name=run.name,
        task_prompt=run.task_prompt,
        agent_type=run.agent_type,
        agent_config=run.agent_config or {},
        mcp_servers=run.mcp_servers or [],
        env_vars=run.env_vars or {},
        credentials=credentials,
        timeout_seconds=run.timeout_seconds,
    )


async def complete_run(
    db: AsyncSession,
    worker_id: str,
    run_id: str,
    status: str,
    result: str | None = None,
    exit_code: int | None = None,
) -> JobRun | None:
    run_result = await db.execute(select(JobRun).where(JobRun.id == run_id))
    run = run_result.scalar_one_or_none()
    if not run:
        return None

    run.status = status
    run.result = result
    run.exit_code = exit_code
    run.completed_at = utcnow()

    # Free the worker
    worker_result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = worker_result.scalar_one_or_none()
    if worker:
        worker.status = "online"
        worker.current_run_id = None

    await db.commit()
    await db.refresh(run)
    return run


async def list_workers(db: AsyncSession) -> list[Worker]:
    result = await db.execute(select(Worker).order_by(Worker.created_at.desc()))
    workers = list(result.scalars().all())

    # Mark stale workers as offline based on heartbeat timeout
    # Strip tzinfo to match SQLite's naive datetime storage
    cutoff = utcnow().replace(tzinfo=None) - timedelta(seconds=settings.worker_heartbeat_timeout)
    changed = False
    for worker in workers:
        if worker.status in ("online", "busy") and worker.last_heartbeat < cutoff:
            worker.status = "offline"
            changed = True
    if changed:
        await db.commit()

    return workers
