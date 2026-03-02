"""Skill Gap Detector テスト"""

import pytest

from app.skills.gap_detector import detect_gaps, SkillGap
from app.skills.framework import SkillRegistry
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep


@pytest.mark.asyncio
async def test_no_gaps_when_all_available():
    registry = SkillRegistry()
    # Register a mock skill name
    plan = OrchestrationPlan(
        intent="test",
        steps=[],  # empty plan = no gaps
    )
    gaps = await detect_gaps(plan, registry)
    assert len(gaps) == 0


@pytest.mark.asyncio
async def test_detect_missing_skill():
    registry = SkillRegistry()
    plan = OrchestrationPlan(
        intent="test",
        steps=[
            OrchestrationStep(step_id="1", skill_name="nonexistent-skill", depends_on=[]),
        ],
    )
    gaps = await detect_gaps(plan, registry)
    assert len(gaps) == 1
    assert gaps[0].required_skill == "nonexistent-skill"
    assert len(gaps[0].options) == 3
