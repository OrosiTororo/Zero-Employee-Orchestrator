"""PolicyPack and SecretRef models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class PolicyPack(Base, TimestampMixin):
    __tablename__ = "policy_packs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    rules_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SecretRef(Base, TimestampMixin):
    __tablename__ = "secret_refs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    secret_type: Mapped[str] = mapped_column(String(60))
    provider: Mapped[str] = mapped_column(String(60))
    masked_value: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rotation_policy_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
