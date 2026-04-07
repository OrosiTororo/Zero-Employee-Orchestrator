"""Ticket management endpoints."""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.validators import parse_uuid
from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.ticket import Ticket, TicketThread
from app.models.user import User
from app.orchestration.interview import (
    FileAttachment,
    InterviewSession,
    create_interview_session,
    generate_spec_from_interview,
)
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection, wrap_external_data

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory interview sessions (production: persist in DB)
_interview_sessions: dict[str, InterviewSession] = {}

# Supported file types
_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
}
_CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
_DOCUMENT_EXTENSIONS = {".pdf"}
_ALL_ALLOWED = _TEXT_EXTENSIONS | _CODE_EXTENSIONS | _IMAGE_EXTENSIONS | _DOCUMENT_EXTENSIONS
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _extract_text_from_file(content: bytes, filename: str, content_type: str) -> str:
    """Extract text from a file."""
    ext = Path(filename).suffix.lower()

    # Text-based files
    if ext in _TEXT_EXTENSIONS | _CODE_EXTENSIONS:
        for encoding in ("utf-8", "shift_jis", "euc-jp", "cp932", "latin-1"):
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode("utf-8", errors="replace")

    # Image file — only metadata if OCR is not available
    if ext in _IMAGE_EXTENSIONS:
        import base64

        size_kb = len(content) / 1024
        b64 = base64.b64encode(content).decode("ascii")
        return (
            f"[Image file: {filename}]\n"
            f"Format: {content_type}\n"
            f"Size: {size_kb:.1f} KB\n"
            f"Base64 data: data:{content_type};base64,{b64[:200]}...\n"
            f"(Full image can be passed directly to LLM for analysis)"
        )

    # PDF — attempt text extraction
    if ext == ".pdf":
        return f"[PDF file: {filename}] Size: {len(content) / 1024:.1f} KB"

    return f"[Unsupported file: {filename}] Size: {len(content)} bytes"


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
    user: User = Depends(get_current_user),
):
    """List tickets."""
    cid = parse_uuid(company_id, "company_id")
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
    company_id: str,
    req: TicketCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new ticket + initialize Design Interview session."""
    cid = parse_uuid(company_id, "company_id")
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
async def get_interview(ticket_id: str, user: User = Depends(get_current_user)):
    """Get Design Interview session."""
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
        "attachments": [
            {
                "filename": att.filename,
                "content_type": att.content_type,
                "size_bytes": att.size_bytes,
                "description": att.description,
                "has_text": bool(att.extracted_text),
            }
            for att in session.attachments
        ],
        "pending_count": len(session.get_pending_questions()),
    }


class InterviewAnswer(BaseModel):
    question_index: int
    answer: str


@router.post("/tickets/{ticket_id}/interview/answer")
@limiter.limit("30/minute")
async def answer_interview(
    request: Request,
    ticket_id: str,
    req: InterviewAnswer,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Answer a Design Interview question."""
    # Prompt injection check (answer text may be embedded in LLM prompt for spec generation)
    guard_result = scan_prompt_injection(req.answer)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected.",
        )

    # PII masking
    pii_result = detect_and_mask_pii(req.answer)
    if pii_result.detected_count > 0:
        logger.warning(
            "PII detected in interview answer: types=%s",
            pii_result.detected_types,
        )

    session = _interview_sessions.get(ticket_id)
    if not session:
        session = create_interview_session(ticket_id)
        _interview_sessions[ticket_id] = session

    session.add_answer(req.question_index, pii_result.masked_text)

    if session.is_complete:
        session.status = "completed"

    return {
        "status": session.status,
        "is_complete": session.is_complete,
        "pending_count": len(session.get_pending_questions()),
    }


