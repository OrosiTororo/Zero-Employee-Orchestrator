"""品質・洞察 API ルート — Quality & Insights.

5つの品質・洞察機能の API エンドポイントを提供する:

1. 前提変化の汎用監視 (Prerequisite Monitor)
   - POST /quality-insights/prerequisites/sources          — 監視対象登録
   - GET  /quality-insights/prerequisites/sources          — 監視対象一覧
   - GET  /quality-insights/prerequisites/sources/{id}     — 監視対象詳細
   - PUT  /quality-insights/prerequisites/sources/{id}     — 監視対象更新
   - DELETE /quality-insights/prerequisites/sources/{id}   — 監視対象削除
   - POST /quality-insights/prerequisites/check            — 手動チェック
   - GET  /quality-insights/prerequisites/changes          — 変更履歴
   - POST /quality-insights/prerequisites/changes/{id}/ack — 変更確認
   - GET  /quality-insights/prerequisites/summary          — サマリー

2. Spec 間矛盾検出 (Spec Contradiction)
   - POST /quality-insights/spec-contradictions/check      — 矛盾検出

3. タスクリプレイ・比較 (Task Replay)
   - POST /quality-insights/task-replay/jobs               — リプレイジョブ作成
   - GET  /quality-insights/task-replay/jobs               — ジョブ一覧
   - GET  /quality-insights/task-replay/jobs/{id}          — ジョブ詳細
   - POST /quality-insights/task-replay/jobs/{id}/execute  — 実行結果記録

4. ユーザー判断振り返り (Judgment Review)
   - POST /quality-insights/judgment-review/record         — 判断記録
   - GET  /quality-insights/judgment-review/report         — レポート生成

5. Plan 品質検証 (Plan Quality)
   - POST /quality-insights/plan-quality/verify            — Plan 品質検証
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User

# Schemas
from app.schemas.judgment_review import (
    CategoryInsightResponse,
    JudgmentPatternResponse,
    JudgmentRecordCreate,
    JudgmentReviewReportResponse,
    TrendPointResponse,
)
from app.schemas.plan_quality import (
    CoverageItemResponse,
    DuplicatePairResponse,
    PlanQualityReportResponse,
    PlanQualityVerifyRequest,
    QualityIssueResponse,
)
from app.schemas.prerequisite_monitor import (
    PrerequisiteChangeResponse,
    PrerequisiteCheckRequest,
    PrerequisiteSourceCreate,
    PrerequisiteSourceResponse,
    PrerequisiteSourceUpdate,
    PrerequisiteSummaryResponse,
)
from app.schemas.spec_contradiction import (
    ContradictionCheckRequest,
    ContradictionDetailResponse,
    SpecContradictionReportResponse,
)
from app.schemas.task_replay import (
    ComparisonResultResponse,
    ReplayExecutionRecordRequest,
    ReplayExecutionResponse,
    ReplayJobCreateRequest,
    ReplayJobResponse,
)

# Services
from app.services.judgment_review_service import (
    JudgmentAction,
    JudgmentCategory,
    judgment_review_service,
)
from app.services.plan_quality_service import (
    PlanInput,
    PlanTaskInput,
    SpecInput,
    plan_quality_verifier,
)
from app.services.prerequisite_monitor_service import (
    PrerequisiteCategory,
    prerequisite_monitor,
)
from app.services.spec_contradiction_service import (
    SpecSummary,
    spec_contradiction_detector,
)
from app.services.task_replay_service import task_replay_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality-insights")


# ===========================================================================
# 1. 前提変化の汎用監視 (Prerequisite Monitor)
# ===========================================================================


@router.post(
    "/prerequisites/sources",
    response_model=PrerequisiteSourceResponse,
    summary="監視対象を登録",
)
async def register_prerequisite_source(
    body: PrerequisiteSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """外部情報源を監視対象として登録する."""
    try:
        category = PrerequisiteCategory(body.category)
    except ValueError:
        category = PrerequisiteCategory.CUSTOM

    source = prerequisite_monitor.register_source(
        company_id=str(current_user.company_id) if current_user.company_id else "",
        name=body.name,
        url=body.url,
        category=category,
        description=body.description,
        check_interval_hours=body.check_interval_hours,
        keywords=body.keywords,
        created_by=str(current_user.id),
        linked_ticket_ids=body.linked_ticket_ids,
    )
    return _source_to_response(source)


@router.get(
    "/prerequisites/sources",
    response_model=list[PrerequisiteSourceResponse],
    summary="監視対象一覧",
)
async def list_prerequisite_sources(
    category: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """登録済みの監視対象を一覧取得する."""
    cat = PrerequisiteCategory(category) if category else None
    sources = prerequisite_monitor.list_sources(
        company_id=str(current_user.company_id) if current_user.company_id else "",
        category=cat,
    )
    return [_source_to_response(s) for s in sources]


@router.get(
    "/prerequisites/sources/{source_id}",
    response_model=PrerequisiteSourceResponse,
    summary="監視対象詳細",
)
async def get_prerequisite_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
):
    """監視対象の詳細を取得する."""
    source = prerequisite_monitor.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return _source_to_response(source)


@router.put(
    "/prerequisites/sources/{source_id}",
    response_model=PrerequisiteSourceResponse,
    summary="監視対象更新",
)
async def update_prerequisite_source(
    source_id: str,
    body: PrerequisiteSourceUpdate,
    current_user: User = Depends(get_current_user),
):
    """監視対象を更新する."""
    updates = body.model_dump(exclude_unset=True)
    try:
        source = prerequisite_monitor.update_source(source_id, **updates)
    except ValueError:
        raise HTTPException(status_code=404, detail="Source not found")
    return _source_to_response(source)


@router.delete(
    "/prerequisites/sources/{source_id}",
    summary="監視対象削除",
)
async def delete_prerequisite_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
):
    """監視対象を削除する."""
    if not prerequisite_monitor.remove_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return {"message": "Source deleted"}


@router.post(
    "/prerequisites/check",
    response_model=PrerequisiteChangeResponse | None,
    summary="手動チェック実行",
)
async def check_prerequisite(
    body: PrerequisiteCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """監視対象の内容を手動でチェックする."""
    try:
        change = prerequisite_monitor.check_source(body.source_id, body.content)
    except ValueError:
        raise HTTPException(status_code=404, detail="Source not found")
    if change is None:
        return None
    return _change_to_response(change)


@router.get(
    "/prerequisites/changes",
    response_model=list[PrerequisiteChangeResponse],
    summary="変更履歴",
)
async def list_prerequisite_changes(
    source_id: str | None = None,
    impact: str | None = None,
    unacknowledged_only: bool = False,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
):
    """検出された変更の履歴を取得する."""
    from app.services.prerequisite_monitor_service import ChangeImpact

    imp = ChangeImpact(impact) if impact else None
    changes = prerequisite_monitor.list_changes(
        company_id=str(current_user.company_id) if current_user.company_id else "",
        source_id=source_id,
        impact=imp,
        unacknowledged_only=unacknowledged_only,
        limit=limit,
    )
    return [_change_to_response(c) for c in changes]


@router.post(
    "/prerequisites/changes/{change_id}/ack",
    summary="変更を確認済みにする",
)
async def acknowledge_prerequisite_change(
    change_id: str,
    current_user: User = Depends(get_current_user),
):
    """変更を確認済みにする."""
    change = prerequisite_monitor.acknowledge_change(change_id, str(current_user.id))
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    return {"message": "Change acknowledged"}


@router.get(
    "/prerequisites/summary",
    response_model=PrerequisiteSummaryResponse,
    summary="監視サマリー",
)
async def get_prerequisite_summary(
    current_user: User = Depends(get_current_user),
):
    """監視のサマリーを取得する."""
    company_id = str(current_user.company_id) if current_user.company_id else ""
    summary = prerequisite_monitor.get_summary(company_id)
    return PrerequisiteSummaryResponse(**summary)


# ===========================================================================
# 2. Spec 間矛盾検出 (Spec Contradiction)
# ===========================================================================


@router.post(
    "/spec-contradictions/check",
    response_model=SpecContradictionReportResponse,
    summary="Spec 間矛盾検出",
)
async def check_spec_contradictions(
    body: ContradictionCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """複数の Spec 間の矛盾を検出する."""
    specs = [
        SpecSummary(
            spec_id=s.spec_id,
            ticket_id=s.ticket_id,
            ticket_title=s.ticket_title,
            objective=s.objective,
            constraints=s.constraints,
            acceptance_criteria=s.acceptance_criteria,
            risk_notes=s.risk_notes,
            priority=s.priority,
            estimated_budget=s.estimated_budget,
            deadline=s.deadline,
        )
        for s in body.specs
    ]

    company_id = str(current_user.company_id) if current_user.company_id else ""
    report = spec_contradiction_detector.detect_contradictions(
        specs, company_id=company_id, project_id=body.project_id
    )

    return SpecContradictionReportResponse(
        id=report.id,
        company_id=report.company_id,
        project_id=report.project_id,
        analyzed_specs=report.analyzed_specs,
        contradictions=[
            ContradictionDetailResponse(
                id=c.id,
                type=c.type.value,
                severity=c.severity.value,
                spec_a_id=c.spec_a_id,
                spec_a_ticket=c.spec_a_ticket,
                spec_b_id=c.spec_b_id,
                spec_b_ticket=c.spec_b_ticket,
                field_a=c.field_a,
                value_a=c.value_a,
                field_b=c.field_b,
                value_b=c.value_b,
                description=c.description,
                suggestion=c.suggestion,
            )
            for c in report.contradictions
        ],
        critical_count=report.critical_count,
        error_count=report.error_count,
        warning_count=report.warning_count,
        info_count=report.info_count,
        overall_consistency_score=report.overall_consistency_score,
        analyzed_at=report.analyzed_at.isoformat(),
    )


# ===========================================================================
# 3. タスクリプレイ・比較 (Task Replay)
# ===========================================================================


@router.post(
    "/task-replay/jobs",
    response_model=ReplayJobResponse,
    summary="リプレイジョブ作成",
)
async def create_replay_job(
    body: ReplayJobCreateRequest,
    current_user: User = Depends(get_current_user),
):
    """タスクのリプレイジョブを作成する."""
    configs = [c.model_dump() for c in body.configs]
    job = task_replay_service.create_replay_job(
        task_id=body.task_id,
        task_description=body.task_description,
        original_output=body.original_output,
        configs=configs,
        created_by=str(current_user.id),
    )
    return _job_to_response(job)


@router.get(
    "/task-replay/jobs",
    response_model=list[ReplayJobResponse],
    summary="リプレイジョブ一覧",
)
async def list_replay_jobs(
    task_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
):
    """リプレイジョブを一覧取得する."""
    from app.services.task_replay_service import ReplayStatus

    st = ReplayStatus(status) if status else None
    jobs = task_replay_service.list_jobs(task_id=task_id, status=st, limit=limit)
    return [_job_to_response(j) for j in jobs]


@router.get(
    "/task-replay/jobs/{job_id}",
    response_model=ReplayJobResponse,
    summary="リプレイジョブ詳細",
)
async def get_replay_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """リプレイジョブの詳細を取得する."""
    job = task_replay_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.post(
    "/task-replay/jobs/{job_id}/execute",
    response_model=ReplayExecutionResponse,
    summary="リプレイ実行結果記録",
)
async def record_replay_execution(
    job_id: str,
    body: ReplayExecutionRecordRequest,
    current_user: User = Depends(get_current_user),
):
    """リプレイ実行結果を記録する."""
    try:
        execution = task_replay_service.record_execution(
            job_id=job_id,
            config_index=body.config_index,
            output=body.output,
            execution_time_ms=body.execution_time_ms,
            token_count=body.token_count,
            estimated_cost=body.estimated_cost,
            output_metadata=body.output_metadata,
            error=body.error,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ReplayExecutionResponse(
        id=execution.id,
        model_id=execution.config.model_id,
        quality_score=execution.quality_score,
        execution_time_ms=execution.execution_time_ms,
        token_count=execution.token_count,
        estimated_cost=execution.estimated_cost,
        error=execution.error,
    )


# ===========================================================================
# 4. ユーザー判断振り返り (Judgment Review)
# ===========================================================================


@router.post(
    "/judgment-review/record",
    summary="判断を記録する",
)
async def record_judgment(
    body: JudgmentRecordCreate,
    current_user: User = Depends(get_current_user),
):
    """ユーザーの判断（承認・却下等）を記録する."""
    try:
        action = JudgmentAction(body.action)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid action: {body.action}")
    try:
        category = JudgmentCategory(body.category)
    except ValueError:
        category = JudgmentCategory.OTHER

    company_id = str(current_user.company_id) if current_user.company_id else ""
    record = judgment_review_service.record_judgment(
        user_id=str(current_user.id),
        company_id=company_id,
        action=action,
        category=category,
        target_type=body.target_type,
        target_id=body.target_id,
        risk_level=body.risk_level,
        reason=body.reason,
        response_time_seconds=body.response_time_seconds,
    )
    return {"id": record.id, "message": "Judgment recorded"}


@router.get(
    "/judgment-review/report",
    response_model=JudgmentReviewReportResponse,
    summary="判断振り返りレポート生成",
)
async def get_judgment_review_report(
    period_days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
):
    """ユーザーの判断傾向を分析したレポートを生成する."""
    company_id = str(current_user.company_id) if current_user.company_id else ""
    report = judgment_review_service.generate_report(
        user_id=str(current_user.id),
        company_id=company_id,
        period_days=period_days,
    )
    return JudgmentReviewReportResponse(
        id=report.id,
        user_id=report.user_id,
        company_id=report.company_id,
        period_start=report.period_start.isoformat(),
        period_end=report.period_end.isoformat(),
        total_decisions=report.total_decisions,
        approval_rate=report.approval_rate,
        rejection_rate=report.rejection_rate,
        avg_response_time_seconds=report.avg_response_time_seconds,
        category_insights=[
            CategoryInsightResponse(
                category=ci.category,
                total=ci.total,
                approved=ci.approved,
                rejected=ci.rejected,
                deferred=ci.deferred,
                approval_rate=ci.approval_rate,
                avg_response_time_seconds=ci.avg_response_time_seconds,
            )
            for ci in report.category_insights
        ],
        risk_distribution=report.risk_distribution,
        weekly_trend=[
            TrendPointResponse(
                period=tp.period,
                total=tp.total,
                approved=tp.approved,
                rejected=tp.rejected,
                approval_rate=tp.approval_rate,
            )
            for tp in report.weekly_trend
        ],
        detected_patterns=[
            JudgmentPatternResponse(
                pattern_type=p.pattern_type,
                description=p.description,
                confidence=p.confidence,
                suggestion=p.suggestion,
            )
            for p in report.detected_patterns
        ],
        generated_at=report.generated_at.isoformat(),
    )


# ===========================================================================
# 5. Plan 品質検証 (Plan Quality)
# ===========================================================================


@router.post(
    "/plan-quality/verify",
    response_model=PlanQualityReportResponse,
    summary="Plan 品質検証",
)
async def verify_plan_quality(
    body: PlanQualityVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Spec → Plan 分解の品質を検証する（MECE チェック）."""
    spec = SpecInput(
        spec_id=body.spec.spec_id,
        objective=body.spec.objective,
        constraints=body.spec.constraints,
        acceptance_criteria=body.spec.acceptance_criteria,
        risk_notes=body.spec.risk_notes,
    )
    plan = PlanInput(
        plan_id=body.plan.plan_id,
        spec_id=body.plan.spec_id,
        tasks=[
            PlanTaskInput(
                task_id=t.task_id,
                title=t.title,
                description=t.description,
                depends_on=t.depends_on,
                estimated_hours=t.estimated_hours,
                estimated_cost=t.estimated_cost,
            )
            for t in body.plan.tasks
        ],
    )

    report = plan_quality_verifier.verify(spec, plan)

    return PlanQualityReportResponse(
        id=report.id,
        plan_id=report.plan_id,
        spec_id=report.spec_id,
        quality_level=report.quality_level.value,
        overall_score=report.overall_score,
        objective_coverage=CoverageItemResponse(
            source_type=report.objective_coverage.source_type,
            source_text=report.objective_coverage.source_text,
            status=report.objective_coverage.status.value,
            matched_task_ids=report.objective_coverage.matched_task_ids,
            matched_task_titles=report.objective_coverage.matched_task_titles,
            similarity_score=report.objective_coverage.similarity_score,
        )
        if report.objective_coverage
        else None,
        constraint_coverage=[
            CoverageItemResponse(
                source_type=c.source_type,
                source_text=c.source_text,
                status=c.status.value,
                matched_task_ids=c.matched_task_ids,
                matched_task_titles=c.matched_task_titles,
                similarity_score=c.similarity_score,
            )
            for c in report.constraint_coverage
        ],
        acceptance_coverage=[
            CoverageItemResponse(
                source_type=c.source_type,
                source_text=c.source_text,
                status=c.status.value,
                matched_task_ids=c.matched_task_ids,
                matched_task_titles=c.matched_task_titles,
                similarity_score=c.similarity_score,
            )
            for c in report.acceptance_coverage
        ],
        duplicate_tasks=[
            DuplicatePairResponse(
                task_a_id=d.task_a_id,
                task_a_title=d.task_a_title,
                task_b_id=d.task_b_id,
                task_b_title=d.task_b_title,
                similarity=d.similarity,
            )
            for d in report.duplicate_tasks
        ],
        issues=[
            QualityIssueResponse(
                id=i.id,
                type=i.type.value,
                severity=i.severity.value,
                description=i.description,
                affected_items=i.affected_items,
                suggestion=i.suggestion,
            )
            for i in report.issues
        ],
        total_tasks=report.total_tasks,
        covered_objectives=report.covered_objectives,
        covered_constraints=report.covered_constraints,
        covered_acceptance=report.covered_acceptance,
        verified_at=report.verified_at.isoformat(),
    )


