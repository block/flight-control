from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id, utcnow


class Worker(Base, TimestampMixin):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="online")  # online, offline, busy
    labels: Mapped[dict | None] = mapped_column(JSON, default=dict)
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    current_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
