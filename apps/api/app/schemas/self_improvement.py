"""AI Self-Improvement API schemas -- Level 2: Seeds of self-improvement.

DTOs for Skill analysis, improvement, Judge tuning, failure learning, A/B testing, and auto test generation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Skill Analyzer
# ---------------------------------------------------------------------------


class SkillAnalysisRequest(BaseModel):
    """Skill analysis request."""

    skill_id: str = Field(..., description="ID of the skill to analyze")


class AnalysisFindingResponse(BaseModel):
    """Individual analysis finding."""

    category: str
    priority: str
    title: str
    description: str
    suggestion: str


class SkillAnalysisResponse(BaseModel):
    """Skill analysis result."""

    skill_id: str
    skill_slug: str
    overall_score: float
    findings: list[AnalysisFindingResponse]
    summary: str
    analyzed_at: str


# ---------------------------------------------------------------------------
# 2. Skill Improver
# ---------------------------------------------------------------------------


class SkillImproveRequest(BaseModel):
    """Skill improvement request."""

    skill_id: str = Field(..., description="ID of the skill to improve")


class SkillImprovementResponse(BaseModel):
    """Skill improvement proposal."""

    original_skill_id: str
    original_version: str
    proposed_version: str
    original_code: str
    improved_code: str
    changes_summary: list[str]
    expected_improvements: list[str]
    requires_approval: bool
    created_at: str


class SkillImprovementApplyRequest(BaseModel):
    """Skill improvement apply request (after approval)."""

    skill_id: str
    improved_code: str
    proposed_version: str


# ---------------------------------------------------------------------------
# 3. Judge Tuner
# ---------------------------------------------------------------------------


class JudgeTuneRequest(BaseModel):
    """Judge tuning request."""

    company_id: str = Field(..., description="Target company ID")


class JudgeTuningRuleResponse(BaseModel):
    """Judge tuning rule."""

    rule_name: str
    rule_type: str
    condition: dict[str, Any]
    action: str
    confidence: float
    source_patterns: int
    description: str


class JudgeTuningResponse(BaseModel):
    """Judge tuning result."""

    company_id: str
    proposed_rules: list[JudgeTuningRuleResponse]
    analyzed_patterns: int
    approval_rate: float
    rejection_rate: float
    summary: str
    tuned_at: str


class JudgeTuningApplyRequest(BaseModel):
    """Judge tuning apply request (after approval)."""

    company_id: str
    rule_names: list[str] = Field(
        default_factory=list,
        description="List of rule names to apply (empty means all rules)",
    )


class JudgeTuningApplyResponse(BaseModel):
    """Judge tuning apply result."""

    applied_count: int
    message: str


# ---------------------------------------------------------------------------
# 4. Failure-to-Skill
# ---------------------------------------------------------------------------


class FailureToSkillRequest(BaseModel):
    """Request to generate a Skill from failure patterns."""

    company_id: str
    min_occurrences: int = Field(default=2, ge=1, description="Minimum number of occurrences")


class FailureToSkillProposalResponse(BaseModel):
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


class FailureToSkillResponse(BaseModel):
    """List of Skill proposals generated from failure patterns."""

    proposals: list[FailureToSkillProposalResponse]
    total_failures_analyzed: int


class FailureToSkillRegisterRequest(BaseModel):
    """Failure prevention Skill registration request (after approval)."""

    company_id: str
    slug: str
    name: str
    description: str
    code: str


# ---------------------------------------------------------------------------
# 5. Skill A/B Test
# ---------------------------------------------------------------------------


class SkillABTestRequest(BaseModel):
    """Skill A/B test request."""

    skill_a_id: str = Field(..., description="ID of Skill A to compare")
    skill_b_id: str = Field(..., description="ID of Skill B to compare")
    test_input: dict[str, Any] = Field(default_factory=dict, description="Test input data")
    iterations: int = Field(default=3, ge=1, le=10, description="Number of iterations")


class SkillABTestResponse(BaseModel):
    """Skill A/B test result."""

    test_id: str
    skill_a_id: str
    skill_b_id: str
    skill_a_scores: list[float]
    skill_b_scores: list[float]
    skill_a_avg_time_ms: float
    skill_b_avg_time_ms: float
    winner: str
    winner_reason: str
    details: list[dict[str, Any]]
    completed_at: str


# ---------------------------------------------------------------------------
# 6. Auto Test Generator
# ---------------------------------------------------------------------------


class AutoTestRequest(BaseModel):
    """Auto test generation request."""

    skill_id: str = Field(..., description="ID of the skill to generate tests for")


class GeneratedTestCaseResponse(BaseModel):
    """Auto-generated test case."""

    test_name: str
    test_type: str
    input_data: dict[str, Any]
    expected_behavior: str
    test_code: str


class AutoTestResponse(BaseModel):
    """Auto test generation result."""

    skill_id: str
    skill_slug: str
    test_cases: list[GeneratedTestCaseResponse]
    total_tests: int
    normal_tests: int
    edge_tests: int
    error_tests: int
    generated_at: str


# ---------------------------------------------------------------------------
# Self-Improvement Dashboard
# ---------------------------------------------------------------------------


class SelfImprovementStatusResponse(BaseModel):
    """Self-Improvement overall status."""

    plugin_version: str
    skills_analyzed: int
    improvements_proposed: int
    improvements_applied: int
    judge_rules_proposed: int
    judge_rules_applied: int
    failure_skills_proposed: int
    ab_tests_completed: int
    tests_generated: int
