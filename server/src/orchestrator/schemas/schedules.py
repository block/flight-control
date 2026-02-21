from datetime import datetime

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    job_definition_id: str
    cron_expression: str
    enabled: bool = True
    name: str | None = None


class ScheduleUpdate(BaseModel):
    cron_expression: str | None = None
    enabled: bool | None = None
    name: str | None = None


class ScheduleResponse(BaseModel):
    id: str
    job_definition_id: str
    cron_expression: str
    enabled: bool
    name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
