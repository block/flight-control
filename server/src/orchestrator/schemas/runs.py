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
    required_labels: dict[str, str] = {}  # Labels required on worker to run this job
    timeout_seconds: int = 1800


class RunResponse(BaseModel):
    id: str
    workspace_id: str
    job_definition_id: str | None = None
    status: str
    worker_id: str | None = None
    name: str
    task_prompt: str
    agent_type: str
    agent_config: dict = {}
    mcp_servers: list = []
    credential_ids: list = []
    required_labels: dict = {}
    timeout_seconds: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    exit_code: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunCompleteRequest(BaseModel):
    status: str  # completed, failed
    result: str | None = None
    exit_code: int | None = None
