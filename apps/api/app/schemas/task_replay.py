"""Task replay and comparison API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReplayConfigSchema(BaseModel):
    """Replay configuration."""

    model_id: str = Field(..., description="Model ID to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    quality_mode: str = Field(default="standard")
    custom_params: dict[str, Any] = Field(default_factory=dict)


class ReplayJobCreateRequest(BaseModel):
    """Replay job creation request."""

    task_id: str = Field(..., description="Original task ID")
    task_description: str = Field(..., description="Task description")
    original_output: str = Field(..., description="Original output")
    configs: list[ReplayConfigSchema] = Field(..., min_length=1, max_length=10)


class ReplayExecutionRecordRequest(BaseModel):
    """Request to record replay execution results."""

    config_index: int = Field(..., ge=0)
    output: str = Field(...)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    token_count: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    output_metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ComparisonResultResponse(BaseModel):
    """Comparison result response."""

    dimension: str
    winner_execution_id: str
    winner_model: str
    scores: dict[str, float]
    details: str


class ReplayExecutionResponse(BaseModel):
    """Replay execution response."""

    id: str
    model_id: str
    quality_score: float
    execution_time_ms: float
    token_count: int
    estimated_cost: float
    error: str | None


class ReplayJobResponse(BaseModel):
    """Replay job response."""

    id: str
    original_task_id: str
    status: str
    executions: list[ReplayExecutionResponse]
    comparisons: list[ComparisonResultResponse]
    created_at: str
    completed_at: str | None
    summary: str
