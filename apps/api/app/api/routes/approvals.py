"""Approval management endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.review import ApprovalRequest

router = APIRouter()


@router.get("/companies/{company_id}/approvals")
async def list_approvals(
    company_id: str, status: str | None = None, db: AsyncSession = Depends(get_db)
):
    """承認待ち一覧"""
    cid = uuid.UUID(company_id)
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
            "requested_at": a.requested_at.isoformat() if a.requested_at else None,
        }
        for a in approvals
    ]


@router.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, db: AsyncSession = Depends(get_db)):
    """承認"""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == uuid.UUID(approval_id))
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "approved"
    approval.decided_at = datetime.utcnow()
    return {"status": "approved"}


@router.post("/approvals/{approval_id}/reject")
async def reject(
    approval_id: str, reason: str = "", db: AsyncSession = Depends(get_db)
):
    """却下"""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == uuid.UUID(approval_id))
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "rejected"
    approval.decided_at = datetime.utcnow()
    return {"status": "rejected"}
