"""Generic prerequisite change monitoring API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PrerequisiteSourceCreate(BaseModel):
    """Request to register a monitoring target."""

    name: str = Field(..., description="Name of the monitoring target")
    url: str = Field(..., description="URL of the monitoring target")
    category: str = Field(default="custom", description="Category")
    description: str = Field(default="", description="Description")
    check_interval_hours: int = Field(default=24, ge=1, le=720)
    keywords: list[str] = Field(default_factory=list, description="Monitoring keywords")
    linked_ticket_ids: list[str] = Field(default_factory=list)


class PrerequisiteSourceUpdate(BaseModel):
    """Request to update a monitoring target."""

    name: str | None = None
    url: str | None = None
    category: str | None = None
    description: str | None = None
    check_interval_hours: int | None = None
    keywords: list[str] | None = None
    status: str | None = None
    linked_ticket_ids: list[str] | None = None


class PrerequisiteSourceResponse(BaseModel):
    """Response for a monitoring target."""

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
    """Response for a detected change."""

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
    """Manual check request."""

    source_id: str = Field(..., description="Source ID to check")
    content: str = Field(..., description="Retrieved content")


class PrerequisiteSummaryResponse(BaseModel):
    """Summary response."""

    total_sources: int
    active_sources: int
    total_changes_detected: int
    unacknowledged_changes: int
    critical_changes: int
    high_changes: int
    sources_by_category: dict[str, int]
