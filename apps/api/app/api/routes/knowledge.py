"""Knowledge & Preferences API — ナレッジストア・変更検知.

ユーザー設定やファイル権限、フォルダ位置などの記憶と検索。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.orchestration.knowledge_store import KnowledgeStore

router = APIRouter()


class KnowledgeRememberRequest(BaseModel):
    category: str
    key: str
    value: str
    company_id: str | None = None
    user_id: str | None = None
    metadata: dict | None = None
    source: str = "user_input"


class KnowledgeRecallRequest(BaseModel):
    category: str | None = None
    key: str | None = None
    company_id: str | None = None
    user_id: str | None = None


class KnowledgeResponse(BaseModel):
    id: str
    category: str
    key: str
    value: str
    source: str
    use_count: int
    is_active: bool


class FilePermissionRequest(BaseModel):
    path: str
    permission: str  # read, write, execute, full
    company_id: str | None = None
    user_id: str | None = None


class FolderLocationRequest(BaseModel):
    name: str
    path: str
    company_id: str | None = None
    user_id: str | None = None


@router.post("/knowledge/remember")
async def remember_knowledge(
    req: KnowledgeRememberRequest,
    db: AsyncSession = Depends(get_db),
):
    """ナレッジを記憶する."""
    store = KnowledgeStore(db)
    record = await store.remember(
        req.category, req.key, req.value,
        company_id=req.company_id,
        user_id=req.user_id,
        metadata=req.metadata,
        source=req.source,
    )
    await db.commit()
    return {"id": str(record.id), "category": record.category, "key": record.key, "stored": True}


@router.post("/knowledge/recall")
async def recall_knowledge(
    req: KnowledgeRecallRequest,
    db: AsyncSession = Depends(get_db),
):
    """ナレッジを検索する."""
    store = KnowledgeStore(db)
    records = await store.recall(
        req.category, req.key,
        company_id=req.company_id,
        user_id=req.user_id,
    )
    await db.commit()
    return {
        "results": [
            {
                "id": str(r.id),
                "category": r.category,
                "key": r.key,
                "value": r.value,
                "source": r.source,
                "use_count": r.use_count,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.post("/knowledge/file-permission")
async def remember_file_permission(
    req: FilePermissionRequest,
    db: AsyncSession = Depends(get_db),
):
    """ファイル/フォルダの操作権限を記憶."""
    store = KnowledgeStore(db)
    record = await store.remember_file_permission(
        req.path, req.permission,
        company_id=req.company_id,
        user_id=req.user_id,
    )
    await db.commit()
    return {"id": str(record.id), "path": req.path, "permission": req.permission, "stored": True}


@router.post("/knowledge/folder-location")
async def remember_folder_location(
    req: FolderLocationRequest,
    db: AsyncSession = Depends(get_db),
):
    """業務資料フォルダの場所を記憶."""
    store = KnowledgeStore(db)
    record = await store.remember_folder_location(
        req.name, req.path,
        company_id=req.company_id,
        user_id=req.user_id,
    )
    await db.commit()
    return {"id": str(record.id), "name": req.name, "path": req.path, "stored": True}


@router.get("/knowledge/permissions")
async def list_permissions(
    company_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """全ファイル権限を取得."""
    store = KnowledgeStore(db)
    records = await store.get_all_permissions(company_id)
    await db.commit()
    return {
        "permissions": [
            {"id": str(r.id), "path": r.key, "permission": r.value}
            for r in records
        ],
    }


@router.get("/knowledge/folders")
async def list_folder_locations(
    company_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """全フォルダ位置を取得."""
    store = KnowledgeStore(db)
    records = await store.get_all_folder_locations(company_id)
    await db.commit()
    return {
        "folders": [
            {"id": str(r.id), "name": r.key, "path": r.value}
            for r in records
        ],
    }


@router.get("/knowledge/changes")
async def list_changes(
    company_id: str | None = None,
    unacknowledged_only: bool = True,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """変更検知の一覧."""
    store = KnowledgeStore(db)
    changes = await store.get_changes(company_id, unacknowledged_only, limit)
    await db.commit()
    return {
        "changes": [
            {
                "id": str(c.id),
                "entity_type": c.entity_type,
                "change_type": c.change_type,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "detected_at": str(c.detected_at),
                "acknowledged": c.acknowledged,
            }
            for c in changes
        ],
    }


@router.post("/knowledge/changes/{change_id}/acknowledge")
async def acknowledge_change(
    change_id: str,
    db: AsyncSession = Depends(get_db),
):
    """変更を確認済みにする."""
    store = KnowledgeStore(db)
    ok = await store.acknowledge_change(change_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=404, detail="変更が見つかりません")
    return {"acknowledged": True}


@router.delete("/knowledge/{record_id}")
async def forget_knowledge(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """ナレッジを無効化."""
    store = KnowledgeStore(db)
    ok = await store.forget(record_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=404, detail="ナレッジが見つかりません")
    return {"forgotten": True}
