"""Settings and connection management endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.connection import ToolConnection

router = APIRouter()


class ConnectionCreate(BaseModel):
    name: str
    connection_type: str
    auth_type: str = "api_key"
    config_json: dict | None = None


@router.get("/companies/{company_id}/settings")
async def get_settings(company_id: str):
    """会社設定を取得"""
    return {"company_id": company_id, "settings": {}}


@router.patch("/companies/{company_id}/settings")
async def update_settings(company_id: str, settings: dict | None = None):
    """会社設定を更新"""
    return {"company_id": company_id, "status": "updated"}


@router.get("/companies/{company_id}/tool-connections")
async def list_connections(company_id: str, db: AsyncSession = Depends(get_db)):
    """接続先一覧"""
    cid = uuid.UUID(company_id)
    result = await db.execute(select(ToolConnection).where(ToolConnection.company_id == cid))
    connections = result.scalars().all()
    return [
        {
            "id": str(c.id), "name": c.name, "connection_type": c.connection_type,
            "status": c.status, "auth_type": c.auth_type,
        }
        for c in connections
    ]


@router.post("/companies/{company_id}/tool-connections")
async def create_connection(company_id: str, req: ConnectionCreate, db: AsyncSession = Depends(get_db)):
    """接続先を追加"""
    conn = ToolConnection(
        id=uuid.uuid4(), company_id=uuid.UUID(company_id),
        name=req.name, connection_type=req.connection_type,
        status="active", auth_type=req.auth_type,
        config_json=req.config_json or {},
    )
    db.add(conn)
    await db.flush()
    return {"id": str(conn.id), "name": conn.name, "status": conn.status}
