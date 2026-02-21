from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class SkillFile(Base, TimestampMixin):
    __tablename__ = "skill_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    skill_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
