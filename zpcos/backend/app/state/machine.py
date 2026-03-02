"""State Machine — AsyncMachine + aiosqlite 永続化。"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite
from transitions.extensions.asyncio import AsyncMachine
from pydantic import BaseModel


class TaskData(BaseModel):
    id: str
    skill_name: str
    state: str
    input_data: dict
    output_data: Optional[dict] = None
    judge_result: Optional[dict] = None
    created_at: str
    updated_at: str


STATES = [
    "draft", "ai_executing", "ai_completed", "judging", "judge_completed",
    "human_review", "approved", "rejected", "committed", "error",
]

TRANSITIONS = [
    {"trigger": "start_execution", "source": "draft", "dest": "ai_executing"},
    {"trigger": "complete_execution", "source": "ai_executing", "dest": "ai_completed"},
    {"trigger": "start_judging", "source": "ai_completed", "dest": "judging"},
    {"trigger": "complete_judging", "source": "judging", "dest": "judge_completed"},
    {"trigger": "request_review", "source": "judge_completed", "dest": "human_review"},
    {"trigger": "approve", "source": "human_review", "dest": "approved"},
    {"trigger": "reject", "source": "human_review", "dest": "rejected"},
    {"trigger": "commit", "source": "approved", "dest": "committed"},
    {"trigger": "revise", "source": "rejected", "dest": "draft"},
    {"trigger": "fail", "source": "*", "dest": "error"},
]


class TaskStateMachine:
    """タスクの状態機械。"""
    def __init__(self, task_id: str, initial_state: str = "draft"):
        self.task_id = task_id
        self.state = initial_state
        self.machine = AsyncMachine(
            model=self, states=STATES, transitions=TRANSITIONS,
            initial=initial_state, auto_transitions=False,
        )


_db_path: Optional[str] = None


async def init_db(db_path: str = "zpcos_tasks.db") -> None:
    """DB を初期化。"""
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                skill_name TEXT NOT NULL,
                state TEXT NOT NULL,
                input_data TEXT NOT NULL,
                output_data TEXT,
                judge_result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def create_task(skill_name: str, input_data: dict) -> TaskData:
    """新規タスクを作成。"""
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    task = TaskData(
        id=task_id, skill_name=skill_name, state="draft",
        input_data=input_data, created_at=now, updated_at=now,
    )
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO tasks (id, skill_name, state, input_data, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (task.id, task.skill_name, task.state,
             json.dumps(task.input_data), task.created_at, task.updated_at),
        )
        await db.commit()
    return task


async def get_task(task_id: str) -> Optional[TaskData]:
    """タスクを取得。"""
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return TaskData(
            id=row["id"], skill_name=row["skill_name"], state=row["state"],
            input_data=json.loads(row["input_data"]),
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            judge_result=json.loads(row["judge_result"]) if row["judge_result"] else None,
            created_at=row["created_at"], updated_at=row["updated_at"],
        )


async def transition_task(task_id: str, trigger: str) -> TaskData:
    """タスクの状態遷移。"""
    task = await get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    sm = TaskStateMachine(task_id, initial_state=task.state)
    trigger_fn = getattr(sm, trigger, None)
    if trigger_fn is None:
        raise ValueError(f"Unknown trigger: {trigger}")
    await trigger_fn()
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "UPDATE tasks SET state = ?, updated_at = ? WHERE id = ?",
            (sm.state, now, task_id),
        )
        await db.commit()
    task.state = sm.state
    task.updated_at = now
    return task


async def update_task_data(
    task_id: str, output_data: dict = None, judge_result: dict = None
) -> None:
    """タスクの出力データや Judge 結果を更新。"""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path) as db:
        if output_data is not None:
            await db.execute(
                "UPDATE tasks SET output_data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(output_data), now, task_id),
            )
        if judge_result is not None:
            await db.execute(
                "UPDATE tasks SET judge_result = ?, updated_at = ? WHERE id = ?",
                (json.dumps(judge_result), now, task_id),
            )
        await db.commit()


async def list_tasks(limit: int = 50) -> list[TaskData]:
    """タスク一覧を取得。"""
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            TaskData(
                id=row["id"], skill_name=row["skill_name"], state=row["state"],
                input_data=json.loads(row["input_data"]),
                output_data=json.loads(row["output_data"]) if row["output_data"] else None,
                judge_result=json.loads(row["judge_result"]) if row["judge_result"] else None,
                created_at=row["created_at"], updated_at=row["updated_at"],
            )
            for row in rows
        ]
