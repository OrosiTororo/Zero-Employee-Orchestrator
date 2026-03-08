"""Failure Taxonomy tests."""

import pytest

from app.orchestration.failure_taxonomy import (
    FailureCategory,
    FailureRecord,
    FailureSeverity,
    FailureTaxonomy,
)


class TestFailureRecord:
    def test_recovery_success_rate_zero(self):
        record = FailureRecord(
            category=FailureCategory.LLM_ERROR,
            subcategory="timeout",
            severity=FailureSeverity.LOW,
            description="LLM timeout",
            prevention_strategy="Increase timeout",
        )
        assert record.recovery_success_rate == 0.0

    def test_recovery_success_rate_calculated(self):
        record = FailureRecord(
            category=FailureCategory.LLM_ERROR,
            subcategory="timeout",
            severity=FailureSeverity.LOW,
            description="LLM timeout",
            prevention_strategy="Increase timeout",
            occurrence_count=10,
            recovery_success_count=7,
        )
        assert record.recovery_success_rate == 0.7

    def test_auto_timestamp(self):
        record = FailureRecord(
            category=FailureCategory.LLM_ERROR,
            subcategory="timeout",
            severity=FailureSeverity.LOW,
            description="test",
            prevention_strategy="test",
        )
        assert record.last_occurred != ""


class TestFailureTaxonomy:
    def test_record_new_failure(self):
        ft = FailureTaxonomy()
        record = ft.record_failure(
            category=FailureCategory.LLM_ERROR,
            subcategory="timeout",
            severity=FailureSeverity.MEDIUM,
            description="LLM API timeout",
            prevention_strategy="Increase timeout",
        )
        assert record.occurrence_count == 1
        assert len(ft.records) == 1

    def test_record_duplicate_increments_count(self):
        ft = FailureTaxonomy()
        ft.record_failure(
            category="llm_error",
            subcategory="timeout",
            severity="medium",
            description="LLM API timeout",
            prevention_strategy="Increase timeout",
        )
        record = ft.record_failure(
            category="llm_error",
            subcategory="timeout",
            severity="medium",
            description="LLM API timeout again",
            prevention_strategy="Increase timeout more",
        )
        assert record.occurrence_count == 2
        assert len(ft.records) == 1

    def test_record_recovery(self):
        ft = FailureTaxonomy()
        ft.record_failure(
            category=FailureCategory.TOOL_ERROR,
            subcategory="api_fail",
            severity=FailureSeverity.LOW,
            description="API call failed",
            prevention_strategy="Retry",
        )
        result = ft.record_recovery(FailureCategory.TOOL_ERROR, "api_fail")
        assert result is not None
        assert result.recovery_success_count == 1

    def test_record_recovery_nonexistent(self):
        ft = FailureTaxonomy()
        result = ft.record_recovery("llm_error", "nonexistent")
        assert result is None

    def test_get_frequent_failures(self):
        ft = FailureTaxonomy()
        ft.record_failure("llm_error", "timeout", "low", "desc", "prev")
        ft.record_failure("llm_error", "timeout", "low", "desc", "prev")
        ft.record_failure("tool_error", "api", "low", "desc", "prev")

        frequent = ft.get_frequent_failures(min_count=2)
        assert len(frequent) == 1
        assert frequent[0].subcategory == "timeout"

    def test_get_by_severity(self):
        ft = FailureTaxonomy()
        ft.record_failure("llm_error", "a", "low", "desc", "prev")
        ft.record_failure("tool_error", "b", "high", "desc", "prev")
        ft.record_failure("system_error", "c", "high", "desc", "prev")

        high = ft.get_by_severity(FailureSeverity.HIGH)
        assert len(high) == 2

    def test_get_prevention_strategies(self):
        ft = FailureTaxonomy()
        ft.record_failure("llm_error", "timeout", "low", "desc", "retry with backoff")
        strategies = ft.get_prevention_strategies(FailureCategory.LLM_ERROR)
        assert len(strategies) == 1
        assert strategies[0]["prevention"] == "retry with backoff"

    def test_task_id_tracking(self):
        ft = FailureTaxonomy()
        record = ft.record_failure(
            "llm_error", "timeout", "low", "desc", "prev", task_id="task-1"
        )
        assert "task-1" in record.related_task_ids