@router.post("/tickets/{ticket_id}/interview/attach")
async def attach_file_to_interview(
    ticket_id: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    user: User = Depends(get_current_user),
):
    """Attach a file to the interview.

    Supports text, code, image, and PDF files.
    Reads file content and integrates it as text context for spec generation.
    """
    session = _interview_sessions.get(ticket_id)
    if not session:
        session = create_interview_session(ticket_id)
        _interview_sessions[ticket_id] = session

    # File extension check
    ext = Path(file.filename or "unknown").suffix.lower()
    if ext not in _ALL_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"File format '{ext}' is not supported. Supported formats: {sorted(_ALL_ALLOWED)}",
        )

    # Size check
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the limit ({_MAX_FILE_SIZE // (1024 * 1024)} MB)",
        )

    # Text extraction
    extracted = _extract_text_from_file(
        content,
        file.filename or "unknown",
        file.content_type or "application/octet-stream",
    )

    # Wrap extracted text as external data to prevent prompt injection in spec generation
    wrapped_text = wrap_external_data(extracted, source=f"file:{file.filename or 'unknown'}")

    attachment = FileAttachment(
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        extracted_text=wrapped_text,
        size_bytes=len(content),
        description=description,
    )
    session.add_attachment(attachment)

    return {
        "status": "attached",
        "filename": attachment.filename,
        "size_bytes": attachment.size_bytes,
        "extracted_text_length": len(extracted),
        "total_attachments": len(session.attachments),
    }


@router.get("/tickets/{ticket_id}/interview/attachments")
async def list_interview_attachments(ticket_id: str, user: User = Depends(get_current_user)):
    """Get list of interview attachments."""
    session = _interview_sessions.get(ticket_id)
    if not session:
        return {"attachments": []}

    return {
        "attachments": [
            {
                "filename": att.filename,
                "content_type": att.content_type,
                "size_bytes": att.size_bytes,
                "description": att.description,
                "extracted_text_preview": att.extracted_text[:500] if att.extracted_text else "",
            }
            for att in session.attachments
        ]
    }


@router.post("/tickets/{ticket_id}/interview/generate-spec")
async def generate_spec_from_interview_endpoint(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Auto-generate Spec from interview answers and attachments."""
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
async def get_ticket(
    ticket_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get ticket details."""
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
    user: User = Depends(get_current_user),
):
    """Update ticket."""
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
@limiter.limit("30/minute")
async def add_comment(
    request: Request,
    ticket_id: str,
    req: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add comment to ticket."""
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
async def get_thread(
    ticket_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get ticket thread."""
    tid = parse_uuid(ticket_id, "ticket_id")
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
async def close_ticket(
    ticket_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Close ticket."""
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "done"
    ticket.closed_at = datetime.now(UTC)
    await db.commit()
    return {"status": "closed"}


@router.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Reopen ticket."""
    result = await db.execute(select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id")))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "reopened"
    ticket.closed_at = None
    await db.commit()
    return {"status": "reopened"}


# ------------------------------------------------------------------ #
#  Execution — Generate plan & execute ticket
# ------------------------------------------------------------------ #


@router.post(
    "/tickets/{ticket_id}/generate-plan",
    tags=["execution"],
)
@limiter.limit("5/minute")
async def generate_plan(
    request: Request,
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate an execution plan (DAG) for a ticket from its spec."""
    from app.orchestration.executor import get_executor

    result = await db.execute(
        select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id"))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get spec text from interview session or ticket description
    spec_text = ticket.description or ""
    session = _interview_sessions.get(str(ticket.id))
    if session and session.spec_text:
        spec_text = session.spec_text

    if not spec_text.strip():
        raise HTTPException(status_code=400, detail="Ticket has no spec or description to plan from")

    executor = get_executor()
    dag = await executor.generate_plan(ticket.title, spec_text)

    # Store plan in interview session for later execution
    if session is None:
        session = create_interview_session(str(ticket.id), ticket.title, spec_text)
        _interview_sessions[str(ticket.id)] = session
    session.generated_plan = dag.to_dict()

    ticket.status = "open"
    await db.commit()

    return dag.to_dict()


@router.post(
    "/tickets/{ticket_id}/execute",
    tags=["execution"],
)
@limiter.limit("3/minute")
async def execute_ticket(
    request: Request,
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Execute a ticket: generate plan if needed, then run all steps.

    This is the main end-to-end execution endpoint. It:
    1. Generates an execution plan (DAG) from the ticket spec
    2. Executes each step by calling the LLM
    3. Verifies results via the Judge layer
    4. Returns the final output with cost/quality metrics
    """
    from app.orchestration.executor import get_executor

    result = await db.execute(
        select(Ticket).where(Ticket.id == parse_uuid(ticket_id, "ticket_id"))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get spec/description
    spec_text = ticket.description or ""
    session = _interview_sessions.get(str(ticket.id))
    if session and session.spec_text:
        spec_text = session.spec_text

    if not spec_text.strip():
        raise HTTPException(
            status_code=400, detail="Ticket has no spec or description to execute"
        )

    # Mark as executing
    ticket.status = "in_progress"
    ticket.started_at = datetime.now(UTC)
    await db.commit()

    executor = get_executor()

    # Step 1: Generate plan
    dag = await executor.generate_plan(ticket.title, spec_text)

    # Step 2: Execute plan
    plan_result = await executor.execute_plan(dag)

    # Step 3: Update ticket status based on result
    if plan_result.status == "succeeded":
        ticket.status = "resolved"
        ticket.closed_at = datetime.now(UTC)
    else:
        ticket.status = "open"  # Back to open on failure

    # Audit log
    audit = AuditLog(
        id=generate_uuid(),
        company_id=ticket.company_id,
        actor_type="system",
        event_type=f"ticket.execution.{plan_result.status}",
        target_type="ticket",
        target_id=ticket.id,
        details_json={
            "plan_id": plan_result.plan_id,
            "status": plan_result.status,
            "nodes_executed": len(plan_result.node_results),
            "total_cost_usd": plan_result.total_cost_usd,
            "total_tokens": plan_result.total_tokens,
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "ticket_id": str(ticket.id),
        "status": plan_result.status,
        "plan": dag.to_dict(),
        "output": plan_result.final_output,
        "metrics": {
            "total_cost_usd": plan_result.total_cost_usd,
            "total_tokens": plan_result.total_tokens,
            "total_duration_ms": plan_result.total_duration_ms,
            "nodes_executed": len(plan_result.node_results),
            "nodes_succeeded": sum(1 for r in plan_result.node_results if r.success),
        },
        "node_results": [
            {
                "node_id": r.node_id,
                "success": r.success,
                "model_used": r.model_used,
                "judge_score": r.judge_score,
                "judge_verdict": r.judge_verdict,
                "cost_usd": r.cost_usd,
                "duration_ms": r.duration_ms,
                "error": r.error,
            }
            for r in plan_result.node_results
        ],
        "failure_reason": plan_result.failure_reason,
    }
