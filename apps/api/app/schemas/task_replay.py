"""タスクリプレイ・比較 API スキーマ."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReplayConfigSchema(BaseModel):
    """リプレイ設定."""

    model_id: str = Field(..., description="使用するモデルID")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    quality_mode: str = Field(default="standard")
    custom_params: dict[str, Any] = Field(default_factory=dict)


class ReplayJobCreateRequest(BaseModel):
    """リプレイジョブ作成リクエスト."""

    task_id: str = Field(..., description="元タスクのID")
    task_description: str = Field(..., description="タスクの説明")
    original_output: str = Field(..., description="元の出力")
    configs: list[ReplayConfigSchema] = Field(..., min_length=1, max_length=10)


class ReplayExecutionRecordRequest(BaseModel):
    """リプレイ実行結果の記録リクエスト."""

    config_index: int = Field(..., ge=0)
    output: str = Field(...)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    token_count: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    output_metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ComparisonResultResponse(BaseModel):
    """比較結果のレスポンス."""

    dimension: str
    winner_execution_id: str
    winner_model: str
    scores: dict[str, float]
    details: str


class ReplayExecutionResponse(BaseModel):
    """リプレイ実行のレスポンス."""

    id: str
    model_id: str
    quality_score: float
    execution_time_ms: float
    token_count: int
    estimated_cost: float
    error: str | None


class ReplayJobResponse(BaseModel):
    """リプレイジョブのレスポンス."""

    id: str
    original_task_id: str
    status: str
    executions: list[ReplayExecutionResponse]
    comparisons: list[ComparisonResultResponse]
    created_at: str
    completed_at: str | None
    summary: str
