"""Artifact Bridge — 業務間の成果物接続。"""

import json
import uuid
import aiosqlite
from pydantic import BaseModel


class ArtifactSlot(BaseModel):
    id: str = ""
    slot_type: str  # insight | copy | data | analysis
    content: str
    source_task_id: str
    tags: list[str] = []


_db_path: str | None = None


async def init_artifact_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY, slot_type TEXT,
                content TEXT, source_task_id TEXT, tags TEXT
            )
        """)
        await db.commit()


async def save_artifact(slot: ArtifactSlot) -> None:
    slot.id = str(uuid.uuid4())
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO artifacts VALUES (?,?,?,?,?)",
            (slot.id, slot.slot_type, slot.content,
             slot.source_task_id, json.dumps(slot.tags)),
        )
        await db.commit()


async def find_relevant_artifacts(tags: list[str], limit: int = 5) -> list[ArtifactSlot]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM artifacts ORDER BY rowid DESC LIMIT ?", (limit * 3,)
        )
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            stored_tags = json.loads(r["tags"])
            if any(t in stored_tags for t in tags):
                results.append(ArtifactSlot(
                    id=r["id"], slot_type=r["slot_type"], content=r["content"],
                    source_task_id=r["source_task_id"], tags=stored_tags,
                ))
            if len(results) >= limit:
                break
        return results
