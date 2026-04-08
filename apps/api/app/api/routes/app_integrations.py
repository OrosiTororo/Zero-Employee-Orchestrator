"""General application integration API endpoints.

API for listing external applications, establishing connections, data synchronization,
and knowledge store import.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.integrations.app_connector import (
    AppCategory,
    AppConnectionStatus,
    AppDataDirection,
    AppPermission,
    app_connector_hub,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app-integrations", tags=["app-integrations"])


# ------------------------------------------------------------------ #
#  Request / Response schemas
# ------------------------------------------------------------------ #


class AppPermissionSchema(BaseModel):
    """Permission settings."""

    read: bool = True
    write: bool = False
    delete: bool = False
    sync: bool = False
    export: bool = False
    allowed_paths: list[str] = Field(default_factory=list)
    blocked_paths: list[str] = Field(default_factory=list)


class ConnectRequest(BaseModel):
    """App connection request."""

    app_id: str
    config: dict[str, Any] = Field(default_factory=dict)
    permissions: AppPermissionSchema | None = None


class SyncRequest(BaseModel):
    """Sync request."""

    direction: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ImportRequest(BaseModel):
    """Knowledge store import request."""

    query: str = ""
    tags: list[str] = Field(default_factory=list)
    limit: int = 100


class UpdatePermissionsRequest(BaseModel):
    """Permission update request."""

    permissions: AppPermissionSchema


class CustomAppRequest(BaseModel):
    """Custom app registration request."""

    name: str
    category: str = "custom"
    description: str = ""
    description_en: str = ""
    auth_method: str = "api_key"
    env_key: str = ""
    base_url: str = ""
    capabilities: list[str] = Field(default_factory=list)


# ------------------------------------------------------------------ #
#  Response schemas
# ------------------------------------------------------------------ #


class AppDetailResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str = ""
    description_en: str = ""
    auth_method: str = ""
    data_direction: str = ""
    env_key: str = ""
    capabilities: list[str] = Field(default_factory=list)
    requires_approval: bool = False


class AppListResponse(BaseModel):
    apps: list[AppDetailResponse]
    count: int


class CategoryListResponse(BaseModel):
    categories: list[dict]


class CustomAppRegisteredResponse(BaseModel):
    app_id: str
    name: str
    status: str


class ConnectionResponse(BaseModel):
    connection_id: str = ""
    id: str = ""
    app_id: str
    status: str
    connected_at: str | None = None
    last_sync_at: str | None = None
    permissions: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class ConnectionListResponse(BaseModel):
    connections: list[dict]
    count: int


class StatusUpdateResponse(BaseModel):
    connection_id: str
    status: str


class SyncResultResponse(BaseModel):
    connection_id: str
    app_id: str = ""
    direction: str = ""
    items_read: int = 0
    items_written: int = 0
    items_skipped: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    status: str = ""
    errors: list[str] = Field(default_factory=list)


class SyncHistoryResponse(BaseModel):
    history: list[dict]
    count: int


class IntegrationSummaryResponse(BaseModel):
    total_apps: int = 0
    connected: int = 0
    categories: dict = Field(default_factory=dict)


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #


@router.get("/apps", response_model=AppListResponse)
async def list_apps(category: str | None = None, _user: User = Depends(get_current_user)) -> dict:
    """Return list of supported applications."""
    filter_category: AppCategory | None = None
    if category:
        try:
            filter_category = AppCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid: {[c.value for c in AppCategory]}",
            )

    apps = app_connector_hub.list_apps(category=filter_category)
    return {
        "apps": [
            {
                "id": a.id,
                "name": a.name,
                "category": a.category.value,
                "description": a.description,
                "description_en": a.description_en,
                "auth_method": a.auth_method.value,
                "data_direction": a.data_direction.value,
                "capabilities": a.capabilities,
                "requires_approval": a.requires_approval,
            }
            for a in apps
        ],
        "count": len(apps),
    }


@router.get("/apps/{app_id}", response_model=AppDetailResponse)
async def get_app(app_id: str, _user: User = Depends(get_current_user)) -> dict:
    """Return app definition details."""
    app_def = app_connector_hub.get_app(app_id)
    if app_def is None:
        raise HTTPException(status_code=404, detail=f"App not found: {app_id}")
    return {
        "id": app_def.id,
        "name": app_def.name,
        "category": app_def.category.value,
        "description": app_def.description,
        "description_en": app_def.description_en,
        "auth_method": app_def.auth_method.value,
        "data_direction": app_def.data_direction.value,
        "env_key": app_def.env_key,
        "capabilities": app_def.capabilities,
        "requires_approval": app_def.requires_approval,
    }


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(_user: User = Depends(get_current_user)) -> dict:
    """Return category list."""
    return {"categories": app_connector_hub.list_categories()}


@router.post("/apps/custom", response_model=CustomAppRegisteredResponse)
async def register_custom_app(
    req: CustomAppRequest, user: User = Depends(get_current_user)
) -> dict:
    """Register a custom app."""
    from app.integrations.app_connector import AppAuthMethod, AppDefinition

    try:
        category = AppCategory(req.category)
    except ValueError:
        category = AppCategory.CUSTOM

    try:
        auth_method = AppAuthMethod(req.auth_method)
    except ValueError:
        auth_method = AppAuthMethod.API_KEY

    app_def = AppDefinition(
        id="",
        name=req.name,
        category=category,
        description=req.description,
        description_en=req.description_en or req.description,
        auth_method=auth_method,
        env_key=req.env_key,
        base_url=req.base_url,
        capabilities=req.capabilities,
    )

    app_id = app_connector_hub.register_custom_app(app_def)
    return {"app_id": app_id, "name": req.name, "status": "registered"}


@router.post("/connections")
async def connect_app(req: ConnectRequest, user: User = Depends(get_current_user)) -> dict:
    """Establish an application connection."""
    permissions = None
    if req.permissions:
        permissions = AppPermission(
            read=req.permissions.read,
            write=req.permissions.write,
            delete=req.permissions.delete,
            sync=req.permissions.sync,
            export=req.permissions.export,
            allowed_paths=req.permissions.allowed_paths,
            blocked_paths=req.permissions.blocked_paths,
        )

    try:
        conn = app_connector_hub.connect(
            app_id=req.app_id,
            user_id=str(user.id),
            config=req.config,
            permissions=permissions,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"App not found: {req.app_id}")

    return {
        "connection_id": conn.id,
        "app_id": conn.app_id,
        "status": conn.status.value,
        "connected_at": conn.connected_at,
    }


@router.get("/connections")
async def list_connections(
    app_id: str | None = None,
    status: str | None = None,
    user: User = Depends(get_current_user),
) -> dict:
    """Return connection list."""
    filter_status: AppConnectionStatus | None = None
    if status:
        try:
            filter_status = AppConnectionStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    conns = app_connector_hub.list_connections(
        user_id=str(user.id),
        app_id=app_id,
        status=filter_status,
    )
    return {
        "connections": [
            {
                "id": c.id,
                "app_id": c.app_id,
                "status": c.status.value,
                "connected_at": c.connected_at,
                "last_sync_at": c.last_sync_at,
                "permissions": {
                    "read": c.permissions.read,
                    "write": c.permissions.write,
                    "delete": c.permissions.delete,
                    "sync": c.permissions.sync,
                    "export": c.permissions.export,
                },
            }
            for c in conns
        ],
        "count": len(conns),
    }


@router.get("/connections/{connection_id}")
async def get_connection(connection_id: str, user: User = Depends(get_current_user)) -> dict:
    """Return connection details."""
    conn = app_connector_hub.get_connection(connection_id)
    if conn is None:
        raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")

    return {
        "id": conn.id,
        "app_id": conn.app_id,
        "status": conn.status.value,
        "connected_at": conn.connected_at,
        "last_sync_at": conn.last_sync_at,
        "permissions": {
            "read": conn.permissions.read,
            "write": conn.permissions.write,
            "delete": conn.permissions.delete,
            "sync": conn.permissions.sync,
            "export": conn.permissions.export,
            "allowed_paths": conn.permissions.allowed_paths,
            "blocked_paths": conn.permissions.blocked_paths,
        },
        "metadata": conn.metadata,
    }


@router.put("/connections/{connection_id}/permissions", response_model=StatusUpdateResponse)
async def update_permissions(
    connection_id: str,
    req: UpdatePermissionsRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Update connection permissions."""
    permissions = AppPermission(
        read=req.permissions.read,
        write=req.permissions.write,
        delete=req.permissions.delete,
        sync=req.permissions.sync,
        export=req.permissions.export,
        allowed_paths=req.permissions.allowed_paths,
        blocked_paths=req.permissions.blocked_paths,
    )

    updated = app_connector_hub.update_permissions(connection_id, permissions)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")

    return {"connection_id": connection_id, "status": "updated"}


