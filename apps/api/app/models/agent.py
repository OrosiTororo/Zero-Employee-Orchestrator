"""Agent model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("teams.id"), nullable=True
    )
    manager_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(String(60))
    runtime_type: Mapped[str] = mapped_column(String(60))
    provider_name: Mapped[str] = mapped_column(String(60))
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="provisioning")
    autonomy_level: Mapped[str] = mapped_column(String(30))
    can_delegate: Mapped[bool] = mapped_column(Boolean, default=False)
    can_write_external: Mapped[bool] = mapped_column(Boolean, default=False)
    can_spend_budget: Mapped[bool] = mapped_column(Boolean, default=False)
    heartbeat_policy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    budget_policy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
