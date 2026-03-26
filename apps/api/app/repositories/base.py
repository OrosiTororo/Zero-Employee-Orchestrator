"""Generic repository base -- DB I/O abstraction.

Based on DESIGN.md section 42.1, implements separation of concerns across
routes -> services -> repositories -> models. Entity-specific repositories
inherit from this base class.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Common operations for SQLAlchemy async repositories."""

    model_class: type[T]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: uuid.UUID) -> T | None:
        result = await self.db.execute(
            select(self.model_class).where(self.model_class.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_company(
        self,
        company_id: uuid.UUID,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[T]:
        stmt = select(self.model_class).where(self.model_class.company_id == company_id)
        if status:
            stmt = stmt.where(self.model_class.status == status)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_by_company(self, company_id: uuid.UUID, *, status: str | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.company_id == company_id)
        )
        if status:
            stmt = stmt.where(self.model_class.status == status)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: T) -> T:
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def update(self, entity: T, updates: dict[str, Any]) -> T:
        for key, value in updates.items():
            setattr(entity, key, value)
        await self.db.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self.db.delete(entity)
        await self.db.flush()
