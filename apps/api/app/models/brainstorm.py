"""Brainstorm session ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BrainstormSessionRecord(Base):
    """壁打ち（ブレインストーミング）セッションの記録."""

    __tablename__ = "brainstorm_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_type: Mapped[str] = mapped_column(String(60), default="brainstorm")
    # brainstorm | debate | review | ideation | strategy
    model_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 壁打ちに使用するモデル一覧
    conversation_history: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {"messages": [{"role": "user"|"assistant"|"model:<id>", "content": ..., "timestamp": ...}]}
    insights_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    # active | paused | completed | archived
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_chars: Mapped[int] = mapped_column(Integer, default=0)
    is_multi_model: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )
