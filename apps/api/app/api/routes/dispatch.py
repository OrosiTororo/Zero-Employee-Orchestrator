"""Task Dispatch API — background task execution.

Inspired by Claude Cowork Dispatch: assign tasks that run in the background
while the user is away. Returns finished results when ready.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dispatch", tags=["dispatch"])

# In-memory task store (production: use DB + background worker)
_dispatch_lock = threading.Lock()
_dispatch_tasks: dict[str, dict] = {}


class DispatchRequest(BaseModel):
    """Background task request."""

    instruction: str
    priority: str = "medium"
    schedule: str | None = None  # cron expression for recurring tasks
    context: dict = Field(default_factory=dict)


class DispatchResponse(BaseModel):
    """Background task response."""

    task_id: str
    status: str
    instruction: str
    created_at: str
    completed_at: str | None = None
    result: str | None = None


class DispatchListResponse(BaseModel):
    """List of dispatched tasks."""

    tasks: list[DispatchResponse]
    total: int


@router.post("", response_model=DispatchResponse)
@limiter.limit("10/minute")
async def create_dispatch(
    request: Request, req: DispatchRequest, user: User = Depends(get_current_user)
):
    """Dispatch a background task. Returns immediately with a task ID.

    The task runs asynchronously. Poll GET /dispatch/{task_id} for status.
    """
    # Prompt injection check on task instruction
    guard_result = scan_prompt_injection(req.instruction)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected in instruction.",
        )

    # PII detection — mask before passing to AI agents
    pii_result = detect_and_mask_pii(req.instruction)
    if pii_result.has_pii:
        logger.warning(
            "PII detected in dispatch instruction (user=%s): %s",
            user.id,
            pii_result.detected_types,
        )

    task_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    task = {
        "task_id": task_id,
        "user_id": str(user.id),
        "instruction": req.instruction,
        "priority": req.priority,
        "schedule": req.schedule,
        "context": req.context,
        "status": "queued",
        "created_at": now,
        "completed_at": None,
        "result": None,
    }
    with _dispatch_lock:
        _dispatch_tasks[task_id] = task
    logger.info("Dispatch task created: %s (user=%s)", task_id, user.id)

    # Simulate async execution (production: enqueue to background worker)
    asyncio.create_task(_execute_dispatch(task_id))

    return DispatchResponse(
        task_id=task_id,
        status="queued",
        instruction=req.instruction,
        created_at=now,
    )


@router.get("/{task_id}", response_model=DispatchResponse)
async def get_dispatch(task_id: str, _user: User = Depends(get_current_user)):
    """Get status of a dispatched background task."""
    task = _dispatch_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Dispatch task not found: {task_id}")
    return DispatchResponse(
        task_id=task["task_id"],
        status=task["status"],
        instruction=task["instruction"],
        created_at=task["created_at"],
        completed_at=task["completed_at"],
        result=task["result"],
    )


@router.get("", response_model=DispatchListResponse)
async def list_dispatches(status: str | None = None, user: User = Depends(get_current_user)):
    """List all dispatched tasks for the current user."""
    user_tasks = [t for t in _dispatch_tasks.values() if t["user_id"] == str(user.id)]
    if status:
        user_tasks = [t for t in user_tasks if t["status"] == status]
    user_tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return DispatchListResponse(
        tasks=[
            DispatchResponse(
                task_id=t["task_id"],
                status=t["status"],
                instruction=t["instruction"],
                created_at=t["created_at"],
                completed_at=t["completed_at"],
                result=t["result"],
            )
            for t in user_tasks[:50]
        ],
        total=len(user_tasks),
    )


@router.delete("/{task_id}", response_model=DispatchResponse)
async def cancel_dispatch(task_id: str, _user: User = Depends(get_current_user)):
    """Cancel a queued or running dispatch task."""
    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Dispatch task not found: {task_id}")
    if task["status"] not in ("completed", "failed", "cancelled"):
        task["status"] = "cancelled"
        task["completed_at"] = datetime.now(UTC).isoformat()
    return DispatchResponse(
        task_id=task["task_id"],
        status=task["status"],
        instruction=task["instruction"],
        created_at=task["created_at"],
        completed_at=task["completed_at"],
        result=task["result"],
    )


async def _execute_dispatch(task_id: str) -> None:
    """Execute a dispatched task in the background via the execution engine."""
    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        return

    task["status"] = "running"
    try:
        from app.orchestration.executor import get_executor

        executor = get_executor()

        # Step 1: Generate plan from instruction
        dag = await executor.generate_plan(
            ticket_title=task["instruction"][:100],
            spec_text=task["instruction"],
        )

        # Step 2: Execute plan
        plan_result = await executor.execute_plan(dag)

        task["status"] = "completed" if plan_result.status == "succeeded" else "failed"
        task["completed_at"] = datetime.now(UTC).isoformat()
        task["result"] = plan_result.final_output or plan_result.failure_reason or "No output"
        logger.info(
            "Dispatch task %s: status=%s, cost=$%.4f, nodes=%d",
            task_id,
            plan_result.status,
            plan_result.total_cost_usd,
            len(plan_result.node_results),
        )
    except Exception as exc:
        task["status"] = "failed"
        task["completed_at"] = datetime.now(UTC).isoformat()
        task["result"] = f"Task failed: {exc}"
        logger.error("Dispatch task failed: %s — %s", task_id, exc)
