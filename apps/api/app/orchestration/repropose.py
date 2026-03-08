"""Re-Propose Layer (Layer 6) - Rework, Plan Diff, partial re-execution.

When a task or plan is rejected/failed, this layer generates alternative
proposals, computes diffs, and manages partial re-execution.
"""

from dataclasses import dataclass, field


@dataclass
class ReworkReason:
    category: str  # "quality" | "scope" | "cost" | "policy" | "error" | "timeout"
    description: str
    severity: str = "medium"  # low | medium | high | critical


@dataclass
class PlanDiff:
    added_tasks: list[str] = field(default_factory=list)
    removed_tasks: list[str] = field(default_factory=list)
    modified_tasks: list[str] = field(default_factory=list)
    cost_change_usd: float = 0.0
    time_change_minutes: int = 0
    reason: str = ""


@dataclass
class ReproposalResult:
    original_plan_id: str
    new_plan_summary: str
    diff: PlanDiff
    rework_reasons: list[ReworkReason]
    requires_approval: bool = True
    confidence_score: float = 0.0


# Rework reason classification (Failure Taxonomy)
FAILURE_CATEGORIES = {
    "quality_insufficient": ReworkReason(
        category="quality",
        description="品質基準を満たしていない",
    ),
    "scope_mismatch": ReworkReason(
        category="scope",
        description="要件との不一致",
    ),
    "cost_exceeded": ReworkReason(
        category="cost",
        description="予算を超過した",
    ),
    "policy_violation": ReworkReason(
        category="policy",
        description="ポリシー違反が検出された",
    ),
    "execution_error": ReworkReason(
        category="error",
        description="実行時エラーが発生した",
    ),
    "timeout": ReworkReason(
        category="timeout",
        description="実行時間の上限を超えた",
    ),
    "skill_gap": ReworkReason(
        category="error",
        description="必要なSkillが不足している",
    ),
    "dependency_broken": ReworkReason(
        category="error",
        description="依存関係が崩れた",
    ),
    "model_incompatible": ReworkReason(
        category="error",
        description="モデル特性による不適合",
    ),
}


def classify_failure(error_code: str | None, error_message: str | None) -> ReworkReason:
    """Classify a failure into the Failure Taxonomy."""
    if error_code and error_code in FAILURE_CATEGORIES:
        return FAILURE_CATEGORIES[error_code]

    # Heuristic classification based on error message
    msg = (error_message or "").lower()
    if "budget" in msg or "cost" in msg:
        return FAILURE_CATEGORIES["cost_exceeded"]
    if "policy" in msg or "approval" in msg:
        return FAILURE_CATEGORIES["policy_violation"]
    if "timeout" in msg or "deadline" in msg:
        return FAILURE_CATEGORIES["timeout"]
    if "skill" in msg:
        return FAILURE_CATEGORIES["skill_gap"]
    if "quality" in msg:
        return FAILURE_CATEGORIES["quality_insufficient"]

    return FAILURE_CATEGORIES["execution_error"]


def generate_reproposal(
    original_plan: dict,
    rework_reasons: list[ReworkReason],
    constraints: dict | None = None,
) -> ReproposalResult:
    """Generate a re-proposal based on failure analysis.

    In production, this would call the LLM to generate an alternative plan.
    Currently returns a structured template for the orchestration engine.
    """
    diff = PlanDiff(
        reason="; ".join(r.description for r in rework_reasons),
    )

    return ReproposalResult(
        original_plan_id=original_plan.get("id", ""),
        new_plan_summary=f"修正計画: {diff.reason}に対応",
        diff=diff,
        rework_reasons=rework_reasons,
        requires_approval=any(r.severity in ("high", "critical") for r in rework_reasons),
        confidence_score=0.7,
    )
