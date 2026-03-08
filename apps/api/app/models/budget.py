"""BudgetPolicy and CostLedger models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class BudgetPolicy(Base, TimestampMixin):
    __tablename__ = "budget_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    scope_type: Mapped[str] = mapped_column(String(30))
    scope_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    period_type: Mapped[str] = mapped_column(String(30))
    limit_usd: Mapped[float] = mapped_column(Numeric(12, 4))
    warn_threshold_pct: Mapped[int] = mapped_column(Integer, default=80)
    stop_threshold_pct: Mapped[int] = mapped_column(Integer, default=100)


class CostLedger(Base):
    __tablename__ = "cost_ledger"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    scope_type: Mapped[str] = mapped_column(String(30))
    scope_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    provider_name: Mapped[str] = mapped_column(String(60))
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6))
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    run_type: Mapped[str] = mapped_column(String(30))
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
