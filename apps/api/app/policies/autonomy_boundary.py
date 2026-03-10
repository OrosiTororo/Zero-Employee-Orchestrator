"""自律実行の境界 — 自律実行可能な操作と承認必須操作の判定.

Zero-Employee Orchestrator.md §25 に基づき、AI の自律実行範囲を定義する。

自律実行可能:
- 調査、分析、下書き作成、情報整理

承認必須:
- 公開、投稿、課金、削除、権限変更、外部送信
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AutonomyLevel(str, Enum):
    """Agent の自律レベル."""

    OBSERVE = "observe"  # 観察のみ
    ASSIST = "assist"  # 補助（提案のみ）
    SEMI_AUTO = "semi_auto"  # 半自動（承認後実行）
    AUTONOMOUS = "autonomous"  # 自律（安全範囲内で自動実行）


# 自律実行が許可される操作タイプ
AUTONOMOUS_OPERATIONS: set[str] = {
    "research",
    "analyze",
    "draft",
    "summarize",
    "organize",
    "translate",
    "calculate",
    "compare",
    "search",
    "read_file",
    "format",
    "classify",
    "extract",
}

# 承認が必須な操作タイプ
APPROVAL_REQUIRED_OPERATIONS: set[str] = {
    "publish",
    "post",
    "send",
    "delete",
    "charge",
    "change_permission",
    "change_credential",
    "git_push",
    "git_release",
    "overwrite_important_file",
    "external_api_write",
    "create_agent",
    "modify_policy",
}


@dataclass
class AutonomyCheckResult:
    """自律実行可否の判定結果."""

    allowed: bool
    requires_approval: bool
    reason: str
    operation: str
    autonomy_level: AutonomyLevel


def check_autonomy(
    operation: str,
    agent_autonomy_level: AutonomyLevel = AutonomyLevel.SEMI_AUTO,
) -> AutonomyCheckResult:
    """操作が自律実行可能かどうかを判定する."""
    if operation in APPROVAL_REQUIRED_OPERATIONS:
        return AutonomyCheckResult(
            allowed=False,
            requires_approval=True,
            reason=f"操作 '{operation}' は承認必須です",
            operation=operation,
            autonomy_level=agent_autonomy_level,
        )

    if operation in AUTONOMOUS_OPERATIONS:
        if agent_autonomy_level in (AutonomyLevel.AUTONOMOUS, AutonomyLevel.SEMI_AUTO):
            return AutonomyCheckResult(
                allowed=True,
                requires_approval=False,
                reason=f"操作 '{operation}' は自律実行可能です",
                operation=operation,
                autonomy_level=agent_autonomy_level,
            )

    # デフォルト: 半自動以上なら承認要求、観察/補助なら拒否
    if agent_autonomy_level == AutonomyLevel.OBSERVE:
        return AutonomyCheckResult(
            allowed=False,
            requires_approval=False,
            reason="観察モードでは実行できません",
            operation=operation,
            autonomy_level=agent_autonomy_level,
        )

    return AutonomyCheckResult(
        allowed=False,
        requires_approval=True,
        reason=f"操作 '{operation}' は不明な操作のため、承認が必要です",
        operation=operation,
        autonomy_level=agent_autonomy_level,
    )
