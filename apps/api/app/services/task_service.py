"""Task lifecycle service with state machine enforcement."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.task import Task, TaskRun

# Valid state transitions for tasks
TASK_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["ready", "cancelled"],
    "ready": ["running", "blocked"],
    "running": ["succeeded", "failed", "awaiting_approval", "blocked"],
    "awaiting_approval": ["running", "cancelled"],
    "blocked": ["ready", "cancelled"],
    "failed": ["retrying", "cancelled"],
    "retrying": ["running", "failed"],
    "succeeded": ["verified", "archived"],
    "verified": ["archived", "rework_requested"],
    "rework_requested": ["ready", "running"],
    "cancelled": [],
    "archived": [],
}


def validate_task_transition(current: str, target: str) -> bool:
    return target in TASK_TRANSITIONS.get(current, [])


async def start_task(
    db: AsyncSession,
    task: Task,
    executor_agent_id: str | None = None,
) -> TaskRun:
    if not validate_task_transition(task.status, "running"):
        raise ValueError(f"Cannot start task in status: {task.status}")

    task.status = "running"
    task.started_at = datetime.now(UTC)

    # Count existing runs
    result = await db.execute(select(TaskRun).where(TaskRun.task_id == task.id))
    existing_runs = len(result.scalars().all())

    run = TaskRun(
        id=generate_uuid(),
        company_id=task.company_id,
        task_id=task.id,
        run_no=existing_runs + 1,
        executor_agent_id=uuid.UUID(executor_agent_id) if executor_agent_id else None,
        status="running",
        started_at=datetime.now(UTC),
    )
    db.add(run)

    audit = AuditLog(
        id=generate_uuid(),
        company_id=task.company_id,
        actor_type="agent" if executor_agent_id else "system",
        actor_agent_id=uuid.UUID(executor_agent_id) if executor_agent_id else None,
        event_type="task.started",
        target_type="task",
        target_id=task.id,
        task_id=task.id,
        details_json={"run_no": run.run_no},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(run)
    return run


async def complete_task(
    db: AsyncSession,
    task: Task,
    task_run: TaskRun,
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
    output_snapshot_json: dict | None = None,
) -> Task:
    new_status = "succeeded" if success else "failed"
    if not validate_task_transition(task.status, new_status):
        raise ValueError(f"Cannot transition to {new_status} from {task.status}")

    task.status = new_status
    if success:
        task.completed_at = datetime.now(UTC)

    task_run.status = "succeeded" if success else "failed"
    task_run.finished_at = datetime.now(UTC)
    task_run.error_code = error_code
    task_run.error_message = error_message
    task_run.output_snapshot_json = output_snapshot_json or {}

    audit = AuditLog(
        id=generate_uuid(),
        company_id=task.company_id,
        actor_type="system",
        event_type=f"task.{'completed' if success else 'failed'}",
        target_type="task",
        target_id=task.id,
        task_id=task.id,
        details_json={"success": success, "error_code": error_code},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(task)
    return task


async def request_task_approval(
    db: AsyncSession,
    task: Task,
) -> Task:
    if not validate_task_transition(task.status, "awaiting_approval"):
        raise ValueError(f"Cannot request approval from status: {task.status}")

    task.status = "awaiting_approval"
    await db.commit()
    await db.refresh(task)
    return task
