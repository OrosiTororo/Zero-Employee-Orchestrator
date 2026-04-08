"""Heartbeat policy and run endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.heartbeat import HeartbeatPolicy, HeartbeatRun
from app.models.user import User

router = APIRouter()


class HeartbeatPolicyCreate(BaseModel):
    name: str
    cron_expr: str = "0 * * * *"
    timezone: str = "UTC"
    enabled: bool = True
    jitter_seconds: int = 0
    max_parallel_runs: int = 1


# ---------- Response Schemas ----------


class HeartbeatPolicyItem(BaseModel):
    """Single heartbeat policy in list response."""

    id: str
    name: str
    cron_expr: str
    enabled: bool
    timezone: str


class HeartbeatPolicyCreateResponse(BaseModel):
    """Response for heartbeat policy creation."""

    id: str
    name: str


class HeartbeatRunItem(BaseModel):
    """Single heartbeat run in list response."""

    id: str
    status: str
    summary: dict | None = None
    started_at: str | None = None
    finished_at: str | None = None


@router.get("/companies/{company_id}/heartbeat-policies", response_model=list[HeartbeatPolicyItem])
async def list_policies(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List heartbeat policies."""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(HeartbeatPolicy).where(HeartbeatPolicy.company_id == cid))
    policies = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "cron_expr": p.cron_expr,
            "enabled": p.enabled,
            "timezone": p.timezone,
        }
        for p in policies
    ]


@router.post(
    "/companies/{company_id}/heartbeat-policies", response_model=HeartbeatPolicyCreateResponse
)
async def create_policy(
    company_id: str,
    req: HeartbeatPolicyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a heartbeat policy."""
    policy = HeartbeatPolicy(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        name=req.name,
        cron_expr=req.cron_expr,
        timezone=req.timezone,
        enabled=req.enabled,
        jitter_seconds=req.jitter_seconds,
        max_parallel_runs=req.max_parallel_runs,
    )
    db.add(policy)
    await db.flush()
    return {"id": str(policy.id), "name": policy.name}


@router.get("/companies/{company_id}/heartbeat-runs", response_model=list[HeartbeatRunItem])
async def list_runs(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List heartbeat run history."""
    cid = uuid.UUID(company_id)
    result = await db.execute(
        select(HeartbeatRun)
        .where(HeartbeatRun.company_id == cid)
        .order_by(HeartbeatRun.started_at.desc())
        .limit(50)
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "status": r.status,
            "summary": r.summary_json,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]
