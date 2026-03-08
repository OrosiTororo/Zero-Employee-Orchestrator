"""Ticket management endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.ticket import Ticket, TicketThread

router = APIRouter()


class TicketCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    source_type: str = "user"
    project_id: str | None = None


class TicketResponse(BaseModel):
    id: str
    ticket_no: int
    title: str
    description: str
    priority: str
    status: str
    source_type: str
    created_at: datetime


class CommentCreate(BaseModel):
    body_markdown: str
    message_type: str = "comment"


@router.get("/companies/{company_id}/tickets", response_model=list[TicketResponse])
async def list_tickets(
    company_id: str,
    status: str | None = None,
    priority: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """チケット一覧"""
    cid = uuid.UUID(company_id)
    query = select(Ticket).where(Ticket.company_id == cid)
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    query = query.order_by(Ticket.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [
        TicketResponse(
            id=str(t.id), ticket_no=t.ticket_no, title=t.title,
            description=t.description or "", priority=t.priority,
            status=t.status, source_type=t.source_type or "",
            created_at=t.created_at,
        )
        for t in tickets
    ]


@router.post("/companies/{company_id}/tickets", response_model=TicketResponse)
async def create_ticket(company_id: str, req: TicketCreate, db: AsyncSession = Depends(get_db)):
    """新規チケット作成"""
    cid = uuid.UUID(company_id)
    max_no = await db.execute(
        select(func.coalesce(func.max(Ticket.ticket_no), 0)).where(Ticket.company_id == cid)
    )
    next_no = max_no.scalar() + 1
    ticket = Ticket(
        id=uuid.uuid4(),
        company_id=cid,
        ticket_no=next_no,
        title=req.title,
        description=req.description,
        priority=req.priority,
        status="draft",
        source_type=req.source_type,
        project_id=uuid.UUID(req.project_id) if req.project_id else None,
    )
    db.add(ticket)
    await db.flush()
    return TicketResponse(
        id=str(ticket.id), ticket_no=ticket.ticket_no, title=ticket.title,
        description=ticket.description or "", priority=ticket.priority,
        status=ticket.status, source_type=ticket.source_type or "",
        created_at=ticket.created_at,
    )


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケット詳細"""
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {
        "id": str(ticket.id),
        "ticket_no": ticket.ticket_no,
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": ticket.status,
        "source_type": ticket.source_type,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, title: str | None = None, status: str | None = None, db: AsyncSession = Depends(get_db)):
    """チケット更新"""
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if title:
        ticket.title = title
    if status:
        ticket.status = status
    return {"status": "updated"}


@router.post("/tickets/{ticket_id}/comments")
async def add_comment(ticket_id: str, req: CommentCreate, db: AsyncSession = Depends(get_db)):
    """チケットにコメント追加"""
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    thread = TicketThread(
        id=uuid.uuid4(),
        company_id=ticket.company_id,
        ticket_id=ticket.id,
        author_type="user",
        message_type=req.message_type,
        body_markdown=req.body_markdown,
    )
    db.add(thread)
    await db.flush()
    return {"id": str(thread.id), "status": "created"}


@router.get("/tickets/{ticket_id}/thread")
async def get_thread(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットのスレッドを取得"""
    tid = uuid.UUID(ticket_id)
    result = await db.execute(
        select(TicketThread).where(TicketThread.ticket_id == tid).order_by(TicketThread.created_at)
    )
    threads = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "author_type": t.author_type,
            "message_type": t.message_type,
            "body_markdown": t.body_markdown,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in threads
    ]


@router.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットを閉じる"""
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "done"
    ticket.closed_at = datetime.utcnow()
    return {"status": "closed"}


@router.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットを再開"""
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "reopened"
    ticket.closed_at = None
    return {"status": "reopened"}
