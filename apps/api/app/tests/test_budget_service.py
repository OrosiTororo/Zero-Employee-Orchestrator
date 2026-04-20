"""Tests for budget_service."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetPolicy
from app.models.company import Company
from app.services import budget_service


async def _seed_company(db: AsyncSession) -> str:
    company = Company(
        id=uuid.uuid4(),
        slug=f"budget-{uuid.uuid4().hex[:8]}",
        name="Budget Test Co",
    )
    db.add(company)
    await db.commit()
    return str(company.id)


async def _seed_policy(
    db: AsyncSession,
    company_id: str,
    scope_id: str,
    *,
    limit_usd: float,
    warn_pct: int = 80,
    stop_pct: int = 100,
) -> None:
    policy = BudgetPolicy(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        name="test-policy",
        scope_type="project",
        scope_id=uuid.UUID(scope_id),
        period_type="monthly",
        limit_usd=limit_usd,
        warn_threshold_pct=warn_pct,
        stop_threshold_pct=stop_pct,
    )
    db.add(policy)
    await db.commit()


@pytest.mark.asyncio
async def test_check_budget_allows_without_policy(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    scope_id = str(uuid.uuid4())
    result = await budget_service.check_budget(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        estimated_cost_usd=5.0,
    )
    assert result.allowed is True
    assert result.policy_name == ""


@pytest.mark.asyncio
async def test_check_budget_warns_near_threshold(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    scope_id = str(uuid.uuid4())
    await _seed_policy(db_session, company_id, scope_id, limit_usd=100.0, warn_pct=80)
    await budget_service.record_cost(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        provider_name="openrouter",
        cost_usd=75.0,
    )
    result = await budget_service.check_budget(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        estimated_cost_usd=10.0,
    )
    assert result.allowed is True
    assert result.warning is not None


@pytest.mark.asyncio
async def test_check_budget_blocks_when_stop_reached(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    scope_id = str(uuid.uuid4())
    await _seed_policy(db_session, company_id, scope_id, limit_usd=100.0, stop_pct=100)
    await budget_service.record_cost(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        provider_name="openrouter",
        cost_usd=95.0,
    )
    result = await budget_service.check_budget(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        estimated_cost_usd=10.0,
    )
    assert result.allowed is False
    assert "Budget limit reached" in (result.warning or "")


@pytest.mark.asyncio
async def test_record_cost_and_summary(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    scope_id = str(uuid.uuid4())
    await budget_service.record_cost(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        provider_name="openrouter",
        cost_usd=3.5,
    )
    await budget_service.record_cost(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
        provider_name="openrouter",
        cost_usd=2.5,
    )
    summary = await budget_service.get_cost_summary(
        db=db_session,
        company_id=company_id,
        scope_type="project",
        scope_id=scope_id,
    )
    assert summary["transaction_count"] == 2
    assert summary["total_cost_usd"] == pytest.approx(6.0, abs=0.01)
