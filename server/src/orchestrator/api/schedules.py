from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import require_auth
from orchestrator.database import get_db
from orchestrator.models.schedule import Schedule
from orchestrator.schemas.schedules import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)

router = APIRouter(
    prefix="/schedules", tags=["schedules"], dependencies=[Depends(require_auth)]
)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).order_by(Schedule.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    schedule = Schedule(
        job_definition_id=data.job_definition_id,
        cron_expression=data.cron_expression,
        enabled=data.enabled,
        name=data.name,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
    await db.commit()
