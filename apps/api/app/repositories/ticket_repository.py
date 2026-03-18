"""チケットリポジトリ — Ticket / TicketThread の DB 操作."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models.ticket import Ticket, TicketThread
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    model_class = Ticket

    async def get_by_company_sorted(
        self,
        company_id: uuid.UUID,
        *,
        status: str | None = None,
        priority: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Ticket]:
        stmt = select(Ticket).where(Ticket.company_id == company_id)
        if status:
            stmt = stmt.where(Ticket.status == status)
        if priority:
            stmt = stmt.where(Ticket.priority == priority)
        stmt = stmt.order_by(Ticket.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_next_ticket_no(self, company_id: uuid.UUID) -> int:
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.coalesce(func.max(Ticket.ticket_no), 0)).where(
                Ticket.company_id == company_id
            )
        )
        return result.scalar_one() + 1


class TicketThreadRepository(BaseRepository[TicketThread]):
    model_class = TicketThread

    async def get_by_ticket(self, ticket_id: uuid.UUID) -> Sequence[TicketThread]:
        stmt = (
            select(TicketThread)
            .where(TicketThread.ticket_id == ticket_id)
            .order_by(TicketThread.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
