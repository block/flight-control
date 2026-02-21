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


async def list_schedules(db: AsyncSession) -> list[ScheduleResponse]:
    result = await db.execute(
        select(Schedule, JobDefinition.name.label("job_name"))
        .outerjoin(JobDefinition, Schedule.job_definition_id == JobDefinition.id)
        .order_by(Schedule.created_at.desc())
    )
    rows = result.all()
    return [
        ScheduleResponse.model_validate(row.Schedule, update={"job_name": row.job_name})
        for row in rows
    ]


async def get_schedule(db: AsyncSession, schedule_id: str) -> Schedule | None:
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    return result.scalar_one_or_none()


async def create_schedule(db: AsyncSession, data: ScheduleCreate) -> Schedule:
    if not croniter.is_valid(data.cron_expression):
        raise ValueError(f"Invalid cron expression: {data.cron_expression}")

    schedule = Schedule(
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
    db: AsyncSession, schedule_id: str, data: ScheduleUpdate
) -> Schedule | None:
    schedule = await get_schedule(db, schedule_id)
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


async def delete_schedule(db: AsyncSession, schedule_id: str) -> bool:
    schedule = await get_schedule(db, schedule_id)
    if not schedule:
        return False
    await db.delete(schedule)
    await db.commit()
    return True
