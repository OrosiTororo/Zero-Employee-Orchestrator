"""Plan 品質検証 API スキーマ."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlanTaskForVerification(BaseModel):
    """検証用のタスク."""

    task_id: str
    title: str
    description: str = ""
    depends_on: list[str] = Field(default_factory=list)
    estimated_hours: float | None = None
    estimated_cost: float | None = None


class SpecForVerification(BaseModel):
    """検証用の Spec."""

    spec_id: str
    objective: str = ""
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    risk_notes: str = ""


class PlanForVerification(BaseModel):
    """検証用の Plan."""

    plan_id: str
    spec_id: str
    tasks: list[PlanTaskForVerification] = Field(default_factory=list)


class PlanQualityVerifyRequest(BaseModel):
    """Plan 品質検証リクエスト."""

    spec: SpecForVerification
    plan: PlanForVerification


class CoverageItemResponse(BaseModel):
    """カバレッジ項目のレスポンス."""

    source_type: str
    source_text: str
    status: str
    matched_task_ids: list[str]
    matched_task_titles: list[str]
    similarity_score: float


class DuplicatePairResponse(BaseModel):
    """重複ペアのレスポンス."""

    task_a_id: str
    task_a_title: str
    task_b_id: str
    task_b_title: str
    similarity: float


class QualityIssueResponse(BaseModel):
    """品質問題のレスポンス."""

    id: str
    type: str
    severity: str
    description: str
    affected_items: list[str]
    suggestion: str


class PlanQualityReportResponse(BaseModel):
    """Plan 品質検証レポートのレスポンス."""

    id: str
    plan_id: str
    spec_id: str
    quality_level: str
    overall_score: float
    objective_coverage: CoverageItemResponse | None
    constraint_coverage: list[CoverageItemResponse]
    acceptance_coverage: list[CoverageItemResponse]
    duplicate_tasks: list[DuplicatePairResponse]
    issues: list[QualityIssueResponse]
    total_tasks: int
    covered_objectives: int
    covered_constraints: int
    covered_acceptance: int
    verified_at: str
