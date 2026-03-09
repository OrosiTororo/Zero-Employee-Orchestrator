"""承認ゲート — 危険操作の自動検出と承認要求.

Zero-Employee Orchestrator.md §12.3, §36.6 に基づき、以下の操作は
人間承認を必須とする:
- 外部送信 / 投稿 / 公開
- 削除 / 課金
- Git push / release
- 重要ファイルの上書き
- 権限変更
- API キー関連処理
- 外部認証情報の更新反映
- 新規 Agent / Team の作成
- 予算上限変更
- Policy Pack の変更
- 自律実行範囲の拡張
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ApprovalCategory(str, Enum):
    """承認が必要な操作のカテゴリ."""

    EXTERNAL_SEND = "external_send"
    PUBLISH = "publish"
    DELETE = "delete"
    BILLING = "billing"
    GIT_PUSH = "git_push"
    FILE_OVERWRITE = "file_overwrite"
    PERMISSION_CHANGE = "permission_change"
    CREDENTIAL_CHANGE = "credential_change"
    AGENT_CREATE = "agent_create"
    BUDGET_CHANGE = "budget_change"
    POLICY_CHANGE = "policy_change"
    AUTONOMY_EXPAND = "autonomy_expand"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalGateResult:
    """承認ゲート判定結果."""

    requires_approval: bool
    category: ApprovalCategory | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    reason: str = ""
    suggested_approver: str | None = None  # user_id or role


# 操作名 → カテゴリ + リスクレベル のマッピング
_DANGEROUS_OPERATIONS: dict[str, tuple[ApprovalCategory, RiskLevel]] = {
    "send_email": (ApprovalCategory.EXTERNAL_SEND, RiskLevel.HIGH),
    "post_sns": (ApprovalCategory.PUBLISH, RiskLevel.HIGH),
    "publish_content": (ApprovalCategory.PUBLISH, RiskLevel.HIGH),
    "delete_file": (ApprovalCategory.DELETE, RiskLevel.MEDIUM),
    "delete_data": (ApprovalCategory.DELETE, RiskLevel.HIGH),
    "charge_payment": (ApprovalCategory.BILLING, RiskLevel.CRITICAL),
    "git_push": (ApprovalCategory.GIT_PUSH, RiskLevel.MEDIUM),
    "git_release": (ApprovalCategory.GIT_PUSH, RiskLevel.HIGH),
    "overwrite_config": (ApprovalCategory.FILE_OVERWRITE, RiskLevel.HIGH),
    "change_permission": (ApprovalCategory.PERMISSION_CHANGE, RiskLevel.CRITICAL),
    "update_api_key": (ApprovalCategory.CREDENTIAL_CHANGE, RiskLevel.CRITICAL),
    "rotate_secret": (ApprovalCategory.CREDENTIAL_CHANGE, RiskLevel.HIGH),
    "create_agent": (ApprovalCategory.AGENT_CREATE, RiskLevel.MEDIUM),
    "create_team": (ApprovalCategory.AGENT_CREATE, RiskLevel.MEDIUM),
    "change_budget": (ApprovalCategory.BUDGET_CHANGE, RiskLevel.HIGH),
    "change_policy": (ApprovalCategory.POLICY_CHANGE, RiskLevel.HIGH),
    "expand_autonomy": (ApprovalCategory.AUTONOMY_EXPAND, RiskLevel.CRITICAL),
}


def check_approval_required(operation: str) -> ApprovalGateResult:
    """操作が人間承認を必要とするか判定する."""
    entry = _DANGEROUS_OPERATIONS.get(operation)
    if entry is None:
        return ApprovalGateResult(requires_approval=False)

    category, risk_level = entry
    return ApprovalGateResult(
        requires_approval=True,
        category=category,
        risk_level=risk_level,
        reason=f"操作 '{operation}' は {category.value} カテゴリに該当し、人間承認が必要です",
    )


def check_operations_batch(operations: list[str]) -> list[ApprovalGateResult]:
    """複数操作の承認要否を一括判定する."""
    return [check_approval_required(op) for op in operations]


def get_highest_risk(results: list[ApprovalGateResult]) -> RiskLevel:
    """複数の判定結果から最も高いリスクレベルを返す."""
    risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    max_idx = 0
    for r in results:
        if r.requires_approval:
            idx = risk_order.index(r.risk_level)
            max_idx = max(max_idx, idx)
    return risk_order[max_idx]
