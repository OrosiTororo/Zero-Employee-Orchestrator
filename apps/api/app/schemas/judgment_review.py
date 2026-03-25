"""ユーザー判断振り返りレポート API スキーマ."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JudgmentRecordCreate(BaseModel):
    """判断記録の作成リクエスト."""

    action: str = Field(..., description="判断アクション: approved/rejected/deferred")
    category: str = Field(default="other", description="判断カテゴリ")
    target_type: str = Field(default="", description="対象タイプ")
    target_id: str = Field(default="", description="対象ID")
    risk_level: str = Field(default="low", description="リスクレベル")
    reason: str = Field(default="", description="判断理由")
    response_time_seconds: float | None = Field(default=None)


class CategoryInsightResponse(BaseModel):
    """カテゴリ別洞察のレスポンス."""

    category: str
    total: int
    approved: int
    rejected: int
    deferred: int
    approval_rate: float
    avg_response_time_seconds: float | None


class TrendPointResponse(BaseModel):
    """トレンドデータポイント."""

    period: str
    total: int
    approved: int
    rejected: int
    approval_rate: float


class JudgmentPatternResponse(BaseModel):
    """検出パターンのレスポンス."""

    pattern_type: str
    description: str
    confidence: float
    suggestion: str


class JudgmentReviewReportResponse(BaseModel):
    """振り返りレポートのレスポンス."""

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
