from datetime import datetime

from pydantic import BaseModel


class SkillFileResponse(BaseModel):
    id: str
    file_path: str
    size_bytes: int
    checksum_sha256: str
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillSummaryResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str
    license: str | None = None
    compatibility: str | None = None
    allowed_tools: str | None = None
    total_size_bytes: int
    file_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillDetailResponse(SkillSummaryResponse):
    metadata_kv: dict | None = None
    instructions: str
    files: list[SkillFileResponse] = []


class SkillUpdate(BaseModel):
    description: str | None = None
    license: str | None = None
    compatibility: str | None = None
    metadata_kv: dict | None = None
    allowed_tools: str | None = None
    instructions: str | None = None
