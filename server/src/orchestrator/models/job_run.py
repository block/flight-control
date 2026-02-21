from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class JobRun(Base, TimestampMixin):
    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_definition_id: Mapped[str | None] = mapped_column(String, nullable=True)  # null for ad-hoc runs
    status: Mapped[str] = mapped_column(String, default="queued")  # queued, assigned, running, completed, failed, timeout, cancelled
    worker_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Snapshotted config at run time
    name: Mapped[str] = mapped_column(String, nullable=False)
    task_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String, default="goose")
    agent_config: Mapped[dict | None] = mapped_column(JSON, default=dict)
    mcp_servers: Mapped[list | None] = mapped_column(JSON, default=list)
    env_vars: Mapped[dict | None] = mapped_column(JSON, default=dict)
    credential_ids: Mapped[list | None] = mapped_column(JSON, default=list)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=1800)
    
    # Retry configuration (snapshotted from job definition)
    max_retries: Mapped[int] = mapped_column(Integer, default=0)
    retry_backoff_seconds: Mapped[int] = mapped_column(Integer, default=60)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    parent_run_id: Mapped[str | None] = mapped_column(String, nullable=True)  # Links retries

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
