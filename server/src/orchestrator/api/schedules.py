from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import require_auth
from orchestrator.database import get_db
from orchestrator.schemas.schedules import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from orchestrator.services import schedule_service

router = APIRouter(
    prefix="/schedules", tags=["schedules"], dependencies=[Depends(require_auth)]
)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    return await schedule_service.list_schedules(db)


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    try:
        schedule = await schedule_service.create_schedule(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ScheduleResponse.model_validate(schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        schedule = await schedule_service.update_schedule(db, schedule_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await schedule_service.delete_schedule(db, schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
