"""前提変化の汎用監視 API スキーマ."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PrerequisiteSourceCreate(BaseModel):
    """監視対象の登録リクエスト."""

    name: str = Field(..., description="監視対象の名前")
    url: str = Field(..., description="監視対象のURL")
    category: str = Field(default="custom", description="カテゴリ")
    description: str = Field(default="", description="説明")
    check_interval_hours: int = Field(default=24, ge=1, le=720)
    keywords: list[str] = Field(default_factory=list, description="監視キーワード")
    linked_ticket_ids: list[str] = Field(default_factory=list)


class PrerequisiteSourceUpdate(BaseModel):
    """監視対象の更新リクエスト."""

    name: str | None = None
    url: str | None = None
    category: str | None = None
    description: str | None = None
    check_interval_hours: int | None = None
    keywords: list[str] | None = None
    status: str | None = None
    linked_ticket_ids: list[str] | None = None


class PrerequisiteSourceResponse(BaseModel):
    """監視対象のレスポンス."""

    id: str
    company_id: str
    name: str
    url: str
    category: str
    description: str
    check_interval_hours: int
    keywords: list[str]
    status: str
    last_checked: str | None
    last_change_detected: str | None
    created_at: str
    linked_ticket_ids: list[str]


class PrerequisiteChangeResponse(BaseModel):
    """検出された変更のレスポンス."""

    id: str
    source_id: str
    source_name: str
    category: str
    title: str
    summary: str
    diff_snippet: str
    impact: str
    detected_at: str
    acknowledged: bool
    affected_ticket_ids: list[str]
    matched_keywords: list[str]


class PrerequisiteCheckRequest(BaseModel):
    """手動チェックリクエスト."""

    source_id: str = Field(..., description="チェック対象のソースID")
    content: str = Field(..., description="取得したコンテンツ")


class PrerequisiteSummaryResponse(BaseModel):
    """サマリーレスポンス."""

    total_sources: int
    active_sources: int
    total_changes_detected: int
    unacknowledged_changes: int
    critical_changes: int
    high_changes: int
    sources_by_category: dict[str, int]
