"""監査ログリポジトリ — AuditLog の DB 操作.

監査ログは append-only を前提とし、更新・削除を原則禁止する。
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditLogRepository:
    """監査ログ専用リポジトリ（append-only）."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def append(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_by_company(
        self,
        company_id: uuid.UUID,
        *,
        event_type: str | None = None,
        target_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.company_id == company_id)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if target_type:
            stmt = stmt.where(AuditLog.target_type == target_type)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_trace_id(self, trace_id: str) -> Sequence[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.trace_id == trace_id)
            .order_by(AuditLog.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_ticket(self, ticket_id: uuid.UUID, *, limit: int = 100) -> Sequence[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.ticket_id == ticket_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
