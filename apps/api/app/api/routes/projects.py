"""Project and goal endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.project import Goal, Project
from app.models.user import User

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    goal: str = ""
    description: str = ""
    priority: str = "medium"


class GoalCreate(BaseModel):
    title: str
    description: str = ""
    goal_level: str = "project"


class ProjectResponse(BaseModel):
    id: str
    name: str
    goal: str = ""
    priority: str = "medium"
    status: str = "active"


class ProjectCreateResponse(BaseModel):
    id: str
    name: str


class GoalResponse(BaseModel):
    id: str
    title: str
    goal_level: str = "project"
    status: str = "active"


class GoalCreateResponse(BaseModel):
    id: str
    title: str


@router.get("/companies/{company_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    company_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List projects."""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(Project).where(Project.company_id == cid))
    projects = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "goal": p.goal,
            "priority": p.priority,
            "status": p.status,
        }
        for p in projects
    ]


@router.post("/companies/{company_id}/projects", response_model=ProjectCreateResponse)
async def create_project(
    company_id: str,
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a project."""
    project = Project(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        name=req.name,
        goal=req.goal,
        description=req.description,
        priority=req.priority,
        status="active",
    )
    db.add(project)
    await db.flush()
    return {"id": str(project.id), "name": project.name}


@router.get("/projects/{project_id}/goals", response_model=list[GoalResponse])
async def list_goals(
    project_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """List project goals."""
    pid = uuid.UUID(project_id)
    result = await db.execute(select(Goal).where(Goal.project_id == pid))
    goals = result.scalars().all()
    return [
        {
            "id": str(g.id),
            "title": g.title,
            "goal_level": g.goal_level,
            "status": g.status,
        }
        for g in goals
    ]


@router.post("/projects/{project_id}/goals", response_model=GoalCreateResponse)
async def create_goal(
    project_id: str,
    req: GoalCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a goal."""
    goal = Goal(
        id=uuid.uuid4(),
        project_id=uuid.UUID(project_id),
        title=req.title,
        description=req.description,
        goal_level=req.goal_level,
        status="active",
    )
    db.add(goal)
    await db.flush()
    return {"id": str(goal.id), "title": goal.title}
