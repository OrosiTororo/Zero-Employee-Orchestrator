"""Cost Guard テスト"""

import pytest

from app.orchestrator.cost_guard import estimate_cost
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep


@pytest.mark.asyncio
async def test_estimate_basic():
    plan = OrchestrationPlan(
        intent="test plan",
        steps=[
            OrchestrationStep(step_id="1", skill_name="test-skill", depends_on=[]),
        ],
    )
    cost = await estimate_cost(plan, "balanced")
    assert cost.estimated_cost_usd >= 0
    assert cost.total_api_calls >= 1


@pytest.mark.asyncio
async def test_high_quality_costs_more():
    plan = OrchestrationPlan(
        intent="test",
        steps=[
            OrchestrationStep(step_id="1", skill_name="s1", depends_on=[]),
            OrchestrationStep(step_id="2", skill_name="s2", depends_on=["1"]),
        ],
    )
    cost_balanced = await estimate_cost(plan, "balanced")
    cost_hq = await estimate_cost(plan, "high_quality")
    assert cost_hq.estimated_cost_usd >= cost_balanced.estimated_cost_usd
