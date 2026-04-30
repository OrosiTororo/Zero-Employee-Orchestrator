"""Plan model."""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tickets.id"), nullable=True, index=True
    )
    spec_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("specs.id"), nullable=True, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str] = mapped_column(String(30))
    plan_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True
    )
    # Standalone proposal mode: original natural-language goal stored when the
    # plan was generated via /plans without a ticket/spec attached.
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Sub-orchestrator parent plan — when a delegated agent (CrewAI, Dify, …)
    # returns its own plan, ZEO persists it as a child Plan and links the
    # parent via this column so the full delegation tree is auditable.
    parent_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("plans.id"), nullable=True, index=True
    )
    # Free-form provenance metadata: originating framework name, sub-plan
    # extraction source, intermediate reasoning. Kept loose so adapters can
    # write whatever the upstream framework exposes without a schema rev.
    delegation_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
