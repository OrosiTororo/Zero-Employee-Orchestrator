"""Resource import API endpoints.

Provides import, search, and management functionality
for business manuals, rules, document folders, etc.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services.resource_import_service import (
    ImportedResource,
    ImportStatus,
    ResourceType,
    resource_import_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class ImportFileBody(BaseModel):
    """File import request."""

    file_path: str = Field(..., description="Path of the file to import")
    resource_type: ResourceType | None = Field(
        default=None, description="Resource type (auto-detected if omitted)"
    )
    tags: list[str] = Field(default_factory=list, description="Tags")


class ImportFolderBody(BaseModel):
    """Folder import request."""

    folder_path: str = Field(..., description="Path of the folder to import")
    recursive: bool = Field(default=True, description="Process subfolders recursively")
    file_types: list[str] | None = Field(
        default=None,
        description='Target file extensions (e.g., [".txt", ".pdf"])',
    )


class ImportUrlBody(BaseModel):
    """URL import request."""

    url: str = Field(..., description="URL to import")
    tags: list[str] = Field(default_factory=list, description="Tags")


class ResourceResponse(BaseModel):
    """Resource response."""

    id: str
    name: str
    resource_type: str
    source_path: str
    status: str
    size_bytes: int
    content_summary: str
    tags: list[str]
    imported_at: str
    processed_at: str | None


class ResourceListResponse(BaseModel):
    """Resource list response."""

    resources: list[ResourceResponse]
    total: int


class ImportFolderResponse(BaseModel):
    """Folder import response."""

    imported: list[ResourceResponse]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_response(r: ImportedResource) -> ResourceResponse:
    """Convert ImportedResource to ResourceResponse."""
    return ResourceResponse(
        id=r.id,
        name=r.name,
        resource_type=r.resource_type.value,
        source_path=r.source_path,
        status=r.status.value,
        size_bytes=r.size_bytes,
        content_summary=r.content_summary,
        tags=r.tags,
        imported_at=r.imported_at.isoformat(),
        processed_at=r.processed_at.isoformat() if r.processed_at else None,
    )


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------
@router.post("/import/file", response_model=ResourceResponse)
async def import_file(
    body: ImportFileBody, user: User = Depends(get_current_user)
) -> ResourceResponse:
    """Import a single file."""
    try:
        resource = await resource_import_service.import_file(
            file_path=body.file_path,
            resource_type=body.resource_type,
            tags=body.tags,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc
    return _to_response(resource)


@router.post("/import/folder", response_model=ImportFolderResponse)
async def import_folder(
    body: ImportFolderBody, user: User = Depends(get_current_user)
) -> ImportFolderResponse:
    """Batch import resources from a folder."""
    file_types = set(body.file_types) if body.file_types else None
    try:
        resources = await resource_import_service.import_folder(
            folder_path=body.folder_path,
            recursive=body.recursive,
            file_types=file_types,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Folder import failed: {exc}"
        ) from exc
    return ImportFolderResponse(
        imported=[_to_response(r) for r in resources],
        total=len(resources),
    )


@router.post("/import/url", response_model=ResourceResponse)
async def import_url(
    body: ImportUrlBody, user: User = Depends(get_current_user)
) -> ResourceResponse:
    """Import a resource from a URL."""
    try:
        resource = await resource_import_service.import_url(
            url=body.url,
            tags=body.tags,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"URL import failed: {exc}") from exc
    return _to_response(resource)


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    status: ImportStatus | None = Query(default=None, description="Status filter"),
    resource_type: ResourceType | None = Query(default=None, description="Resource type filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max items to retrieve"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    user: User = Depends(get_current_user),
) -> ResourceListResponse:
    """Get resource list."""
    resources = await resource_import_service.list_resources(
        status=status,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )
    total = len(resource_import_service._resources)
    return ResourceListResponse(
        resources=[_to_response(r) for r in resources],
        total=total,
    )


@router.get("/search", response_model=ResourceListResponse)
async def search_resources(
    q: str = Query(..., min_length=1, description="Search query"),
    resource_type: ResourceType | None = Query(default=None, description="Resource type filter"),
    tags: list[str] | None = Query(default=None, description="Tag filter"),
    user: User = Depends(get_current_user),
) -> ResourceListResponse:
    """Search resources."""
    results = await resource_import_service.search_resources(
        query=q,
        resource_type=resource_type,
        tags=tags,
    )
    return ResourceListResponse(
        resources=[_to_response(r) for r in results],
        total=len(results),
    )


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str, user: User = Depends(get_current_user)
) -> ResourceResponse:
    """Get resource details."""
    resource = resource_import_service.get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _to_response(resource)


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Delete a resource."""
    deleted = await resource_import_service.delete_resource(resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"message": "Resource deleted"}
