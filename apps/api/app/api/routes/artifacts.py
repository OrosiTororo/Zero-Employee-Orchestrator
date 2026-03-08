"""Artifact management endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.artifact import Artifact

router = APIRouter()


class ArtifactCreate(BaseModel):
    artifact_type: str
    title: str
    storage_type: str = "local"
    path_or_uri: str = ""
    mime_type: str = ""
    summary: str = ""


@router.get("/tickets/{ticket_id}/artifacts")
async def list_artifacts(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """チケットの成果物一覧"""
    tid = uuid.UUID(ticket_id)
    result = await db.execute(select(Artifact).where(Artifact.ticket_id == tid).order_by(Artifact.created_at.desc()))
    artifacts = result.scalars().all()
    return [
        {
            "id": str(a.id), "artifact_type": a.artifact_type,
            "title": a.title, "mime_type": a.mime_type,
            "summary": a.summary,
        }
        for a in artifacts
    ]


@router.post("/tickets/{ticket_id}/artifacts")
async def create_artifact(ticket_id: str, req: ArtifactCreate, db: AsyncSession = Depends(get_db)):
    """成果物を追加"""
    artifact = Artifact(
        id=uuid.uuid4(),
        ticket_id=uuid.UUID(ticket_id),
        artifact_type=req.artifact_type,
        title=req.title,
        storage_type=req.storage_type,
        path_or_uri=req.path_or_uri,
        mime_type=req.mime_type,
        version_no=1,
        summary=req.summary,
        created_by_type="user",
    )
    db.add(artifact)
    await db.flush()
    return {"id": str(artifact.id), "title": artifact.title}
