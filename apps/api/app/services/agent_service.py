"""Agent lifecycle service with state machine enforcement."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.agent import Agent
from app.models.audit import AuditLog
from app.orchestration.state_machine import AgentStateMachine

# Re-export from the canonical source
AGENT_TRANSITIONS = AgentStateMachine.transitions


def validate_agent_transition(current: str, target: str) -> bool:
    """エージェントの状態遷移が有効か検証する."""
    return target in AGENT_TRANSITIONS.get(current, [])


async def provision_agent(
    db: AsyncSession,
    company_id: str,
    name: str,
    title: str,
    agent_type: str,
    runtime_type: str,
    provider_name: str,
    autonomy_level: str,
    *,
    team_id: str | None = None,
    model_name: str | None = None,
    description: str | None = None,
    can_delegate: bool = False,
    can_write_external: bool = False,
    can_spend_budget: bool = False,
    config_json: dict | None = None,
) -> Agent:
    """新規エージェントをプロビジョニングする."""
    agent = Agent(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        team_id=uuid.UUID(team_id) if team_id else None,
        name=name,
        title=title,
        description=description,
        agent_type=agent_type,
        runtime_type=runtime_type,
        provider_name=provider_name,
        model_name=model_name,
        status="provisioning",
        autonomy_level=autonomy_level,
        can_delegate=can_delegate,
        can_write_external=can_write_external,
        can_spend_budget=can_spend_budget,
        config_json=config_json or {},
    )
    db.add(agent)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=uuid.UUID(company_id),
        actor_type="system",
        event_type="agent.provisioned",
        target_type="agent",
        target_id=agent.id,
        details_json={"name": name, "agent_type": agent_type},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(agent)
    return agent


async def activate_agent(
    db: AsyncSession,
    agent: Agent,
) -> Agent:
    """エージェントをアクティブ (idle) 状態にする."""
    if not validate_agent_transition(agent.status, "idle"):
        raise ValueError(f"Cannot activate agent in status: {agent.status}")

    old_status = agent.status
    agent.status = "idle"

    audit = AuditLog(
        id=generate_uuid(),
        company_id=agent.company_id,
        actor_type="system",
        event_type="agent.activated",
        target_type="agent",
        target_id=agent.id,
        details_json={"old_status": old_status},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(agent)
    return agent


async def assign_agent_task(
    db: AsyncSession,
    agent: Agent,
) -> Agent:
    """エージェントをビジー状態にする (タスク割当時)."""
    if not validate_agent_transition(agent.status, "busy"):
        raise ValueError(f"Cannot assign task to agent in status: {agent.status}")

    agent.status = "busy"

    audit = AuditLog(
        id=generate_uuid(),
        company_id=agent.company_id,
        actor_type="system",
        event_type="agent.busy",
        target_type="agent",
        target_id=agent.id,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(agent)
    return agent


async def release_agent(
    db: AsyncSession,
    agent: Agent,
) -> Agent:
    """エージェントをアイドル状態に戻す (タスク完了時)."""
    if not validate_agent_transition(agent.status, "idle"):
        raise ValueError(f"Cannot release agent in status: {agent.status}")

    agent.status = "idle"

    audit = AuditLog(
        id=generate_uuid(),
        company_id=agent.company_id,
        actor_type="system",
        event_type="agent.released",
        target_type="agent",
        target_id=agent.id,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(agent)
    return agent


async def decommission_agent(
    db: AsyncSession,
    agent: Agent,
    reason: str = "",
) -> Agent:
    """エージェントを廃止する."""
    if not validate_agent_transition(agent.status, "decommissioned"):
        raise ValueError(f"Cannot decommission agent in status: {agent.status}")

    old_status = agent.status
    agent.status = "decommissioned"

    audit = AuditLog(
        id=generate_uuid(),
        company_id=agent.company_id,
        actor_type="system",
        event_type="agent.decommissioned",
        target_type="agent",
        target_id=agent.id,
        details_json={"old_status": old_status, "reason": reason},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(agent)
    return agent


async def get_available_agents(
    db: AsyncSession,
    company_id: str,
    agent_type: str | None = None,
) -> list[Agent]:
    """利用可能な (idle 状態の) エージェントを取得."""
    stmt = select(Agent).where(
        Agent.company_id == uuid.UUID(company_id),
        Agent.status == "idle",
    )
    if agent_type:
        stmt = stmt.where(Agent.agent_type == agent_type)

    result = await db.execute(stmt)
    return list(result.scalars().all())
