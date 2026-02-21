from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import AuthContext, require_auth
from orchestrator.database import get_db
from orchestrator.schemas.schedules import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from orchestrator.services import schedule_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await schedule_service.list_schedules(db, auth.workspace_id)


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    data: ScheduleCreate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    try:
        schedule = await schedule_service.create_schedule(db, data, auth.workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ScheduleResponse.model_validate(schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    data: ScheduleUpdate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    try:
        schedule = await schedule_service.update_schedule(db, schedule_id, data, auth.workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    deleted = await schedule_service.delete_schedule(db, schedule_id, auth.workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
