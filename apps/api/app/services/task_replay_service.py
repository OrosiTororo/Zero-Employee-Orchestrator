"""Task execution replay and comparison service -- Task Replay & Comparison.

Re-executes the same task with different models or parameters and compares results.
An extension of A/B testing, enabling comparison at the task level rather than Skill level.

Use cases:
- Output quality comparison across models
- Parameter tuning effect verification
- Cost vs. quality tradeoff analysis
- Reproducibility verification of the same task
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from app.orchestration.judge import (
    CrossModelJudge,
    _jaccard_similarity,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class ReplayStatus(str, Enum):
    """Replay job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComparisonDimension(str, Enum):
    """Comparison dimension."""

    QUALITY = "quality"
    SPEED = "speed"
    COST = "cost"
    CONSISTENCY = "consistency"
    OVERALL = "overall"


@dataclass
class ReplayConfig:
    """Replay configuration."""

    model_id: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    quality_mode: str = "standard"
    custom_params: dict = field(default_factory=dict)


@dataclass
class ReplayExecution:
    """Replay execution result."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: ReplayConfig = field(default_factory=ReplayConfig)
    output: str = ""
    output_metadata: dict = field(default_factory=dict)
    quality_score: float = 0.0
    judge_result: dict | None = None
    execution_time_ms: float = 0.0
    token_count: int = 0
    estimated_cost: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


@dataclass
class ComparisonResult:
    """Comparison result."""

    dimension: ComparisonDimension = ComparisonDimension.OVERALL
    winner_execution_id: str = ""
    winner_model: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    details: str = ""


@dataclass
class ReplayJob:
    """Full replay job."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_task_id: str = ""
    original_task_description: str = ""
    original_output: str = ""
    configs: list[ReplayConfig] = field(default_factory=list)
    executions: list[ReplayExecution] = field(default_factory=list)
    comparisons: list[ComparisonResult] = field(default_factory=list)
    status: ReplayStatus = ReplayStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""
    completed_at: datetime | None = None
    summary: str = ""


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------


