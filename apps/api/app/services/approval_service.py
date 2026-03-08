"""Approval request management with forced approval for dangerous operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.review import ApprovalRequest
from app.models.audit import AuditLog

# Operations that ALWAYS require human approval (Section 12.3, 25.1)
FORCED_APPROVAL_OPERATIONS = {
    "external_send",
    "publish",
    "post",
    "delete",
    "charge",
    "git_push",
    "git_release",
    "file_overwrite_important",
    "permission_change",
    "api_key_update",
    "credential_update",
}

# Valid state transitions for approval requests
APPROVAL_TRANSITIONS: dict[str, list[str]] = {
    "requested": ["approved", "rejected", "expired", "cancelled"],
    "approved": ["executed"],
    "rejected": ["superseded"],
    "expired": ["requested", "cancelled"],
    "cancelled": [],
    "executed": [],
    "superseded": [],
}


def requires_forced_approval(operation_type: str) -> bool:
    return operation_type in FORCED_APPROVAL_OPERATIONS


async def create_approval_request(
    db: AsyncSession,
    company_id: str,
    target_type: str,
    target_id: str,
    reason: str,
    risk_level: str = "medium",
    requested_by_type: str = "agent",
    requested_by_agent_id: str | None = None,
    requested_by_user_id: str | None = None,
    payload_json: dict | None = None,
) -> ApprovalRequest:
    req = ApprovalRequest(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        target_type=target_type,
        target_id=uuid.UUID(target_id),
        requested_by_type=requested_by_type,
        requested_by_agent_id=uuid.UUID(requested_by_agent_id) if requested_by_agent_id else None,
        requested_by_user_id=uuid.UUID(requested_by_user_id) if requested_by_user_id else None,
        status="requested",
        reason=reason,
        risk_level=risk_level,
        payload_json=payload_json or {},
        requested_at=datetime.now(timezone.utc),
    )
    db.add(req)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        actor_type=requested_by_type,
        actor_agent_id=uuid.UUID(requested_by_agent_id) if requested_by_agent_id else None,
        actor_user_id=uuid.UUID(requested_by_user_id) if requested_by_user_id else None,
        event_type="approval.requested",
        target_type=target_type,
        target_id=uuid.UUID(target_id),
        details_json={"reason": reason, "risk_level": risk_level},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(req)
    return req


async def decide_approval(
    db: AsyncSession,
    approval: ApprovalRequest,
    decision: str,
    approver_user_id: str,
    reason: str | None = None,
) -> ApprovalRequest:
    if approval.status != "requested":
        raise ValueError(f"Cannot decide on approval in status: {approval.status}")

    approval.status = decision  # "approved" or "rejected"
    approval.approver_user_id = uuid.UUID(approver_user_id)
    approval.decided_at = datetime.now(timezone.utc)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=approval.company_id,
        actor_type="user",
        actor_user_id=uuid.UUID(approver_user_id),
        event_type=f"approval.{decision}",
        target_type=approval.target_type,
        target_id=approval.target_id,
        details_json={"decision": decision, "reason": reason},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(approval)
    return approval
