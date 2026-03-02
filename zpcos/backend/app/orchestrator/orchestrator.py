"""Task Orchestrator — ZPCOS の司令塔。"""

import uuid
from datetime import datetime, timezone

from app.orchestrator.models import Orchestration, OrchestrationPlan
from app.orchestrator.planner import generate_plan
from app.orchestrator.integrator import execute_plan
from app.orchestrator.cost_guard import estimate_cost
from app.orchestrator.quality_sla import QualityMode, should_run_judge
from app.skills.framework import SkillRegistry

# メモリ内ストレージ（MVPではSQLite不要）
_orchestrations: dict[str, Orchestration] = {}


async def start_orchestration(
    user_input: str,
    skill_registry: SkillRegistry,
    quality_mode: str = "balanced",
) -> Orchestration:
    """オーケストレーションを開始。Plan を生成して返す（実行はしない）。"""
    orch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    available_skills = [s.name for s in skill_registry.list_skills()]
    plan = await generate_plan(user_input, available_skills, quality_mode)

    cost = await estimate_cost(plan, quality_mode)

    orch = Orchestration(
        id=orch_id,
        user_input=user_input,
        plan=plan,
        status="awaiting_approval",
        cost_estimate=cost.model_dump(),
        created_at=now,
    )
    _orchestrations[orch_id] = orch

    # Webhook: orchestration.started
    from app.webhook.dispatcher import dispatch_event
    from app.webhook.models import WebhookEvent
    await dispatch_event(WebhookEvent.ORCHESTRATION_STARTED, {
        "orchestration_id": orch_id,
        "user_input": user_input,
        "quality_mode": quality_mode,
        "step_count": len(plan.steps),
    })

    return orch


async def approve_and_execute(
    orch_id: str,
    skill_registry: SkillRegistry,
) -> Orchestration:
    """Plan を承認して実行。"""
    orch = _orchestrations.get(orch_id)
    if not orch:
        raise ValueError(f"Orchestration {orch_id} not found")
    if not orch.plan:
        raise ValueError("No plan to execute")

    orch.status = "executing"
    try:
        results = await execute_plan(orch.plan, skill_registry)
        orch.results = results
        orch.status = "completed"

        from app.webhook.dispatcher import dispatch_event
        from app.webhook.models import WebhookEvent
        await dispatch_event(WebhookEvent.ORCHESTRATION_COMPLETED, {
            "orchestration_id": orch_id,
            "results": results,
        })
    except Exception as e:
        orch.status = "failed"
        orch.results = {"error": str(e)}

        from app.webhook.dispatcher import dispatch_event
        from app.webhook.models import WebhookEvent
        await dispatch_event(WebhookEvent.ORCHESTRATION_FAILED, {
            "orchestration_id": orch_id,
            "error": str(e),
        })

    return orch


def get_orchestration(orch_id: str) -> Orchestration | None:
    return _orchestrations.get(orch_id)
