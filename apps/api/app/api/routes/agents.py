"""Agent management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.agent import Agent

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    title: str = ""
    description: str = ""
    agent_type: str = "llm"
    runtime_type: str = "api"
    provider_name: str = "openrouter"
    model_name: str | None = None
    autonomy_level: str = "supervised"


class AgentResponse(BaseModel):
    id: str
    name: str
    title: str
    agent_type: str
    provider_name: str
    model_name: str | None
    status: str
    autonomy_level: str


@router.get("/companies/{company_id}/agents", response_model=list[AgentResponse])
async def list_agents(company_id: str, db: AsyncSession = Depends(get_db)):
    """エージェント一覧"""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(Agent).where(Agent.company_id == cid))
    agents = result.scalars().all()
    return [
        AgentResponse(
            id=str(a.id),
            name=a.name,
            title=a.title or "",
            agent_type=a.agent_type,
            provider_name=a.provider_name,
            model_name=a.model_name,
            status=a.status,
            autonomy_level=a.autonomy_level,
        )
        for a in agents
    ]


@router.post("/companies/{company_id}/agents", response_model=AgentResponse)
async def create_agent(
    company_id: str, req: AgentCreate, db: AsyncSession = Depends(get_db)
):
    """エージェント作成"""
    agent = Agent(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        name=req.name,
        title=req.title,
        description=req.description,
        agent_type=req.agent_type,
        runtime_type=req.runtime_type,
        provider_name=req.provider_name,
        model_name=req.model_name,
        status="provisioning",
        autonomy_level=req.autonomy_level,
        can_delegate=False,
        can_write_external=False,
        can_spend_budget=False,
    )
    db.add(agent)
    await db.flush()
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        title=agent.title or "",
        agent_type=agent.agent_type,
        provider_name=agent.provider_name,
        model_name=agent.model_name,
        status=agent.status,
        autonomy_level=agent.autonomy_level,
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """エージェント詳細"""
    result = await db.execute(select(Agent).where(Agent.id == uuid.UUID(agent_id)))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        title=agent.title or "",
        agent_type=agent.agent_type,
        provider_name=agent.provider_name,
        model_name=agent.model_name,
        status=agent.status,
        autonomy_level=agent.autonomy_level,
    )


@router.post("/agents/{agent_id}/pause")
async def pause_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """エージェントを一時停止"""
    result = await db.execute(select(Agent).where(Agent.id == uuid.UUID(agent_id)))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "paused"
    return {"status": "paused"}


@router.post("/agents/{agent_id}/resume")
async def resume_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """エージェントを再開"""
    result = await db.execute(select(Agent).where(Agent.id == uuid.UUID(agent_id)))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "active"
    return {"status": "active"}
