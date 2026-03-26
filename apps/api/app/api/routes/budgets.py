"""Budget and cost management endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.budget import BudgetPolicy, CostLedger
from app.models.user import User

router = APIRouter()


class BudgetPolicyCreate(BaseModel):
    name: str
    scope_type: str = "company"
    period_type: str = "monthly"
    limit_usd: float = 100.0
    warn_threshold_pct: int = 80
    stop_threshold_pct: int = 100


@router.get("/companies/{company_id}/budgets")
async def list_budgets(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List budget policies."""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(BudgetPolicy).where(BudgetPolicy.company_id == cid))
    budgets = result.scalars().all()
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "scope_type": b.scope_type,
            "period_type": b.period_type,
            "limit_usd": float(b.limit_usd),
            "warn_threshold_pct": b.warn_threshold_pct,
            "stop_threshold_pct": b.stop_threshold_pct,
        }
        for b in budgets
    ]


@router.post("/companies/{company_id}/budgets")
async def create_budget(
    company_id: str,
    req: BudgetPolicyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a budget policy."""
    policy = BudgetPolicy(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        name=req.name,
        scope_type=req.scope_type,
        period_type=req.period_type,
        limit_usd=req.limit_usd,
        warn_threshold_pct=req.warn_threshold_pct,
        stop_threshold_pct=req.stop_threshold_pct,
    )
    db.add(policy)
    await db.flush()
    return {"id": str(policy.id), "name": policy.name}


@router.get("/companies/{company_id}/costs/summary")
async def get_cost_summary(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get cost summary."""
    cid = uuid.UUID(company_id)
    total = await db.execute(
        select(func.coalesce(func.sum(CostLedger.cost_usd), 0)).where(CostLedger.company_id == cid)
    )
    return {"total_cost_usd": float(total.scalar()), "currency": "USD"}
