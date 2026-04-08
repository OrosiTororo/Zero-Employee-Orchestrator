"""Artifact export API endpoints.

API for exporting artifacts in PDF / Markdown / HTML / JSON / CSV / DOCX format
and sending them to local or external services.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.integrations.artifact_export import (
    ExportFormat,
    ExportRequest,
    ExportTarget,
    artifact_exporter,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


# ------------------------------------------------------------------ #
#  Request / Response schemas
# ------------------------------------------------------------------ #


class ArtifactExportRequest(BaseModel):
    """Artifact export request."""

    content: str | list[dict[str, Any]]
    format: str
    target: str = "local"
    filename: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExportResultResponse(BaseModel):
    success: bool
    file_path: str | None = None
    url: str | None = None
    size_bytes: int = 0
    format: str = ""
    exported_at: str | None = None


class FormatsResponse(BaseModel):
    formats: list[dict[str, Any]]


class TargetsResponse(BaseModel):
    targets: list[dict[str, Any]]


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #


@router.post("/artifact", response_model=ExportResultResponse)
async def export_artifact(
    req: ArtifactExportRequest, user: User = Depends(get_current_user)
) -> dict:
    """Export an artifact."""
    try:
        export_format = ExportFormat(req.format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(f"Invalid format: {req.format}. Valid: {[f.value for f in ExportFormat]}"),
        )

    try:
        export_target = ExportTarget(req.target)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(f"Invalid target: {req.target}. Valid: {[t.value for t in ExportTarget]}"),
        )

    export_req = ExportRequest(
        content=req.content,
        format=export_format,
        target=export_target,
        filename=req.filename,
        metadata=req.metadata,
    )

    result = await artifact_exporter.export(export_req)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": result.success,
        "file_path": result.file_path,
        "url": result.url,
        "size_bytes": result.size_bytes,
        "format": result.format.value,
        "exported_at": result.exported_at,
    }


@router.get("/formats", response_model=FormatsResponse)
async def list_formats(user: User = Depends(get_current_user)) -> dict:
    """Return list of supported export formats."""
    return {"formats": artifact_exporter.get_supported_formats()}


@router.get("/targets", response_model=TargetsResponse)
async def list_targets(user: User = Depends(get_current_user)) -> dict:
    """Return list of supported export targets."""
    return {"targets": artifact_exporter.get_supported_targets()}
