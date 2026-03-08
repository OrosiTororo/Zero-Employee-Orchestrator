"""Artifact model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tickets.id"), nullable=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tasks.id"), nullable=True
    )
    artifact_type: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(500))
    storage_type: Mapped[str] = mapped_column(String(30))
    path_or_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by_type: Mapped[str] = mapped_column(String(30))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
