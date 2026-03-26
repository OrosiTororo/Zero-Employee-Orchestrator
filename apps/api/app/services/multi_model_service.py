"""Multi-model comparison, brainstorming, and conversation memory service.

Sends the same input to multiple LLM models and compares responses,
and manages brainstorming sessions with users.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# ---------------------------------------------------------------------------
# Text utility (accurate character counting)
# ---------------------------------------------------------------------------


class TextAnalyzer:
    """テキスト分析ユーティリティ — 正確な文字数カウント."""

    @staticmethod
    def count_characters(text: str) -> dict[str, int]:
        """正確な文字数カウント（Unicode 対応）."""
        total = len(text)
        # カテゴリ別カウント
        hiragana = 0
        katakana = 0
        kanji = 0
        ascii_chars = 0
        digits = 0
        spaces = 0
        newlines = 0
        other = 0

        for ch in text:
            if ch == "\n":
                newlines += 1
            elif ch == " " or ch == "\u3000":
                spaces += 1
            elif "\u3040" <= ch <= "\u309f":
                hiragana += 1
            elif "\u30a0" <= ch <= "\u30ff":
                katakana += 1
            elif "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf":
                kanji += 1
            elif ch.isascii() and ch.isalpha():
                ascii_chars += 1
            elif ch.isdigit():
                digits += 1
            else:
                other += 1

        return {
            "total": total,
            "total_excluding_spaces": total - spaces - newlines,
            "hiragana": hiragana,
            "katakana": katakana,
            "kanji": kanji,
            "ascii": ascii_chars,
            "digits": digits,
            "spaces": spaces,
            "newlines": newlines,
            "other": other,
            "words_estimate": len(text.split()),
        }

    @staticmethod
    def truncate_to_length(text: str, max_chars: int) -> str:
        """指定文字数で切り詰め."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars]

    @staticmethod
    def validate_length(text: str, min_chars: int = 0, max_chars: int | None = None) -> dict:
        """文字数バリデーション."""
        length = len(text)
        valid = length >= min_chars
        if max_chars is not None:
            valid = valid and length <= max_chars
        return {
            "length": length,
            "min_required": min_chars,
            "max_allowed": max_chars,
            "is_valid": valid,
            "over_by": max(0, length - max_chars) if max_chars else 0,
            "under_by": max(0, min_chars - length),
        }


# ---------------------------------------------------------------------------
# DB models
# ---------------------------------------------------------------------------


class MultiModelComparisonRecord(Base):
    """マルチモデル比較リクエストの記録."""

    __tablename__ = "multi_model_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    input_text: Mapped[str] = mapped_column(Text)
    input_char_count: Mapped[int] = mapped_column(Integer, default=0)
    models_requested: Mapped[list] = mapped_column(JSON)  # ["gpt-4", "claude-3", ...]
    responses_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # responses_json: {model_id: {text, tokens, latency_ms, char_count, error}}
    comparison_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | processing | completed | failed
    session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


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


class ConversationMemoryRecord(Base):
    """会話記憶の永続化 — ユーザーとエージェントの全会話を保管."""

    __tablename__ = "conversation_memories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    session_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(60))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(60), default="text")
    # text | brainstorm | comparison | task | secretary
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


class AgentRoleModelConfig(Base):
    """エージェント役割ごとのモデル設定."""

    __tablename__ = "agent_role_model_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    role_name: Mapped[str] = mapped_column(String(120), index=True)
    # secretary | advisor | researcher | engineer | marketer | pm | custom
    model_id: Mapped[str] = mapped_column(String(255))
    # e.g. "anthropic/claude-opus", "openai/gpt"
    fallback_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Multi-model comparison service
# ---------------------------------------------------------------------------


