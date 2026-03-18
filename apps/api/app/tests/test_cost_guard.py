"""Cost Guard tests."""

from app.orchestration.cost_guard import (
    CostDecision,
    check_budget,
    estimate_cost,
    pre_execution_check,
)


class TestEstimateCost:
    def test_known_model(self):
        est = estimate_cost("gpt-5.4", estimated_input_tokens=1000, estimated_output_tokens=500)
        assert est.model_name == "gpt-5.4"
        assert est.estimated_input_tokens == 1000
        assert est.estimated_output_tokens == 500
        assert est.estimated_cost_usd > 0
        assert "input_cost" in est.breakdown
        assert "output_cost" in est.breakdown

    def test_unknown_model_uses_fallback(self):
        est = estimate_cost("unknown-model-xyz")
        assert est.estimated_cost_usd > 0

    def test_zero_tokens(self):
        est = estimate_cost("gpt-5.4", estimated_input_tokens=0, estimated_output_tokens=0)
        assert est.estimated_cost_usd == 0.0

    def test_gpt54_is_more_expensive_than_mini(self):
        gpt54 = estimate_cost("gpt-5.4", 1000, 1000)
        mini = estimate_cost("gpt-5-mini", 1000, 1000)
        assert gpt54.estimated_cost_usd > mini.estimated_cost_usd


class TestCheckBudget:
    def test_allow_within_budget(self):
        result = check_budget(
            estimated_cost_usd=1.0,
            budget_limit_usd=100.0,
            current_usage_usd=10.0,
        )
        assert result.decision == CostDecision.ALLOW
        assert result.projected_usage_usd == 11.0

    def test_warn_near_budget(self):
        result = check_budget(
            estimated_cost_usd=5.0,
            budget_limit_usd=100.0,
            current_usage_usd=80.0,
        )
        assert result.decision == CostDecision.WARN

    def test_block_over_budget(self):
        result = check_budget(
            estimated_cost_usd=10.0,
            budget_limit_usd=100.0,
            current_usage_usd=95.0,
        )
        assert result.decision == CostDecision.BLOCK

    def test_no_budget_limit(self):
        result = check_budget(
            estimated_cost_usd=100.0,
            budget_limit_usd=0.0,
            current_usage_usd=0.0,
        )
        assert result.decision == CostDecision.ALLOW

    def test_custom_thresholds(self):
        result = check_budget(
            estimated_cost_usd=5.0,
            budget_limit_usd=100.0,
            current_usage_usd=55.0,
            warn_threshold_pct=50.0,
        )
        assert result.decision == CostDecision.WARN


class TestPreExecutionCheck:
    def test_integration(self):
        result = pre_execution_check(
            model_name="gpt-5-mini",
            budget_limit_usd=10.0,
            current_usage_usd=0.0,
        )
        assert result.decision == CostDecision.ALLOW
        assert result.estimate is not None
        assert result.estimate.model_name == "gpt-5-mini"

    def test_block_when_budget_exceeded(self):
        result = pre_execution_check(
            model_name="gpt-5.4",
            budget_limit_usd=0.01,
            current_usage_usd=0.009,
            estimated_input_tokens=10000,
            estimated_output_tokens=5000,
        )
        assert result.decision == CostDecision.BLOCK
