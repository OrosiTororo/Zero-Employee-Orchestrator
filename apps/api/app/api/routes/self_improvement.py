"""AI Self-Improvement API routes — Level 2: seeds of self-improvement.

Provides API endpoints for 6 self-improvement skills:
1. POST /self-improvement/analyze          — Skill analysis
2. POST /self-improvement/improve          — Skill improvement proposal generation
3. POST /self-improvement/improve/apply    — Apply improvement (after approval)
4. POST /self-improvement/judge/tune       — Judge criteria auto-tuning
5. POST /self-improvement/judge/tune/apply — Apply Judge tuning (after approval)
6. POST /self-improvement/failure-to-skill — Generate skill from failures
7. POST /self-improvement/failure-to-skill/register — Register failure prevention skill
8. POST /self-improvement/ab-test          — A/B test execution
9. POST /self-improvement/generate-tests   — Auto test generation
10. GET  /self-improvement/status          — Dashboard
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.schemas.self_improvement import (
    AnalysisFindingResponse,
    AutoTestRequest,
    AutoTestResponse,
    FailureToSkillProposalResponse,
    FailureToSkillRegisterRequest,
    FailureToSkillRequest,
    FailureToSkillResponse,
    GeneratedTestCaseResponse,
    JudgeTuneRequest,
    JudgeTuningApplyRequest,
    JudgeTuningApplyResponse,
    JudgeTuningResponse,
    JudgeTuningRuleResponse,
    SelfImprovementStatusResponse,
    SkillABTestRequest,
    SkillABTestResponse,
    SkillAnalysisRequest,
    SkillAnalysisResponse,
    SkillImprovementApplyRequest,
    SkillImprovementResponse,
    SkillImproveRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/self-improvement")

# ---------------------------------------------------------------------------
# Internal counters (in-memory for v0.1, to be persisted to DB in the future)
# ---------------------------------------------------------------------------

_stats = {
    "skills_analyzed": 0,
    "improvements_proposed": 0,
    "improvements_applied": 0,
    "judge_rules_proposed": 0,
    "judge_rules_applied": 0,
    "failure_skills_proposed": 0,
    "ab_tests_completed": 0,
    "tests_generated": 0,
}

class ImprovementApplyResponse(PydanticBaseModel):
    status: str
    skill_id: str
    new_version: str
    message: str


class FailureSkillRegisterResponse(PydanticBaseModel):
    status: str
    skill_id: str
    slug: str
    message: str


# Cache latest results (for approval flow)
_latest_tuning: dict = {}
_latest_improvement: dict = {}


# ---------------------------------------------------------------------------
# 1. Skill Analyzer
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=SkillAnalysisResponse)
async def analyze_skill_endpoint(
    request: SkillAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SkillAnalysisResponse:
    """AI analyzes an existing skill and generates improvement proposals."""
    from app.services.self_improvement_service import analyze_skill

    try:
        skill_id = uuid.UUID(request.skill_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid skill ID")

    try:
        result = await analyze_skill(db, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    _stats["skills_analyzed"] += 1

    return SkillAnalysisResponse(
        skill_id=result.skill_id,
        skill_slug=result.skill_slug,
        overall_score=result.overall_score,
        findings=[
            AnalysisFindingResponse(
                category=f.category.value,
                priority=f.priority.value,
                title=f.title,
                description=f.description,
                suggestion=f.suggestion,
            )
            for f in result.findings
        ],
        summary=result.summary,
        analyzed_at=result.analyzed_at,
    )


# ---------------------------------------------------------------------------
# 2. Skill Improver
# ---------------------------------------------------------------------------


@router.post("/improve", response_model=SkillImprovementResponse)
async def improve_skill_endpoint(
    request: SkillImproveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SkillImprovementResponse:
    """Analyze a skill and generate an improved version (approval required to apply)."""
    from app.services.self_improvement_service import improve_skill

    try:
        skill_id = uuid.UUID(request.skill_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid skill ID")

    try:
        proposal = await improve_skill(db, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    _stats["improvements_proposed"] += 1

    # Cache for approval flow
    _latest_improvement[request.skill_id] = proposal

    return SkillImprovementResponse(
        original_skill_id=proposal.original_skill_id,
        original_version=proposal.original_version,
        proposed_version=proposal.proposed_version,
        original_code=proposal.original_code,
        improved_code=proposal.improved_code,
        changes_summary=proposal.changes_summary,
        expected_improvements=proposal.expected_improvements,
        requires_approval=proposal.requires_approval,
        created_at=proposal.created_at,
    )


@router.post("/improve/apply", response_model=ImprovementApplyResponse)
async def apply_improvement_endpoint(
    request: SkillImprovementApplyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Apply an improvement proposal (called after approval)."""
    from app.services.self_improvement_service import (
        SkillImprovementProposal,
        apply_improvement,
    )

    try:
        skill_id = uuid.UUID(request.skill_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid skill ID")

    proposal = SkillImprovementProposal(
        original_skill_id=request.skill_id,
        original_version="",
        proposed_version=request.proposed_version,
        original_code="",
        improved_code=request.improved_code,
        changes_summary=["Improvement applied based on approval"],
        expected_improvements=[],
    )

    try:
        skill = await apply_improvement(db, skill_id, proposal)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    _stats["improvements_applied"] += 1

    return {
        "status": "applied",
        "skill_id": str(skill.id),
        "new_version": skill.version,
        "message": f"Skill '{skill.slug}' updated to v{skill.version}",
    }


# ---------------------------------------------------------------------------
# 3. Judge Tuner
# ---------------------------------------------------------------------------


@router.post("/judge/tune", response_model=JudgeTuningResponse)
async def tune_judge_endpoint(
    request: JudgeTuneRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JudgeTuningResponse:
    """Propose Judge criteria adjustments from Experience Memory."""
    from app.services.self_improvement_service import tune_judge_from_experience

    try:
        company_id = uuid.UUID(request.company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID")

    result = await tune_judge_from_experience(db, company_id)
    _stats["judge_rules_proposed"] += len(result.proposed_rules)

    # Cache for approval flow
    _latest_tuning[request.company_id] = result

    return JudgeTuningResponse(
        company_id=result.company_id,
        proposed_rules=[
            JudgeTuningRuleResponse(
                rule_name=r.rule_name,
                rule_type=r.rule_type,
                condition=r.condition,
                action=r.action,
                confidence=r.confidence,
                source_patterns=r.source_patterns,
                description=r.description,
            )
            for r in result.proposed_rules
        ],
        analyzed_patterns=result.analyzed_patterns,
        approval_rate=result.approval_rate,
        rejection_rate=result.rejection_rate,
        summary=result.summary,
        tuned_at=result.tuned_at,
    )


@router.post("/judge/tune/apply", response_model=JudgeTuningApplyResponse)
async def apply_judge_tuning_endpoint(
    request: JudgeTuningApplyRequest,
    user: User = Depends(get_current_user),
) -> JudgeTuningApplyResponse:
    """Apply proposed Judge rules (after approval)."""
    from app.services.self_improvement_service import (
        apply_judge_tuning,
    )

    cached = _latest_tuning.get(request.company_id)
    if cached is None:
        raise HTTPException(
            status_code=404,
            detail="Please generate tuning proposals first via /judge/tune",
        )

    # Apply only specific rules if specified
    if request.rule_names:
        cached.proposed_rules = [
            r for r in cached.proposed_rules if r.rule_name in request.rule_names
        ]

    applied = await apply_judge_tuning(cached)
    _stats["judge_rules_applied"] += applied

    return JudgeTuningApplyResponse(
        applied_count=applied,
        message=f"Applied {applied} Judge rules",
    )


# ---------------------------------------------------------------------------
# 4. Failure-to-Skill
# ---------------------------------------------------------------------------


@router.post("/failure-to-skill", response_model=FailureToSkillResponse)
async def failure_to_skill_endpoint(
    request: FailureToSkillRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FailureToSkillResponse:
    """Auto-generate prevention skills from failure patterns."""
    from app.services.self_improvement_service import generate_skills_from_failures

    try:
        company_id = uuid.UUID(request.company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID")

    proposals = await generate_skills_from_failures(
        db, company_id, min_occurrences=request.min_occurrences
    )
    _stats["failure_skills_proposed"] += len(proposals)

    return FailureToSkillResponse(
        proposals=[
            FailureToSkillProposalResponse(
                failure_category=p.failure_category,
                failure_subcategory=p.failure_subcategory,
                occurrence_count=p.occurrence_count,
                proposed_skill_slug=p.proposed_skill_slug,
                proposed_skill_name=p.proposed_skill_name,
                proposed_skill_description=p.proposed_skill_description,
                proposed_code=p.proposed_code,
                prevention_strategy=p.prevention_strategy,
                confidence=p.confidence,
            )
            for p in proposals
        ],
        total_failures_analyzed=len(proposals),
    )


@router.post("/failure-to-skill/register", response_model=FailureSkillRegisterResponse)
async def register_failure_skill_endpoint(
    request: FailureToSkillRegisterRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Register a failure prevention skill (after approval)."""
    from app.services.skill_service import (
        SkillCreate,
        analyze_code_safety,
        create_skill,
    )

    # Safety check
    safety = analyze_code_safety(request.code)
    if safety.risk_level == "high":
        raise HTTPException(
            status_code=400,
            detail=f"Safety check failed: {safety.summary}",
        )

    skill = await create_skill(
        db,
        SkillCreate(
            slug=request.slug,
            name=request.name,
            skill_type="prevention",
            description=request.description,
            version="0.1.0",
            source_type="failure-generated",
        ),
        generated_code=request.code,
    )
    await db.commit()

    return {
        "status": "registered",
        "skill_id": str(skill.id),
        "slug": skill.slug,
        "message": f"Failure prevention skill '{skill.name}' registered",
    }


# ---------------------------------------------------------------------------
# 5. Skill A/B Test
# ---------------------------------------------------------------------------


@router.post("/ab-test", response_model=SkillABTestResponse)
async def skill_ab_test_endpoint(
    request: SkillABTestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SkillABTestResponse:
    """Compare two skills via A/B testing."""
    from app.services.self_improvement_service import run_skill_ab_test

    try:
        skill_a = uuid.UUID(request.skill_a_id)
        skill_b = uuid.UUID(request.skill_b_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid skill ID")

    try:
        result = await run_skill_ab_test(
            db, skill_a, skill_b, request.test_input, request.iterations
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    _stats["ab_tests_completed"] += 1

    return SkillABTestResponse(
        test_id=result.test_id,
        skill_a_id=result.skill_a_id,
        skill_b_id=result.skill_b_id,
        skill_a_scores=result.skill_a_scores,
        skill_b_scores=result.skill_b_scores,
        skill_a_avg_time_ms=result.skill_a_avg_time_ms,
        skill_b_avg_time_ms=result.skill_b_avg_time_ms,
        winner=result.winner,
        winner_reason=result.winner_reason,
        details=result.details,
        completed_at=result.completed_at,
    )


# ---------------------------------------------------------------------------
# 6. Auto Test Generator
# ---------------------------------------------------------------------------


@router.post("/generate-tests", response_model=AutoTestResponse)
async def generate_tests_endpoint(
    request: AutoTestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AutoTestResponse:
    """Auto-generate test code for a skill."""
    from app.services.self_improvement_service import generate_tests_for_skill

    try:
        skill_id = uuid.UUID(request.skill_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid skill ID")

    try:
        result = await generate_tests_for_skill(db, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    _stats["tests_generated"] += result.total_tests

    return AutoTestResponse(
        skill_id=result.skill_id,
        skill_slug=result.skill_slug,
        test_cases=[
            GeneratedTestCaseResponse(
                test_name=tc.test_name,
                test_type=tc.test_type,
                input_data=tc.input_data,
                expected_behavior=tc.expected_behavior,
                test_code=tc.test_code,
            )
            for tc in result.test_cases
        ],
        total_tests=result.total_tests,
        normal_tests=result.normal_tests,
        edge_tests=result.edge_tests,
        error_tests=result.error_tests,
        generated_at=result.generated_at,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/status", response_model=SelfImprovementStatusResponse)
async def self_improvement_status(
    user: User = Depends(get_current_user),
) -> SelfImprovementStatusResponse:
    """Return the overall status of AI Self-Improvement."""
    return SelfImprovementStatusResponse(
        plugin_version="0.1.0",
        **_stats,
    )