class MultiModelService:
    """複数モデルに同一入力を送り、回答を比較するサービス."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_comparison(
        self,
        company_id: str,
        input_text: str,
        model_ids: list[str],
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> MultiModelComparisonRecord:
        """マルチモデル比較リクエストを作成."""
        char_count = len(input_text)
        record = MultiModelComparisonRecord(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id),
            user_id=uuid.UUID(user_id) if user_id else None,
            input_text=input_text,
            input_char_count=char_count,
            models_requested=model_ids,
            status="pending",
            session_id=uuid.UUID(session_id) if session_id else None,
            metadata_json=metadata or {},
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def record_model_response(
        self,
        comparison_id: str,
        model_id: str,
        response_text: str,
        *,
        latency_ms: int = 0,
        tokens_used: int = 0,
        error: str | None = None,
    ) -> MultiModelComparisonRecord | None:
        """個別モデルの回答を記録."""
        result = await self._db.execute(
            select(MultiModelComparisonRecord).where(
                MultiModelComparisonRecord.id == uuid.UUID(comparison_id)
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        responses = record.responses_json or {}
        char_analysis = TextAnalyzer.count_characters(response_text)
        responses[model_id] = {
            "text": response_text,
            "tokens": tokens_used,
            "latency_ms": latency_ms,
            "char_count": char_analysis["total"],
            "char_analysis": char_analysis,
            "error": error,
            "recorded_at": time.time(),
        }
        record.responses_json = responses

        # 全モデル回答完了かチェック
        all_done = all(mid in responses for mid in record.models_requested)
        if all_done:
            record.status = "completed"

        await self._db.flush()
        return record

    async def get_comparison(self, comparison_id: str) -> MultiModelComparisonRecord | None:
        """比較結果を取得."""
        result = await self._db.execute(
            select(MultiModelComparisonRecord).where(
                MultiModelComparisonRecord.id == uuid.UUID(comparison_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_comparisons(
        self,
        company_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MultiModelComparisonRecord]:
        """比較一覧を取得."""
        stmt = (
            select(MultiModelComparisonRecord)
            .where(MultiModelComparisonRecord.company_id == uuid.UUID(company_id))
            .order_by(MultiModelComparisonRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Brainstorming service
# ---------------------------------------------------------------------------


class BrainstormService:
    """壁打ち（ブレインストーミング）セッション管理."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(
        self,
        company_id: str,
        *,
        user_id: str | None = None,
        title: str = "",
        topic: str | None = None,
        session_type: str = "brainstorm",
        model_ids: list[str] | None = None,
        is_multi_model: bool = False,
    ) -> BrainstormSessionRecord:
        """壁打ちセッションを作成."""
        record = BrainstormSessionRecord(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id),
            user_id=uuid.UUID(user_id) if user_id else None,
            title=title or f"壁打ちセッション ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            topic=topic,
            session_type=session_type,
            model_ids=model_ids or [],
            conversation_history={"messages": []},
            insights_json=[],
            status="active",
            message_count=0,
            total_chars=0,
            is_multi_model=is_multi_model,
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        model_id: str | None = None,
        metadata: dict | None = None,
    ) -> BrainstormSessionRecord | None:
        """壁打ちセッションにメッセージを追加."""
        result = await self._db.execute(
            select(BrainstormSessionRecord).where(
                BrainstormSessionRecord.id == uuid.UUID(session_id)
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        history = record.conversation_history or {"messages": []}
        char_count = len(content)
        message = {
            "role": role if not model_id else f"model:{model_id}",
            "content": content,
            "char_count": char_count,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        history["messages"].append(message)
        record.conversation_history = history
        record.message_count += 1
        record.total_chars += char_count

        await self._db.flush()
        return record

    async def get_session(self, session_id: str) -> BrainstormSessionRecord | None:
        """セッションを取得."""
        result = await self._db.execute(
            select(BrainstormSessionRecord).where(
                BrainstormSessionRecord.id == uuid.UUID(session_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        company_id: str,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[BrainstormSessionRecord]:
        """セッション一覧を取得."""
        stmt = select(BrainstormSessionRecord).where(
            BrainstormSessionRecord.company_id == uuid.UUID(company_id),
        )
        if status:
            stmt = stmt.where(BrainstormSessionRecord.status == status)
        stmt = stmt.order_by(BrainstormSessionRecord.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update_session_status(
        self,
        session_id: str,
        status: str,
    ) -> BrainstormSessionRecord | None:
        """セッションのステータスを更新."""
        record = await self.get_session(session_id)
        if not record:
            return None
        record.status = status
        await self._db.flush()
        return record

    async def search_sessions(
        self,
        company_id: str,
        query: str,
        *,
        limit: int = 20,
    ) -> list[BrainstormSessionRecord]:
        """壁打ちセッションを検索."""
        cid = uuid.UUID(company_id)
        pattern = f"%{query}%"
        stmt = (
            select(BrainstormSessionRecord)
            .where(
                BrainstormSessionRecord.company_id == cid,
                (
                    BrainstormSessionRecord.title.ilike(pattern)
                    | BrainstormSessionRecord.topic.ilike(pattern)
                ),
            )
            .order_by(BrainstormSessionRecord.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Conversation memory service
# ---------------------------------------------------------------------------


class ConversationMemoryService:
    """ユーザーとエージェントの全会話を保管するサービス."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def store_message(
        self,
        company_id: str,
        role: str,
        content: str,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        session_ref: str | None = None,
        content_type: str = "text",
        metadata: dict | None = None,
    ) -> ConversationMemoryRecord:
        """会話メッセージを保存."""
        record = ConversationMemoryRecord(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id),
            user_id=uuid.UUID(user_id) if user_id else None,
            agent_id=uuid.UUID(agent_id) if agent_id else None,
            session_ref=session_ref,
            role=role,
            content=content,
            char_count=len(content),
            content_type=content_type,
            metadata_json=metadata or {},
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def get_conversation_history(
        self,
        company_id: str,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        session_ref: str | None = None,
        content_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ConversationMemoryRecord]:
        """会話履歴を取得."""
        stmt = select(ConversationMemoryRecord).where(
            ConversationMemoryRecord.company_id == uuid.UUID(company_id)
        )
        if user_id:
            stmt = stmt.where(ConversationMemoryRecord.user_id == uuid.UUID(user_id))
        if agent_id:
            stmt = stmt.where(ConversationMemoryRecord.agent_id == uuid.UUID(agent_id))
        if session_ref:
            stmt = stmt.where(ConversationMemoryRecord.session_ref == session_ref)
        if content_type:
            stmt = stmt.where(ConversationMemoryRecord.content_type == content_type)
        stmt = stmt.order_by(ConversationMemoryRecord.created_at.asc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_memories(
        self,
        company_id: str,
        query: str,
        *,
        limit: int = 50,
    ) -> list[ConversationMemoryRecord]:
        """会話記憶を検索（過去の会話から関連情報を見つける）."""
        cid = uuid.UUID(company_id)
        pattern = f"%{query}%"
        stmt = (
            select(ConversationMemoryRecord)
            .where(
                ConversationMemoryRecord.company_id == cid,
                ConversationMemoryRecord.content.ilike(pattern),
            )
            .order_by(ConversationMemoryRecord.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_total_stats(
        self,
        company_id: str,
        *,
        user_id: str | None = None,
    ) -> dict:
        """会話記憶の統計を取得."""
        cid = uuid.UUID(company_id)
        stmt = select(ConversationMemoryRecord).where(ConversationMemoryRecord.company_id == cid)
        if user_id:
            stmt = stmt.where(ConversationMemoryRecord.user_id == uuid.UUID(user_id))
        result = await self._db.execute(stmt)
        records = list(result.scalars().all())

        total_messages = len(records)
        total_chars = sum(r.char_count for r in records)
        role_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        for r in records:
            role_counts[r.role] = role_counts.get(r.role, 0) + 1
            type_counts[r.content_type] = type_counts.get(r.content_type, 0) + 1

        return {
            "total_messages": total_messages,
            "total_characters": total_chars,
            "by_role": role_counts,
            "by_content_type": type_counts,
        }


# ---------------------------------------------------------------------------
# Agent role model configuration service
# ---------------------------------------------------------------------------


class AgentRoleModelService:
    """エージェントの役割ごとに使用するモデルを設定・管理するサービス."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def set_role_model(
        self,
        company_id: str,
        role_name: str,
        model_id: str,
        *,
        agent_id: str | None = None,
        fallback_model_id: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        system_prompt: str | None = None,
    ) -> AgentRoleModelConfig:
        """役割に対するモデル設定を追加または更新."""
        cid = uuid.UUID(company_id)
        stmt = select(AgentRoleModelConfig).where(
            AgentRoleModelConfig.company_id == cid,
            AgentRoleModelConfig.role_name == role_name,
        )
        if agent_id:
            stmt = stmt.where(AgentRoleModelConfig.agent_id == uuid.UUID(agent_id))
        else:
            stmt = stmt.where(AgentRoleModelConfig.agent_id.is_(None))

        result = await self._db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.model_id = model_id
            if fallback_model_id is not None:
                existing.fallback_model_id = fallback_model_id
            if max_tokens is not None:
                existing.max_tokens = max_tokens
            if temperature is not None:
                existing.temperature = temperature
            if system_prompt is not None:
                existing.system_prompt = system_prompt
            await self._db.flush()
            return existing

        config = AgentRoleModelConfig(
            id=uuid.uuid4(),
            company_id=cid,
            agent_id=uuid.UUID(agent_id) if agent_id else None,
            role_name=role_name,
            model_id=model_id,
            fallback_model_id=fallback_model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
        )
        self._db.add(config)
        await self._db.flush()
        return config

    async def get_role_model(
        self,
        company_id: str,
        role_name: str,
        *,
        agent_id: str | None = None,
    ) -> AgentRoleModelConfig | None:
        """役割に設定されたモデルを取得（エージェント個別設定優先）."""
        cid = uuid.UUID(company_id)

        # エージェント個別設定を優先
        if agent_id:
            stmt = select(AgentRoleModelConfig).where(
                AgentRoleModelConfig.company_id == cid,
                AgentRoleModelConfig.role_name == role_name,
                AgentRoleModelConfig.agent_id == uuid.UUID(agent_id),
                AgentRoleModelConfig.is_active.is_(True),
            )
            result = await self._db.execute(stmt)
            config = result.scalar_one_or_none()
            if config:
                return config

        # 全体設定にフォールバック
        stmt = select(AgentRoleModelConfig).where(
            AgentRoleModelConfig.company_id == cid,
            AgentRoleModelConfig.role_name == role_name,
            AgentRoleModelConfig.agent_id.is_(None),
            AgentRoleModelConfig.is_active.is_(True),
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_role_models(
        self,
        company_id: str,
    ) -> list[AgentRoleModelConfig]:
        """全役割モデル設定を取得."""
        stmt = (
            select(AgentRoleModelConfig)
            .where(AgentRoleModelConfig.company_id == uuid.UUID(company_id))
            .order_by(AgentRoleModelConfig.role_name)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def delete_role_model(
        self,
        config_id: str,
    ) -> bool:
        """役割モデル設定を削除."""
        result = await self._db.execute(
            select(AgentRoleModelConfig).where(AgentRoleModelConfig.id == uuid.UUID(config_id))
        )
        config = result.scalar_one_or_none()
        if config:
            await self._db.delete(config)
            await self._db.flush()
            return True
        return False
