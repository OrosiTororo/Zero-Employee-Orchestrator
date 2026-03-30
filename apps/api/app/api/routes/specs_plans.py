"""Spec, Plan, and Task management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.validators import parse_uuid
from app.api.routes.auth import get_current_user
from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.plan import Plan
from app.models.spec import Spec
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter()


class SpecCreate(BaseModel):
    objective: str
    constraints_json: dict | None = None
    acceptance_criteria_json: dict | None = None
    risk_notes: str = ""
    file_context: str = ""  # Text extracted from attached files
    attachments: list[dict] | None = None  # Attached file metadata


class PlanCreate(BaseModel):
    spec_id: str
    summary: str
    estimated_cost_usd: float = 0.0
    estimated_minutes: int = 0
    approval_required: bool = True
    risk_level: str = "low"
    plan_json: dict | None = None
    file_context: str = ""  # Text extracted from attached files


@router.get("/tickets/{ticket_id}/specs")
async def list_specs(
    ticket_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List specs for a ticket."""
    tid = parse_uuid(ticket_id, "ticket_id")
    result = await db.execute(
        select(Spec).where(Spec.ticket_id == tid).order_by(Spec.version_no.desc())
    )
    specs = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "version_no": s.version_no,
            "status": s.status,
            "objective": s.objective,
            "risk_notes": s.risk_notes,
        }
        for s in specs
    ]


@router.post("/tickets/{ticket_id}/specs")
async def create_spec(
    ticket_id: str,
    req: SpecCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a spec."""
    tid = parse_uuid(ticket_id, "ticket_id")
    # Look up ticket to get company_id
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == tid))
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    existing = await db.execute(select(Spec).where(Spec.ticket_id == tid))
    count = len(existing.scalars().all())
    spec = Spec(
        id=uuid.uuid4(),
        company_id=ticket.company_id,
        ticket_id=tid,
        version_no=count + 1,
        status="draft",
        objective=req.objective,
        constraints_json=req.constraints_json or {},
        acceptance_criteria_json=req.acceptance_criteria_json or {},
        risk_notes=req.risk_notes,
        created_by_type="user",
        created_by_user_id=user.id,
    )
    db.add(spec)
    await db.flush()
    return {"id": str(spec.id), "version_no": spec.version_no}


@router.get("/tickets/{ticket_id}/plans")
async def list_plans(
    ticket_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List plans for a ticket."""
    tid = parse_uuid(ticket_id, "ticket_id")
    result = await db.execute(
        select(Plan).where(Plan.ticket_id == tid).order_by(Plan.version_no.desc())
    )
    plans = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "version_no": p.version_no,
            "status": p.status,
            "summary": p.summary,
            "estimated_cost_usd": float(p.estimated_cost_usd or 0),
            "estimated_minutes": p.estimated_minutes,
            "risk_level": p.risk_level,
        }
        for p in plans
    ]


@router.post("/tickets/{ticket_id}/plans")
async def create_plan(
    ticket_id: str,
    req: PlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a plan."""
    tid = parse_uuid(ticket_id, "ticket_id")
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == tid))
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    existing = await db.execute(select(Plan).where(Plan.ticket_id == tid))
    count = len(existing.scalars().all())
    plan = Plan(
        id=uuid.uuid4(),
        company_id=ticket.company_id,
        ticket_id=tid,
        spec_id=parse_uuid(req.spec_id, "spec_id"),
        version_no=count + 1,
        status="draft",
        summary=req.summary,
        estimated_cost_usd=req.estimated_cost_usd,
        estimated_minutes=req.estimated_minutes,
        approval_required=req.approval_required,
        risk_level=req.risk_level,
        plan_json=req.plan_json or {},
    )
    db.add(plan)
    await db.flush()
    return {"id": str(plan.id), "version_no": plan.version_no}


@router.post("/plans/{plan_id}/approve")
async def approve_plan(
    plan_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Approve plan + build DAG + generate tasks."""
    pid = parse_uuid(plan_id, "plan_id")
    result = await db.execute(select(Plan).where(Plan.id == pid))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "approved"

    # Build DAG from plan_json and create Task records
    plan_data = plan.plan_json or {}
    tasks_data = plan_data.get("tasks", [])
    created_tasks = []

    for i, t in enumerate(tasks_data):
        task = Task(
            id=uuid.uuid4(),
            company_id=plan.company_id,
            ticket_id=plan.ticket_id,
            plan_id=plan.id,
            title=t.get("title", f"Task {i + 1}"),
            description=t.get("description", ""),
            sequence_no=i,
            status="ready" if not t.get("depends_on") else "pending",
            task_type=t.get("task_type", "execution"),
            requires_approval=t.get("requires_approval", False),
            depends_on_json=t.get("depends_on", []),
            verification_json=t.get("verification", {}),
        )
        db.add(task)
        created_tasks.append(task)

    # Record audit
    audit = AuditLog(
        id=generate_uuid(),
        company_id=plan.company_id,
        actor_type="user",
        event_type="plan.approved",
        target_type="plan",
        target_id=plan.id,
        ticket_id=plan.ticket_id,
        details_json={"tasks_created": len(created_tasks)},
    )
    db.add(audit)

    # Update ticket status
    ticket_result = (
        await db.execute(select(Ticket).where(Ticket.id == plan.ticket_id))
        if hasattr(plan, "ticket_id")
        else None
    )
    if ticket_result:
        ticket = ticket_result.scalar_one_or_none()
        if ticket:
            ticket.status = "in_progress"
            ticket.current_plan_id = plan.id

    await db.commit()
    return {
        "status": "approved",
        "tasks_created": len(created_tasks),
        "task_ids": [str(t.id) for t in created_tasks],
    }


@router.post("/plans/{plan_id}/reject")
async def reject_plan(
    plan_id: str,
    reason: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reject plan."""
    result = await db.execute(select(Plan).where(Plan.id == parse_uuid(plan_id, "plan_id")))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "rejected"
    await db.commit()
    return {"status": "rejected"}


@router.get("/plans/{plan_id}/tasks")
async def list_plan_tasks(
    plan_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List tasks for a plan."""
    pid = parse_uuid(plan_id, "plan_id")
    result = await db.execute(select(Task).where(Task.plan_id == pid).order_by(Task.sequence_no))
    tasks = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "sequence_no": t.sequence_no,
            "status": t.status,
            "task_type": t.task_type,
            "requires_approval": t.requires_approval,
        }
        for t in tasks
    ]
