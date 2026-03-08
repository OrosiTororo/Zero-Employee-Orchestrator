"""Experience Memory — DB永続化層.

ExperienceMemory のインメモリ実装を拡張し、
SQLAlchemy async セッションを通じた永続化インターフェースを提供する。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, String, Text, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import generate_uuid
from app.orchestration.state_machine import (
    ExperienceMemory,
    ExperienceMemoryEntry,
    FailureTaxonomyEntry,
    MemoryType,
)


# ---------------------------------------------------------------------------
# DB Models for Experience Memory persistence
# ---------------------------------------------------------------------------

class ExperienceMemoryRecord(Base):
    """DB永続化された Experience Memory エントリ."""

    __tablename__ = "experience_memory"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    memory_type: Mapped[str] = mapped_column(String(60))
    category: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    source_ticket_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    conditions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    effectiveness_score: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )


class FailureTaxonomyRecord(Base):
    """DB永続化された Failure Taxonomy エントリ."""

    __tablename__ = "failure_taxonomy"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    category: Mapped[str] = mapped_column(String(120))
    subcategory: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    prevention_strategy: Mapped[str] = mapped_column(Text)
    occurrence_count: Mapped[int] = mapped_column(default=1)
    last_occurred: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    recovery_success_rate: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Persistent Experience Memory
# ---------------------------------------------------------------------------

class PersistentExperienceMemory:
    """DB 永続化対応の Experience Memory.

    インメモリの ExperienceMemory と互換性のあるインターフェースを持ちつつ、
    AsyncSession を通じて永続化する。
    """

    def __init__(self, db: AsyncSession, company_id: str | uuid.UUID) -> None:
        self._db = db
        self._company_id = uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id

    async def add_success_pattern(
        self,
        title: str,
        content: str,
        category: str,
        source_ticket_id: str | None = None,
        source_task_id: str | None = None,
    ) -> ExperienceMemoryRecord:
        """成功パターンをDBに記録."""
        record = ExperienceMemoryRecord(
            id=generate_uuid(),
            company_id=self._company_id,
            memory_type=MemoryType.REUSABLE.value,
            category=category,
            title=title,
            content=content,
            source_ticket_id=uuid.UUID(source_ticket_id) if source_ticket_id else None,
            source_task_id=uuid.UUID(source_task_id) if source_task_id else None,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def add_failure(
        self,
        category: str,
        subcategory: str,
        description: str,
        prevention_strategy: str,
    ) -> FailureTaxonomyRecord:
        """障害パターンをDBに記録 (同一カテゴリ・サブカテゴリは更新)."""
        result = await self._db.execute(
            select(FailureTaxonomyRecord).where(
                FailureTaxonomyRecord.company_id == self._company_id,
                FailureTaxonomyRecord.category == category,
                FailureTaxonomyRecord.subcategory == subcategory,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.occurrence_count += 1
            existing.last_occurred = datetime.now(timezone.utc)
            await self._db.commit()
            await self._db.refresh(existing)
            return existing

        record = FailureTaxonomyRecord(
            id=generate_uuid(),
            company_id=self._company_id,
            category=category,
            subcategory=subcategory,
            description=description,
            prevention_strategy=prevention_strategy,
            last_occurred=datetime.now(timezone.utc),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 20,
    ) -> list[ExperienceMemoryRecord]:
        """キーワードで Experience Memory を検索."""
        stmt = select(ExperienceMemoryRecord).where(
            ExperienceMemoryRecord.company_id == self._company_id,
        )
        if category:
            stmt = stmt.where(ExperienceMemoryRecord.category == category)

        # Simple LIKE search
        pattern = f"%{query}%"
        stmt = stmt.where(
            ExperienceMemoryRecord.title.ilike(pattern)
            | ExperienceMemoryRecord.content.ilike(pattern)
        )
        stmt = stmt.limit(limit)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_frequent_failures(
        self,
        min_count: int = 2,
    ) -> list[FailureTaxonomyRecord]:
        """頻発する障害パターンを取得."""
        result = await self._db.execute(
            select(FailureTaxonomyRecord).where(
                FailureTaxonomyRecord.company_id == self._company_id,
                FailureTaxonomyRecord.occurrence_count >= min_count,
            )
        )
        return list(result.scalars().all())
