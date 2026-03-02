"""Re-Propose — 差し戻し時の再提案 + Plan Diff。"""

from enum import Enum
from pydantic import BaseModel
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep
from app.gateway import call_llm
import json


class ReExecuteMode(str, Enum):
    FULL_REGENERATE = "full_regenerate"
    FROM_STEP_N = "from_step_n"
    PLAN_MODIFY = "plan_modify"


class PlanDiff(BaseModel):
    added_steps: list[str] = []
    removed_steps: list[str] = []
    modified_steps: list[str] = []


async def repropose(
    original_plan: OrchestrationPlan,
    feedback: str,
    mode: ReExecuteMode = ReExecuteMode.PLAN_MODIFY,
    available_skills: list[str] | None = None,
) -> tuple[OrchestrationPlan, PlanDiff]:
    """フィードバックに基づいて Plan を再提案。"""
    prompt = f"""以下の実行計画に対してフィードバックがありました。計画を修正してください。

元の計画:
{json.dumps([s.model_dump() for s in original_plan.steps], ensure_ascii=False, indent=2)}

フィードバック: {feedback}
再実行モード: {mode.value}
{f'利用可能なSkill: {available_skills}' if available_skills else ''}

修正後の計画をJSON形式で返してください:
{{"intent": "...", "steps": [...]}}
JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]

    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        data = {"intent": original_plan.intent, "steps": []}

    new_steps = [OrchestrationStep(**s) for s in data.get("steps", [])]
    new_plan = OrchestrationPlan(
        intent=data.get("intent", original_plan.intent),
        steps=new_steps,
        quality_mode=original_plan.quality_mode,
    )

    diff = compute_diff(original_plan, new_plan)
    return new_plan, diff


def compute_diff(old: OrchestrationPlan, new: OrchestrationPlan) -> PlanDiff:
    """2つの Plan の差分を計算。"""
    old_ids = {s.step_id for s in old.steps}
    new_ids = {s.step_id for s in new.steps}

    added = list(new_ids - old_ids)
    removed = list(old_ids - new_ids)

    old_map = {s.step_id: s for s in old.steps}
    new_map = {s.step_id: s for s in new.steps}
    modified = []
    for sid in old_ids & new_ids:
        if old_map[sid].skill_name != new_map[sid].skill_name:
            modified.append(sid)
        elif old_map[sid].input_mapping != new_map[sid].input_mapping:
            modified.append(sid)

    return PlanDiff(added_steps=added, removed_steps=removed, modified_steps=modified)
