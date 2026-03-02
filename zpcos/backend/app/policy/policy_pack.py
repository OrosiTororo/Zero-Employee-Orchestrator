"""Policy Pack — コンプライアンスチェック。
禁止表現・誇大表現・差別表現などのポリシーを提案段階で検出。
"""

from pydantic import BaseModel


class PolicyRule(BaseModel):
    category: str  # forbidden_expression | exaggeration | discrimination | legal_risk
    pattern: str
    severity: str  # error | warning | info
    suggestion: str


class PolicyViolation(BaseModel):
    rule: PolicyRule
    matched_text: str
    position: int = 0


DEFAULT_POLICIES: list[dict] = [
    {"category": "exaggeration", "pattern": "絶対", "severity": "warning",
     "suggestion": "「高い確率で」等の表現に置き換えを検討"},
    {"category": "exaggeration", "pattern": "100%", "severity": "warning",
     "suggestion": "具体的な根拠がない場合は数値の修正を検討"},
    {"category": "forbidden_expression", "pattern": "必ず儲かる", "severity": "error",
     "suggestion": "投資・収益の断定的表現は法的リスクがあります"},
    {"category": "discrimination", "pattern": "〇〇人は", "severity": "error",
     "suggestion": "民族・国籍に基づく一般化は避けてください"},
]


async def check_policy(text: str, custom_rules: list[dict] | None = None) -> list[PolicyViolation]:
    """テキストに対してポリシーチェックを実行。"""
    rules = [PolicyRule(**r) for r in (custom_rules or DEFAULT_POLICIES)]
    violations = []
    for rule in rules:
        if rule.pattern in text:
            pos = text.index(rule.pattern)
            violations.append(PolicyViolation(rule=rule, matched_text=rule.pattern, position=pos))
    return violations
