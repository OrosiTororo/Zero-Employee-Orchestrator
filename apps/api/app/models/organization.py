"""Department and Team models."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    parent_department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("departments.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("departments.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    heartbeat_policy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    budget_policy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
