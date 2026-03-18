"""AI ツール管理 API エンドポイント.

AI が操作可能な外部ツールの一覧表示・設定・有効化/無効化を行う API。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.integrations.ai_tools import (
    ToolCategory,
    ai_tool_registry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


class ToolToggleRequest(BaseModel):
    """ツール有効化/無効化リクエスト."""

    tool_id: str
    enabled: bool


@router.get("")
async def list_all_tools() -> dict:
    """全 AI ツール一覧を返す."""
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


@router.get("/available")
async def list_available_tools() -> dict:
    """利用可能な（設定済み）ツール一覧を返す."""
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


@router.get("/category/{category}")
async def list_tools_by_category(category: str) -> dict:
    """カテゴリ別のツール一覧を返す."""
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
async def toggle_tool(req: ToolToggleRequest) -> dict:
    """ツールの有効化/無効化を切り替える."""
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


@router.get("/summary")
async def get_tools_summary() -> dict:
    """ツール概要を返す."""
    return ai_tool_registry.get_summary()
