"""User judgment review report API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JudgmentRecordCreate(BaseModel):
    """Request to create a judgment record."""

    action: str = Field(..., description="Judgment action: approved/rejected/deferred")
    category: str = Field(default="other", description="Judgment category")
    target_type: str = Field(default="", description="Target type")
    target_id: str = Field(default="", description="Target ID")
    risk_level: str = Field(default="low", description="Risk level")
    reason: str = Field(default="", description="Judgment reason")
    response_time_seconds: float | None = Field(default=None)


class CategoryInsightResponse(BaseModel):
    """Per-category insight response."""

    category: str
    total: int
    approved: int
    rejected: int
    deferred: int
    approval_rate: float
    avg_response_time_seconds: float | None


class TrendPointResponse(BaseModel):
    """Trend data point."""

    period: str
    total: int
    approved: int
    rejected: int
    approval_rate: float


class JudgmentPatternResponse(BaseModel):
    """Detected pattern response."""

    pattern_type: str
    description: str
    confidence: float
    suggestion: str


class JudgmentReviewReportResponse(BaseModel):
    """Review report response."""

    id: str
    user_id: str
    company_id: str
    period_start: str
    period_end: str
    total_decisions: int
    approval_rate: float
    rejection_rate: float
    avg_response_time_seconds: float | None
    category_insights: list[CategoryInsightResponse]
    risk_distribution: dict[str, int]
    weekly_trend: list[TrendPointResponse]
    detected_patterns: list[JudgmentPatternResponse]
    generated_at: str
