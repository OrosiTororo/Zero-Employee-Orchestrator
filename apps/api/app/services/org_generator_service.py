"""Organization auto-generation service.

Automatically generates optimal department, team, and agent configurations
based on interview answers (business description, goals, challenges).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.agent import Agent
from app.models.audit import AuditLog
from app.models.organization import Department, Team


class BusinessCategory(str, Enum):
    """事業カテゴリ."""

    TECH_STARTUP = "tech_startup"
    ECOMMERCE = "ecommerce"
    CONTENT_CREATOR = "content_creator"
    CONSULTING = "consulting"
    SAAS = "saas"
    AGENCY = "agency"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    OTHER = "other"


class PainPoint(str, Enum):
    """困りごとカテゴリ."""

    TASK_MANAGEMENT = "task_management"
    CUSTOMER_ACQUISITION = "customer_acquisition"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    ACCOUNTING = "accounting"
    CUSTOMER_SUPPORT = "customer_support"
    RESEARCH = "research"
    DEVELOPMENT = "development"


@dataclass
class OrgInterviewAnswer:
    """組織構築ヒアリング回答."""

    business_description: str
    business_category: str = "other"
    goals: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    team_size_preference: str = "minimal"  # minimal | standard | full
    start_with_secretary_only: bool = False


@dataclass
class DepartmentTemplate:
    """部署テンプレート."""

    name: str
    code: str
    description: str
    teams: list[TeamTemplate] = field(default_factory=list)


@dataclass
class TeamTemplate:
    """チームテンプレート."""

    name: str
    purpose: str
    agents: list[AgentTemplate] = field(default_factory=list)


@dataclass
class AgentTemplate:
    """エージェントテンプレート."""

    name: str
    title: str
    description: str
    agent_type: str = "llm"
    runtime_type: str = "api"
    provider_name: str = "openrouter"
    autonomy_level: str = "supervised"
    can_delegate: bool = False


@dataclass
class OrgBlueprint:
    """生成された組織設計図."""

    departments: list[DepartmentTemplate]
    secretary_agent: AgentTemplate | None = None


# ---------------------------------------------------------------------------
# 部署テンプレート定義
# ---------------------------------------------------------------------------

SECRETARY_DEPT = DepartmentTemplate(
    name="秘書室",
    code="SEC",
    description="CEO の思考整理・タスク管理・スケジュール調整を担当",
    teams=[
        TeamTemplate(
            name="秘書チーム",
            purpose="CEO のあらゆる情報を整理・蓄積し、業務効率を最大化する",
            agents=[
                AgentTemplate(
                    name="秘書",
                    title="Chief Secretary",
                    description="CEO の思考・アイデア・ToDo の整理、スケジュール管理、情報の蓄積と活用を担当。"
                    "CEO の脳内を理解し、コンテキストを活用して最適な提案を行う。",
                    autonomy_level="semi-autonomous",
                    can_delegate=True,
                ),
            ],
        ),
    ],
)

PM_DEPT = DepartmentTemplate(
    name="プロダクトマネジメント部",
    code="PM",
    description="プロジェクト全体の進捗管理・優先順位付けを担当",
    teams=[
        TeamTemplate(
            name="PM チーム",
            purpose="会社全体の進捗管理・プロジェクト管理・ロードマップ策定",
            agents=[
                AgentTemplate(
                    name="プロダクトマネージャー",
                    title="Product Manager",
                    description="プロジェクトの進捗管理、優先順位付け、タスクの割り振りを行う。",
                    autonomy_level="semi-autonomous",
                    can_delegate=True,
                ),
            ],
        ),
    ],
)

RESEARCH_DEPT = DepartmentTemplate(
    name="リサーチ部",
    code="RES",
    description="市場調査・競合分析・トレンド調査を担当",
    teams=[
        TeamTemplate(
            name="リサーチチーム",
            purpose="競合調査・トレンド分析・市場リサーチ",
            agents=[
                AgentTemplate(
                    name="リサーチアナリスト",
                    title="Research Analyst",
                    description="競合調査、トレンド分析、市場データの収集と分析を行う。",
                    autonomy_level="supervised",
                ),
            ],
        ),
    ],
)

MARKETING_DEPT = DepartmentTemplate(
    name="マーケティング部",
    code="MKT",
    description="集客・SNS運用・コンテンツマーケティングを担当",
    teams=[
        TeamTemplate(
            name="マーケティングチーム",
            purpose="SNS 運用・コンテンツ企画・集客施策の立案と実行",
            agents=[
                AgentTemplate(
                    name="マーケター",
                    title="Marketing Specialist",
                    description="SNS コンテンツの企画、投稿案の作成、集客施策の立案を行う。",
                    autonomy_level="supervised",
                ),
            ],
        ),
    ],
)

DEVELOPMENT_DEPT = DepartmentTemplate(
    name="開発部",
    code="DEV",
    description="プロダクト開発・技術調査を担当",
    teams=[
        TeamTemplate(
            name="開発チーム",
            purpose="プロダクト開発・技術調査・コードレビュー",
            agents=[
                AgentTemplate(
                    name="エンジニア",
                    title="Software Engineer",
                    description="プロダクトの開発、技術調査、コードレビュー、バグ修正を行う。",
                    autonomy_level="supervised",
                ),
            ],
        ),
    ],
)

FINANCE_DEPT = DepartmentTemplate(
    name="経理・ファイナンス部",
    code="FIN",
    description="売上分析・コスト管理・予算管理を担当",
    teams=[
        TeamTemplate(
            name="経理チーム",
            purpose="売上データ分析・支出管理・予算策定",
            agents=[
                AgentTemplate(
                    name="経理担当",
                    title="Finance Analyst",
                    description="売上データの分析、支出の最適化提案、予算管理を行う。",
                    autonomy_level="supervised",
                ),
            ],
        ),
    ],
)

SUPPORT_DEPT = DepartmentTemplate(
    name="カスタマーサポート部",
    code="CS",
    description="顧客対応・問い合わせ管理を担当",
    teams=[
        TeamTemplate(
            name="サポートチーム",
            purpose="顧客対応・問い合わせ管理・FAQ 管理",
            agents=[
                AgentTemplate(
                    name="サポート担当",
                    title="Customer Support Agent",
                    description="顧客からの問い合わせ対応、FAQ の整備、顧客満足度の向上を担当。",
                    autonomy_level="supervised",
                ),
            ],
        ),
    ],
)

CONTENT_DEPT = DepartmentTemplate(
    name="コンテンツ制作部",
    code="CTN",
    description="記事・動画・デザインなどのコンテンツ制作を担当",
    teams=[
        TeamTemplate(
            name="コンテンツチーム",
            purpose="記事・動画台本・デザイン案・コピーの制作",
            agents=[
                AgentTemplate(
                    name="コンテンツクリエイター",
                    title="Content Creator",
                    description="記事、動画台本、広告コピー、ブログ記事の制作を行う。",
                    autonomy_level="supervised",
                ),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------
# 課題→部署のマッピング
# ---------------------------------------------------------------------------

PAIN_POINT_TO_DEPTS: dict[str, list[DepartmentTemplate]] = {
    PainPoint.TASK_MANAGEMENT: [PM_DEPT],
    PainPoint.CUSTOMER_ACQUISITION: [MARKETING_DEPT, RESEARCH_DEPT],
    PainPoint.CONTENT_CREATION: [CONTENT_DEPT, MARKETING_DEPT],
    PainPoint.DATA_ANALYSIS: [RESEARCH_DEPT, FINANCE_DEPT],
    PainPoint.ACCOUNTING: [FINANCE_DEPT],
    PainPoint.CUSTOMER_SUPPORT: [SUPPORT_DEPT],
    PainPoint.RESEARCH: [RESEARCH_DEPT],
    PainPoint.DEVELOPMENT: [DEVELOPMENT_DEPT],
}

CATEGORY_DEFAULT_DEPTS: dict[str, list[DepartmentTemplate]] = {
    BusinessCategory.TECH_STARTUP: [PM_DEPT, DEVELOPMENT_DEPT, MARKETING_DEPT],
    BusinessCategory.ECOMMERCE: [MARKETING_DEPT, SUPPORT_DEPT, FINANCE_DEPT],
    BusinessCategory.CONTENT_CREATOR: [CONTENT_DEPT, MARKETING_DEPT, RESEARCH_DEPT],
    BusinessCategory.CONSULTING: [RESEARCH_DEPT, PM_DEPT, FINANCE_DEPT],
    BusinessCategory.SAAS: [DEVELOPMENT_DEPT, PM_DEPT, SUPPORT_DEPT, MARKETING_DEPT],
    BusinessCategory.AGENCY: [PM_DEPT, CONTENT_DEPT, MARKETING_DEPT],
    BusinessCategory.MANUFACTURING: [PM_DEPT, FINANCE_DEPT, RESEARCH_DEPT],
    BusinessCategory.EDUCATION: [CONTENT_DEPT, RESEARCH_DEPT, SUPPORT_DEPT],
    BusinessCategory.OTHER: [PM_DEPT, RESEARCH_DEPT],
}


def generate_org_blueprint(answers: OrgInterviewAnswer) -> OrgBlueprint:
    """ヒアリング回答から組織設計図を生成する."""
    if answers.start_with_secretary_only:
        return OrgBlueprint(
            departments=[SECRETARY_DEPT],
            secretary_agent=SECRETARY_DEPT.teams[0].agents[0],
        )

    # 秘書室は常に含める
    dept_set: dict[str, DepartmentTemplate] = {SECRETARY_DEPT.code: SECRETARY_DEPT}

    # 課題ベースで部署を追加
    for pain_point in answers.pain_points:
        for dept in PAIN_POINT_TO_DEPTS.get(pain_point, []):
            dept_set[dept.code] = dept

    # カテゴリデフォルトで補完
    if answers.team_size_preference != "minimal":
        for dept in CATEGORY_DEFAULT_DEPTS.get(answers.business_category, []):
            dept_set[dept.code] = dept

    # full モードなら全部署を追加
    if answers.team_size_preference == "full":
        for dept in [
            PM_DEPT,
            RESEARCH_DEPT,
            MARKETING_DEPT,
            DEVELOPMENT_DEPT,
            FINANCE_DEPT,
            SUPPORT_DEPT,
            CONTENT_DEPT,
        ]:
            dept_set[dept.code] = dept

    departments = list(dept_set.values())

    return OrgBlueprint(
        departments=departments,
        secretary_agent=SECRETARY_DEPT.teams[0].agents[0],
    )


async def apply_org_blueprint(
    db: AsyncSession,
    company_id: str,
    blueprint: OrgBlueprint,
    provider_name: str = "openrouter",
) -> dict:
    """組織設計図を DB に反映する（部署・チーム・エージェントを作成）."""
    cid = uuid.UUID(company_id)
    created_departments: list[dict] = []
    created_teams: list[dict] = []
    created_agents: list[dict] = []

    for dept_tmpl in blueprint.departments:
        dept = Department(
            id=uuid.uuid4(),
            company_id=cid,
            name=dept_tmpl.name,
            code=dept_tmpl.code,
            description=dept_tmpl.description,
        )
        db.add(dept)
        await db.flush()

        dept_info = {
            "id": str(dept.id),
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "teams": [],
        }

        for team_tmpl in dept_tmpl.teams:
            team = Team(
                id=uuid.uuid4(),
                company_id=cid,
                department_id=dept.id,
                name=team_tmpl.name,
                purpose=team_tmpl.purpose,
                status="active",
            )
            db.add(team)
            await db.flush()

            team_info = {
                "id": str(team.id),
                "name": team.name,
                "purpose": team.purpose,
                "agents": [],
            }

            for agent_tmpl in team_tmpl.agents:
                agent = Agent(
                    id=generate_uuid(),
                    company_id=cid,
                    team_id=team.id,
                    name=agent_tmpl.name,
                    title=agent_tmpl.title,
                    description=agent_tmpl.description,
                    agent_type=agent_tmpl.agent_type,
                    runtime_type=agent_tmpl.runtime_type,
                    provider_name=provider_name,
                    status="idle",
                    autonomy_level=agent_tmpl.autonomy_level,
                    can_delegate=agent_tmpl.can_delegate,
                    can_write_external=False,
                    can_spend_budget=False,
                    config_json={},
                )
                db.add(agent)
                await db.flush()

                # リードエージェントに設定
                if not team.lead_agent_id:
                    team.lead_agent_id = agent.id
                    await db.flush()

                agent_info = {
                    "id": str(agent.id),
                    "name": agent.name,
                    "title": agent.title,
                    "status": agent.status,
                }
                team_info["agents"].append(agent_info)
                created_agents.append(agent_info)

            dept_info["teams"].append(team_info)
            created_teams.append(team_info)

        created_departments.append(dept_info)

    # 監査ログ
    audit = AuditLog(
        id=generate_uuid(),
        company_id=cid,
        actor_type="system",
        event_type="org.generated",
        target_type="company",
        target_id=str(cid),
        details_json={
            "departments_count": len(created_departments),
            "teams_count": len(created_teams),
            "agents_count": len(created_agents),
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "departments": created_departments,
        "teams": created_teams,
        "agents": created_agents,
        "total_departments": len(created_departments),
        "total_teams": len(created_teams),
        "total_agents": len(created_agents),
    }
