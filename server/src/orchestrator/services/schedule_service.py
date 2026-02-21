from datetime import datetime, timezone

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.job_definition import JobDefinition
from orchestrator.models.schedule import Schedule
from orchestrator.schemas.schedules import ScheduleCreate, ScheduleResponse, ScheduleUpdate


def compute_next_run(cron_expression: str, base_time: datetime | None = None) -> datetime:
    base = base_time or datetime.now(timezone.utc)
    return croniter(cron_expression, base).get_next(datetime).replace(tzinfo=timezone.utc)


async def list_schedules(db: AsyncSession, workspace_id: str) -> list[ScheduleResponse]:
    result = await db.execute(
        select(Schedule, JobDefinition.name.label("job_name"))
        .outerjoin(JobDefinition, Schedule.job_definition_id == JobDefinition.id)
        .where(Schedule.workspace_id == workspace_id)
        .order_by(Schedule.created_at.desc())
    )
    rows = result.all()
    schedules = []
    for row in rows:
        data = ScheduleResponse.model_validate(row.Schedule)
        data.job_name = row.job_name
        schedules.append(data)
    return schedules


async def get_schedule(db: AsyncSession, schedule_id: str, workspace_id: str | None = None) -> Schedule | None:
    query = select(Schedule).where(Schedule.id == schedule_id)
    if workspace_id:
        query = query.where(Schedule.workspace_id == workspace_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_schedule(db: AsyncSession, data: ScheduleCreate, workspace_id: str) -> Schedule:
    if not croniter.is_valid(data.cron_expression):
        raise ValueError(f"Invalid cron expression: {data.cron_expression}")

    schedule = Schedule(
        workspace_id=workspace_id,
        job_definition_id=data.job_definition_id,
        cron_expression=data.cron_expression,
        enabled=data.enabled,
        name=data.name,
    )
    if schedule.enabled:
        schedule.next_run_at = compute_next_run(data.cron_expression)

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def update_schedule(
    db: AsyncSession, schedule_id: str, data: ScheduleUpdate, workspace_id: str
) -> Schedule | None:
    schedule = await get_schedule(db, schedule_id, workspace_id)
    if not schedule:
        return None

    update_data = data.model_dump(exclude_unset=True)

    if "cron_expression" in update_data:
        if not croniter.is_valid(update_data["cron_expression"]):
            raise ValueError(f"Invalid cron expression: {update_data['cron_expression']}")

    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Recompute next_run_at if cron or enabled changed
    if schedule.enabled:
        schedule.next_run_at = compute_next_run(schedule.cron_expression)
    else:
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: str, workspace_id: str) -> bool:
    schedule = await get_schedule(db, schedule_id, workspace_id)
    if not schedule:
        return False
    await db.delete(schedule)
    await db.commit()
    return True
