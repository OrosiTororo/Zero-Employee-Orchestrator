"""iPaaS workflow management API endpoints.

API for registering, triggering, and managing workflows for n8n / Zapier / Make.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.integrations.ipaas import (
    IPaaSProvider,
    IPaaSWorkflow,
    WebhookTrigger,
    ipaas_service,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ipaas", tags=["ipaas"])


# ------------------------------------------------------------------ #
#  Request / Response schemas
# ------------------------------------------------------------------ #


class WebhookTriggerSchema(BaseModel):
    """Webhook trigger settings."""

    url: str
    method: str = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    payload_template: dict[str, Any] = Field(default_factory=dict)


class WorkflowCreateRequest(BaseModel):
    """Workflow registration request."""

    name: str
    provider: str
    triggers: list[WebhookTriggerSchema] = Field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowTriggerRequest(BaseModel):
    """Workflow trigger request."""

    payload: dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------ #
#  Response schemas
# ------------------------------------------------------------------ #


class WorkflowRegisterResponse(BaseModel):
    """Response for workflow registration."""

    workflow_id: str
    name: str
    provider: str
    status: str


class WorkflowItem(BaseModel):
    """Single workflow in list response."""

    id: str
    name: str
    provider: str
    status: str
    description: str
    trigger_count: int
    run_count: int
    last_run_at: str | None = None
    created_at: str | None = None


class WorkflowListResponse(BaseModel):
    """Response for listing workflows."""

    workflows: list[WorkflowItem]
    count: int


class WorkflowTriggerResponse(BaseModel):
    """Response for workflow trigger."""

    workflow_id: str
    run_id: str | None = None
    success: bool
    status_code: int | None = None
    error: str | None = None
    latency_ms: float | None = None


class WorkflowStatusResponse(BaseModel):
    """Response for workflow status."""

    workflow_id: str | None = None
    status: str | None = None
    last_run_at: str | None = None
    run_count: int | None = None


class WorkflowRemoveResponse(BaseModel):
    """Response for workflow removal."""

    workflow_id: str
    status: str


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #


@router.post("/workflows", response_model=WorkflowRegisterResponse)
async def register_workflow(
    req: WorkflowCreateRequest, user: User = Depends(get_current_user)
) -> dict:
    """Register a workflow."""
    try:
        provider = IPaaSProvider(req.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(f"Invalid provider: {req.provider}. Valid: {[p.value for p in IPaaSProvider]}"),
        )

    triggers = [
        WebhookTrigger(
            url=t.url,
            method=t.method,
            headers=t.headers,
            payload_template=t.payload_template,
        )
        for t in req.triggers
    ]

    workflow = IPaaSWorkflow(
        id="",
        name=req.name,
        provider=provider,
        triggers=triggers,
        description=req.description,
        metadata=req.metadata,
    )

    workflow_id = ipaas_service.register_workflow(workflow)
    logger.info("Workflow registered via API: %s (%s)", req.name, req.provider)

    return {
        "workflow_id": workflow_id,
        "name": req.name,
        "provider": provider.value,
        "status": "registered",
    }


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    provider: str | None = None, user: User = Depends(get_current_user)
) -> dict:
    """Return list of registered workflows."""
    filter_provider: IPaaSProvider | None = None
    if provider:
        try:
            filter_provider = IPaaSProvider(provider)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {provider}",
            )

    workflows = ipaas_service.list_workflows(provider=filter_provider)
    return {
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "provider": w.provider.value,
                "status": w.status.value,
                "description": w.description,
                "trigger_count": len(w.triggers),
                "run_count": w.run_count,
                "last_run_at": w.last_run_at,
                "created_at": w.created_at,
            }
            for w in workflows
        ],
        "count": len(workflows),
    }


@router.post("/workflows/{workflow_id}/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow(
    workflow_id: str, req: WorkflowTriggerRequest, user: User = Depends(get_current_user)
) -> dict:
    """Trigger a workflow."""
    result = await ipaas_service.trigger_workflow(workflow_id, req.payload)

    if not result.success and not result.run_id:
        raise HTTPException(status_code=404, detail=result.error)

    return {
        "workflow_id": workflow_id,
        "run_id": result.run_id,
        "success": result.success,
        "status_code": result.status_code,
        "error": result.error,
        "latency_ms": result.latency_ms,
    }


@router.get("/workflows/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str, user: User = Depends(get_current_user)) -> dict:
    """Get workflow status."""
    status = await ipaas_service.sync_status(workflow_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@router.delete("/workflows/{workflow_id}", response_model=WorkflowRemoveResponse)
async def remove_workflow(workflow_id: str, user: User = Depends(get_current_user)) -> dict:
    """Delete a workflow."""
    removed = ipaas_service.remove_workflow(workflow_id)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}",
        )
    return {"workflow_id": workflow_id, "status": "removed"}