class TaskReplayService:
    """タスク実行のリプレイ・比較サービス.

    同一タスクを異なるモデル/パラメータで再実行し、結果を比較する。
    実際の LLM 呼び出しは外部から注入し、本サービスは比較ロジックに集中。
    """

    def __init__(self) -> None:
        self._jobs: dict[str, ReplayJob] = {}
        self._cross_judge = CrossModelJudge()

    def create_replay_job(
        self,
        task_id: str,
        task_description: str,
        original_output: str,
        configs: list[dict],
        created_by: str = "",
    ) -> ReplayJob:
        """Create a replay job."""
        replay_configs = []
        for cfg in configs:
            replay_configs.append(
                ReplayConfig(
                    model_id=cfg.get("model_id", ""),
                    temperature=cfg.get("temperature", 0.7),
                    max_tokens=cfg.get("max_tokens", 4096),
                    quality_mode=cfg.get("quality_mode", "standard"),
                    custom_params=cfg.get("custom_params", {}),
                )
            )

        job = ReplayJob(
            original_task_id=task_id,
            original_task_description=task_description,
            original_output=original_output,
            configs=replay_configs,
            created_by=created_by,
        )
        self._jobs[job.id] = job
        logger.info(
            "Created replay job %s for task %s with %d configs",
            job.id,
            task_id,
            len(replay_configs),
        )
        return job

    def record_execution(
        self,
        job_id: str,
        config_index: int,
        output: str,
        execution_time_ms: float = 0.0,
        token_count: int = 0,
        estimated_cost: float = 0.0,
        output_metadata: dict | None = None,
        error: str | None = None,
    ) -> ReplayExecution:
        """Record replay execution results."""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        if config_index >= len(job.configs):
            raise ValueError(f"Config index out of range: {config_index}")

        config = job.configs[config_index]
        execution = ReplayExecution(
            config=config,
            output=output,
            output_metadata=output_metadata or {},
            execution_time_ms=execution_time_ms,
            token_count=token_count,
            estimated_cost=estimated_cost,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            error=error,
        )

        # Quality score is a simple calculation based on similarity to the original output
        if output and job.original_output:
            execution.quality_score = _jaccard_similarity(job.original_output, output)

        job.executions.append(execution)
        job.status = ReplayStatus.RUNNING

        # Run comparisons when all configs have been executed
        if len(job.executions) >= len(job.configs):
            self._run_comparisons(job)

        return execution

    def _run_comparisons(self, job: ReplayJob) -> None:
        """Compare all execution results."""
        successful = [e for e in job.executions if e.error is None]
        if len(successful) < 2:
            job.status = ReplayStatus.COMPLETED
            job.completed_at = datetime.now(UTC)
            job.summary = "比較に十分な実行結果がありません"
            return

        comparisons: list[ComparisonResult] = []

        # 品質比較
        quality_scores = {e.id: e.quality_score for e in successful}
        best_quality = max(successful, key=lambda e: e.quality_score)
        comparisons.append(
            ComparisonResult(
                dimension=ComparisonDimension.QUALITY,
                winner_execution_id=best_quality.id,
                winner_model=best_quality.config.model_id,
                scores=quality_scores,
                details=f"最高品質スコア: {best_quality.quality_score:.3f} ({best_quality.config.model_id})",  # noqa: E501
            )
        )

        # 速度比較
        speed_scores = {e.id: e.execution_time_ms for e in successful}
        fastest = min(successful, key=lambda e: e.execution_time_ms)
        comparisons.append(
            ComparisonResult(
                dimension=ComparisonDimension.SPEED,
                winner_execution_id=fastest.id,
                winner_model=fastest.config.model_id,
                scores=speed_scores,
                details=f"最速: {fastest.execution_time_ms:.0f}ms ({fastest.config.model_id})",
            )
        )

        # コスト比較
        cost_scores = {e.id: e.estimated_cost for e in successful}
        cheapest = min(successful, key=lambda e: e.estimated_cost)
        comparisons.append(
            ComparisonResult(
                dimension=ComparisonDimension.COST,
                winner_execution_id=cheapest.id,
                winner_model=cheapest.config.model_id,
                scores=cost_scores,
                details=f"最低コスト: ${cheapest.estimated_cost:.4f} ({cheapest.config.model_id})",
            )
        )

        # 一貫性比較（実行間の出力類似度）
        if len(successful) >= 2:
            consistency_scores: dict[str, float] = {}
            for e in successful:
                others = [o for o in successful if o.id != e.id]
                avg_sim = sum(_jaccard_similarity(e.output, o.output) for o in others) / len(others)
                consistency_scores[e.id] = avg_sim
            most_consistent = max(successful, key=lambda e: consistency_scores.get(e.id, 0))
            comparisons.append(
                ComparisonResult(
                    dimension=ComparisonDimension.CONSISTENCY,
                    winner_execution_id=most_consistent.id,
                    winner_model=most_consistent.config.model_id,
                    scores=consistency_scores,
                    details=f"最も一貫性の高い出力: {most_consistent.config.model_id}",
                )
            )

        # 総合判定（品質 50% + 速度 20% + コスト 20% + 一貫性 10%）
        overall_scores: dict[str, float] = {}
        for e in successful:
            q = quality_scores.get(e.id, 0)
            # 速度・コストは低いほうが良いので反転
            max_time = max(speed_scores.values()) or 1
            s = 1.0 - (speed_scores.get(e.id, max_time) / max_time) if max_time > 0 else 0.5
            max_cost = max(cost_scores.values()) or 1
            c = 1.0 - (cost_scores.get(e.id, max_cost) / max_cost) if max_cost > 0 else 0.5
            con = consistency_scores.get(e.id, 0.5) if consistency_scores else 0.5
            overall_scores[e.id] = q * 0.5 + s * 0.2 + c * 0.2 + con * 0.1

        best_overall = max(successful, key=lambda e: overall_scores.get(e.id, 0))
        comparisons.append(
            ComparisonResult(
                dimension=ComparisonDimension.OVERALL,
                winner_execution_id=best_overall.id,
                winner_model=best_overall.config.model_id,
                scores=overall_scores,
                details=(
                    f"総合勝者: {best_overall.config.model_id} "
                    f"(スコア: {overall_scores.get(best_overall.id, 0):.3f})"
                ),
            )
        )

        job.comparisons = comparisons
        job.status = ReplayStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        job.summary = f"{len(successful)} モデルを比較。総合勝者: {best_overall.config.model_id}"

    def get_job(self, job_id: str) -> ReplayJob | None:
        """Get a replay job."""
        return self._jobs.get(job_id)

    def list_jobs(
        self,
        task_id: str | None = None,
        status: ReplayStatus | None = None,
        limit: int = 50,
    ) -> list[ReplayJob]:
        """Get a list of replay jobs."""
        jobs = list(self._jobs.values())
        if task_id:
            jobs = [j for j in jobs if j.original_task_id == task_id]
        if status:
            jobs = [j for j in jobs if j.status == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------

task_replay_service = TaskReplayService()
