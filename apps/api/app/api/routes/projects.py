"""Project and goal endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.project import Goal, Project

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


@router.get("/companies/{company_id}/projects")
async def list_projects(company_id: str, db: AsyncSession = Depends(get_db)):
    """プロジェクト一覧"""
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


@router.post("/companies/{company_id}/projects")
async def create_project(
    company_id: str, req: ProjectCreate, db: AsyncSession = Depends(get_db)
):
    """プロジェクト作成"""
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


@router.get("/projects/{project_id}/goals")
async def list_goals(project_id: str, db: AsyncSession = Depends(get_db)):
    """プロジェクトの目標一覧"""
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


@router.post("/projects/{project_id}/goals")
async def create_goal(
    project_id: str, req: GoalCreate, db: AsyncSession = Depends(get_db)
):
    """目標作成"""
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
