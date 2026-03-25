"""Spec 間矛盾検出 API スキーマ."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpecForContradiction(BaseModel):
    """矛盾検出に使用する Spec データ."""

    spec_id: str
    ticket_id: str = ""
    ticket_title: str = ""
    objective: str = ""
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    risk_notes: str = ""
    priority: str = "medium"
    estimated_budget: float | None = None
    deadline: str | None = None


class ContradictionCheckRequest(BaseModel):
    """矛盾検出リクエスト."""

    specs: list[SpecForContradiction] = Field(..., min_length=2)
    project_id: str | None = None


class ContradictionDetailResponse(BaseModel):
    """矛盾詳細のレスポンス."""

    id: str
    type: str
    severity: str
    spec_a_id: str
    spec_a_ticket: str
    spec_b_id: str
    spec_b_ticket: str
    field_a: str
    value_a: str
    field_b: str
    value_b: str
    description: str
    suggestion: str


class SpecContradictionReportResponse(BaseModel):
    """矛盾検出レポートのレスポンス."""

    id: str
    company_id: str
    project_id: str | None
    analyzed_specs: int
    contradictions: list[ContradictionDetailResponse]
    critical_count: int
    error_count: int
    warning_count: int
    info_count: int
    overall_consistency_score: float
    analyzed_at: str
