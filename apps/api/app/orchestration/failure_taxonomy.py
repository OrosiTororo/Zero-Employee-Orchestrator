"""Failure Taxonomy — 障害分類＋学習.

障害をカテゴリ・サブカテゴリで分類し、予防策や回復成功率を管理する。
Experience Memory と連携して障害パターンの学習と予防を行う。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class FailureCategory(str, Enum):
    """障害の大分類."""

    LLM_ERROR = "llm_error"              # LLM プロバイダ障害
    TOOL_ERROR = "tool_error"            # ツール実行障害
    VALIDATION_ERROR = "validation_error"  # 入出力検証障害
    BUDGET_ERROR = "budget_error"        # 予算超過
    TIMEOUT_ERROR = "timeout_error"      # タイムアウト
    PERMISSION_ERROR = "permission_error"  # 権限不足
    DEPENDENCY_ERROR = "dependency_error"  # 依存タスク障害
    HUMAN_REJECTION = "human_rejection"  # 人間による差し戻し
    SYSTEM_ERROR = "system_error"        # システム内部エラー


class FailureSeverity(str, Enum):
    """障害の重大度."""

    LOW = "low"          # 軽微 (自動リトライで回復可能)
    MEDIUM = "medium"    # 中程度 (代替手段で回復可能)
    HIGH = "high"        # 重大 (人間介入が必要)
    CRITICAL = "critical"  # 致命的 (即座にエスカレーション)


@dataclass
class FailureRecord:
    """障害の記録."""

    category: FailureCategory
    subcategory: str
    severity: FailureSeverity
    description: str
    prevention_strategy: str
    recovery_strategy: str = ""
    occurrence_count: int = 1
    recovery_success_count: int = 0
    last_occurred: str = ""
    related_task_ids: list[str] = field(default_factory=list)

    @property
    def recovery_success_rate(self) -> float:
        if self.occurrence_count == 0:
            return 0.0
        return self.recovery_success_count / self.occurrence_count

    def __post_init__(self) -> None:
        if not self.last_occurred:
            self.last_occurred = datetime.now(timezone.utc).isoformat()


class FailureTaxonomy:
    """障害分類体系の管理.

    障害パターンを蓄積し、予防策の有効性を追跡する。
    """

    def __init__(self) -> None:
        self.records: list[FailureRecord] = []

    def record_failure(
        self,
        category: FailureCategory | str,
        subcategory: str,
        severity: FailureSeverity | str,
        description: str,
        prevention_strategy: str,
        recovery_strategy: str = "",
        task_id: str | None = None,
    ) -> FailureRecord:
        """障害を記録する. 同一カテゴリ・サブカテゴリは更新."""
        if isinstance(category, str):
            category = FailureCategory(category)
        if isinstance(severity, str):
            severity = FailureSeverity(severity)

        # 既存レコード検索
        for record in self.records:
            if record.category == category and record.subcategory == subcategory:
                record.occurrence_count += 1
                record.last_occurred = datetime.now(timezone.utc).isoformat()
                if task_id:
                    record.related_task_ids.append(task_id)
                return record

        record = FailureRecord(
            category=category,
            subcategory=subcategory,
            severity=severity,
            description=description,
            prevention_strategy=prevention_strategy,
            recovery_strategy=recovery_strategy,
            related_task_ids=[task_id] if task_id else [],
        )
        self.records.append(record)
        return record

    def record_recovery(
        self,
        category: FailureCategory | str,
        subcategory: str,
    ) -> FailureRecord | None:
        """回復成功を記録する."""
        if isinstance(category, str):
            category = FailureCategory(category)
        for record in self.records:
            if record.category == category and record.subcategory == subcategory:
                record.recovery_success_count += 1
                return record
        return None

    def get_frequent_failures(self, min_count: int = 2) -> list[FailureRecord]:
        """頻発する障害を取得."""
        return [r for r in self.records if r.occurrence_count >= min_count]

    def get_by_severity(self, severity: FailureSeverity | str) -> list[FailureRecord]:
        """重大度別に障害を取得."""
        if isinstance(severity, str):
            severity = FailureSeverity(severity)
        return [r for r in self.records if r.severity == severity]

    def get_prevention_strategies(
        self,
        category: FailureCategory | str | None = None,
    ) -> list[dict[str, str]]:
        """予防策一覧を取得."""
        if isinstance(category, str):
            category = FailureCategory(category)
        results = []
        for record in self.records:
            if category and record.category != category:
                continue
            results.append({
                "category": record.category.value,
                "subcategory": record.subcategory,
                "prevention": record.prevention_strategy,
                "recovery_rate": f"{record.recovery_success_rate:.0%}",
            })
        return results


# グローバルインスタンス
failure_taxonomy = FailureTaxonomy()
