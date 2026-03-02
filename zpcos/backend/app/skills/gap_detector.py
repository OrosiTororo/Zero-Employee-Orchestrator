"""Skill Gap Negotiation — 不足Skillの検出と提案。"""

from pydantic import BaseModel
from app.skills.framework import SkillRegistry
from app.orchestrator.models import OrchestrationPlan


class SkillGap(BaseModel):
    required_skill: str
    reason: str
    options: list[str]


async def detect_gaps(plan: OrchestrationPlan, registry: SkillRegistry) -> list[SkillGap]:
    """Plan で必要な Skill のうち、未登録のものを検出。"""
    gaps = []
    for step in plan.steps:
        if not registry.has_skill(step.skill_name):
            gaps.append(SkillGap(
                required_skill=step.skill_name,
                reason=f"Plan のステップ '{step.step_id}' で必要ですが未登録です",
                options=[
                    "代替: 既存 Skill で代用する",
                    f"自動生成: '{step.skill_name}' を AI で生成する",
                    "スキップ: このステップを除外して実行する",
                ],
            ))
    return gaps