# ===========================================================================
# ヘルパー関数
# ===========================================================================


def _source_to_response(source) -> PrerequisiteSourceResponse:
    return PrerequisiteSourceResponse(
        id=source.id,
        company_id=source.company_id,
        name=source.name,
        url=source.url,
        category=source.category.value,
        description=source.description,
        check_interval_hours=source.check_interval_hours,
        keywords=source.keywords,
        status=source.status.value,
        last_checked=source.last_checked.isoformat() if source.last_checked else None,
        last_change_detected=(
            source.last_change_detected.isoformat() if source.last_change_detected else None
        ),
        created_at=source.created_at.isoformat(),
        linked_ticket_ids=source.linked_ticket_ids,
    )


def _change_to_response(change) -> PrerequisiteChangeResponse:
    return PrerequisiteChangeResponse(
        id=change.id,
        source_id=change.source_id,
        source_name=change.source_name,
        category=change.category.value,
        title=change.title,
        summary=change.summary,
        diff_snippet=change.diff_snippet,
        impact=change.impact.value,
        detected_at=change.detected_at.isoformat(),
        acknowledged=change.acknowledged,
        affected_ticket_ids=change.affected_ticket_ids,
        matched_keywords=change.matched_keywords,
    )


def _job_to_response(job) -> ReplayJobResponse:
    return ReplayJobResponse(
        id=job.id,
        original_task_id=job.original_task_id,
        status=job.status.value,
        executions=[
            ReplayExecutionResponse(
                id=e.id,
                model_id=e.config.model_id,
                quality_score=e.quality_score,
                execution_time_ms=e.execution_time_ms,
                token_count=e.token_count,
                estimated_cost=e.estimated_cost,
                error=e.error,
            )
            for e in job.executions
        ],
        comparisons=[
            ComparisonResultResponse(
                dimension=c.dimension.value,
                winner_execution_id=c.winner_execution_id,
                winner_model=c.winner_model,
                scores=c.scores,
                details=c.details,
            )
            for c in job.comparisons
        ],
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        summary=job.summary,
    )
