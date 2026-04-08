"""Company and organization endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.agent import Agent
from app.models.company import Company
from app.models.organization import Department, Team
from app.models.user import User

router = APIRouter()


class CompanyCreate(BaseModel):
    name: str
    slug: str
    mission: str = ""
    description: str = ""


class CompanyResponse(BaseModel):
    id: str
    slug: str
    name: str
    mission: str
    description: str
    status: str
    created_at: datetime


class DashboardSummary(BaseModel):
    active_tickets: int = 0
    pending_approvals: int = 0
    active_agents: int = 0
    recent_heartbeats: int = 0
    total_cost_usd: float = 0.0
    errors_count: int = 0


class OrgChartDepartment(BaseModel):
    id: str
    name: str
    code: str


class OrgChartTeam(BaseModel):
    id: str
    name: str
    purpose: str


class OrgChartAgent(BaseModel):
    id: str
    name: str
    title: str | None
    status: str


class OrgChartResponse(BaseModel):
    departments: list[OrgChartDepartment]
    teams: list[OrgChartTeam]
    agents: list[OrgChartAgent]


class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None


class DepartmentCreateResponse(BaseModel):
    id: str
    name: str


class TeamResponse(BaseModel):
    id: str
    name: str
    purpose: str
    status: str


class TeamCreateResponse(BaseModel):
    id: str
    name: str


@router.get("", response_model=list[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List companies."""
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = result.scalars().all()
    return [
        CompanyResponse(
            id=str(c.id),
            slug=c.slug,
            name=c.name,
            mission=c.mission or "",
            description=c.description or "",
            status=c.status,
            created_at=c.created_at,
        )
        for c in companies
    ]


@router.post("", response_model=CompanyResponse)
async def create_company(
    req: CompanyCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Create a new company."""
    company = Company(
        id=uuid.uuid4(),
        slug=req.slug,
        name=req.name,
        mission=req.mission,
        description=req.description,
        status="active",
    )
    db.add(company)
    await db.flush()
    return CompanyResponse(
        id=str(company.id),
        slug=company.slug,
        name=company.name,
        mission=company.mission or "",
        description=company.description or "",
        status=company.status,
        created_at=company.created_at,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get company details."""
    result = await db.execute(select(Company).where(Company.id == uuid.UUID(company_id)))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(
        id=str(company.id),
        slug=company.slug,
        name=company.name,
        mission=company.mission or "",
        description=company.description or "",
        status=company.status,
        created_at=company.created_at,
    )


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    mission: str | None = None
    description: str | None = None


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    req: CompanyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update company details (name, mission, description)."""
    result = await db.execute(select(Company).where(Company.id == uuid.UUID(company_id)))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if req.name is not None:
        company.name = req.name
    if req.mission is not None:
        company.mission = req.mission
    if req.description is not None:
        company.description = req.description
    await db.commit()
    await db.refresh(company)
    return CompanyResponse(
        id=str(company.id),
        slug=company.slug,
        name=company.name,
        mission=company.mission or "",
        description=company.description or "",
        status=company.status,
        created_at=company.created_at,
    )


@router.get("/{company_id}/org-chart", response_model=OrgChartResponse)
async def get_org_chart(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get organization chart."""
    cid = uuid.UUID(company_id)
    depts = (
        (await db.execute(select(Department).where(Department.company_id == cid))).scalars().all()
    )
    teams = (await db.execute(select(Team).where(Team.company_id == cid))).scalars().all()
    agents = (await db.execute(select(Agent).where(Agent.company_id == cid))).scalars().all()
    return {
        "departments": [{"id": str(d.id), "name": d.name, "code": d.code} for d in depts],
        "teams": [{"id": str(t.id), "name": t.name, "purpose": t.purpose} for t in teams],
        "agents": [
            {"id": str(a.id), "name": a.name, "title": a.title, "status": a.status} for a in agents
        ],
    }


@router.get("/{company_id}/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get dashboard summary."""
    return DashboardSummary()


@router.get("/{company_id}/departments", response_model=list[DepartmentResponse])
async def list_departments(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List departments."""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(Department).where(Department.company_id == cid))
    depts = result.scalars().all()
    return [
        {"id": str(d.id), "name": d.name, "code": d.code, "description": d.description}
        for d in depts
    ]


@router.post("/{company_id}/departments", response_model=DepartmentCreateResponse)
async def create_department(
    company_id: str,
    name: str = "",
    code: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a department."""
    dept = Department(id=uuid.uuid4(), company_id=uuid.UUID(company_id), name=name, code=code)
    db.add(dept)
    await db.flush()
    return {"id": str(dept.id), "name": dept.name}


@router.get("/{company_id}/teams", response_model=list[TeamResponse])
async def list_teams(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List teams."""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(Team).where(Team.company_id == cid))
    teams = result.scalars().all()
    return [
        {"id": str(t.id), "name": t.name, "purpose": t.purpose, "status": t.status} for t in teams
    ]


@router.post("/{company_id}/teams", response_model=TeamCreateResponse)
async def create_team(
    company_id: str,
    name: str = "",
    purpose: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a team."""
    team = Team(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        name=name,
        purpose=purpose,
        status="active",
    )
    db.add(team)
    await db.flush()
    return {"id": str(team.id), "name": team.name}
