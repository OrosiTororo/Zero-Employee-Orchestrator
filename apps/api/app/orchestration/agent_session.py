"""Agent Session — AIエージェントのコンテキスト永続化.

AIチームメイトがコンテキストを保持したまま複数ラウンドの
やり取りができるようにするセッション管理。

例: debuggerエージェントが調査を終えた後 idle 状態で待機し、
再メッセージ時に前回のコンテキストを保持したまま再調査に取り掛かれる。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Float, Integer, String, Uuid, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    ACTIVE = "active"  # 作業中
    IDLE = "idle"  # 待機中（コンテキスト保持）
    SUSPENDED = "suspended"  # 一時停止
    EXPIRED = "expired"  # 期限切れ
    TERMINATED = "terminated"


class AgentSessionRecord(Base):
    """エージェントセッションの永続化."""

    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[str] = mapped_column(String(255), index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    role: Mapped[str] = mapped_column(String(60), default="general")

    # コンテキスト
    context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    conversation_history: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    working_memory: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # メトリクス
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    round_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    # タイムスタンプ
    started_at: Mapped[float] = mapped_column(Float, default=time.time)
    last_active_at: Mapped[float] = mapped_column(Float, default=time.time)
    idle_since: Mapped[float | None] = mapped_column(Float, nullable=True)
    expires_at: Mapped[float | None] = mapped_column(Float, nullable=True)


@dataclass
class InMemorySession:
    """インメモリのセッションデータ（高速アクセス用）."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    company_id: str | None = None
    task_id: str | None = None
    role: str = "general"
    status: SessionStatus = SessionStatus.ACTIVE

    # コンテキスト
    context: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    working_memory: dict[str, Any] = field(default_factory=dict)

    # メトリクス
    message_count: int = 0
    round_count: int = 0
    total_tokens_used: int = 0

    # タイムスタンプ
    started_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    idle_since: float | None = None

    # セッション有効期限（秒）
    ttl: float = 86400  # 24時間

    def is_expired(self) -> bool:
        return time.time() > self.started_at + self.ttl

    def add_message(
        self, role: str, content: str, metadata: dict | None = None
    ) -> None:
        """会話履歴にメッセージを追加."""
        self.conversation_history.append(
            {
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": time.time(),
            }
        )
        self.message_count += 1
        self.last_active_at = time.time()
        if self.status == SessionStatus.IDLE:
            self.status = SessionStatus.ACTIVE
            self.idle_since = None

    def add_to_working_memory(self, key: str, value: Any) -> None:
        """ワーキングメモリに情報を追加."""
        self.working_memory[key] = {
            "value": value,
            "stored_at": time.time(),
        }
        self.last_active_at = time.time()

    def get_from_working_memory(self, key: str) -> Any:
        """ワーキングメモリから情報を取得."""
        entry = self.working_memory.get(key)
        return entry["value"] if entry else None

    def go_idle(self) -> None:
        """アイドル状態に移行."""
        self.status = SessionStatus.IDLE
        self.idle_since = time.time()
        self.round_count += 1

    def resume(self) -> None:
        """アイドル状態から復帰."""
        self.status = SessionStatus.ACTIVE
        self.idle_since = None
        self.last_active_at = time.time()

    def get_context_summary(self) -> dict[str, Any]:
        """セッションのコンテキストサマリーを取得."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status.value,
            "message_count": self.message_count,
            "round_count": self.round_count,
            "working_memory_keys": list(self.working_memory.keys()),
            "conversation_length": len(self.conversation_history),
            "idle_seconds": time.time() - self.idle_since if self.idle_since else None,
            "total_seconds": time.time() - self.started_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "company_id": self.company_id,
            "task_id": self.task_id,
            "role": self.role,
            "status": self.status.value,
            "context": self.context,
            "working_memory_keys": list(self.working_memory.keys()),
            "message_count": self.message_count,
            "round_count": self.round_count,
            "total_tokens_used": self.total_tokens_used,
            "started_at": self.started_at,
            "last_active_at": self.last_active_at,
            "idle_since": self.idle_since,
        }


class AgentSessionManager:
    """エージェントセッションの管理."""

    def __init__(self, max_sessions: int = 500) -> None:
        self._sessions: dict[str, InMemorySession] = {}
        self._agent_sessions: dict[str, list[str]] = {}  # agent_id -> session_ids
        self._max = max_sessions

    def create_session(
        self,
        agent_id: str,
        role: str = "general",
        *,
        company_id: str | None = None,
        task_id: str | None = None,
        initial_context: dict[str, Any] | None = None,
        ttl: float = 86400,
    ) -> InMemorySession:
        """新しいセッションを作成."""
        self._cleanup_expired()

        session = InMemorySession(
            agent_id=agent_id,
            company_id=company_id,
            task_id=task_id,
            role=role,
            context=initial_context or {},
            ttl=ttl,
        )
        self._sessions[session.session_id] = session

        if agent_id not in self._agent_sessions:
            self._agent_sessions[agent_id] = []
        self._agent_sessions[agent_id].append(session.session_id)

        logger.info(
            "Session created: %s for agent %s (role: %s)",
            session.session_id,
            agent_id,
            role,
        )
        return session

    def get_session(self, session_id: str) -> InMemorySession | None:
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
            return None
        return session

    def get_active_session(self, agent_id: str) -> InMemorySession | None:
        """エージェントのアクティブまたはアイドルセッションを取得."""
        session_ids = self._agent_sessions.get(agent_id, [])
        for sid in reversed(session_ids):
            s = self._sessions.get(sid)
            if (
                s
                and not s.is_expired()
                and s.status in (SessionStatus.ACTIVE, SessionStatus.IDLE)
            ):
                return s
        return None

    def get_or_create_session(
        self,
        agent_id: str,
        role: str = "general",
        **kwargs: Any,
    ) -> InMemorySession:
        """既存のアクティブ/アイドルセッションを取得、なければ新規作成."""
        existing = self.get_active_session(agent_id)
        if existing:
            existing.resume()
            return existing
        return self.create_session(agent_id, role, **kwargs)

    def list_sessions(
        self,
        company_id: str | None = None,
        status: SessionStatus | None = None,
        agent_id: str | None = None,
    ) -> list[InMemorySession]:
        """セッション一覧を取得."""
        result = list(self._sessions.values())
        if company_id:
            result = [s for s in result if s.company_id == company_id]
        if status:
            result = [s for s in result if s.status == status]
        if agent_id:
            result = [s for s in result if s.agent_id == agent_id]
        return result

    def terminate_session(self, session_id: str) -> bool:
        """セッションを終了."""
        session = self._sessions.get(session_id)
        if session:
            session.status = SessionStatus.TERMINATED
            return True
        return False

    def _cleanup_expired(self) -> None:
        """期限切れセッションをクリーンアップ."""
        if len(self._sessions) < self._max:
            return
        expired = [
            sid
            for sid, s in self._sessions.items()
            if s.is_expired() or s.status == SessionStatus.TERMINATED
        ]
        for sid in expired:
            del self._sessions[sid]

    async def persist_session(self, session: InMemorySession, db: AsyncSession) -> None:
        """セッションをDBに永続化."""
        result = await db.execute(
            select(AgentSessionRecord).where(
                AgentSessionRecord.id == uuid.UUID(session.session_id)
                if len(session.session_id) == 36
                else AgentSessionRecord.agent_id == session.agent_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = session.status.value
            existing.context_json = session.context
            existing.conversation_history = {
                "messages": session.conversation_history[-100:]
            }
            existing.working_memory = session.working_memory
            existing.message_count = session.message_count
            existing.round_count = session.round_count
            existing.total_tokens_used = session.total_tokens_used
            existing.last_active_at = session.last_active_at
            existing.idle_since = session.idle_since
        else:
            record = AgentSessionRecord(
                id=uuid.uuid4(),
                agent_id=session.agent_id,
                company_id=uuid.UUID(session.company_id)
                if session.company_id
                else None,
                task_id=session.task_id,
                status=session.status.value,
                role=session.role,
                context_json=session.context,
                conversation_history={"messages": session.conversation_history[-100:]},
                working_memory=session.working_memory,
                message_count=session.message_count,
                round_count=session.round_count,
                total_tokens_used=session.total_tokens_used,
                started_at=session.started_at,
                last_active_at=session.last_active_at,
                idle_since=session.idle_since,
            )
            db.add(record)
        await db.flush()

    async def restore_session(
        self, agent_id: str, db: AsyncSession
    ) -> InMemorySession | None:
        """DBからセッションを復元."""
        result = await db.execute(
            select(AgentSessionRecord)
            .where(
                AgentSessionRecord.agent_id == agent_id,
                AgentSessionRecord.status.in_(["active", "idle"]),
            )
            .order_by(AgentSessionRecord.last_active_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        session = InMemorySession(
            session_id=str(record.id),
            agent_id=record.agent_id,
            company_id=str(record.company_id) if record.company_id else None,
            task_id=record.task_id,
            role=record.role,
            status=SessionStatus(record.status),
            context=record.context_json or {},
            conversation_history=(record.conversation_history or {}).get(
                "messages", []
            ),
            working_memory=record.working_memory or {},
            message_count=record.message_count,
            round_count=record.round_count,
            total_tokens_used=record.total_tokens_used,
            started_at=record.started_at,
            last_active_at=record.last_active_at,
            idle_since=record.idle_since,
        )

        self._sessions[session.session_id] = session
        if agent_id not in self._agent_sessions:
            self._agent_sessions[agent_id] = []
        self._agent_sessions[agent_id].append(session.session_id)

        session.resume()
        return session


# Global singleton
session_manager = AgentSessionManager()
