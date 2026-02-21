from sqlalchemy import JSON, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, nullable=False, index=True, default="default")
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    license: Mapped[str | None] = mapped_column(String, nullable=True)
    compatibility: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_kv: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    allowed_tools: Mapped[str | None] = mapped_column(String, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    file_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_skill_workspace_name"),
    )
