"""Ticket lifecycle service with state machine enforcement."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.ticket import Ticket, TicketThread

# Valid state transitions for tickets
TICKET_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["triage", "cancelled"],
    "triage": ["planning", "waiting_user", "cancelled"],
    "planning": ["awaiting_plan_approval", "in_progress", "cancelled"],
    "awaiting_plan_approval": ["in_progress", "planning", "rejected"],
    "in_progress": ["awaiting_review", "blocked", "failed", "cancelled"],
    "awaiting_review": ["done", "rework_requested"],
    "rework_requested": ["planning", "in_progress"],
    "blocked": ["in_progress", "cancelled"],
    "failed": ["planning", "in_progress", "cancelled"],
    "done": ["reopened"],
    "rejected": ["draft", "cancelled"],
    "cancelled": ["reopened"],
    "reopened": ["triage", "planning", "in_progress"],
}


def validate_ticket_transition(current: str, target: str) -> bool:
    return target in TICKET_TRANSITIONS.get(current, [])


async def create_ticket(
    db: AsyncSession,
    company_id: str,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    requester_user_id: str | None = None,
    project_id: str | None = None,
    goal_id: str | None = None,
    source_type: str = "human",
    parent_ticket_id: str | None = None,
) -> Ticket:
    # Auto-increment ticket_no within company
    result = await db.execute(
        select(func.coalesce(func.max(Ticket.ticket_no), 0)).where(
            Ticket.company_id == uuid.UUID(company_id)
        )
    )
    next_no = result.scalar() + 1

    ticket = Ticket(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        project_id=uuid.UUID(project_id) if project_id else None,
        goal_id=uuid.UUID(goal_id) if goal_id else None,
        ticket_no=next_no,
        title=title,
        description=description or "",
        priority=priority,
        status="draft",
        source_type=source_type,
        requester_user_id=uuid.UUID(requester_user_id) if requester_user_id else None,
        parent_ticket_id=uuid.UUID(parent_ticket_id) if parent_ticket_id else None,
    )
    db.add(ticket)

    # Audit log
    audit = AuditLog(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        actor_type="user" if requester_user_id else "system",
        actor_user_id=uuid.UUID(requester_user_id) if requester_user_id else None,
        event_type="ticket.created",
        target_type="ticket",
        target_id=ticket.id,
        ticket_id=ticket.id,
        details_json={"title": title, "priority": priority},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ticket)
    return ticket


async def transition_ticket(
    db: AsyncSession,
    ticket: Ticket,
    new_status: str,
    actor_user_id: str | None = None,
) -> Ticket:
    if not validate_ticket_transition(ticket.status, new_status):
        raise ValueError(
            f"Invalid transition: {ticket.status} -> {new_status}. "
            f"Allowed: {TICKET_TRANSITIONS.get(ticket.status, [])}"
        )

    old_status = ticket.status
    ticket.status = new_status

    if new_status == "done":
        ticket.closed_at = datetime.now(UTC)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=ticket.company_id,
        actor_type="user" if actor_user_id else "system",
        actor_user_id=uuid.UUID(actor_user_id) if actor_user_id else None,
        event_type="ticket.status_changed",
        target_type="ticket",
        target_id=ticket.id,
        ticket_id=ticket.id,
        details_json={"from": old_status, "to": new_status},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def add_thread_message(
    db: AsyncSession,
    ticket: Ticket,
    body_markdown: str,
    author_type: str = "user",
    author_user_id: str | None = None,
    author_agent_id: str | None = None,
    message_type: str = "comment",
    meta_json: dict | None = None,
) -> TicketThread:
    thread = TicketThread(
        id=generate_uuid(),
        company_id=ticket.company_id,
        ticket_id=ticket.id,
        author_type=author_type,
        author_user_id=uuid.UUID(author_user_id) if author_user_id else None,
        author_agent_id=uuid.UUID(author_agent_id) if author_agent_id else None,
        message_type=message_type,
        body_markdown=body_markdown,
        meta_json=meta_json or {},
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread
