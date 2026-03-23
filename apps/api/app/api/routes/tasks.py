"""Task execution endpoints with state machine enforcement."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.validators import parse_uuid
from app.api.routes.auth import get_current_user
from app.models.task import Task, TaskRun
from app.models.user import User
from app.services.task_service import (
    complete_task as svc_complete_task,
)
from app.services.task_service import (
    request_task_approval as svc_request_approval,
)
from app.services.task_service import (
    start_task as svc_start_task,
)
from app.services.task_service import (
    validate_task_transition,
)

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    task_type: str = "execution"
    requires_approval: bool = False
    sequence_no: int = 0


@router.post("/plans/{plan_id}/tasks")
async def create_task(
    plan_id: str,
    req: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """タスク作成"""
    task = Task(
        id=uuid.uuid4(),
        plan_id=parse_uuid(plan_id, "plan_id"),
        title=req.title,
        description=req.description,
        sequence_no=req.sequence_no,
        status="pending",
        task_type=req.task_type,
        requires_approval=req.requires_approval,
    )
    db.add(task)
    await db.flush()
    return {"id": str(task.id), "title": task.title, "status": task.status}


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """タスク実行開始 (state machine enforced)"""
    result = await db.execute(select(Task).where(Task.id == parse_uuid(task_id, "task_id")))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        run = await svc_start_task(db, task)
        return {"status": "running", "run_id": str(run.id), "run_no": run.run_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """タスク完了"""
    result = await db.execute(select(Task).where(Task.id == parse_uuid(task_id, "task_id")))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    run_result = await db.execute(
        select(TaskRun).where(TaskRun.task_id == task.id, TaskRun.status == "running")
    )
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=400, detail="No running task run found")

    try:
        task = await svc_complete_task(db, task, run, success=True)
        return {"status": task.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """タスク再試行"""
    result = await db.execute(select(Task).where(Task.id == parse_uuid(task_id, "task_id")))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not validate_task_transition(task.status, "retrying"):
        raise HTTPException(status_code=400, detail=f"Cannot retry from status: {task.status}")
    task.status = "retrying"
    await db.commit()
    return {"status": "retrying"}


@router.post("/tasks/{task_id}/request-approval")
async def request_approval(
    task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """タスクの承認を要求"""
    result = await db.execute(select(Task).where(Task.id == parse_uuid(task_id, "task_id")))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        task = await svc_request_approval(db, task)
        return {"status": task.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/runs")
async def create_task_run(
    task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """タスク実行記録を作成"""
    tid = parse_uuid(task_id, "task_id")
    existing = await db.execute(select(TaskRun).where(TaskRun.task_id == tid))
    count = len(existing.scalars().all())
    run = TaskRun(
        id=uuid.uuid4(),
        task_id=tid,
        run_no=count + 1,
        status="running",
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.flush()
    return {"id": str(run.id), "run_no": run.run_no, "status": run.status}


@router.get("/tasks/{task_id}/runs")
async def list_task_runs(
    task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """タスク実行履歴"""
    tid = parse_uuid(task_id, "task_id")
    result = await db.execute(
        select(TaskRun).where(TaskRun.task_id == tid).order_by(TaskRun.run_no.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "run_no": r.run_no,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]
