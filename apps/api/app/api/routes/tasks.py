"""Task execution endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.task import Task, TaskRun

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    task_type: str = "execution"
    requires_approval: bool = False
    sequence_no: int = 0


@router.post("/plans/{plan_id}/tasks")
async def create_task(plan_id: str, req: TaskCreate, db: AsyncSession = Depends(get_db)):
    """タスク作成"""
    task = Task(
        id=uuid.uuid4(),
        plan_id=uuid.UUID(plan_id),
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
async def start_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """タスク実行開始"""
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "running"
    task.started_at = datetime.utcnow()
    return {"status": "running"}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """タスク完了"""
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "succeeded"
    task.completed_at = datetime.utcnow()
    return {"status": "succeeded"}


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """タスク再試行"""
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "retrying"
    return {"status": "retrying"}


@router.post("/tasks/{task_id}/request-approval")
async def request_approval(task_id: str, db: AsyncSession = Depends(get_db)):
    """タスクの承認を要求"""
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "awaiting_approval"
    return {"status": "awaiting_approval"}


@router.post("/tasks/{task_id}/runs")
async def create_task_run(task_id: str, db: AsyncSession = Depends(get_db)):
    """タスク実行記録を作成"""
    tid = uuid.UUID(task_id)
    existing = await db.execute(select(TaskRun).where(TaskRun.task_id == tid))
    count = len(existing.scalars().all())
    run = TaskRun(
        id=uuid.uuid4(),
        task_id=tid,
        run_no=count + 1,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    await db.flush()
    return {"id": str(run.id), "run_no": run.run_no, "status": run.status}


@router.get("/tasks/{task_id}/runs")
async def list_task_runs(task_id: str, db: AsyncSession = Depends(get_db)):
    """タスク実行履歴"""
    tid = uuid.UUID(task_id)
    result = await db.execute(select(TaskRun).where(TaskRun.task_id == tid).order_by(TaskRun.run_no.desc()))
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id), "run_no": r.run_no, "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]
