"""Integrator — DAGの実行と結果の統合。"""

import asyncio
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep
from app.skills.framework import SkillRegistry


async def execute_plan(
    plan: OrchestrationPlan,
    skill_registry: SkillRegistry,
) -> dict:
    """Plan を実行し、全ステップの結果を統合して返す。"""
    results = {}
    completed = set()

    # DAG のトポロジカル順序で実行
    remaining = list(plan.steps)
    while remaining:
        runnable = [
            step for step in remaining
            if all(dep in completed for dep in step.depends_on)
        ]
        if not runnable:
            # デッドロック防止
            break

        # 並列実行可能なステップを同時実行
        tasks = []
        for step in runnable:
            tasks.append(_execute_step(step, skill_registry, results))

        step_results = await asyncio.gather(*tasks, return_exceptions=True)

        for step, result in zip(runnable, step_results):
            if isinstance(result, Exception):
                step.status = "failed"
                step.output = {"error": str(result)}
            else:
                step.status = "completed"
                step.output = result
            results[step.step_id] = step.output
            completed.add(step.step_id)
            remaining.remove(step)

    return results


async def _execute_step(
    step: OrchestrationStep,
    skill_registry: SkillRegistry,
    previous_results: dict,
) -> dict:
    """1つのステップを実行。"""
    skill = skill_registry.get_skill(step.skill_name)
    if not skill:
        raise ValueError(f"Skill '{step.skill_name}' not found")

    # input_mapping で前のステップの出力を注入
    input_data = dict(step.input_mapping)
    for key, value in input_data.items():
        if isinstance(value, str) and value.startswith("$"):
            ref = value[1:]  # e.g. "$step_1.analysis"
            parts = ref.split(".", 1)
            if len(parts) == 2 and parts[0] in previous_results:
                prev = previous_results[parts[0]]
                if isinstance(prev, dict):
                    input_data[key] = prev.get(parts[1], value)

    step.status = "running"
    return await skill.execute(input_data)
