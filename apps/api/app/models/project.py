"""Project and Goal models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    owner_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    parent_goal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("goals.id"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_level: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    metric_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metric_target: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    metric_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
