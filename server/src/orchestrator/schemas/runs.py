from datetime import datetime

from pydantic import BaseModel


class RunCreate(BaseModel):
    """Ad-hoc run without a saved job definition."""
    name: str = "Ad-hoc Run"
    task_prompt: str
    agent_type: str = "goose"
    agent_config: dict = {}
    mcp_servers: list = []
    env_vars: dict = {}
    credential_ids: list = []
    timeout_seconds: int = 1800
    webhook_url: str | None = None
    webhook_secret: str | None = None


class RunResponse(BaseModel):
    id: str
    job_definition_id: str | None = None
    status: str
    worker_id: str | None = None
    name: str
    task_prompt: str
    agent_type: str
    agent_config: dict = {}
    mcp_servers: list = []
    credential_ids: list = []
    timeout_seconds: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    exit_code: int | None = None
    webhook_url: str | None = None
    # Note: webhook_secret intentionally excluded from response for security
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunCompleteRequest(BaseModel):
    status: str  # completed, failed
    result: str | None = None
    exit_code: int | None = None
