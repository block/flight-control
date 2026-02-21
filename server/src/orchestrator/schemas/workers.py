from datetime import datetime

from pydantic import BaseModel


class WorkerRegisterRequest(BaseModel):
    name: str
    labels: dict[str, str] = {}


class WorkerRegisterResponse(BaseModel):
    id: str
    name: str


class WorkerHeartbeatRequest(BaseModel):
    worker_id: str
    status: str = "online"  # online, busy


class SkillFilePollInfo(BaseModel):
    file_path: str
    size_bytes: int
    checksum_sha256: str
    content_type: str


class SkillPollInfo(BaseModel):
    id: str
    name: str
    instructions: str
    allowed_tools: str | None = None
    files: list[SkillFilePollInfo] = []


class PollResponse(BaseModel):
    run_id: str
    name: str
    task_prompt: str
    agent_type: str
    agent_config: dict = {}
    mcp_servers: list = []
    env_vars: dict = {}
    credentials: dict[str, str] = {}  # env_var -> decrypted value
    skills: list[SkillPollInfo] = []
    timeout_seconds: int


class LogBatchRequest(BaseModel):
    lines: list["LogLine"]


class LogLine(BaseModel):
    stream: str = "stdout"
    line: str
    sequence: int


class WorkerResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    status: str
    labels: dict = {}
    last_heartbeat: datetime
    current_run_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
