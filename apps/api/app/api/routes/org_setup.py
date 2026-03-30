"""Organization auto-builder API endpoints.

Auto-generates departments, teams, and agents based on interview responses.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services.org_generator_service import (
    BusinessCategory,
    OrgInterviewAnswer,
    PainPoint,
    apply_org_blueprint,
    generate_org_blueprint,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OrgInterviewRequest(BaseModel):
    """Organization setup interview request."""

    business_description: str
    business_category: str = "other"
    goals: list[str] = []
    pain_points: list[str] = []
    team_size_preference: str = "minimal"
    start_with_secretary_only: bool = False


class OrgPreviewResponse(BaseModel):
    """Organization design preview."""

    departments: list[dict]
    secretary_agent: dict | None = None
    total_departments: int
    total_teams: int
    total_agents: int


class OrgGenerateRequest(BaseModel):
    """Organization generation execution request."""

    company_id: str
    interview: OrgInterviewRequest
    provider_name: str = "openrouter"


class OrgGenerateResponse(BaseModel):
    """Organization generation result."""

    departments: list[dict]
    teams: list[dict]
    agents: list[dict]
    total_departments: int
    total_teams: int
    total_agents: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


# No auth required: onboarding questions are public
@router.get("/interview/questions")
async def get_interview_questions(request: Request):
    """Get list of organization setup interview questions.

    Returns questions in the language specified by Accept-Language header
    or the configured LANGUAGE setting. Defaults to English.
    """
    from app.core.config import settings

    accept_lang = request.headers.get("accept-language", "").lower()
    lang = settings.LANGUAGE.lower()
    # Use Japanese only if explicitly requested
    use_ja = accept_lang.startswith("ja") or lang == "ja"

    def q(ja: str, en: str) -> str:
        return ja if use_ja else en

    def opt_label(ja: str, en: str) -> dict:
        return {"label": ja if use_ja else en, "label_ja": ja, "label_en": en}

    return {
        "questions": [
            {
                "id": "business_description",
                "text": q(
                    "現在の事業内容を教えてください", "Please describe your current business"
                ),
                "question": "現在の事業内容を教えてください",
                "question_en": "Please describe your current business",
                "type": "text",
                "required": True,
            },
            {
                "id": "business_category",
                "question": "事業カテゴリを選択してください",
                "question_en": "Select your business category",
                "type": "select",
                "required": True,
                "options": [
                    {
                        "value": c.value,
                        "label_ja": _CATEGORY_LABELS_JA[c],
                        "label_en": _CATEGORY_LABELS_EN[c],
                    }
                    for c in BusinessCategory
                ],
            },
            {
                "id": "goals",
                "question": "目標を教えてください（複数選択可）",
                "question_en": "What are your goals? (select multiple)",
                "type": "multi_select",
                "required": False,
                "options": [
                    {
                        "value": "revenue_growth",
                        "label_ja": "売上拡大",
                        "label_en": "Revenue growth",
                    },
                    {
                        "value": "user_growth",
                        "label_ja": "ユーザー獲得",
                        "label_en": "User acquisition",
                    },
                    {
                        "value": "brand_building",
                        "label_ja": "ブランド構築",
                        "label_en": "Brand building",
                    },
                    {
                        "value": "cost_reduction",
                        "label_ja": "コスト削減",
                        "label_en": "Cost reduction",
                    },
                    {
                        "value": "product_launch",
                        "label_ja": "新商品リリース",
                        "label_en": "Product launch",
                    },
                    {
                        "value": "automation",
                        "label_ja": "業務自動化",
                        "label_en": "Automation",
                    },
                ],
            },
            {
                "id": "pain_points",
                "question": "困りごとを教えてください（複数選択可）",
                "question_en": "What are your pain points? (select multiple)",
                "type": "multi_select",
                "required": False,
                "options": [
                    {
                        "value": p.value,
                        "label_ja": _PAIN_LABELS_JA[p],
                        "label_en": _PAIN_LABELS_EN[p],
                    }
                    for p in PainPoint
                ],
            },
            {
                "id": "team_size_preference",
                "question": "組織規模を選択してください",
                "question_en": "Select your preferred organization size",
                "type": "select",
                "required": True,
                "options": [
                    {
                        "value": "minimal",
                        "label_ja": "ミニマル（秘書＋必要最小限）",
                        "label_en": "Minimal (secretary + essentials)",
                    },
                    {
                        "value": "standard",
                        "label_ja": "スタンダード（推奨構成）",
                        "label_en": "Standard (recommended)",
                    },
                    {
                        "value": "full",
                        "label_ja": "フル（全部署）",
                        "label_en": "Full (all departments)",
                    },
                ],
            },
            {
                "id": "start_with_secretary_only",
                "question": "まずは秘書だけで始めますか？",
                "question_en": "Start with secretary only?",
                "type": "boolean",
                "required": False,
            },
        ],
    }


@router.post("/preview", response_model=OrgPreviewResponse)
async def preview_org_structure(req: OrgInterviewRequest, user: User = Depends(get_current_user)):
    """Preview organization structure from interview answers (no DB save)."""
    answers = OrgInterviewAnswer(
        business_description=req.business_description,
        business_category=req.business_category,
        goals=req.goals,
        pain_points=req.pain_points,
        team_size_preference=req.team_size_preference,
        start_with_secretary_only=req.start_with_secretary_only,
    )
    blueprint = generate_org_blueprint(answers)

    departments = []
    total_teams = 0
    total_agents = 0
    for dept in blueprint.departments:
        teams = []
        for team in dept.teams:
            agents = [
                {"name": a.name, "title": a.title, "description": a.description}
                for a in team.agents
            ]
            teams.append(
                {
                    "name": team.name,
                    "purpose": team.purpose,
                    "agents": agents,
                }
            )
            total_agents += len(team.agents)
        departments.append(
            {
                "name": dept.name,
                "code": dept.code,
                "description": dept.description,
                "teams": teams,
            }
        )
        total_teams += len(dept.teams)

    secretary = None
    if blueprint.secretary_agent:
        secretary = {
            "name": blueprint.secretary_agent.name,
            "title": blueprint.secretary_agent.title,
            "description": blueprint.secretary_agent.description,
        }

    return OrgPreviewResponse(
        departments=departments,
        secretary_agent=secretary,
        total_departments=len(departments),
        total_teams=total_teams,
        total_agents=total_agents,
    )


@router.post("/generate", response_model=OrgGenerateResponse)
async def generate_org_structure(
    req: OrgGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate organization structure from interview answers and save to DB."""
    answers = OrgInterviewAnswer(
        business_description=req.interview.business_description,
        business_category=req.interview.business_category,
        goals=req.interview.goals,
        pain_points=req.interview.pain_points,
        team_size_preference=req.interview.team_size_preference,
        start_with_secretary_only=req.interview.start_with_secretary_only,
    )
    blueprint = generate_org_blueprint(answers)

    result = await apply_org_blueprint(
        db=db,
        company_id=req.company_id,
        blueprint=blueprint,
        provider_name=req.provider_name,
    )

    return OrgGenerateResponse(**result)


