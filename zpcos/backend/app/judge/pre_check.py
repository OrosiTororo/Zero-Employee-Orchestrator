"""Two-stage Detection — Stage 1: 安価なルールベースチェック。
Stage 1 が PASS した場合のみ Stage 2（Cross-Model Judge）を実行。
"""

from pydantic import BaseModel
from app.policy.policy_pack import check_policy


class PreCheckResult(BaseModel):
    passed: bool
    issues: list[str] = []
    stage: int = 1


async def pre_check(text: str, context: str = "") -> PreCheckResult:
    """Stage 1: 安価なチェック。"""
    issues = []

    if not text or len(text.strip()) < 10:
        issues.append("入力が短すぎます（最低10文字）")

    violations = await check_policy(text)
    for v in violations:
        if v.rule.severity == "error":
            issues.append(f"ポリシー違反: {v.rule.suggestion}")

    estimated_tokens = len(text) * 2
    if estimated_tokens > 100000:
        issues.append(f"テキストが長すぎます（推定{estimated_tokens}トークン）。分割を検討してください。")

    return PreCheckResult(passed=len(issues) == 0, issues=issues, stage=1)
