"""Data models for the Self-Improvement plugin.

Extracted from ``self_improvement_service.py`` in v0.1.8 so the main service
module can focus on the six skill implementations (analyzer, improver,
judge-tuner, failure-to-skill, A/B test, auto-test-generator) without
carrying ~180 lines of dataclass / enum definitions inline.

All public names are re-exported from ``app.services.self_improvement_service``
so existing imports like::

    from app.services.self_improvement_service import AnalysisFinding

continue to work without modification.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class AnalysisCategory(str, Enum):
    """Skill analysis category."""

    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    SECURITY = "security"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"


class ImprovementPriority(str, Enum):
    """Improvement proposal priority."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalysisFinding:
    """Individual item in analysis results."""

    category: AnalysisCategory
    priority: ImprovementPriority
    title: str
    description: str
    suggestion: str
    line_range: tuple[int, int] | None = None


@dataclass
class SkillAnalysisResult:
    """Skill analysis result."""

    skill_id: str
    skill_slug: str
    overall_score: float  # 0.0 - 1.0
    findings: list[AnalysisFinding]
    summary: str
    analyzed_at: str = ""

    def __post_init__(self) -> None:
        if not self.analyzed_at:
            self.analyzed_at = datetime.now(UTC).isoformat()


@dataclass
class SkillImprovementProposal:
    """Skill improvement proposal."""

    original_skill_id: str
    original_version: str
    proposed_version: str
    original_code: str
    improved_code: str
    changes_summary: list[str]
    expected_improvements: list[str]
    requires_approval: bool = True
    applied: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


@dataclass
class JudgeTuningRule:
    """Judge auto-tuning rule."""

    rule_name: str
    rule_type: str  # "pattern_match" | "threshold" | "category_filter"
    condition: dict[str, Any]
    action: str  # "warn" | "fail" | "pass"
    confidence: float  # 0.0 - 1.0
    source_patterns: int  # Number of patterns used as evidence
    description: str


@dataclass
class JudgeTuningResult:
    """Judge tuning result."""

    company_id: str
    proposed_rules: list[JudgeTuningRule]
    analyzed_patterns: int
    approval_rate: float
    rejection_rate: float
    summary: str
    tuned_at: str = ""

    def __post_init__(self) -> None:
        if not self.tuned_at:
            self.tuned_at = datetime.now(UTC).isoformat()


@dataclass
class FailureToSkillProposal:
    """Skill proposal generated from failure patterns."""

    failure_category: str
    failure_subcategory: str
    occurrence_count: int
    proposed_skill_slug: str
    proposed_skill_name: str
    proposed_skill_description: str
    proposed_code: str
    prevention_strategy: str
    confidence: float


@dataclass
class ABTestConfig:
    """A/B test configuration."""

    test_id: str
    skill_a_id: str
    skill_b_id: str
    test_input: dict[str, Any]
    iterations: int = 3
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.test_id:
            self.test_id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


@dataclass
class ABTestResult:
    """A/B test result."""

    test_id: str
    skill_a_id: str
    skill_b_id: str
    skill_a_scores: list[float]
    skill_b_scores: list[float]
    skill_a_avg_time_ms: float
    skill_b_avg_time_ms: float
    winner: str  # skill_a_id | skill_b_id | "tie"
    winner_reason: str
    details: list[dict[str, Any]]
    completed_at: str = ""

    def __post_init__(self) -> None:
        if not self.completed_at:
            self.completed_at = datetime.now(UTC).isoformat()


@dataclass
class GeneratedTestCase:
    """Auto-generated test case."""

    test_name: str
    test_type: str  # "normal" | "edge" | "error"
    input_data: dict[str, Any]
    expected_behavior: str
    test_code: str


@dataclass
class AutoTestResult:
    """Auto test generation result."""

    skill_id: str
    skill_slug: str
    test_cases: list[GeneratedTestCase]
    total_tests: int
    normal_tests: int
    edge_tests: int
    error_tests: int
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(UTC).isoformat()


__all__ = [
    "ABTestConfig",
    "ABTestResult",
    "AnalysisCategory",
    "AnalysisFinding",
    "AutoTestResult",
    "FailureToSkillProposal",
    "GeneratedTestCase",
    "ImprovementPriority",
    "JudgeTuningResult",
    "JudgeTuningRule",
    "SkillAnalysisResult",
    "SkillImprovementProposal",
]
