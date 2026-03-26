"""Skill, Plugin, and Extension models."""

import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    """Skill -- A single-purpose AI execution capability unit.

    Skills with is_system_protected=True are essential for system operation and cannot be deleted.
    """

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    skill_type: Mapped[str] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="experimental")
    source_type: Mapped[str] = mapped_column(String(30))
    source_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    policy_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_system_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_code: Mapped[str | None] = mapped_column(Text, nullable=True)


class Plugin(Base, TimestampMixin):
    """Plugin -- A business feature package that bundles multiple Skills."""

    __tablename__ = "plugins"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    manifest_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_system_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Extension(Base, TimestampMixin):
    """Extension -- App environment, UI, and connectivity extensions."""

    __tablename__ = "extensions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    manifest_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_system_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
