from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.job_definition import JobDefinition
from orchestrator.models.job_run import JobRun
from orchestrator.schemas.jobs import JobDefinitionCreate, JobDefinitionUpdate


async def list_jobs(db: AsyncSession) -> list[JobDefinition]:
    result = await db.execute(
        select(JobDefinition).order_by(JobDefinition.created_at.desc())
    )
    return list(result.scalars().all())


async def get_job(db: AsyncSession, job_id: str) -> JobDefinition | None:
    result = await db.execute(
        select(JobDefinition).where(JobDefinition.id == job_id)
    )
    return result.scalar_one_or_none()


async def create_job(db: AsyncSession, data: JobDefinitionCreate) -> JobDefinition:
    job = JobDefinition(
        name=data.name,
        description=data.description,
        task_prompt=data.task_prompt,
        agent_type=data.agent_type,
        agent_config=data.agent_config if isinstance(data.agent_config, dict) else data.agent_config.model_dump(),
        mcp_servers=[s if isinstance(s, dict) else s.model_dump() for s in data.mcp_servers],
        env_vars=data.env_vars,
        credential_ids=data.credential_ids,
        labels=data.labels,
        timeout_seconds=data.timeout_seconds,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job(
    db: AsyncSession, job_id: str, data: JobDefinitionUpdate
) -> JobDefinition | None:
    job = await get_job(db, job_id)
    if not job:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "agent_config" and not isinstance(value, dict):
            value = value.model_dump()
        if field == "mcp_servers" and value is not None:
            value = [s if isinstance(s, dict) else s.model_dump() for s in value]
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    return job


async def delete_job(db: AsyncSession, job_id: str) -> bool:
    job = await get_job(db, job_id)
    if not job:
        return False
    await db.delete(job)
    await db.commit()
    return True


async def trigger_run(db: AsyncSession, job_id: str) -> JobRun:
    """Create a run from a saved job definition (snapshot config)."""
    job = await get_job(db, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    run = JobRun(
        job_definition_id=job.id,
        name=job.name,
        task_prompt=job.task_prompt,
        agent_type=job.agent_type,
        agent_config=job.agent_config,
        mcp_servers=job.mcp_servers,
        env_vars=job.env_vars,
        credential_ids=job.credential_ids,
        required_labels=job.labels,  # Copy job labels as required worker labels
        timeout_seconds=job.timeout_seconds,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run
