"""Knowledge Store — Persistent storage for user settings and knowledge.

Persists and utilizes file/folder permissions, business document locations,
and user preferences to avoid repeating the same questions during planning.

Features:
  - User setting storage (folder paths, permissions, preferences)
  - Change detection (diff detection from previous information)
  - Integration with Experience Memory
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, String, Text, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

logger = logging.getLogger(__name__)


class KnowledgeCategory(str, Enum):
    """Knowledge category."""

    FILE_PERMISSION = "file_permission"  # File/folder access permission
    FOLDER_LOCATION = "folder_location"  # Business document folder location
    USER_PREFERENCE = "user_preference"  # User preferences/settings
    TOOL_CONFIG = "tool_config"  # Tool connection configuration
    WORKFLOW_PATTERN = "workflow_pattern"  # Frequently used workflow patterns
    AGENT_INSTRUCTION = "agent_instruction"  # Permanent instructions for agents
    ENVIRONMENT = "environment"  # Environment info (OS, paths, etc.)
    CREDENTIAL_HINT = "credential_hint"  # Credential hints (actual values are not stored)
    CHANGE_LOG = "change_log"  # Change history


class KnowledgeRecord(Base):
    """Persisted knowledge entry."""

    __tablename__ = "knowledge_store"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    key: Mapped[str] = mapped_column(String(500), index=True)
    value: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(120), default="user_input")
    last_used_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)
    use_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


class ChangeDetectionRecord(Base):
    """Change detection record."""

    __tablename__ = "change_detections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(255))
    change_type: Mapped[str] = mapped_column(String(30))  # created, updated, deleted
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class KnowledgeStore:
    """Persistent management of user settings and knowledge."""

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
        """Store knowledge (updates existing keys).

        File path and folder-related knowledge is checked via workspace_isolation.
        """
        cat = category.value if isinstance(category, KnowledgeCategory) else category

        # Workspace isolation check: when storing file/folder paths
        if cat in (
            KnowledgeCategory.FILE_PERMISSION.value if isinstance(category, str) else "",
            KnowledgeCategory.FILE_PERMISSION.value,
            KnowledgeCategory.FOLDER_LOCATION.value,
        ):
            try:
                from app.security.workspace_isolation import workspace_isolation

                ws_check = workspace_isolation.check_access(value)
                if not ws_check.allowed:
                    logger.warning(
                        "Workspace isolation blocked knowledge store: path=%s reason=%s",
                        value,
                        ws_check.reason,
                    )
                    raise PermissionError(
                        f"Workspace isolation: access to path '{value}' is not allowed — "
                        f"{ws_check.reason}"
                    )
            except (ImportError, AttributeError):
                pass  # Skip if workspace_isolation is unavailable
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
            existing.updated_at = datetime.now(UTC)

            # Change detection
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
        """Search knowledge."""
        stmt = select(KnowledgeRecord).where(KnowledgeRecord.is_active.is_(True))

        if category:
            cat = category.value if isinstance(category, KnowledgeCategory) else category
            stmt = stmt.where(KnowledgeRecord.category == cat)
        if key:
            stmt = stmt.where(KnowledgeRecord.key == key)
        if company_id:
            cid = (
                uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id
            )
            stmt = stmt.where(KnowledgeRecord.company_id == cid)
        if user_id:
            uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
            stmt = stmt.where(KnowledgeRecord.user_id == uid)

        result = await self._db.execute(stmt)
        records = list(result.scalars().all())

        # Update usage count
        for r in records:
            r.use_count += 1
            r.last_used_at = datetime.now(UTC)
        await self._db.flush()

        return records

    async def recall_one(
        self,
        category: KnowledgeCategory | str,
        key: str,
        **kwargs: Any,
    ) -> KnowledgeRecord | None:
        """Get a single knowledge entry."""
        records = await self.recall(category, key, **kwargs)
        return records[0] if records else None

    async def forget(
        self,
        record_id: str | uuid.UUID,
    ) -> bool:
        """Deactivate knowledge (soft delete)."""
        rid = uuid.UUID(str(record_id)) if not isinstance(record_id, uuid.UUID) else record_id
        result = await self._db.execute(select(KnowledgeRecord).where(KnowledgeRecord.id == rid))
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
        """Check if knowledge exists."""
        record = await self.recall_one(category, key, **kwargs)
        return record is not None

    async def get_changes(
        self,
        company_id: str | uuid.UUID | None = None,
        unacknowledged_only: bool = True,
        limit: int = 50,
    ) -> list[ChangeDetectionRecord]:
        """Get list of change detections."""
        stmt = select(ChangeDetectionRecord)
        if company_id:
            cid = (
                uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id
            )
            stmt = stmt.where(ChangeDetectionRecord.company_id == cid)
        if unacknowledged_only:
            stmt = stmt.where(ChangeDetectionRecord.acknowledged.is_(False))
        stmt = stmt.order_by(ChangeDetectionRecord.detected_at.desc()).limit(limit)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def acknowledge_change(self, change_id: str | uuid.UUID) -> bool:
        """Mark a change as acknowledged."""
        cid = uuid.UUID(str(change_id)) if not isinstance(change_id, uuid.UUID) else change_id
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
        """Store file/folder operation permissions."""
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
        """Store business document folder location."""
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
        """Get all file permissions."""
        return await self.recall(KnowledgeCategory.FILE_PERMISSION, company_id=company_id)

    async def get_all_folder_locations(
        self, company_id: str | uuid.UUID | None = None
    ) -> list[KnowledgeRecord]:
        """Get all folder locations."""
        return await self.recall(KnowledgeCategory.FOLDER_LOCATION, company_id=company_id)
