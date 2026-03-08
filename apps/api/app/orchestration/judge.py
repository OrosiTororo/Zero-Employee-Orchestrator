"""Judge Layer (Layer 5) - Two-stage Detection + Cross-Model Verification.

Provides quality assurance, policy compliance checking, and output verification.
"""

from dataclasses import dataclass
from enum import Enum


class JudgeVerdict(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


@dataclass
class JudgeResult:
    verdict: JudgeVerdict
    score: float  # 0.0 - 1.0
    reasons: list[str]
    suggestions: list[str]
    policy_violations: list[str]
    requires_human_review: bool = False


class RuleBasedJudge:
    """Stage 1: Fast rule-based checks."""

    def __init__(self) -> None:
        self.rules: list[dict] = []

    def add_rule(self, name: str, check_fn, severity: str = "error") -> None:
        self.rules.append({"name": name, "check": check_fn, "severity": severity})

    def evaluate(self, output: dict, context: dict | None = None) -> JudgeResult:
        violations = []
        warnings = []
        score = 1.0

        for rule in self.rules:
            try:
                passed = rule["check"](output, context or {})
                if not passed:
                    if rule["severity"] == "error":
                        violations.append(rule["name"])
                        score -= 0.2
                    else:
                        warnings.append(rule["name"])
                        score -= 0.05
            except Exception:
                warnings.append(f"Rule check failed: {rule['name']}")

        score = max(0.0, score)

        if violations:
            verdict = JudgeVerdict.FAIL
        elif warnings:
            verdict = JudgeVerdict.WARN
        else:
            verdict = JudgeVerdict.PASS

        return JudgeResult(
            verdict=verdict,
            score=score,
            reasons=violations + warnings,
            suggestions=[],
            policy_violations=violations,
            requires_human_review=len(violations) > 0,
        )


class PolicyPackJudge:
    """Evaluates output against Policy Pack rules (compliance control)."""

    def __init__(self, policy_rules: dict | None = None) -> None:
        self.rules = policy_rules or {}

    def check_dangerous_operations(self, operations: list[str]) -> list[str]:
        """Check if any operations require forced approval."""
        dangerous = {
            "external_send", "publish", "post", "delete",
            "charge", "git_push", "git_release",
            "file_overwrite_important", "permission_change",
            "api_key_update", "credential_update",
        }
        return [op for op in operations if op in dangerous]

    def check_credential_exposure(self, content: str) -> bool:
        """Check if content might contain credential values."""
        suspicious_patterns = [
            "sk-", "Bearer ", "api_key=", "password=",
            "secret=", "token=", "AKIA",
        ]
        return any(p in content for p in suspicious_patterns)

    def evaluate(self, output: dict, operations: list[str] | None = None) -> JudgeResult:
        violations = []
        suggestions = []

        # Check dangerous operations
        if operations:
            dangerous = self.check_dangerous_operations(operations)
            if dangerous:
                violations.extend([
                    f"承認必須操作が含まれています: {op}" for op in dangerous
                ])

        # Check credential exposure
        content = str(output)
        if self.check_credential_exposure(content):
            violations.append("認証情報が平文で含まれている可能性があります")
            suggestions.append("機密情報をマスキングまたは参照ID化してください")

        score = 1.0 - (len(violations) * 0.3)
        score = max(0.0, score)

        return JudgeResult(
            verdict=JudgeVerdict.FAIL if violations else JudgeVerdict.PASS,
            score=score,
            reasons=violations,
            suggestions=suggestions,
            policy_violations=violations,
            requires_human_review=len(violations) > 0,
        )


class CrossModelJudge:
    """Cross-Model Verification: 複数モデルの出力を比較して品質を検証.

    HIGH / CRITICAL 品質モードで使用し、異なる LLM の出力の
    一致度を評価して信頼性を担保する。
    """

    def __init__(self, agreement_threshold: float = 0.7) -> None:
        self.agreement_threshold = agreement_threshold

    def evaluate(self, outputs: list[dict], context: dict | None = None) -> JudgeResult:
        """複数モデル出力の一致度を評価する.

        Args:
            outputs: 各モデルの出力辞書リスト
            context: 評価コンテキスト
        """
        if len(outputs) < 2:
            return JudgeResult(
                verdict=JudgeVerdict.WARN,
                score=0.5,
                reasons=["クロスモデル検証には2つ以上の出力が必要です"],
                suggestions=["追加モデルでの検証を推奨します"],
                policy_violations=[],
                requires_human_review=False,
            )

        # Compare key overlap across outputs
        all_keys: set[str] = set()
        for out in outputs:
            all_keys.update(out.keys())

        if not all_keys:
            return JudgeResult(
                verdict=JudgeVerdict.WARN,
                score=0.5,
                reasons=["出力が空です"],
                suggestions=[],
                policy_violations=[],
            )

        # Structural agreement: fraction of keys present in all outputs
        common_keys = all_keys.copy()
        for out in outputs:
            common_keys &= set(out.keys())
        structural_score = len(common_keys) / len(all_keys) if all_keys else 0.0

        # Value agreement: fraction of common keys with matching values
        matching_values = 0
        for key in common_keys:
            values = [str(out.get(key, "")) for out in outputs]
            if len(set(values)) == 1:
                matching_values += 1
        value_score = matching_values / len(common_keys) if common_keys else 0.0

        overall_score = (structural_score + value_score) / 2
        reasons = []
        suggestions = []

        if structural_score < self.agreement_threshold:
            reasons.append(
                f"構造一致度が低い: {structural_score:.0%} "
                f"(閾値 {self.agreement_threshold:.0%})"
            )
        if value_score < self.agreement_threshold:
            reasons.append(
                f"値一致度が低い: {value_score:.0%} "
                f"(閾値 {self.agreement_threshold:.0%})"
            )

        if overall_score < self.agreement_threshold:
            verdict = JudgeVerdict.NEEDS_REVIEW
            suggestions.append("人間レビューによる最終判断を推奨します")
        elif reasons:
            verdict = JudgeVerdict.WARN
        else:
            verdict = JudgeVerdict.PASS

        return JudgeResult(
            verdict=verdict,
            score=round(overall_score, 3),
            reasons=reasons,
            suggestions=suggestions,
            policy_violations=[],
            requires_human_review=verdict == JudgeVerdict.NEEDS_REVIEW,
        )


# Default judge instances
rule_judge = RuleBasedJudge()
policy_judge = PolicyPackJudge()
cross_model_judge = CrossModelJudge()


def judge_output(
    output: dict,
    operations: list[str] | None = None,
    context: dict | None = None,
) -> JudgeResult:
    """Two-stage judge: rule-based first, then policy check."""
    # Stage 1
    rule_result = rule_judge.evaluate(output, context)
    if rule_result.verdict == JudgeVerdict.FAIL:
        return rule_result

    # Stage 2
    policy_result = policy_judge.evaluate(output, operations)
    if policy_result.verdict == JudgeVerdict.FAIL:
        return policy_result

    # Combine
    combined_score = (rule_result.score + policy_result.score) / 2
    combined_reasons = rule_result.reasons + policy_result.reasons
    combined_suggestions = rule_result.suggestions + policy_result.suggestions

    return JudgeResult(
        verdict=JudgeVerdict.PASS if not combined_reasons else JudgeVerdict.WARN,
        score=combined_score,
        reasons=combined_reasons,
        suggestions=combined_suggestions,
        policy_violations=rule_result.policy_violations + policy_result.policy_violations,
        requires_human_review=rule_result.requires_human_review or policy_result.requires_human_review,
    )
