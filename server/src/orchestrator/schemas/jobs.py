from datetime import datetime

from pydantic import BaseModel


class McpServerConfig(BaseModel):
    name: str
    type: str = "stdio"
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class AgentConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5"
    max_turns: int = 30


class JobDefinitionCreate(BaseModel):
    name: str
    description: str | None = None
    task_prompt: str
    agent_type: str = "goose"
    agent_config: AgentConfig | dict = {}
    mcp_servers: list[McpServerConfig | dict] = []
    env_vars: dict[str, str] = {}
    credential_ids: list[str] = []
    labels: dict[str, str] = {}
    timeout_seconds: int = 1800
    webhook_url: str | None = None
    webhook_secret: str | None = None


class JobDefinitionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    task_prompt: str | None = None
    agent_type: str | None = None
    agent_config: AgentConfig | dict | None = None
    mcp_servers: list[McpServerConfig | dict] | None = None
    env_vars: dict[str, str] | None = None
    credential_ids: list[str] | None = None
    labels: dict[str, str] | None = None
    timeout_seconds: int | None = None
    webhook_url: str | None = None
    webhook_secret: str | None = None


class JobDefinitionResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    task_prompt: str
    agent_type: str
    agent_config: dict = {}
    mcp_servers: list = []
    env_vars: dict = {}
    credential_ids: list = []
    labels: dict = {}
    timeout_seconds: int
    webhook_url: str | None = None
    # Note: webhook_secret intentionally excluded from response for security
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
