"""Cost Guard — 実行前コスト見積もり＋予算チェック.

タスク実行前にコストを見積もり、予算ポリシーと照合して
実行可否を判定する。予算超過時はタスクをブロックし、
警告閾値到達時は通知を返す。
"""

from dataclasses import dataclass
from enum import Enum


class CostDecision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


# Default cost estimates per model family (USD per 1K tokens).
# Loaded dynamically from model_catalog.json via ModelRegistry when available.
# This inline fallback is used only when the registry is unavailable.
_FALLBACK_COST_TABLE: dict[str, dict[str, float]] = {
    "gpt-5.4": {"input": 0.005, "output": 0.015},
    "gpt-5-mini": {"input": 0.00015, "output": 0.0006},
    "claude-opus-4-6": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5-20251001": {"input": 0.001, "output": 0.005},
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-flash-lite": {"input": 0.00005, "output": 0.0002},
}


def _load_cost_table() -> dict[str, dict[str, float]]:
    """ModelRegistry からコストテーブルを読み込む."""
    try:
        from app.providers.model_registry import get_model_registry
        registry = get_model_registry()
        table = registry.get_cost_table()
        if table:
            return table
    except Exception:
        pass
    return _FALLBACK_COST_TABLE


DEFAULT_COST_TABLE: dict[str, dict[str, float]] = _load_cost_table()


@dataclass
class CostEstimate:
    """タスク実行の推定コスト."""

    model_name: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    breakdown: dict[str, float]


@dataclass
class CostGuardResult:
    """コストガード判定結果."""

    decision: CostDecision
    estimate: CostEstimate | None
    budget_limit_usd: float
    current_usage_usd: float
    projected_usage_usd: float
    usage_pct: float
    message: str


def estimate_cost(
    model_name: str,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 500,
    cost_table: dict[str, dict[str, float]] | None = None,
) -> CostEstimate:
    """モデルとトークン数からコストを見積もる."""
    table = cost_table or DEFAULT_COST_TABLE

    # Find matching model in cost table (longest prefix match)
    rates = {"input": 0.002, "output": 0.002}  # fallback
    model_lower = model_name.lower()
    best_match_len = 0
    for key, value in table.items():
        key_lower = key.lower()
        if model_lower.startswith(key_lower) and len(key_lower) > best_match_len:
            rates = value
            best_match_len = len(key_lower)

    input_cost = (estimated_input_tokens / 1000) * rates["input"]
    output_cost = (estimated_output_tokens / 1000) * rates["output"]
    total = input_cost + output_cost

    return CostEstimate(
        model_name=model_name,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        estimated_cost_usd=round(total, 6),
        breakdown={"input_cost": round(input_cost, 6), "output_cost": round(output_cost, 6)},
    )


def check_budget(
    estimated_cost_usd: float,
    budget_limit_usd: float,
    current_usage_usd: float,
    warn_threshold_pct: float = 80.0,
    stop_threshold_pct: float = 100.0,
) -> CostGuardResult:
    """予算チェックを実行し、実行可否を判定する."""
    if budget_limit_usd <= 0:
        return CostGuardResult(
            decision=CostDecision.ALLOW,
            estimate=None,
            budget_limit_usd=budget_limit_usd,
            current_usage_usd=current_usage_usd,
            projected_usage_usd=current_usage_usd + estimated_cost_usd,
            usage_pct=0.0,
            message="予算制限なし",
        )

    projected = current_usage_usd + estimated_cost_usd
    usage_pct = (projected / budget_limit_usd) * 100

    if usage_pct >= stop_threshold_pct:
        decision = CostDecision.BLOCK
        message = f"予算上限超過: {usage_pct:.1f}% (上限 ${budget_limit_usd:.2f})"
    elif usage_pct >= warn_threshold_pct:
        decision = CostDecision.WARN
        message = f"予算警告: {usage_pct:.1f}% (上限 ${budget_limit_usd:.2f})"
    else:
        decision = CostDecision.ALLOW
        message = f"予算内: {usage_pct:.1f}% (残り ${budget_limit_usd - current_usage_usd:.2f})"

    return CostGuardResult(
        decision=decision,
        estimate=None,
        budget_limit_usd=budget_limit_usd,
        current_usage_usd=current_usage_usd,
        projected_usage_usd=projected,
        usage_pct=round(usage_pct, 2),
        message=message,
    )


def pre_execution_check(
    model_name: str,
    budget_limit_usd: float,
    current_usage_usd: float,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 500,
    warn_threshold_pct: float = 80.0,
    stop_threshold_pct: float = 100.0,
) -> CostGuardResult:
    """タスク実行前の統合チェック: コスト見積もり + 予算チェック."""
    estimate = estimate_cost(model_name, estimated_input_tokens, estimated_output_tokens)
    result = check_budget(
        estimated_cost_usd=estimate.estimated_cost_usd,
        budget_limit_usd=budget_limit_usd,
        current_usage_usd=current_usage_usd,
        warn_threshold_pct=warn_threshold_pct,
        stop_threshold_pct=stop_threshold_pct,
    )
    result.estimate = estimate
    return result
