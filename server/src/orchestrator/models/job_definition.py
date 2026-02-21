from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class JobDefinition(Base, TimestampMixin):
    __tablename__ = "job_definitions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, nullable=False, index=True, default="default")
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String, default="goose")
    agent_config: Mapped[dict | None] = mapped_column(JSON, default=dict)
    mcp_servers: Mapped[list | None] = mapped_column(JSON, default=list)
    env_vars: Mapped[dict | None] = mapped_column(JSON, default=dict)
    credential_ids: Mapped[list | None] = mapped_column(JSON, default=list)
    labels: Mapped[dict | None] = mapped_column(JSON, default=dict)
    skill_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)  # null=all, []=none, ["name"]=specific
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=1800)
