"""Secretary / Brain Dump API endpoints.

Functionality to dump, organize, and accumulate CEO thoughts, ideas, and todos.
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.services.secretary_service import SecretaryService

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BrainDumpRequest(BaseModel):
    """Brain dump post request."""

    raw_text: str
    category: str | None = None
    priority: str | None = None
    tags: list[str] | None = None


class BrainDumpResponse(BaseModel):
    """Brain dump response."""

    id: str
    raw_text: str
    category: str
    priority: str
    title: str | None = None
    tags: list[str] = []
    action_items: list[str] = []
    is_processed: bool = False
    is_archived: bool = False
    created_at: str


class BrainDumpUpdateRequest(BaseModel):
    """Brain dump update request."""

    category: str | None = None
    priority: str | None = None
    tags: list[str] | None = None
    is_archived: bool | None = None
    is_processed: bool | None = None


class DailyStatsResponse(BaseModel):
    """Daily statistics response."""

    date: str
    total_dumps: int
    category_breakdown: dict[str, int]
    total_action_items: int
    ideas_count: int
    todos_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_response(record) -> BrainDumpResponse:
    return BrainDumpResponse(
        id=str(record.id),
        raw_text=record.raw_text,
        category=record.category,
        priority=record.priority,
        title=record.title,
        tags=record.tags_json or [],
        action_items=record.action_items_json or [],
        is_processed=record.is_processed,
        is_archived=record.is_archived,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/companies/{company_id}/brain-dump", response_model=BrainDumpResponse)
@limiter.limit("30/minute")
async def create_brain_dump(
    request: Request,
    company_id: str,
    req: BrainDumpRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dump thoughts, ideas, and todos."""
    # PII detection and masking
    pii_result = detect_and_mask_pii(req.raw_text)
    if pii_result.detected_count > 0:
        logger.warning(
            "PII detected in brain dump: types=%s, count=%d",
            pii_result.detected_types,
            pii_result.detected_count,
        )

    svc = SecretaryService(db)
    record = await svc.brain_dump(
        company_id=company_id,
        raw_text=pii_result.masked_text,
        category=req.category,
        priority=req.priority,
        tags=req.tags,
    )
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.get("/companies/{company_id}/brain-dumps", response_model=list[BrainDumpResponse])
async def list_brain_dumps(
    company_id: str,
    category: str | None = None,
    priority: str | None = None,
    is_archived: bool = False,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List brain dumps."""
    svc = SecretaryService(db)
    records = await svc.list_dumps(
        company_id=company_id,
        category=category,
        priority=priority,
        is_archived=is_archived,
        offset=offset,
        limit=limit,
    )
    return [_to_response(r) for r in records]


@router.get("/brain-dumps/{dump_id}", response_model=BrainDumpResponse)
async def get_brain_dump(
    dump_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single brain dump."""
    svc = SecretaryService(db)
    record = await svc.get_dump(dump_id)
    if not record:
        raise HTTPException(status_code=404, detail="Brain dump not found")
    return _to_response(record)


@router.patch("/brain-dumps/{dump_id}", response_model=BrainDumpResponse)
async def update_brain_dump(
    dump_id: str,
    req: BrainDumpUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a brain dump."""
    svc = SecretaryService(db)
    record = await svc.update_dump(
        dump_id=dump_id,
        category=req.category,
        priority=req.priority,
        tags=req.tags,
        is_archived=req.is_archived,
        is_processed=req.is_processed,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Brain dump not found")
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.get("/companies/{company_id}/brain-dumps/search", response_model=list[BrainDumpResponse])
async def search_brain_dumps(
    company_id: str,
    q: str = "",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Search brain dumps by keyword."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    svc = SecretaryService(db)
    records = await svc.search_dumps(company_id=company_id, query=q, limit=limit)
    return [_to_response(r) for r in records]


@router.get("/companies/{company_id}/brain-dumps/action-items")
async def get_action_items(
    company_id: str,
    unprocessed_only: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate action items from all brain dumps."""
    svc = SecretaryService(db)
    items = await svc.get_action_items(
        company_id=company_id,
        unprocessed_only=unprocessed_only,
    )
    return {"action_items": items, "total": len(items)}


@router.get("/companies/{company_id}/brain-dumps/daily-stats", response_model=DailyStatsResponse)
async def get_daily_stats(
    company_id: str,
    target_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get brain dump statistics for a specified date."""
    date_str = target_date or date.today().isoformat()
    svc = SecretaryService(db)
    stats = await svc.get_daily_stats(company_id=company_id, date_str=date_str)
    return DailyStatsResponse(**stats)
