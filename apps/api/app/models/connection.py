"""ToolConnection and ToolCallTrace models."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class ToolConnection(Base, TimestampMixin):
    __tablename__ = "tool_connections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    connection_type: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30))
    auth_type: Mapped[str] = mapped_column(String(30))
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ToolCallTrace(Base):
    __tablename__ = "tool_call_traces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    task_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("task_runs.id"), nullable=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("agents.id"), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(255))
    request_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
