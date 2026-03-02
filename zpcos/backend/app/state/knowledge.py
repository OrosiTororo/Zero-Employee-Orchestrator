"""Knowledge Refresh — ソース登録・差分取得・要約。MVP では手動トリガー。"""

import json
import uuid
from datetime import datetime, timezone
import aiosqlite
from pydantic import BaseModel


class KnowledgeSource(BaseModel):
    id: str = ""
    name: str
    source_type: str  # url | file | api
    source_url: str = ""
    last_fetched: str = ""
    content_hash: str = ""


_db_path: str | None = None


async def init_knowledge_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_sources (
                id TEXT PRIMARY KEY, name TEXT, source_type TEXT,
                source_url TEXT, last_fetched TEXT, content_hash TEXT
            )
        """)
        await db.commit()


async def register_source(source: KnowledgeSource) -> KnowledgeSource:
    source.id = str(uuid.uuid4())
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO knowledge_sources VALUES (?,?,?,?,?,?)",
            (source.id, source.name, source.source_type,
             source.source_url, source.last_fetched, source.content_hash),
        )
        await db.commit()
    return source


async def list_sources() -> list[KnowledgeSource]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM knowledge_sources")
        rows = await cursor.fetchall()
        return [KnowledgeSource(**dict(r)) for r in rows]
