"""Audit Logger -- Audit event recording helper.

Utility for recording audit logs of important operations in a consistent format.
Simplifies writing to the AuditLog model and is available from all layers.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.audit import AuditLog


async def record_audit_event(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    event_type: str,
    target_type: str,
    *,
    actor_type: str = "system",
    actor_user_id: str | uuid.UUID | None = None,
    actor_agent_id: str | uuid.UUID | None = None,
    target_id: str | uuid.UUID | None = None,
    ticket_id: str | uuid.UUID | None = None,
    task_id: str | uuid.UUID | None = None,
    details: dict | None = None,
    trace_id: str | None = None,
    auto_commit: bool = True,
) -> AuditLog:
    """Record an audit event.

    Args:
        db: Database session
        company_id: Company ID
        event_type: Event type (e.g., "task.started", "approval.requested")
        target_type: Target type (e.g., "task", "ticket", "agent")
        actor_type: Actor type ("user", "agent", "system")
        actor_user_id: Acting user ID (when actor_type="user")
        actor_agent_id: Acting agent ID (when actor_type="agent")
        target_id: Target resource ID
        ticket_id: Related ticket ID
        task_id: Related task ID
        details: Additional details (JSON)
        trace_id: Trace ID (for distributed tracing)
        auto_commit: Whether to auto-commit
    """

    def _to_uuid(v: str | uuid.UUID | None) -> uuid.UUID | None:
        if v is None:
            return None
        return uuid.UUID(str(v)) if not isinstance(v, uuid.UUID) else v

    log = AuditLog(
        id=generate_uuid(),
        company_id=_to_uuid(company_id),  # type: ignore[arg-type]
        actor_type=actor_type,
        actor_user_id=_to_uuid(actor_user_id),
        actor_agent_id=_to_uuid(actor_agent_id),
        event_type=event_type,
        target_type=target_type,
        target_id=_to_uuid(target_id),
        ticket_id=_to_uuid(ticket_id),
        task_id=_to_uuid(task_id),
        details_json=details or {},
        trace_id=trace_id,
    )
    db.add(log)

    if auto_commit:
        await db.commit()
        await db.refresh(log)

    return log


async def record_state_change(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    target_type: str,
    target_id: str | uuid.UUID,
    old_status: str,
    new_status: str,
    *,
    actor_type: str = "system",
    actor_user_id: str | uuid.UUID | None = None,
    actor_agent_id: str | uuid.UUID | None = None,
    reason: str | None = None,
    auto_commit: bool = True,
) -> AuditLog:
    """Record a state transition in the audit log."""
    return await record_audit_event(
        db=db,
        company_id=company_id,
        event_type=f"{target_type}.status_changed",
        target_type=target_type,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        actor_agent_id=actor_agent_id,
        target_id=target_id,
        details={
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
        },
        auto_commit=auto_commit,
    )


async def record_dangerous_operation(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    operation_type: str,
    target_type: str,
    target_id: str | uuid.UUID,
    *,
    actor_type: str = "agent",
    actor_agent_id: str | uuid.UUID | None = None,
    details: dict | None = None,
    auto_commit: bool = True,
) -> AuditLog:
    """Record the execution of a dangerous operation in the audit log."""
    return await record_audit_event(
        db=db,
        company_id=company_id,
        event_type=f"dangerous_operation.{operation_type}",
        target_type=target_type,
        actor_type=actor_type,
        actor_agent_id=actor_agent_id,
        target_id=target_id,
        details={
            "operation_type": operation_type,
            **(details or {}),
        },
        auto_commit=auto_commit,
    )
