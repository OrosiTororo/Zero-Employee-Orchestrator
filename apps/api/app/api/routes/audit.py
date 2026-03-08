"""Audit log endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.audit import AuditLog

router = APIRouter()


@router.get("/companies/{company_id}/audit-logs")
async def list_audit_logs(
    company_id: str,
    event_type: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """監査ログ一覧"""
    cid = uuid.UUID(company_id)
    query = select(AuditLog).where(AuditLog.company_id == cid)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "actor_type": log.actor_type,
            "event_type": log.event_type,
            "target_type": log.target_type,
            "target_id": str(log.target_id) if log.target_id else None,
            "trace_id": log.trace_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
