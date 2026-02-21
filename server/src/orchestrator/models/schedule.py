from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_definition_id: Mapped[str] = mapped_column(String, nullable=False)
    cron_expression: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
