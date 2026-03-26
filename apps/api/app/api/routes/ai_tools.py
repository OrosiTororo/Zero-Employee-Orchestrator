"""AI tool management API endpoints.

API for listing, configuring, and enabling/disabling external tools operable by AI.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.integrations.ai_tools import (
    ToolCategory,
    ai_tool_registry,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


class ToolToggleRequest(BaseModel):
    """Tool enable/disable request."""

    tool_id: str
    enabled: bool


# No auth required: tool list is public information
@router.get("")
async def list_all_tools() -> dict:
    """Return all AI tools."""
    tools = ai_tool_registry.get_all_tools()
    return {
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category.value,
                "description": t.description,
                "description_en": t.description_en,
                "status": t.status.value,
                "requires_api_key": t.requires_api_key,
                "env_key": t.env_key,
                "requires_approval": t.requires_approval,
                "capabilities": t.capabilities,
            }
            for t in tools
        ],
        "summary": ai_tool_registry.get_summary(),
    }


# No auth required: tool list is public information
@router.get("/available")
async def list_available_tools() -> dict:
    """Return available (configured) tools."""
    tools = ai_tool_registry.get_available_tools()
    return {
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category.value,
                "description": t.description,
                "capabilities": t.capabilities,
            }
            for t in tools
        ],
        "count": len(tools),
    }


# No auth required: tool list is public information
@router.get("/category/{category}")
async def list_tools_by_category(category: str) -> dict:
    """Return tools by category."""
    try:
        cat = ToolCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}. Valid: {[c.value for c in ToolCategory]}",
        )
    tools = ai_tool_registry.get_tools_by_category(cat)
    return {
        "category": category,
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "status": t.status.value,
                "capabilities": t.capabilities,
            }
            for t in tools
        ],
    }


@router.post("/toggle")
async def toggle_tool(req: ToolToggleRequest, user: User = Depends(get_current_user)) -> dict:
    """Toggle tool enable/disable."""
    if req.enabled:
        success = ai_tool_registry.enable_tool(req.tool_id)
    else:
        success = ai_tool_registry.disable_tool(req.tool_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Tool not found: {req.tool_id}")

    return {
        "tool_id": req.tool_id,
        "enabled": req.enabled,
        "status": "updated",
    }


# No auth required: tool list is public information
@router.get("/summary")
async def get_tools_summary() -> dict:
    """Return tools summary."""
    return ai_tool_registry.get_summary()
