from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.models.base import Base, TimestampMixin, new_id


class Credential(Base, TimestampMixin):
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    env_var: Mapped[str] = mapped_column(String, nullable=False)  # e.g. ANTHROPIC_API_KEY
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
