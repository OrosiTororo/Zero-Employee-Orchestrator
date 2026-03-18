"""Spec model."""

import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Spec(Base, TimestampMixin):
    __tablename__ = "specs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tickets.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    acceptance_criteria_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_type: Mapped[str] = mapped_column(String(30))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
