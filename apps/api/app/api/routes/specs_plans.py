"""Spec, Plan, and Task management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.spec import Spec
from app.models.plan import Plan
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.audit import AuditLog
from app.core.security import generate_uuid

router = APIRouter()


class SpecCreate(BaseModel):
    objective: str
    constraints_json: dict | None = None
    acceptance_criteria_json: dict | None = None
    risk_notes: str = ""


class PlanCreate(BaseModel):
    spec_id: str
    summary: str
    estimated_cost_usd: float = 0.0
    estimated_minutes: int = 0
    approval_required: bool = True
    risk_level: str = "low"
    plan_json: dict | None = None


@router.get("/tickets/{ticket_id}/specs")
async def list_specs(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットのspec一覧"""
    tid = uuid.UUID(ticket_id)
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
    ticket_id: str, req: SpecCreate, db: AsyncSession = Depends(get_db)
):
    """spec作成"""
    tid = uuid.UUID(ticket_id)
    existing = await db.execute(select(Spec).where(Spec.ticket_id == tid))
    count = len(existing.scalars().all())
    spec = Spec(
        id=uuid.uuid4(),
        ticket_id=tid,
        version_no=count + 1,
        status="draft",
        objective=req.objective,
        constraints_json=req.constraints_json or {},
        acceptance_criteria_json=req.acceptance_criteria_json or {},
        risk_notes=req.risk_notes,
        created_by_type="user",
    )
    db.add(spec)
    await db.flush()
    return {"id": str(spec.id), "version_no": spec.version_no}


@router.get("/tickets/{ticket_id}/plans")
async def list_plans(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットのplan一覧"""
    tid = uuid.UUID(ticket_id)
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
    ticket_id: str, req: PlanCreate, db: AsyncSession = Depends(get_db)
):
    """plan作成"""
    tid = uuid.UUID(ticket_id)
    existing = await db.execute(select(Plan).where(Plan.ticket_id == tid))
    count = len(existing.scalars().all())
    plan = Plan(
        id=uuid.uuid4(),
        ticket_id=tid,
        spec_id=uuid.UUID(req.spec_id),
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
async def approve_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    """planを承認 + DAG構築 + タスク生成"""
    pid = uuid.UUID(plan_id)
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

    await db.flush()
    return {
        "status": "approved",
        "tasks_created": len(created_tasks),
        "task_ids": [str(t.id) for t in created_tasks],
    }


@router.post("/plans/{plan_id}/reject")
async def reject_plan(
    plan_id: str, reason: str = "", db: AsyncSession = Depends(get_db)
):
    """planを却下"""
    result = await db.execute(select(Plan).where(Plan.id == uuid.UUID(plan_id)))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "rejected"
    return {"status": "rejected"}


@router.get("/plans/{plan_id}/tasks")
async def list_plan_tasks(plan_id: str, db: AsyncSession = Depends(get_db)):
    """planのtask一覧"""
    pid = uuid.UUID(plan_id)
    result = await db.execute(
        select(Task).where(Task.plan_id == pid).order_by(Task.sequence_no)
    )
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
