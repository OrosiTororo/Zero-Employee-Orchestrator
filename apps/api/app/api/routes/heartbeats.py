"""Heartbeat policy and run endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.heartbeat import HeartbeatPolicy, HeartbeatRun

router = APIRouter()


class HeartbeatPolicyCreate(BaseModel):
    name: str
    cron_expr: str = "0 * * * *"
    timezone: str = "UTC"
    enabled: bool = True
    jitter_seconds: int = 0
    max_parallel_runs: int = 1


@router.get("/companies/{company_id}/heartbeat-policies")
async def list_policies(company_id: str, db: AsyncSession = Depends(get_db)):
    """Heartbeatポリシー一覧"""
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


@router.post("/companies/{company_id}/heartbeat-policies")
async def create_policy(
    company_id: str, req: HeartbeatPolicyCreate, db: AsyncSession = Depends(get_db)
):
    """Heartbeatポリシー作成"""
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


@router.get("/companies/{company_id}/heartbeat-runs")
async def list_runs(company_id: str, db: AsyncSession = Depends(get_db)):
    """Heartbeat実行履歴"""
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
            "summary": r.summary,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]
