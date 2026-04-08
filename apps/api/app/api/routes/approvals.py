"""Approval management endpoints.

All approval endpoints require authentication.
Approval and rejection can only be performed by human users (per CLAUDE.md §12.3).
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.review import ApprovalRequest
from app.models.user import User
from app.policies.approval_gate import (
    check_operations_batch,
    generate_action_preview,
    get_highest_risk,
)

router = APIRouter()


class OperationDetail(BaseModel):
    """An operation with optional payload for preview generation."""

    name: str
    payload: dict | None = None


class BatchApprovalRequest(BaseModel):
    """Plan approval at planning time: batch-check all operations."""

    operations: list[str]
    operation_details: list[OperationDetail] | None = None
    plan_id: str | None = None
    auto_approve_safe: bool = False


class BatchApprovalDecision(BaseModel):
    """Approve or reject multiple approval requests at once."""

    approval_ids: list[str]
    decision: str  # "approved" or "rejected"
    reason: str = ""


def _validate_uuid(value: str, name: str = "ID") -> uuid.UUID:
    """Safely parse a UUID string."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid {name}: {value}")


@router.get("/companies/{company_id}/approvals")
async def list_approvals(
    company_id: str,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List pending approvals."""
    cid = _validate_uuid(company_id, "company_id")
    query = select(ApprovalRequest).where(ApprovalRequest.company_id == cid)
    if status:
        query = query.where(ApprovalRequest.status == status)
    query = query.order_by(ApprovalRequest.requested_at.desc())
    result = await db.execute(query)
    approvals = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "target_type": a.target_type,
            "target_id": str(a.target_id),
            "status": a.status,
            "reason": a.reason,
            "risk_level": a.risk_level,
            "preview": generate_action_preview(
                a.target_type,
                a.payload_json if a.payload_json else None,
            ),
            "task_context": {
                "task_id": (a.payload_json or {}).get("task_id"),
                "ticket_id": (a.payload_json or {}).get("ticket_id"),
                "task_name": (a.payload_json or {}).get("task_name"),
            },
            "requested_at": a.requested_at.isoformat() if a.requested_at else None,
        }
        for a in approvals
    ]


@router.post("/companies/{company_id}/approvals/batch-check")
async def batch_check_approvals(
    company_id: str,
    req: BatchApprovalRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Plan approval: batch-check all operations at planning time.

    Returns which operations require approval and overall risk level,
    allowing users to approve all at once during the planning phase.
    """
    _validate_uuid(company_id, "company_id")
    results = check_operations_batch(req.operations)
    needs_approval = [r for r in results if r.requires_approval]
    highest_risk = get_highest_risk(results)

    # Build per-operation previews from operation_details payloads if available
    details_map: dict[int, dict | None] = {}
    if req.operation_details:
        for idx, detail in enumerate(req.operation_details):
            details_map[idx] = detail.payload

    return {
        "plan_id": req.plan_id,
        "total_operations": len(req.operations),
        "requires_approval_count": len(needs_approval),
        "highest_risk": highest_risk.value,
        "operations": [
            {
                "operation": req.operations[i],
                "requires_approval": r.requires_approval,
                "category": r.category.value if r.category else None,
                "risk_level": r.risk_level.value,
                "reason": r.reason,
                "preview": generate_action_preview(
                    req.operations[i],
                    details_map.get(i),
                ),
            }
            for i, r in enumerate(results)
        ],
    }


@router.post("/companies/{company_id}/approvals/batch-decide")
async def batch_decide_approvals(
    company_id: str,
    req: BatchApprovalDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Batch approve/reject multiple approval requests at once.

    Used during planning phase to handle all pending approvals together.
    """
    _validate_uuid(company_id, "company_id")
    if req.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    decided = []
    for aid in req.approval_ids:
        aid_uuid = _validate_uuid(aid, "approval_id")
        result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == aid_uuid))
        approval = result.scalar_one_or_none()
        if not approval or approval.status != "requested":
            continue

        approval.status = req.decision
        approval.decided_at = datetime.now(UTC)
        approval.decided_by = str(user.id)

        audit = AuditLog(
            id=generate_uuid(),
            company_id=approval.company_id,
            actor_type="user",
            actor_id=user.id,
            event_type=f"approval.{req.decision}",
            target_type=approval.target_type,
            target_id=approval.target_id,
            details_json={
                "decision": req.decision,
                "reason": req.reason,
                "batch": True,
                "decided_by": str(user.id),
            },
        )
        db.add(audit)
        decided.append(str(approval.id))

    await db.commit()
    return {"decided": decided, "decision": req.decision, "count": len(decided)}


@router.post("/approvals/{approval_id}/approve")
async def approve(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Approve — only authenticated users can perform this action."""
    aid = _validate_uuid(approval_id, "approval_id")
    result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == aid))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "requested":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve: current status is {approval.status}",
        )
    approval.status = "approved"
    approval.decided_at = datetime.now(UTC)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=approval.company_id,
        actor_type="user",
        actor_id=user.id,
        event_type="approval.approved",
        target_type=approval.target_type,
        target_id=approval.target_id,
        details_json={"decided_by": str(user.id)},
    )
    db.add(audit)
    await db.commit()
    return {"status": "approved"}


@router.post("/approvals/{approval_id}/reject")
async def reject(
    approval_id: str,
    reason: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reject — only authenticated users can perform this action."""
    aid = _validate_uuid(approval_id, "approval_id")
    result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == aid))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "requested":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject: current status is {approval.status}",
        )
    approval.status = "rejected"
    approval.decided_at = datetime.now(UTC)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=approval.company_id,
        actor_type="user",
        actor_id=user.id,
        event_type="approval.rejected",
        target_type=approval.target_type,
        target_id=approval.target_id,
        details_json={"decided_by": str(user.id), "reason": reason},
    )
    db.add(audit)
    await db.commit()
    return {"status": "rejected", "reason": reason}
