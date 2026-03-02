"""Experience Memory — 成功体験の横展開。"""

import json
import uuid
from datetime import datetime, timezone
import aiosqlite
from pydantic import BaseModel


class ExperienceCard(BaseModel):
    id: str = ""
    task_type: str
    success_factors: list[str]
    model_used: str
    score: float
    context: str
    created_at: str = ""


_db_path: str | None = None


async def init_experience_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                task_type TEXT, success_factors TEXT,
                model_used TEXT, score REAL, context TEXT,
                created_at TEXT
            )
        """)
        await db.commit()


async def save_experience(card: ExperienceCard) -> None:
    card.id = str(uuid.uuid4())
    card.created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO experiences VALUES (?,?,?,?,?,?,?)",
            (card.id, card.task_type, json.dumps(card.success_factors),
             card.model_used, card.score, card.context, card.created_at),
        )
        await db.commit()


async def get_relevant_experiences(task_type: str, limit: int = 5) -> list[ExperienceCard]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM experiences WHERE task_type = ? ORDER BY score DESC LIMIT ?",
            (task_type, limit),
        )
        rows = await cursor.fetchall()
        return [
            ExperienceCard(
                id=r["id"], task_type=r["task_type"],
                success_factors=json.loads(r["success_factors"]),
                model_used=r["model_used"], score=r["score"],
                context=r["context"], created_at=r["created_at"],
            )
            for r in rows
        ]
