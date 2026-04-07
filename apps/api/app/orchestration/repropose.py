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
        description="Quality criteria not met",
    ),
    "scope_mismatch": ReworkReason(
        category="scope",
        description="Requirements mismatch",
    ),
    "cost_exceeded": ReworkReason(
        category="cost",
        description="Budget exceeded",
    ),
    "policy_violation": ReworkReason(
        category="policy",
        description="Policy violation detected",
    ),
    "execution_error": ReworkReason(
        category="error",
        description="Runtime error occurred",
    ),
    "timeout": ReworkReason(
        category="timeout",
        description="Execution time limit exceeded",
    ),
    "skill_gap": ReworkReason(
        category="error",
        description="Required Skill is missing",
    ),
    "dependency_broken": ReworkReason(
        category="error",
        description="Dependency chain broken",
    ),
    "model_incompatible": ReworkReason(
        category="error",
        description="Incompatibility due to model characteristics",
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

    Analyzes the failure reasons and generates a structured reproposal with
    plan diffs and confidence scoring based on failure severity.
    """
    reasons_text = "; ".join(r.description for r in rework_reasons)

    # Compute plan diff based on failure analysis
    added = []
    removed = []
    modified = []

    for reason in rework_reasons:
        if reason.category == "quality":
            modified.append("Add verification step for quality criteria")
        elif reason.category == "cost":
            modified.append("Switch to lower-cost model or reduce scope")
            removed.append("Optional elaboration steps")
        elif reason.category == "timeout":
            modified.append("Split long tasks into smaller subtasks")
        elif reason.category == "error":
            added.append("Add error handling / retry wrapper")
            modified.append("Simplify failing step")

    diff = PlanDiff(
        added_tasks=added,
        removed_tasks=removed,
        modified_tasks=modified,
        reason=reasons_text,
    )

    # Confidence based on severity — critical failures have lower confidence
    severity_weights = {"low": 0.9, "medium": 0.75, "high": 0.5, "critical": 0.3}
    confidence = min(
        severity_weights.get(r.severity, 0.5) for r in rework_reasons
    ) if rework_reasons else 0.5

    return ReproposalResult(
        original_plan_id=original_plan.get("plan_id", original_plan.get("id", "")),
        new_plan_summary=f"Revised plan: {reasons_text}. "
        f"Changes: +{len(added)} added, -{len(removed)} removed, ~{len(modified)} modified.",
        diff=diff,
        rework_reasons=rework_reasons,
        requires_approval=any(r.severity in ("high", "critical") for r in rework_reasons),
        confidence_score=round(confidence, 2),
    )
