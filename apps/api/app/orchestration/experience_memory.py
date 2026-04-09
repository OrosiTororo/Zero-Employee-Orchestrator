"""Experience Memory — Database persistence layer.

Extends the in-memory ExperienceMemory implementation and provides
a persistence interface through SQLAlchemy async sessions.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, String, Text, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import generate_uuid
from app.orchestration.state_machine import (
    MemoryType,
)

# ---------------------------------------------------------------------------
# DB Models for Experience Memory persistence
# ---------------------------------------------------------------------------


class ExperienceMemoryRecord(Base):
    """Database-persisted Experience Memory entry."""

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
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


class FailureTaxonomyRecord(Base):
    """Database-persisted Failure Taxonomy entry."""

    __tablename__ = "failure_taxonomy"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    category: Mapped[str] = mapped_column(String(120))
    subcategory: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    prevention_strategy: Mapped[str] = mapped_column(Text)
    occurrence_count: Mapped[int] = mapped_column(default=1)
    last_occurred: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    recovery_success_rate: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())


# ---------------------------------------------------------------------------
# Persistent Experience Memory
# ---------------------------------------------------------------------------


class PersistentExperienceMemory:
    """Database-backed Experience Memory.

    Provides an interface compatible with the in-memory ExperienceMemory
    while persisting through AsyncSession.
    """

    def __init__(self, db: AsyncSession, company_id: str | uuid.UUID) -> None:
        self._db = db
        self._company_id = (
            uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id
        )

    async def add_success_pattern(
        self,
        title: str,
        content: str,
        category: str,
        source_ticket_id: str | None = None,
        source_task_id: str | None = None,
    ) -> ExperienceMemoryRecord:
        """Record a success pattern in the database."""
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
        """Record a failure pattern in the database (updates existing category/subcategory)."""
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
            existing.last_occurred = datetime.now(UTC)
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
            last_occurred=datetime.now(UTC),
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
        """Search Experience Memory by keyword with TF-IDF re-ranking.

        Uses SQL ILIKE as the initial filter for efficiency, then applies an
        in-memory TF-IDF + cosine similarity re-ranking pass to improve semantic
        matching across different phrasings.
        """
        stmt = select(ExperienceMemoryRecord).where(
            ExperienceMemoryRecord.company_id == self._company_id,
        )
        if category:
            stmt = stmt.where(ExperienceMemoryRecord.category == category)

        # SQL ILIKE filter (initial candidate selection)
        pattern = f"%{query}%"
        stmt = stmt.where(
            ExperienceMemoryRecord.title.ilike(pattern)
            | ExperienceMemoryRecord.content.ilike(pattern)
        )
        stmt = stmt.limit(limit * 3)  # Fetch more candidates for re-ranking

        result = await self._db.execute(stmt)
        records = list(result.scalars().all())

        # TF-IDF + cosine similarity re-ranking (in-memory)
        if query.strip() and records:
            import math
            import re as _re

            query_terms = query.strip().lower().split()
            doc_count = len(records)

            # Build document frequency map for IDF
            df: dict[str, int] = {}
            for r in records:
                text_tokens = set(
                    _re.findall(r"[a-zA-Z0-9\u3040-\u9fff]+", f"{r.title} {r.content}".lower())
                )
                for t in text_tokens:
                    df[t] = df.get(t, 0) + 1

            scored: list[tuple[float, ExperienceMemoryRecord]] = []
            for r in records:
                text = f"{r.title} {r.content}".lower()
                text_tokens = _re.findall(r"[a-zA-Z0-9\u3040-\u9fff]+", text)
                token_freq: dict[str, int] = {}
                for t in text_tokens:
                    token_freq[t] = token_freq.get(t, 0) + 1

                # TF-IDF score for query terms
                tf_idf_score = 0.0
                for qt in query_terms:
                    tf = token_freq.get(qt, 0) / max(len(text_tokens), 1)
                    idf = math.log((doc_count + 1) / (df.get(qt, 0) + 1)) + 1.0
                    tf_idf_score += tf * idf

                # Cosine similarity (bag-of-words)
                all_terms = set(query_terms) | set(token_freq.keys())
                dot = sum(query_terms.count(t) * token_freq.get(t, 0) for t in all_terms)
                mag_q = math.sqrt(sum(query_terms.count(t) ** 2 for t in all_terms))
                mag_d = math.sqrt(sum(token_freq.get(t, 0) ** 2 for t in all_terms))
                cosine = dot / (mag_q * mag_d) if mag_q > 0 and mag_d > 0 else 0.0

                # Effectiveness score boost
                effectiveness = (
                    min(r.effectiveness_score / 10.0, 1.0) if r.effectiveness_score else 0.0
                )

                final_score = tf_idf_score * 0.45 + cosine * 0.45 + effectiveness * 0.10
                scored.append((final_score, r))

            scored.sort(key=lambda x: x[0], reverse=True)
            records = [r for _, r in scored]

        return records[:limit]

    async def get_frequent_failures(
        self,
        min_count: int = 2,
    ) -> list[FailureTaxonomyRecord]:
        """Get frequently occurring failure patterns."""
        result = await self._db.execute(
            select(FailureTaxonomyRecord).where(
                FailureTaxonomyRecord.company_id == self._company_id,
                FailureTaxonomyRecord.occurrence_count >= min_count,
            )
        )
        return list(result.scalars().all())
