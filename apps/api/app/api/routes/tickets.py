"""Ticket management endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.validators import parse_uuid
from app.models.ticket import Ticket, TicketThread
from app.models.audit import AuditLog
from app.core.security import generate_uuid
from app.orchestration.interview import (
    InterviewSession,
    create_interview_session,
    generate_spec_from_interview,
)

router = APIRouter()

# In-memory interview sessions (production: persist in DB)
_interview_sessions: dict[str, InterviewSession] = {}


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
    cid = parse_uuid(company_id, "company_id")
    query = select(Ticket).where(Ticket.company_id == cid)
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    query = (
        query.order_by(Ticket.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [
        TicketResponse(
            id=str(t.id),
            ticket_no=t.ticket_no,
            title=t.title,
            description=t.description or "",
            priority=t.priority,
            status=t.status,
            source_type=t.source_type or "",
            created_at=t.created_at,
        )
        for t in tickets
    ]


@router.post("/companies/{company_id}/tickets", response_model=TicketResponse)
async def create_ticket(
    company_id: str, req: TicketCreate, db: AsyncSession = Depends(get_db)
):
    """新規チケット作成 + Design Interview セッション初期化"""
    cid = parse_uuid(company_id, "company_id")
    max_no = await db.execute(
        select(func.coalesce(func.max(Ticket.ticket_no), 0)).where(
            Ticket.company_id == cid
        )
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

    audit = AuditLog(
        id=generate_uuid(),
        company_id=cid,
        actor_type="user",
        event_type="ticket.created",
        target_type="ticket",
        target_id=ticket.id,
        ticket_id=ticket.id,
        details_json={"title": req.title, "priority": req.priority},
    )
    db.add(audit)
    await db.flush()

    # Initialize Design Interview session
    session = create_interview_session(str(ticket.id))
    _interview_sessions[str(ticket.id)] = session

    return TicketResponse(
        id=str(ticket.id),
        ticket_no=ticket.ticket_no,
        title=ticket.title,
        description=ticket.description or "",
        priority=ticket.priority,
        status=ticket.status,
        source_type=ticket.source_type or "",
        created_at=ticket.created_at,
    )


@router.get("/tickets/{ticket_id}/interview")
async def get_interview(ticket_id: str):
    """Design Interview のセッション取得"""
    session = _interview_sessions.get(ticket_id)
    if not session:
        session = create_interview_session(ticket_id)
        _interview_sessions[ticket_id] = session
    return {
        "ticket_id": session.ticket_id,
        "status": session.status,
        "is_complete": session.is_complete,
        "questions": [
            {
                "index": i,
                "question": q.question,
                "category": q.category,
                "required": q.required,
                "answered": q.answered,
                "answer": q.answer,
            }
            for i, q in enumerate(session.questions)
        ],
        "pending_count": len(session.get_pending_questions()),
    }


class InterviewAnswer(BaseModel):
    question_index: int
    answer: str


@router.post("/tickets/{ticket_id}/interview/answer")
async def answer_interview(
    ticket_id: str, req: InterviewAnswer, db: AsyncSession = Depends(get_db)
):
    """Design Interview の質問に回答"""
    session = _interview_sessions.get(ticket_id)
    if not session:
        session = create_interview_session(ticket_id)
        _interview_sessions[ticket_id] = session

    session.add_answer(req.question_index, req.answer)

    if session.is_complete:
        session.status = "completed"

    return {
        "status": session.status,
        "is_complete": session.is_complete,
        "pending_count": len(session.get_pending_questions()),
    }


@router.post("/tickets/{ticket_id}/interview/generate-spec")
async def generate_spec_from_interview_endpoint(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Interview 回答から Spec を自動生成"""
    from app.models.spec import Spec

    session = _interview_sessions.get(ticket_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    spec_data = generate_spec_from_interview(session)

    tid = parse_uuid(ticket_id, "ticket_id")
    existing = await db.execute(select(Spec).where(Spec.ticket_id == tid))
    count = len(existing.scalars().all())

    spec = Spec(
        id=uuid.uuid4(),
        ticket_id=tid,
        version_no=count + 1,
        status="draft",
        objective=spec_data["objective"],
        constraints_json=spec_data["constraints_json"],
        acceptance_criteria_json=spec_data["acceptance_criteria_json"],
        risk_notes=spec_data.get("risk_notes", ""),
        created_by_type="ai",
    )
    db.add(spec)

    # Update ticket status to interviewing -> spec_generated
    result = await db.execute(select(Ticket).where(Ticket.id == tid))
    ticket = result.scalar_one_or_none()
    if ticket:
        ticket.status = "spec_ready"
        ticket.current_spec_id = spec.id

    await db.flush()
    return {"spec_id": str(spec.id), "version_no": spec.version_no, "spec": spec_data}


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケット詳細"""
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
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
async def update_ticket(
    ticket_id: str,
    title: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """チケット更新"""
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if title:
        ticket.title = title
    if status:
        ticket.status = status
    await db.commit()
    return {"status": "updated"}


@router.post("/tickets/{ticket_id}/comments")
async def add_comment(
    ticket_id: str, req: CommentCreate, db: AsyncSession = Depends(get_db)
):
    """チケットにコメント追加"""
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
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
    tid = parse_uuid(ticket_id, "ticket_id")
    result = await db.execute(
        select(TicketThread)
        .where(TicketThread.ticket_id == tid)
        .order_by(TicketThread.created_at)
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
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "done"
    ticket.closed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "closed"}


@router.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットを再開"""
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "reopened"
    ticket.closed_at = None
    await db.commit()
    return {"status": "reopened"}
