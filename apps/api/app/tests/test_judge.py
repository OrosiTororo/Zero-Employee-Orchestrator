"""Direct tests for the Judge layer (RuleBasedJudge + CrossModelJudge)."""

from __future__ import annotations

from app.orchestration.judge import (
    CrossModelJudge,
    JudgeVerdict,
    PolicyPackJudge,
    RuleBasedJudge,
)


class TestRuleBasedJudge:
    def test_no_rules_passes(self):
        judge = RuleBasedJudge()
        result = judge.evaluate({"content": "anything"})
        assert result.verdict == JudgeVerdict.PASS
        assert result.score == 1.0

    def test_error_rule_failure_produces_fail_verdict(self):
        judge = RuleBasedJudge()
        judge.add_rule(
            "non_empty_content",
            lambda out, ctx: bool(out.get("content")),
            severity="error",
        )
        result = judge.evaluate({"content": ""})
        assert result.verdict == JudgeVerdict.FAIL
        assert "non_empty_content" in result.policy_violations
        assert result.requires_human_review is True

    def test_warning_rule_failure_produces_warn_verdict(self):
        judge = RuleBasedJudge()
        judge.add_rule(
            "minimum_length",
            lambda out, ctx: len(out.get("content", "")) >= 10,
            severity="warning",
        )
        result = judge.evaluate({"content": "short"})
        assert result.verdict == JudgeVerdict.WARN
        assert result.policy_violations == []

    def test_rule_exception_is_caught_as_warning(self):
        judge = RuleBasedJudge()
        judge.add_rule(
            "boom",
            lambda out, ctx: out["nonexistent_key"],
            severity="error",
        )
        # Rule raises KeyError → recorded as warning instead of crashing.
        result = judge.evaluate({"content": "x"})
        assert result.verdict == JudgeVerdict.WARN


class TestPolicyPackJudge:
    def test_dangerous_operations_are_flagged(self):
        judge = PolicyPackJudge()
        flagged = judge.check_dangerous_operations(["external_send", "read"])
        assert "external_send" in flagged
        assert "read" not in flagged

    def test_credential_exposure_detection(self):
        judge = PolicyPackJudge()
        assert judge.check_credential_exposure("api_key=sk_live_abcdef1234567890") is True
        assert judge.check_credential_exposure("this is a safe description") is False


class TestCrossModelJudge:
    def test_single_output_needs_more_models(self):
        judge = CrossModelJudge()
        result = judge.evaluate([{"answer": "42"}])
        assert result.verdict == JudgeVerdict.WARN
        assert "Cross-model verification requires" in result.reasons[0]

    def test_perfect_agreement_passes(self):
        judge = CrossModelJudge()
        result = judge.evaluate(
            [{"answer": "42", "confidence": "high"}, {"answer": "42", "confidence": "high"}]
        )
        assert result.verdict == JudgeVerdict.PASS
        assert result.score >= 0.9

    def test_numeric_tolerance_accepts_close_values(self):
        judge = CrossModelJudge(numeric_tolerance=0.05)
        # 100 vs 103 is within 5% tolerance
        assert judge._values_match("100", "103") is True
        # 100 vs 200 is not
        assert judge._values_match("100", "200") is False

    def test_empty_outputs_warn(self):
        judge = CrossModelJudge()
        result = judge.evaluate([{}, {}])
        assert result.verdict == JudgeVerdict.WARN