# ---------------------------------------------------------------------------
# Label mappings
# ---------------------------------------------------------------------------

_CATEGORY_LABELS_JA: dict[BusinessCategory, str] = {
    BusinessCategory.TECH_STARTUP: "テックスタートアップ",
    BusinessCategory.ECOMMERCE: "EC / オンラインショップ",
    BusinessCategory.CONTENT_CREATOR: "コンテンツクリエイター",
    BusinessCategory.CONSULTING: "コンサルティング",
    BusinessCategory.SAAS: "SaaS",
    BusinessCategory.AGENCY: "代理店 / エージェンシー",
    BusinessCategory.MANUFACTURING: "製造業",
    BusinessCategory.EDUCATION: "教育",
    BusinessCategory.OTHER: "その他",
}

_CATEGORY_LABELS_EN: dict[BusinessCategory, str] = {
    BusinessCategory.TECH_STARTUP: "Tech Startup",
    BusinessCategory.ECOMMERCE: "E-commerce",
    BusinessCategory.CONTENT_CREATOR: "Content Creator",
    BusinessCategory.CONSULTING: "Consulting",
    BusinessCategory.SAAS: "SaaS",
    BusinessCategory.AGENCY: "Agency",
    BusinessCategory.MANUFACTURING: "Manufacturing",
    BusinessCategory.EDUCATION: "Education",
    BusinessCategory.OTHER: "Other",
}

_PAIN_LABELS_JA: dict[PainPoint, str] = {
    PainPoint.TASK_MANAGEMENT: "タスク管理",
    PainPoint.CUSTOMER_ACQUISITION: "集客・顧客獲得",
    PainPoint.CONTENT_CREATION: "コンテンツ制作",
    PainPoint.DATA_ANALYSIS: "データ分析",
    PainPoint.ACCOUNTING: "経理・会計",
    PainPoint.CUSTOMER_SUPPORT: "カスタマーサポート",
    PainPoint.RESEARCH: "リサーチ・調査",
    PainPoint.DEVELOPMENT: "開発",
}

_PAIN_LABELS_EN: dict[PainPoint, str] = {
    PainPoint.TASK_MANAGEMENT: "Task Management",
    PainPoint.CUSTOMER_ACQUISITION: "Customer Acquisition",
    PainPoint.CONTENT_CREATION: "Content Creation",
    PainPoint.DATA_ANALYSIS: "Data Analysis",
    PainPoint.ACCOUNTING: "Accounting",
    PainPoint.CUSTOMER_SUPPORT: "Customer Support",
    PainPoint.RESEARCH: "Research",
    PainPoint.DEVELOPMENT: "Development",
}
