"""Plan-first endpoints — proposal generation, sub-plan tree, plan diff.

Web-side counterpart to the existing CLI ``/plan`` command. The legacy
``specs_plans`` router only exposes plans nested under a ticket; this router
gives the orchestrator a goal-only proposal flow so the UI's plan-mode
overlay (and external API consumers) can ask for a plan without first
manufacturing a ticket and a spec.

Endpoints
---------

* ``POST   /companies/{cid}/plans``                   — generate a proposal
* ``GET    /companies/{cid}/plans``                   — list standalone proposals
* ``GET    /companies/{cid}/plans/{plan_id}``         — fetch one
* ``GET    /companies/{cid}/plans/{plan_id}/tree``    — sub-plan delegation tree
* ``GET    /companies/{cid}/plans/{plan_id}/diff``    — diff against another plan
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.validators import parse_uuid
from app.api.routes.auth import get_current_user
from app.models.audit import AuditLog
from app.models.plan import Plan
from app.models.task import Task
from app.models.user import User
from app.orchestration.repropose import diff_persisted_plans
from app.policies.approval_gate import check_approval_required
from app.policies.autonomy_boundary import AutonomyLevel

router = APIRouter()


# ---------- Schemas ----------


class PlanProposalRequest(BaseModel):
    goal: str = Field(..., min_length=3, max_length=2000)
    autonomy: str = Field(default=AutonomyLevel.SEMI_AUTO.value)
    ticket_id: str | None = None
    spec_id: str | None = None


class PlanProposalResponse(BaseModel):
    plan_id: str
    summary: str
    plan_md: str
    estimated_cost_usd: float
    estimated_minutes: int
    requires_approval: bool
    autonomy: str
    tasks: list[dict[str, Any]]


class PlanListItem(BaseModel):
    id: str
    version_no: int
    status: str
    summary: str | None
    goal: str | None
    estimated_cost_usd: float
    estimated_minutes: int
    risk_level: str
    parent_plan_id: str | None


class PlanTreeNode(BaseModel):
    id: str
    summary: str | None
    goal: str | None
    status: str
    framework: str | None
    delegation_metadata: dict | None
    children: list[PlanTreeNode] = []


class PlanDiffResponse(BaseModel):
    base_plan_id: str
    against_plan_id: str
    added_tasks: list[str]
    removed_tasks: list[str]
    modified_tasks: list[str]
    added_task_ids: list[str]
    removed_task_ids: list[str]
    modified_task_ids: list[str]
    cost_change_usd: float
    time_change_minutes: int


# ---------- Helpers ----------


def _normalize_autonomy(raw: str) -> AutonomyLevel:
    candidate = (raw or "").strip().lower().replace("-", "_")
    try:
        return AutonomyLevel(candidate)
    except ValueError as exc:
        valid = ", ".join(level.value for level in AutonomyLevel)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid autonomy '{raw}'. Allowed: {valid}",
        ) from exc


async def _next_version(db: AsyncSession, company_uuid: uuid.UUID) -> int:
    res = await db.execute(
        select(Plan.version_no)
        .where(Plan.company_id == company_uuid)
        .where(Plan.ticket_id.is_(None))
        .order_by(Plan.version_no.desc())
        .limit(1)
    )
    latest = res.scalar_one_or_none()
    return (latest or 0) + 1


async def _plan_with_task_payload(db: AsyncSession, plan: Plan) -> dict:
    """Return the ``{tasks: [...], estimated_cost_usd, estimated_minutes}``
    shape consumed by :func:`diff_persisted_plans`."""
    if plan.ticket_id is None and plan.parent_plan_id is None:
        # Standalone proposal — tasks live inside ``plan_json["tasks"]``.
        plan_json = plan.plan_json or {}
        tasks_payload = plan_json.get("tasks", [])
    else:
        res = await db.execute(
            select(Task).where(Task.plan_id == plan.id).order_by(Task.sequence_no)
        )
        tasks_payload = [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "task_type": t.task_type,
                "requires_approval": t.requires_approval,
            }
            for t in res.scalars().all()
        ]
    return {
        "tasks": tasks_payload,
        "estimated_cost_usd": float(plan.estimated_cost_usd or 0),
        "estimated_minutes": plan.estimated_minutes or 0,
    }


# ---------- Routes ----------


@router.post("/companies/{company_id}/plans", response_model=PlanProposalResponse)
async def propose_plan(
    company_id: str,
    req: PlanProposalRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlanProposalResponse:
    """Generate a Plan proposal from a natural-language goal.

    Wraps the same ``PlanWriterSkill`` machinery the CLI ``/plan`` command
    uses, then persists the result so the UI can display, diff, and (with
    a separate explicit step) approve it.
    """
    autonomy = _normalize_autonomy(req.autonomy)
    company_uuid = parse_uuid(company_id, "company_id")

    try:
        from skills.builtin.plan_writer import generate_plan_template, plan_to_markdown
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="plan_writer skill not available in this install",
        ) from exc

    spec_uuid = parse_uuid(req.spec_id, "spec_id") if req.spec_id else None
    ticket_uuid = parse_uuid(req.ticket_id, "ticket_id") if req.ticket_id else None

    template = generate_plan_template(
        spec_id=str(spec_uuid) if spec_uuid else "proposal",
        goal=req.goal,
        scope=req.goal,
    )
    plan_md = plan_to_markdown(template)

    requires_approval = autonomy in (AutonomyLevel.OBSERVE, AutonomyLevel.ASSIST)
    if not requires_approval:
        for planned in template.tasks:
            if planned.requires_approval:
                requires_approval = True
                break
            gate = check_approval_required(planned.task_type)
            if gate.requires_approval:
                requires_approval = True
                break

    next_version = await _next_version(db, company_uuid)
    plan = Plan(
        id=uuid.uuid4(),
        company_id=company_uuid,
        ticket_id=ticket_uuid,
        spec_id=spec_uuid,
        version_no=next_version,
        status="proposal",
        summary=f"Plan proposal for: {req.goal[:120]}",
        estimated_cost_usd=0.0,
        estimated_minutes=template.estimated_total_minutes,
        approval_required=requires_approval,
        risk_level="low",
        plan_json={
            "tasks": [
                {
                    "id": f"proposal-{t.sequence_no}",
                    "title": t.title,
                    "description": t.description,
                    "task_type": t.task_type,
                    "requires_approval": t.requires_approval,
                    "depends_on": t.depends_on,
                    "estimated_minutes": t.estimated_minutes,
                    "skill_name": t.skill_name,
                }
                for t in template.tasks
            ],
            "autonomy": autonomy.value,
            "plan_md": plan_md,
        },
        goal=req.goal,
    )
    db.add(plan)

    audit = AuditLog(
        id=uuid.uuid4(),
        company_id=company_uuid,
        actor_type="user",
        actor_user_id=user.id,
        event_type="plan.proposed",
        target_type="plan",
        target_id=plan.id,
        details_json={
            "goal": req.goal,
            "autonomy": autonomy.value,
            "task_count": len(template.tasks),
        },
    )
    db.add(audit)
    await db.commit()

    return PlanProposalResponse(
        plan_id=str(plan.id),
        summary=plan.summary or "",
        plan_md=plan_md,
        estimated_cost_usd=float(plan.estimated_cost_usd or 0),
        estimated_minutes=plan.estimated_minutes or 0,
        requires_approval=requires_approval,
        autonomy=autonomy.value,
        tasks=plan.plan_json.get("tasks", []) if plan.plan_json else [],
    )


@router.get("/companies/{company_id}/plans", response_model=list[PlanListItem])
async def list_proposals(
    company_id: str,
    include_attached: bool = Query(
        default=False,
        description="Include plans attached to a ticket (legacy nested plans).",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PlanListItem]:
    """List Plan proposals for a company, newest first."""
    company_uuid = parse_uuid(company_id, "company_id")
    stmt = select(Plan).where(Plan.company_id == company_uuid)
    if not include_attached:
        stmt = stmt.where(Plan.ticket_id.is_(None))
    stmt = stmt.order_by(Plan.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return [
        PlanListItem(
            id=str(p.id),
            version_no=p.version_no,
            status=p.status,
            summary=p.summary,
            goal=p.goal,
            estimated_cost_usd=float(p.estimated_cost_usd or 0),
            estimated_minutes=p.estimated_minutes or 0,
            risk_level=p.risk_level,
            parent_plan_id=str(p.parent_plan_id) if p.parent_plan_id else None,
        )
        for p in res.scalars().all()
    ]


@router.get("/companies/{company_id}/plans/{plan_id}/tree", response_model=PlanTreeNode)
async def get_plan_tree(
    company_id: str,
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PlanTreeNode:
    """Return the parent → child sub-plan tree for a Plan.

    Sub-plans are written by ``AgentAdapterRegistry._persist_audit`` whenever
    a delegated framework returns its own intermediate steps.
    """
    company_uuid = parse_uuid(company_id, "company_id")
    root_uuid = parse_uuid(plan_id, "plan_id")

    res = await db.execute(
        select(Plan).where(Plan.company_id == company_uuid).where(Plan.id == root_uuid)
    )
    root = res.scalar_one_or_none()
    if root is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    res = await db.execute(select(Plan).where(Plan.company_id == company_uuid))
    by_parent: dict[uuid.UUID | None, list[Plan]] = {}
    for plan in res.scalars().all():
        by_parent.setdefault(plan.parent_plan_id, []).append(plan)

    def _build(node: Plan) -> PlanTreeNode:
        meta = node.delegation_metadata or {}
        return PlanTreeNode(
            id=str(node.id),
            summary=node.summary,
            goal=node.goal,
            status=node.status,
            framework=meta.get("framework") if isinstance(meta, dict) else None,
            delegation_metadata=meta if isinstance(meta, dict) else None,
            children=[_build(child) for child in by_parent.get(node.id, [])],
        )

    return _build(root)


@router.get("/companies/{company_id}/plans/{plan_id}/diff", response_model=PlanDiffResponse)
async def get_plan_diff(
    company_id: str,
    plan_id: str,
    against: str = Query(..., description="Plan id to diff against (the older revision)."),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PlanDiffResponse:
    """Compute task-level diff between two Plan revisions."""
    company_uuid = parse_uuid(company_id, "company_id")
    base_uuid = parse_uuid(plan_id, "plan_id")
    against_uuid = parse_uuid(against, "against")

    res = await db.execute(
        select(Plan)
        .where(Plan.company_id == company_uuid)
        .where(Plan.id.in_([base_uuid, against_uuid]))
    )
    plans = {p.id: p for p in res.scalars().all()}
    if base_uuid not in plans or against_uuid not in plans:
        raise HTTPException(status_code=404, detail="One or both plans not found")

    new_payload = await _plan_with_task_payload(db, plans[base_uuid])
    prev_payload = await _plan_with_task_payload(db, plans[against_uuid])

    diff = diff_persisted_plans(prev_payload, new_payload)
    return PlanDiffResponse(
        base_plan_id=str(base_uuid),
        against_plan_id=str(against_uuid),
        added_tasks=diff.added_tasks,
        removed_tasks=diff.removed_tasks,
        modified_tasks=diff.modified_tasks,
        added_task_ids=diff.added_task_ids,
        removed_task_ids=diff.removed_task_ids,
        modified_task_ids=diff.modified_task_ids,
        cost_change_usd=diff.cost_change_usd,
        time_change_minutes=diff.time_change_minutes,
    )


PlanTreeNode.model_rebuild()
