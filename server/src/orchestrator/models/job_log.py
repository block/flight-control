from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class JobLog(Base, TimestampMixin):
    __tablename__ = "job_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    stream: Mapped[str] = mapped_column(String, default="stdout")  # stdout, stderr
    line: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
