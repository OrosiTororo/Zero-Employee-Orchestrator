"""HeartbeatPolicy and HeartbeatRun models."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class HeartbeatPolicy(Base, TimestampMixin):
    __tablename__ = "heartbeat_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    cron_expr: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(60), default="UTC")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    jitter_seconds: Mapped[int] = mapped_column(Integer, default=0)
    max_parallel_runs: Mapped[int] = mapped_column(Integer, default=1)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class HeartbeatRun(Base):
    __tablename__ = "heartbeat_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("heartbeat_policies.id"), index=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("agents.id"), nullable=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("teams.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
