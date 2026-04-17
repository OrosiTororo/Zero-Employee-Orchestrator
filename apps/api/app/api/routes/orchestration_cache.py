"""Orchestration cache observability — exposes DAG node-result cache stats.

LangGraph-inspired memoisation is opt-in via ``ZEO_DAG_CACHE=1``. This route
surfaces hit / miss / size so operators can confirm the cache is doing useful
work and tune ``maxsize`` if needed.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from app.api.routes.auth import get_current_user
from app.models.user import User
from app.orchestration.executor import get_default_cache

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


@router.get("/cache/stats")
async def cache_stats(_: User = Depends(get_current_user)) -> dict:
    enabled = os.getenv("ZEO_DAG_CACHE", "0") in {"1", "true", "True"}
    stats = get_default_cache().stats()
    return {
        "enabled": enabled,
        **stats,
        "env_flag": "ZEO_DAG_CACHE",
    }
