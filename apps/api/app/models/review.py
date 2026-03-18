"""Review and ApprovalRequest models."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tickets.id"), nullable=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("tasks.id"), nullable=True)
    reviewer_type: Mapped[str] = mapped_column(String(30))
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    reviewer_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30))
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    comments_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(60))
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    requested_by_type: Mapped[str] = mapped_column(String(30))
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    requested_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
    approver_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), default="requested")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(30))
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