@router.post("/connections/{connection_id}/disconnect", response_model=StatusUpdateResponse)
async def disconnect_app(connection_id: str, user: User = Depends(get_current_user)) -> dict:
    """Disconnect a connection."""
    success = app_connector_hub.disconnect(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")
    return {"connection_id": connection_id, "status": "disconnected"}


@router.delete("/connections/{connection_id}", response_model=StatusUpdateResponse)
async def remove_connection(connection_id: str, user: User = Depends(get_current_user)) -> dict:
    """Completely remove a connection."""
    removed = app_connector_hub.remove_connection(connection_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")
    return {"connection_id": connection_id, "status": "removed"}


@router.post("/connections/{connection_id}/sync", response_model=SyncResultResponse)
async def sync_connection(
    connection_id: str,
    req: SyncRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Synchronize data with connected app."""
    direction = None
    if req.direction:
        try:
            direction = AppDataDirection(req.direction)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid direction: {req.direction}")

    result = await app_connector_hub.sync(
        connection_id=connection_id,
        direction=direction,
        options=req.options,
    )

    if result.errors:
        return {
            "connection_id": connection_id,
            "status": "error",
            "errors": result.errors,
        }

    return {
        "connection_id": connection_id,
        "app_id": result.app_id,
        "direction": result.direction,
        "items_read": result.items_read,
        "items_written": result.items_written,
        "items_skipped": result.items_skipped,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }


@router.post("/connections/{connection_id}/import-knowledge")
async def import_to_knowledge(
    connection_id: str,
    req: ImportRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Import from connected app to knowledge store."""
    result = await app_connector_hub.import_to_knowledge_store(
        connection_id=connection_id,
        query=req.query,
        tags=req.tags,
        limit=req.limit,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/connections/{connection_id}/sync-history", response_model=SyncHistoryResponse)
async def get_sync_history(
    connection_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
) -> dict:
    """Return sync history."""
    history = app_connector_hub.get_sync_history(
        connection_id=connection_id,
        limit=limit,
    )
    return {
        "history": [
            {
                "connection_id": h.connection_id,
                "app_id": h.app_id,
                "direction": h.direction,
                "items_read": h.items_read,
                "items_written": h.items_written,
                "items_skipped": h.items_skipped,
                "errors": h.errors,
                "started_at": h.started_at,
                "finished_at": h.finished_at,
            }
            for h in history
        ],
        "count": len(history),
    }


@router.get("/summary", response_model=IntegrationSummaryResponse)
async def get_summary() -> dict:
    """Return integration hub summary."""
    return app_connector_hub.get_summary()
