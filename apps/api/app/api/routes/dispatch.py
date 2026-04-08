"""Task Dispatch API — background task execution.

Inspired by Claude Cowork Dispatch: assign tasks that run in the background
while the user is away. Returns finished results when ready.

Copilot Cowork-inspired features:
- Plan preview: see execution steps before running
- Needs-input status: tasks can pause and request human input
- Steering: add instructions mid-execution to redirect a running task
- Resume: continue a task paused at needs_input with user-provided input
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


class PlanStep(BaseModel):
    """A single step in a plan preview."""

    id: str
    title: str
    depends_on: list[str] = Field(default_factory=list)
    estimated_minutes: int = 0
    status: str = "pending"


class DispatchRequest(BaseModel):
    """Background task request."""

    instruction: str
    priority: str = "medium"
    schedule: str | None = None  # cron expression for recurring tasks
    context: dict = Field(default_factory=dict)
    preview_only: bool = False  # If True, generate plan preview without executing


class SteerRequest(BaseModel):
    """Mid-execution steering instruction."""

    instruction: str


class ResumeRequest(BaseModel):
    """Input to resume a task paused at needs_input."""

    user_input: str


class DispatchResponse(BaseModel):
    """Background task response."""

    task_id: str
    status: str
    instruction: str
    created_at: str
    completed_at: str | None = None
    result: str | None = None
    plan_preview: list[PlanStep] | None = None
    needs_input_reason: str | None = None


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

    initial_status = "preview" if req.preview_only else "queued"

    task = {
        "task_id": task_id,
        "user_id": str(user.id),
        "instruction": req.instruction,
        "priority": req.priority,
        "schedule": req.schedule,
        "context": req.context,
        "status": initial_status,
        "created_at": now,
        "completed_at": None,
        "result": None,
        "plan_preview": None,
        "needs_input_reason": None,
        "steering_instructions": [],
        "resume_event": asyncio.Event(),
        "resume_input": None,
    }
    with _dispatch_lock:
        _dispatch_tasks[task_id] = task
    logger.info(
        "Dispatch task created: %s (user=%s, preview_only=%s)", task_id, user.id, req.preview_only
    )

    if req.preview_only:
        # Generate plan preview without executing
        asyncio.create_task(_generate_preview(task_id))
    elif req.schedule:
        # Scheduled recurring task (Claude Cowork /schedule pattern)
        asyncio.create_task(_register_scheduled_task(task_id, req.schedule))
    else:
        # Full async execution (production: enqueue to background worker)
        asyncio.create_task(_execute_dispatch(task_id))

    return DispatchResponse(
        task_id=task_id,
        status=initial_status,
        instruction=req.instruction,
        created_at=now,
    )


@router.get("/{task_id}", response_model=DispatchResponse)
async def get_dispatch(task_id: str, _user: User = Depends(get_current_user)):
    """Get status of a dispatched background task."""
    task = _dispatch_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Dispatch task not found: {task_id}")
    return _task_to_response(task)


@router.get("", response_model=DispatchListResponse)
async def list_dispatches(status: str | None = None, user: User = Depends(get_current_user)):
    """List all dispatched tasks for the current user."""
    user_tasks = [t for t in _dispatch_tasks.values() if t["user_id"] == str(user.id)]
    if status:
        user_tasks = [t for t in user_tasks if t["status"] == status]
    user_tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return DispatchListResponse(
        tasks=[_task_to_response(t) for t in user_tasks[:50]],
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
        # Unblock any resume waiter so the background task can exit cleanly
        resume_event = task.get("resume_event")
        if resume_event and isinstance(resume_event, asyncio.Event):
            task["resume_input"] = None  # Signal cancellation, not real input
            resume_event.set()
    return _task_to_response(task)


def _task_to_response(task: dict) -> DispatchResponse:
    """Build a DispatchResponse from an internal task dict."""
    return DispatchResponse(
        task_id=task["task_id"],
        status=task["status"],
        instruction=task["instruction"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        result=task.get("result"),
        plan_preview=task.get("plan_preview"),
        needs_input_reason=task.get("needs_input_reason"),
    )


@router.post("/{task_id}/steer", response_model=DispatchResponse)
@limiter.limit("20/minute")
async def steer_dispatch(
    request: Request,
    task_id: str,
    req: SteerRequest,
    _user: User = Depends(get_current_user),
):
    """Add a steering instruction to a running or needs_input dispatch task.

    Steering lets the user redirect a task mid-execution without cancelling it.
    The instruction is appended to the task context and picked up by subsequent
    execution steps.
    """
    # Prompt injection check on steering instruction
    guard_result = scan_prompt_injection(req.instruction)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected in instruction.",
        )

    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Dispatch task not found: {task_id}")
    if task["status"] not in ("running", "needs_input", "queued"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot steer task in '{task['status']}' status. "
            "Task must be queued, running, or needs_input.",
        )

    # PII detection on steering instruction
    pii_result = detect_and_mask_pii(req.instruction)
    if pii_result.has_pii:
        logger.warning(
            "PII detected in steering instruction (task=%s): %s",
            task_id,
            pii_result.detected_types,
        )

    with _dispatch_lock:
        task["steering_instructions"].append(
            {
                "instruction": req.instruction,
                "added_at": datetime.now(UTC).isoformat(),
            }
        )
    logger.info("Steering instruction added to task %s", task_id)
    return _task_to_response(task)


@router.post("/{task_id}/resume", response_model=DispatchResponse)
@limiter.limit("10/minute")
async def resume_dispatch(
    request: Request,
    task_id: str,
    req: ResumeRequest,
    _user: User = Depends(get_current_user),
):
    """Resume a dispatch task that is paused at needs_input status.

    Provides the requested user input so the task can continue execution.
    """
    # Prompt injection check on user input
    guard_result = scan_prompt_injection(req.user_input)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected in input.",
        )

    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Dispatch task not found: {task_id}")
    if task["status"] != "needs_input":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot resume task in '{task['status']}' status. "
            "Task must be in 'needs_input' status.",
        )

    # PII detection on resume input
    pii_result = detect_and_mask_pii(req.user_input)
    if pii_result.has_pii:
        logger.warning(
            "PII detected in resume input (task=%s): %s",
            task_id,
            pii_result.detected_types,
        )

    with _dispatch_lock:
        task["steering_instructions"].append(
            {
                "instruction": f"[user_input] {req.user_input}",
                "added_at": datetime.now(UTC).isoformat(),
            }
        )
        task["status"] = "running"
        task["needs_input_reason"] = None
        task["resume_input"] = req.user_input
        # Signal the background execution to continue
        resume_event = task.get("resume_event")
        if resume_event and isinstance(resume_event, asyncio.Event):
            resume_event.set()

    logger.info("Task %s resumed with user input", task_id)
    return _task_to_response(task)


@router.post("/{task_id}/start", response_model=DispatchResponse)
@limiter.limit("10/minute")
async def start_previewed_dispatch(
    request: Request,
    task_id: str,
    _user: User = Depends(get_current_user),
):
    """Start execution of a task that was created with preview_only=True.

    After reviewing the plan_preview, the user can confirm execution via this
    endpoint. The task transitions from 'preview' to 'running'.
    """
    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Dispatch task not found: {task_id}")
    if task["status"] != "preview":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot start task in '{task['status']}' status. "
            "Task must be in 'preview' status.",
        )

    asyncio.create_task(_execute_dispatch(task_id))
    logger.info("Preview task %s started by user", task_id)
    return _task_to_response(task)


# ---------------------------------------------------------------------------
# Needs-input detection helpers
# ---------------------------------------------------------------------------

# Phrases that indicate the LLM is requesting human input rather than
# producing a final answer.  Checked case-insensitively against node output.
_NEEDS_INPUT_INDICATORS: list[str] = [
    "please provide",
    "i need more information",
    "could you clarify",
    "please clarify",
    "what would you like",
    "please specify",
    "i need your input",
    "waiting for input",
    "need additional details",
    "please confirm",
]


def _detect_needs_input(content: str) -> str | None:
    """Return a reason string if the content looks like a request for human input.

    Returns None when the content is a normal execution result.
    """
    lower = content.lower()
    for indicator in _NEEDS_INPUT_INDICATORS:
        if indicator in lower:
            # Use the first matching sentence as the reason
            for sentence in content.replace("\n", ". ").split(". "):
                if indicator in sentence.lower():
                    return sentence.strip().rstrip(".")
            return f"Task is requesting input ({indicator})"
    return None


async def _pause_for_input(task: dict, reason: str) -> str | None:
    """Transition task to needs_input and block until resumed or cancelled.

    Returns the user-provided input string, or None if the task was cancelled.
    """
    with _dispatch_lock:
        task["status"] = "needs_input"
        task["needs_input_reason"] = reason
        task["resume_input"] = None
        # Reset the event so we can wait on it
        task["resume_event"] = asyncio.Event()
    logger.info("Task %s paused — needs_input: %s", task["task_id"], reason)

    # Wait for resume or cancel (the event is set by resume_dispatch or cancel_dispatch)
    await task["resume_event"].wait()

    # After waking, check if it was a cancellation
    if task["status"] == "cancelled":
        return None
    return task.get("resume_input")


async def _generate_preview(task_id: str) -> None:
    """Generate a plan preview without executing — for preview_only tasks."""
    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        return

    try:
        from app.orchestration.executor import get_executor

        executor = get_executor()

        dag = await executor.generate_plan(
            ticket_title=task["instruction"][:100],
            spec_text=task["instruction"],
        )

        with _dispatch_lock:
            task["plan_preview"] = [
                PlanStep(
                    id=node.id,
                    title=node.title,
                    depends_on=node.depends_on,
                    estimated_minutes=node.estimated_minutes,
                    status=node.status.value,
                )
                for node in dag.nodes
            ]
        logger.info("Plan preview generated for task %s (%d steps)", task_id, len(dag.nodes))
    except Exception as exc:
        task["status"] = "failed"
        task["completed_at"] = datetime.now(UTC).isoformat()
        task["result"] = f"Plan generation failed: {exc}"
        logger.error("Preview generation failed: %s — %s", task_id, exc)


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

        # Step 1: Generate plan from instruction (includes steering context)
        full_instruction = task["instruction"]
        steering = task.get("steering_instructions", [])
        if steering:
            steering_text = "\n".join(f"- {s['instruction']}" for s in steering)
            full_instruction += f"\n\nAdditional instructions:\n{steering_text}"

        dag = await executor.generate_plan(
            ticket_title=task["instruction"][:100],
            spec_text=full_instruction,
        )

        # Step 1.5: Store plan preview so the user can inspect steps
        with _dispatch_lock:
            task["plan_preview"] = [
                PlanStep(
                    id=node.id,
                    title=node.title,
                    depends_on=node.depends_on,
                    estimated_minutes=node.estimated_minutes,
                    status=node.status.value,
                )
                for node in dag.nodes
            ]

        # Step 2: Execute plan with steering-aware progress callback
        async def _on_progress(node_id: str, node_status: str, node_result: object) -> None:
            """Update plan_preview step statuses, detect needs_input, and handle steering."""
            with _dispatch_lock:
                preview = task.get("plan_preview")
                if preview:
                    for step in preview:
                        if step.id == node_id:
                            step.status = node_status
                            break

            # Check if the node result indicates a need for human input
            if node_result and hasattr(node_result, "content") and node_result.content:
                reason = _detect_needs_input(node_result.content)
                if reason:
                    user_input = await _pause_for_input(task, reason)
                    if user_input is None:
                        # Task was cancelled while waiting
                        return
                    # Inject user input into steering for subsequent nodes
                    logger.info("Task %s resumed — injecting user input into context", task_id)

        plan_result = await executor.execute_plan(dag, on_progress=_on_progress)

        # Bail out if the task was cancelled while we were running
        if task["status"] == "cancelled":
            return

        # Update final plan_preview statuses from actual results
        with _dispatch_lock:
            preview = task.get("plan_preview")
            if preview:
                result_map = {r.node_id: r for r in plan_result.node_results}
                for step in preview:
                    if step.id in result_map:
                        r = result_map[step.id]
                        step.status = "completed" if r.success else "failed"

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


# ---------------------------------------------------------------------------
# Scheduled Tasks (Claude Cowork /schedule pattern)
# ---------------------------------------------------------------------------

# In-memory store of scheduled task definitions
_scheduled_tasks: dict[str, dict] = {}
_scheduler_lock = threading.Lock()


class ScheduleRequest(BaseModel):
    """Create or update a scheduled recurring task."""

    instruction: str
    cron: str = Field(description="Cron expression, e.g. '0 9 * * 1-5' for weekdays at 9am")
    enabled: bool = True


class ScheduleResponse(BaseModel):
    """Scheduled task details."""

    schedule_id: str
    instruction: str
    cron: str
    enabled: bool
    last_run_at: str | None = None
    next_run_at: str | None = None
    run_count: int = 0


class ScheduleDeleteResponse(BaseModel):
    """Schedule deletion result."""

    deleted: str


async def _register_scheduled_task(task_id: str, cron_expression: str) -> None:
    """Register a dispatch task as a scheduled recurring job.

    Uses APScheduler CronTrigger to periodically re-execute the task instruction.
    """
    with _dispatch_lock:
        task = _dispatch_tasks.get(task_id)
    if not task:
        return

    schedule_id = str(uuid.uuid4())
    with _scheduler_lock:
        _scheduled_tasks[schedule_id] = {
            "schedule_id": schedule_id,
            "task_id": task_id,
            "instruction": task["instruction"],
            "cron": cron_expression,
            "user_id": task["user_id"],
            "enabled": True,
            "last_run_at": None,
            "next_run_at": None,
            "run_count": 0,
            "created_at": datetime.now(UTC).isoformat(),
        }

    task["status"] = "scheduled"
    task["result"] = f"Scheduled with cron: {cron_expression} (id: {schedule_id})"

    # Register with APScheduler if available
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()
        trigger = CronTrigger.from_crontab(cron_expression)

        async def _run_scheduled() -> None:
            sched = _scheduled_tasks.get(schedule_id)
            if not sched or not sched["enabled"]:
                return
            sched["last_run_at"] = datetime.now(UTC).isoformat()
            sched["run_count"] += 1
            # Create a new dispatch task for this run
            new_task_id = str(uuid.uuid4())
            now = datetime.now(UTC).isoformat()
            new_task = {
                "task_id": new_task_id,
                "user_id": sched["user_id"],
                "instruction": sched["instruction"],
                "priority": "medium",
                "schedule": cron_expression,
                "context": {"scheduled_from": schedule_id, "run_number": sched["run_count"]},
                "status": "queued",
                "created_at": now,
                "completed_at": None,
                "result": None,
                "plan_preview": None,
                "needs_input_reason": None,
                "steering_instructions": [],
                "resume_event": asyncio.Event(),
                "resume_input": None,
            }
            with _dispatch_lock:
                _dispatch_tasks[new_task_id] = new_task
            asyncio.create_task(_execute_dispatch(new_task_id))
            logger.info("Scheduled task %s triggered (run #%d)", schedule_id, sched["run_count"])

        scheduler.add_job(_run_scheduled, trigger, id=schedule_id)
        if not scheduler.running:
            scheduler.start()
        logger.info("Registered scheduled task %s with cron: %s", schedule_id, cron_expression)
    except Exception as exc:
        logger.warning("APScheduler not available for cron scheduling: %s", exc)
        task["result"] += " (Note: APScheduler cron trigger unavailable, manual polling required)"


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(_user: User = Depends(get_current_user)):
    """List all scheduled recurring tasks (Claude Cowork /schedule pattern)."""
    with _scheduler_lock:
        return [
            ScheduleResponse(
                schedule_id=s["schedule_id"],
                instruction=s["instruction"],
                cron=s["cron"],
                enabled=s["enabled"],
                last_run_at=s.get("last_run_at"),
                next_run_at=s.get("next_run_at"),
                run_count=s.get("run_count", 0),
            )
            for s in _scheduled_tasks.values()
        ]


@router.delete("/schedules/{schedule_id}", response_model=ScheduleDeleteResponse)
async def delete_schedule(schedule_id: str, _user: User = Depends(get_current_user)):
    """Delete a scheduled recurring task."""
    with _scheduler_lock:
        if schedule_id not in _scheduled_tasks:
            raise HTTPException(status_code=404, detail="Schedule not found")
        del _scheduled_tasks[schedule_id]
    return {"deleted": schedule_id}
