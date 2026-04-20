"""Tests for the Re-Propose layer (failure classification + reproposal)."""

from __future__ import annotations

from app.orchestration.repropose import (
    FAILURE_CATEGORIES,
    PlanDiff,
    ReworkReason,
    classify_failure,
    generate_reproposal,
)


class TestClassifyFailure:
    def test_known_error_code_wins(self):
        reason = classify_failure("skill_gap", "random message")
        assert reason is FAILURE_CATEGORIES["skill_gap"]

    def test_unknown_code_falls_back_to_heuristic(self):
        reason = classify_failure("unknown_code", "Budget exceeded for this ticket")
        assert reason.category == "cost"

    def test_heuristic_detects_timeout(self):
        reason = classify_failure(None, "Task hit the execution deadline")
        assert reason.category == "timeout"

    def test_policy_violation_heuristic(self):
        reason = classify_failure(None, "approval required: policy violation")
        assert reason.category == "policy"

    def test_default_is_execution_error(self):
        reason = classify_failure(None, "weird unexpected thing happened")
        assert reason is FAILURE_CATEGORIES["execution_error"]


class TestGenerateReproposal:
    def test_cost_reason_adds_cost_fixes(self):
        cost_reason = ReworkReason(
            category="cost", description="Budget exceeded", severity="medium"
        )
        result = generate_reproposal(
            {"plan_id": "p-1"}, [cost_reason]
        )
        assert result.original_plan_id == "p-1"
        assert any("lower-cost" in m for m in result.diff.modified_tasks)
        assert any("Optional" in r for r in result.diff.removed_tasks)

    def test_critical_severity_lowers_confidence_and_requires_approval(self):
        reason = ReworkReason(
            category="policy", description="policy broken", severity="critical"
        )
        result = generate_reproposal({"plan_id": "p-1"}, [reason])
        assert result.confidence_score <= 0.3
        assert result.requires_approval is True

    def test_low_severity_still_requires_approval_only_if_high_critical(self):
        reason = ReworkReason(
            category="error", description="minor error", severity="low"
        )
        result = generate_reproposal({"plan_id": "p-1"}, [reason])
        assert result.requires_approval is False

    def test_empty_reasons_yields_default_confidence(self):
        result = generate_reproposal({"plan_id": "p-1"}, [])
        assert result.confidence_score == 0.5
        assert result.diff == PlanDiff(reason="")
