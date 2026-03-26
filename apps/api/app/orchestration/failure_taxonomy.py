"""Failure Taxonomy — Failure classification + learning.

Classifies failures by category and subcategory, managing prevention strategies
and recovery success rates. Works with Experience Memory for failure pattern
learning and prevention.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class FailureCategory(str, Enum):
    """Failure category (top-level classification)."""

    LLM_ERROR = "llm_error"  # LLM provider failure
    TOOL_ERROR = "tool_error"  # Tool execution failure
    VALIDATION_ERROR = "validation_error"  # Input/output validation failure
    BUDGET_ERROR = "budget_error"  # Budget exceeded
    TIMEOUT_ERROR = "timeout_error"  # Timeout
    PERMISSION_ERROR = "permission_error"  # Insufficient permissions
    DEPENDENCY_ERROR = "dependency_error"  # Dependent task failure
    HUMAN_REJECTION = "human_rejection"  # Rejected by human
    SYSTEM_ERROR = "system_error"  # Internal system error


class FailureSeverity(str, Enum):
    """Failure severity."""

    LOW = "low"  # Minor (recoverable by automatic retry)
    MEDIUM = "medium"  # Moderate (recoverable by alternative means)
    HIGH = "high"  # Serious (requires human intervention)
    CRITICAL = "critical"  # Fatal (immediate escalation required)


@dataclass
class FailureRecord:
    """Failure record."""

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
            self.last_occurred = datetime.now(UTC).isoformat()


class FailureTaxonomy:
    """Failure taxonomy management.

    Accumulates failure patterns and tracks the effectiveness of prevention strategies.
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
                record.last_occurred = datetime.now(UTC).isoformat()
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
            results.append(
                {
                    "category": record.category.value,
                    "subcategory": record.subcategory,
                    "prevention": record.prevention_strategy,
                    "recovery_rate": f"{record.recovery_success_rate:.0%}",
                }
            )
        return results


# グローバルインスタンス
failure_taxonomy = FailureTaxonomy()
