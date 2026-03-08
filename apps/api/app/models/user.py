"""User and CompanyMember models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="user")
    status: Mapped[str] = mapped_column(String(30), default="active")
    auth_provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CompanyMember(Base, TimestampMixin):
    __tablename__ = "company_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), index=True
    )
    company_role: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
