"""Per-user transient autonomy override.

Persists short-lived autonomy-level overrides (for example, "drop to ASSIST
for the next 30 minutes") that the operator can flip from the Autonomy Dial
in the status bar. The persistent per-company default lives in app_config
under the AUTONOMY_LEVEL key; this table only stores time-boxed deviations.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AutonomySessionOverride(Base):
    __tablename__ = "autonomy_session_overrides"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=True, index=True
    )
    autonomy_level: Mapped[str] = mapped_column(String(30), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
