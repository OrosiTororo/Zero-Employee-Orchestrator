"""Cost Guard — コスト見積りと予算管理。"""

from app.orchestrator.models import OrchestrationPlan, CostEstimate

# モデルごとの概算コスト（1000トークンあたり USD）
MODEL_COSTS = {
    "fast": 0.0001,
    "think": 0.005,
    "quality": 0.003,
    "free": 0.0,
    "reason": 0.002,
    "value": 0.001,
}

# 品質モードごとの追加乗数
QUALITY_MULTIPLIERS = {
    "fastest": 1.0,
    "balanced": 1.5,
    "high_quality": 3.0,
}


async def estimate_cost(
    plan: OrchestrationPlan,
    quality_mode: str = "balanced",
    budget_limit_usd: float | None = None,
) -> CostEstimate:
    """Plan のコストを見積もる。"""
    total_calls = len(plan.steps)
    # 各ステップで平均 2000 トークン使用と仮定
    tokens_per_step = 2000
    total_tokens = total_calls * tokens_per_step

    multiplier = QUALITY_MULTIPLIERS.get(quality_mode, 1.5)

    # Judge のコスト追加（balanced以上）
    judge_calls = total_calls if quality_mode != "fastest" else 0
    judge_tokens = judge_calls * 3000  # Judge は 3 モデル × 1000 トークン

    model_breakdown = {}
    base_cost = 0.0
    for step in plan.steps:
        model = "quality"  # デフォルト
        cost = MODEL_COSTS.get(model, 0.003) * tokens_per_step / 1000
        base_cost += cost
        model_breakdown[step.skill_name] = {
            "model": model,
            "tokens": tokens_per_step,
            "cost_usd": round(cost, 4),
        }

    judge_cost = judge_tokens * MODEL_COSTS.get("fast", 0.0001) / 1000
    total_cost = (base_cost + judge_cost) * multiplier
    time_per_step = 5  # 秒

    budget_exceeded = False
    if budget_limit_usd is not None and total_cost > budget_limit_usd:
        budget_exceeded = True

    return CostEstimate(
        total_api_calls=total_calls + judge_calls,
        estimated_tokens=total_tokens + judge_tokens,
        estimated_cost_usd=round(total_cost, 4),
        estimated_time_seconds=int(total_calls * time_per_step * multiplier),
        model_breakdown=model_breakdown,
        budget_exceeded=budget_exceeded,
    )
