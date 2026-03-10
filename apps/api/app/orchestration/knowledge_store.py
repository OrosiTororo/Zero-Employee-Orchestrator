"""Knowledge Store — ユーザー設定・ナレッジの永続記憶.

計画時にユーザーに同じ質問を繰り返さないよう、
ファイル/フォルダの権限設定、業務資料の場所、ユーザーの好みなどを
永続化して活用する。

機能:
  - ユーザー設定の記憶（フォルダパス・権限・好み）
  - 変更検知（前回の情報との差分検出）
  - Experience Memory との統合
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import JSON, String, Text, Uuid, func, select, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

logger = logging.getLogger(__name__)


class KnowledgeCategory(str, Enum):
    """ナレッジの種類."""

    FILE_PERMISSION = "file_permission"  # ファイル・フォルダへのアクセス許可
    FOLDER_LOCATION = "folder_location"  # 業務資料フォルダの場所
    USER_PREFERENCE = "user_preference"  # ユーザーの好み・設定
    TOOL_CONFIG = "tool_config"  # ツール接続設定
    WORKFLOW_PATTERN = "workflow_pattern"  # よく使うワークフローパターン
    AGENT_INSTRUCTION = "agent_instruction"  # エージェントへの恒久指示
    ENVIRONMENT = "environment"  # 環境情報（OS、パスなど）
    CREDENTIAL_HINT = "credential_hint"  # 認証情報のヒント（値自体は保存しない）
    CHANGE_LOG = "change_log"  # 変更履歴


class KnowledgeRecord(Base):
    """永続化されたナレッジエントリ."""

    __tablename__ = "knowledge_store"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    key: Mapped[str] = mapped_column(String(500), index=True)
    value: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(120), default="user_input")
    last_used_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)
    use_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


class ChangeDetectionRecord(Base):
    """変更検知の記録."""

    __tablename__ = "change_detections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(255))
    change_type: Mapped[str] = mapped_column(String(30))  # created, updated, deleted
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class KnowledgeStore:
    """ユーザー設定・ナレッジの永続管理."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def remember(
        self,
        category: KnowledgeCategory | str,
        key: str,
        value: str,
        *,
        company_id: str | uuid.UUID | None = None,
        user_id: str | uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        source: str = "user_input",
    ) -> KnowledgeRecord:
        """ナレッジを記憶する（既存キーは更新）."""
        cat = category.value if isinstance(category, KnowledgeCategory) else category
        cid = uuid.UUID(str(company_id)) if company_id else None
        uid = uuid.UUID(str(user_id)) if user_id else None

        stmt = select(KnowledgeRecord).where(
            KnowledgeRecord.category == cat,
            KnowledgeRecord.key == key,
        )
        if cid:
            stmt = stmt.where(KnowledgeRecord.company_id == cid)
        if uid:
            stmt = stmt.where(KnowledgeRecord.user_id == uid)

        result = await self._db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            old_value = existing.value
            existing.value = value
            existing.metadata_json = metadata or existing.metadata_json
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)

            # 変更検知
            if old_value != value:
                change = ChangeDetectionRecord(
                    id=uuid.uuid4(),
                    company_id=cid,
                    entity_type="knowledge",
                    entity_id=str(existing.id),
                    change_type="updated",
                    old_value=old_value,
                    new_value=value,
                )
                self._db.add(change)

            await self._db.flush()
            return existing

        record = KnowledgeRecord(
            id=uuid.uuid4(),
            company_id=cid,
            user_id=uid,
            category=cat,
            key=key,
            value=value,
            metadata_json=metadata,
            source=source,
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def recall(
        self,
        category: KnowledgeCategory | str | None = None,
        key: str | None = None,
        *,
        company_id: str | uuid.UUID | None = None,
        user_id: str | uuid.UUID | None = None,
    ) -> list[KnowledgeRecord]:
        """ナレッジを検索する."""
        stmt = select(KnowledgeRecord).where(KnowledgeRecord.is_active.is_(True))

        if category:
            cat = (
                category.value if isinstance(category, KnowledgeCategory) else category
            )
            stmt = stmt.where(KnowledgeRecord.category == cat)
        if key:
            stmt = stmt.where(KnowledgeRecord.key == key)
        if company_id:
            cid = (
                uuid.UUID(str(company_id))
                if not isinstance(company_id, uuid.UUID)
                else company_id
            )
            stmt = stmt.where(KnowledgeRecord.company_id == cid)
        if user_id:
            uid = (
                uuid.UUID(str(user_id))
                if not isinstance(user_id, uuid.UUID)
                else user_id
            )
            stmt = stmt.where(KnowledgeRecord.user_id == uid)

        result = await self._db.execute(stmt)
        records = list(result.scalars().all())

        # 使用回数を更新
        for r in records:
            r.use_count += 1
            r.last_used_at = datetime.now(timezone.utc)
        await self._db.flush()

        return records

    async def recall_one(
        self,
        category: KnowledgeCategory | str,
        key: str,
        **kwargs: Any,
    ) -> KnowledgeRecord | None:
        """単一のナレッジを取得."""
        records = await self.recall(category, key, **kwargs)
        return records[0] if records else None

    async def forget(
        self,
        record_id: str | uuid.UUID,
    ) -> bool:
        """ナレッジを無効化する（ソフトデリート）."""
        rid = (
            uuid.UUID(str(record_id))
            if not isinstance(record_id, uuid.UUID)
            else record_id
        )
        result = await self._db.execute(
            select(KnowledgeRecord).where(KnowledgeRecord.id == rid)
        )
        record = result.scalar_one_or_none()
        if record:
            record.is_active = False
            await self._db.flush()
            return True
        return False

    async def has_knowledge(
        self,
        category: KnowledgeCategory | str,
        key: str,
        **kwargs: Any,
    ) -> bool:
        """ナレッジが存在するか確認."""
        record = await self.recall_one(category, key, **kwargs)
        return record is not None

    async def get_changes(
        self,
        company_id: str | uuid.UUID | None = None,
        unacknowledged_only: bool = True,
        limit: int = 50,
    ) -> list[ChangeDetectionRecord]:
        """変更検知の一覧を取得."""
        stmt = select(ChangeDetectionRecord)
        if company_id:
            cid = (
                uuid.UUID(str(company_id))
                if not isinstance(company_id, uuid.UUID)
                else company_id
            )
            stmt = stmt.where(ChangeDetectionRecord.company_id == cid)
        if unacknowledged_only:
            stmt = stmt.where(ChangeDetectionRecord.acknowledged.is_(False))
        stmt = stmt.order_by(ChangeDetectionRecord.detected_at.desc()).limit(limit)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def acknowledge_change(self, change_id: str | uuid.UUID) -> bool:
        """変更を確認済みにする."""
        cid = (
            uuid.UUID(str(change_id))
            if not isinstance(change_id, uuid.UUID)
            else change_id
        )
        result = await self._db.execute(
            select(ChangeDetectionRecord).where(ChangeDetectionRecord.id == cid)
        )
        record = result.scalar_one_or_none()
        if record:
            record.acknowledged = True
            await self._db.flush()
            return True
        return False

    async def remember_file_permission(
        self,
        path: str,
        permission: str,
        *,
        company_id: str | uuid.UUID | None = None,
        user_id: str | uuid.UUID | None = None,
    ) -> KnowledgeRecord:
        """ファイル/フォルダの操作権限を記憶."""
        return await self.remember(
            KnowledgeCategory.FILE_PERMISSION,
            path,
            permission,
            company_id=company_id,
            user_id=user_id,
            metadata={"type": "file_permission", "path": path},
        )

    async def remember_folder_location(
        self,
        name: str,
        path: str,
        *,
        company_id: str | uuid.UUID | None = None,
        user_id: str | uuid.UUID | None = None,
    ) -> KnowledgeRecord:
        """業務資料フォルダの場所を記憶."""
        return await self.remember(
            KnowledgeCategory.FOLDER_LOCATION,
            name,
            path,
            company_id=company_id,
            user_id=user_id,
            metadata={"type": "folder_location", "name": name},
        )

    async def get_all_permissions(
        self, company_id: str | uuid.UUID | None = None
    ) -> list[KnowledgeRecord]:
        """全ファイル権限を取得."""
        return await self.recall(
            KnowledgeCategory.FILE_PERMISSION, company_id=company_id
        )

    async def get_all_folder_locations(
        self, company_id: str | uuid.UUID | None = None
    ) -> list[KnowledgeRecord]:
        """全フォルダ位置を取得."""
        return await self.recall(
            KnowledgeCategory.FOLDER_LOCATION, company_id=company_id
        )
