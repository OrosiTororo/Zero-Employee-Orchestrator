"""Budget enforcement service.

Checks cost limits before task execution and records costs after completion.
Implements warn/stop thresholds per BudgetPolicy.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.budget import BudgetPolicy, CostLedger


class BudgetCheckResult:
    def __init__(
        self,
        allowed: bool,
        usage_pct: float = 0.0,
        remaining_usd: float = 0.0,
        policy_name: str = "",
        warning: str | None = None,
    ):
        self.allowed = allowed
        self.usage_pct = usage_pct
        self.remaining_usd = remaining_usd
        self.policy_name = policy_name
        self.warning = warning


async def check_budget(
    db: AsyncSession,
    company_id: str,
    scope_type: str,
    scope_id: str,
    estimated_cost_usd: float = 0.0,
) -> BudgetCheckResult:
    """Check if a task execution is allowed under budget constraints."""
    cid = uuid.UUID(company_id)
    sid = uuid.UUID(scope_id)

    # Find applicable budget policy
    result = await db.execute(
        select(BudgetPolicy).where(
            BudgetPolicy.company_id == cid,
            BudgetPolicy.scope_type == scope_type,
            BudgetPolicy.scope_id == sid,
        )
    )
    policy = result.scalar_one_or_none()

    if not policy:
        # No budget policy - allow execution
        return BudgetCheckResult(allowed=True)

    limit = float(policy.limit_usd or 0)
    if limit <= 0:
        return BudgetCheckResult(allowed=True, policy_name=policy.name)

    # Sum current costs for this scope
    cost_result = await db.execute(
        select(func.coalesce(func.sum(CostLedger.cost_usd), 0)).where(
            CostLedger.company_id == cid,
            CostLedger.scope_type == scope_type,
            CostLedger.scope_id == sid,
        )
    )
    current_cost = float(cost_result.scalar() or 0)
    projected = current_cost + estimated_cost_usd
    usage_pct = (projected / limit) * 100
    remaining = max(0, limit - current_cost)

    stop_pct = float(policy.stop_threshold_pct or 100)
    warn_pct = float(policy.warn_threshold_pct or 80)

    if usage_pct >= stop_pct:
        return BudgetCheckResult(
            allowed=False,
            usage_pct=usage_pct,
            remaining_usd=remaining,
            policy_name=policy.name,
            warning=f"Budget limit reached: {usage_pct:.1f}% of ${limit:.2f}",
        )

    warning = None
    if usage_pct >= warn_pct:
        warning = f"Budget warning: {usage_pct:.1f}% of ${limit:.2f} used"

    return BudgetCheckResult(
        allowed=True,
        usage_pct=usage_pct,
        remaining_usd=remaining,
        policy_name=policy.name,
        warning=warning,
    )


async def record_cost(
    db: AsyncSession,
    company_id: str,
    scope_type: str,
    scope_id: str,
    provider_name: str,
    cost_usd: float,
    run_type: str = "task",
    run_id: str | None = None,
    model_name: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
) -> CostLedger:
    """Record a cost entry in the ledger."""
    entry = CostLedger(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        scope_type=scope_type,
        scope_id=uuid.UUID(scope_id),
        provider_name=provider_name,
        model_name=model_name,
        cost_usd=cost_usd,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        occurred_at=datetime.now(UTC),
        run_type=run_type,
        run_id=uuid.UUID(run_id) if run_id else None,
    )
    db.add(entry)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        actor_type="system",
        event_type="cost.recorded",
        target_type=scope_type,
        target_id=uuid.UUID(scope_id),
        details_json={
            "cost_usd": cost_usd,
            "provider": provider_name,
            "model": model_name,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(entry)
    return entry


async def get_cost_summary(
    db: AsyncSession,
    company_id: str,
    scope_type: str | None = None,
    scope_id: str | None = None,
) -> dict:
    """Get cost summary for a company, optionally filtered by scope."""
    cid = uuid.UUID(company_id)

    query = select(
        func.coalesce(func.sum(CostLedger.cost_usd), 0).label("total"),
        func.count(CostLedger.id).label("count"),
    ).where(CostLedger.company_id == cid)

    if scope_type:
        query = query.where(CostLedger.scope_type == scope_type)
    if scope_id:
        query = query.where(CostLedger.scope_id == uuid.UUID(scope_id))

    result = await db.execute(query)
    row = result.one()
    return {
        "total_cost_usd": float(row.total),
        "transaction_count": row.count,
    }
