"""汎用リポジトリ基盤 — DB 入出力の抽象化.

DESIGN.md §42.1 に基づき、routes → services → repositories → models の
責務分離を実現する。各エンティティ固有のリポジトリはこの基底クラスを継承する。
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """SQLAlchemy async リポジトリの共通操作."""

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
        stmt = select(self.model_class).where(
            self.model_class.company_id == company_id
        )
        if status:
            stmt = stmt.where(self.model_class.status == status)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_by_company(
        self, company_id: uuid.UUID, *, status: str | None = None
    ) -> int:
        stmt = select(func.count()).select_from(self.model_class).where(
            self.model_class.company_id == company_id
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
