from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="worker")  # admin, worker
