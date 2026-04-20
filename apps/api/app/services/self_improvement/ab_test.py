"""Skill A/B Test — performance comparison between Skill versions."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.services.self_improvement_models import ABTestResult

logger = logging.getLogger(__name__)


async def run_skill_ab_test(
    db: AsyncSession,
    skill_a_id: uuid.UUID,
    skill_b_id: uuid.UUID,
    test_input: dict[str, Any],
    iterations: int = 3,
) -> ABTestResult:
    """Execute two Skills with the same input and compare quality and speed."""
    result_a = await db.execute(select(Skill).where(Skill.id == skill_a_id))
    skill_a = result_a.scalar_one_or_none()
    result_b = await db.execute(select(Skill).where(Skill.id == skill_b_id))
    skill_b = result_b.scalar_one_or_none()

    if skill_a is None:
        raise ValueError(f"Skill A not found: {skill_a_id}")
    if skill_b is None:
        raise ValueError(f"Skill B not found: {skill_b_id}")

    test_id = uuid.uuid4().hex[:12]
    a_scores: list[float] = []
    b_scores: list[float] = []
    a_times: list[float] = []
    b_times: list[float] = []
    details: list[dict[str, Any]] = []

    for i in range(iterations):
        # Execute Skill A
        a_result, a_time = await _execute_skill_for_test(skill_a, test_input)
        a_score = _evaluate_output_quality(a_result)
        a_scores.append(a_score)
        a_times.append(a_time)

        # Execute Skill B
        b_result, b_time = await _execute_skill_for_test(skill_b, test_input)
        b_score = _evaluate_output_quality(b_result)
        b_scores.append(b_score)
        b_times.append(b_time)

        details.append(
            {
                "iteration": i + 1,
                "skill_a": {
                    "score": a_score,
                    "time_ms": a_time,
                    "output_preview": str(a_result.get("output", ""))[:200],
                },
                "skill_b": {
                    "score": b_score,
                    "time_ms": b_time,
                    "output_preview": str(b_result.get("output", ""))[:200],
                },
            }
        )

    avg_a_score = sum(a_scores) / len(a_scores) if a_scores else 0
    avg_b_score = sum(b_scores) / len(b_scores) if b_scores else 0
    avg_a_time = sum(a_times) / len(a_times) if a_times else 0
    avg_b_time = sum(b_times) / len(b_times) if b_times else 0

    # Winner determination: prioritize quality, use speed as tiebreaker
    score_diff = avg_a_score - avg_b_score
    if abs(score_diff) > 0.05:
        winner = str(skill_a_id) if score_diff > 0 else str(skill_b_id)
        winner_reason = f"Quality score difference: {abs(score_diff):.2f} (A: {avg_a_score:.2f}, B: {avg_b_score:.2f})"
    elif abs(avg_a_time - avg_b_time) > 100:  # More than 100ms difference
        winner = str(skill_a_id) if avg_a_time < avg_b_time else str(skill_b_id)
        winner_reason = (
            f"Quality equivalent, speed difference: {abs(avg_a_time - avg_b_time):.0f}ms "
            f"(A: {avg_a_time:.0f}ms, B: {avg_b_time:.0f}ms)"
        )
    else:
        winner = "tie"
        winner_reason = f"Quality and speed both equivalent (A: {avg_a_score:.2f}/{avg_a_time:.0f}ms, B: {avg_b_score:.2f}/{avg_b_time:.0f}ms)"

    return ABTestResult(
        test_id=test_id,
        skill_a_id=str(skill_a_id),
        skill_b_id=str(skill_b_id),
        skill_a_scores=a_scores,
        skill_b_scores=b_scores,
        skill_a_avg_time_ms=avg_a_time,
        skill_b_avg_time_ms=avg_b_time,
        winner=winner,
        winner_reason=winner_reason,
        details=details,
    )


async def _execute_skill_for_test(
    skill: Skill,
    test_input: dict[str, Any],
) -> tuple[dict[str, Any], float]:
    """Execute a Skill for testing and return the result and execution time."""
    code = skill.generated_code or ""
    if not code.strip():
        return {"status": "error", "output": "No code"}, 0.0

    context = {
        "input": test_input.get("input", ""),
        "local_context": test_input.get("local_context", {}),
        "provider": None,
        "settings": test_input.get("settings", {}),
    }

    start = time.monotonic()
    try:
        # Sandbox execution: extract execute function via compile + exec and run safely
        namespace: dict[str, Any] = {}
        compiled = compile(code, f"<skill:{skill.slug}>", "exec")
        exec(compiled, namespace)  # noqa: S102 — sandbox execution

        execute_fn = namespace.get("execute")
        if execute_fn is None:
            return {"status": "error", "output": "execute function not defined"}, 0.0

        import asyncio

        if asyncio.iscoroutinefunction(execute_fn):
            result = await execute_fn(context)
        else:
            result = execute_fn(context)

        elapsed = (time.monotonic() - start) * 1000
        return result if isinstance(result, dict) else {
            "status": "success",
            "output": str(result),
        }, elapsed

    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return {"status": "error", "output": f"Execution error: {exc}"}, elapsed


def _evaluate_output_quality(output: dict[str, Any]) -> float:
    """Score the quality of the output."""
    score = 0.0

    # Status check
    status = output.get("status", "")
    if status == "success":
        score += 0.4
    elif status == "warning":
        score += 0.2

    # Output content richness
    content = str(output.get("output", ""))
    if content and content != "No code":
        score += 0.3
        if len(content) > 50:
            score += 0.1

    # Presence of artifacts
    artifacts = output.get("artifacts", [])
    if artifacts:
        score += 0.1

    # No errors
    if "error" not in content.lower() and "エラー" not in content:
        score += 0.1

    return min(1.0, score)
