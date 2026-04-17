"""External agent-framework adapter management endpoints.

Exposes the agent_adapter_registry so users can:
- List installed / installable frameworks (CrewAI, AutoGen, LangChain, Dify, n8n, OpenClaw)
- Switch the active framework
- Delegate a task to a specific framework under approval + audit gates
- Health-check running frameworks
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User
from app.tools.agent_adapter import (
    _FRAMEWORK_ADAPTERS,
    AgentTask,
    agent_adapter_registry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-adapters", tags=["agent-adapters"])


class AdapterExecuteRequest(BaseModel):
    framework: str | None = Field(
        default=None,
        description="Framework to delegate to. Falls back to the active adapter if omitted.",
    )
    instruction: str = Field(..., description="Natural-language instruction for the sub-agent.")
    context: dict[str, Any] = Field(default_factory=dict)
    tools: list[str] = Field(default_factory=list)
    max_steps: int = 50
    timeout_seconds: int = 300
    require_approval: bool = True


class AdapterRegisterRequest(BaseModel):
    framework: str = Field(
        ..., description="One of: crewai, autogen, langchain, openclaw, dify, n8n"
    )
    config: dict[str, Any] = Field(default_factory=dict)


@router.get("/installable")
async def list_installable(_: User = Depends(get_current_user)) -> dict:
    """Enumerate every agent framework ZEO knows how to delegate to."""
    return {"installable": agent_adapter_registry.list_installable()}


@router.get("")
async def list_adapters(_: User = Depends(get_current_user)) -> dict:
    """Currently-registered adapters."""
    return {"adapters": agent_adapter_registry.list_adapters()}


@router.post("/register")
async def register_adapter(
    request: AdapterRegisterRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Instantiate and register a built-in framework adapter."""
    if request.framework not in _FRAMEWORK_ADAPTERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown framework '{request.framework}'. "
            f"Supported: {sorted(k.value for k in _FRAMEWORK_ADAPTERS)}",
        )
    agent_adapter_registry.register(request.framework, config=request.config)
    return {"registered": request.framework, "active": True}


@router.post("/{framework}/activate")
async def activate_adapter(framework: str, _: User = Depends(get_current_user)) -> dict:
    """Make the given adapter the default for subsequent task executions."""
    if not agent_adapter_registry.set_active(framework):
        raise HTTPException(
            status_code=404,
            detail=f"Adapter not registered: {framework}. Register it first via POST /agent-adapters/register.",
        )
    return {"active": framework}


@router.get("/health")
async def health(
    framework: str | None = None,
    _: User = Depends(get_current_user),
) -> dict:
    """Health-check a specific framework or all registered adapters."""
    return await agent_adapter_registry.health_check(framework)


@router.post("/execute")
async def execute(
    request: AdapterExecuteRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Delegate a task to an external agent framework.

    Goes through approval-gate + audit logging via AgentAdapterRegistry.execute_task.
    """
    task = AgentTask(
        instruction=request.instruction,
        context=request.context,
        tools=request.tools,
        max_steps=request.max_steps,
        timeout_seconds=request.timeout_seconds,
        require_approval=request.require_approval,
        framework=request.framework or "",
    )
    result = await agent_adapter_registry.execute_task(task)
    return {
        "id": result.id,
        "framework": result.framework,
        "status": result.status.value,
        "result": result.result,
        "error": result.error,
        "token_usage": result.token_usage,
        "cost_estimate": result.cost_estimate,
        "created_at": result.created_at,
        "completed_at": result.completed_at,
    }


@router.get("/history")
async def history(limit: int = 50, _: User = Depends(get_current_user)) -> dict:
    """Recent task executions across all frameworks."""
    return {"history": agent_adapter_registry.get_task_history(limit=limit)}
