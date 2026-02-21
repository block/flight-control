from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.job_run import JobRun
from orchestrator.schemas.runs import RunCreate


async def list_runs(
    db: AsyncSession, workspace_id: str, job_id: str | None = None, status: str | None = None
) -> list[JobRun]:
    query = select(JobRun).where(JobRun.workspace_id == workspace_id).order_by(JobRun.created_at.desc())
    if job_id:
        query = query.where(JobRun.job_definition_id == job_id)
    if status:
        query = query.where(JobRun.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_run(db: AsyncSession, run_id: str, workspace_id: str | None = None) -> JobRun | None:
    query = select(JobRun).where(JobRun.id == run_id)
    if workspace_id:
        query = query.where(JobRun.workspace_id == workspace_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_adhoc_run(db: AsyncSession, data: RunCreate, workspace_id: str) -> JobRun:
    run = JobRun(
        workspace_id=workspace_id,
        name=data.name,
        task_prompt=data.task_prompt,
        agent_type=data.agent_type,
        agent_config=data.agent_config,
        mcp_servers=data.mcp_servers,
        env_vars=data.env_vars,
        credential_ids=data.credential_ids,
        required_labels=data.required_labels,
        timeout_seconds=data.timeout_seconds,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def cancel_run(db: AsyncSession, run_id: str, workspace_id: str) -> JobRun | None:
    run = await get_run(db, run_id, workspace_id)
    if not run or run.status not in ("queued", "assigned", "running"):
        return None
    run.status = "cancelled"
    await db.commit()
    await db.refresh(run)
    return run
