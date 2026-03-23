"""Skill マーケットプレイス API エンドポイント.

コミュニティ Skill / Plugin / Extension の公開・検索・レビュー・
インストールを提供する。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services.marketplace_service import (
    ListingStatus,
    MarketplaceCategory,
    MarketplaceListing,
    marketplace_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ---------- Schemas ----------


class PublishRequest(BaseModel):
    """Listing 公開リクエスト."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    author: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="0.1.0")
    category: str = Field(default="other")
    skill_type: str = Field(default="skill", description="skill | plugin | extension")
    manifest: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    """レビュー投稿リクエスト."""

    user_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


class InstallRequest(BaseModel):
    """インストールリクエスト."""

    company_id: str = Field(..., min_length=1)


# ---------- Endpoints ----------


# 認証不要: マーケットプレイス閲覧は公開
@router.get("/search")
async def search_listings(
    query: str = "",
    category: str | None = None,
    sort_by: str = Query(default="downloads", pattern="^(downloads|rating|name|created_at)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """マーケットプレイスの Listing を検索する."""
    cat = None
    if category:
        try:
            cat = MarketplaceCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"無効なカテゴリ: {category}。"
                f"有効値: {[c.value for c in MarketplaceCategory]}",
            )

    results = await marketplace_service.search(
        query=query, category=cat, sort_by=sort_by, limit=limit, offset=offset
    )
    return [_listing_to_dict(r) for r in results]


# 認証不要: マーケットプレイス閲覧は公開
@router.get("/trending")
async def get_trending(
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    """トレンドの Listing を取得する."""
    results = await marketplace_service.get_trending(limit=limit)
    return [_listing_to_dict(r) for r in results]


# 認証不要: マーケットプレイス閲覧は公開
@router.get("/{listing_id}")
async def get_listing(listing_id: str) -> dict:
    """Listing を ID で取得する."""
    listing = await marketplace_service.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing が見つかりません")
    return _listing_to_dict(listing)


@router.post("/publish", status_code=201)
async def publish_listing(
    req: PublishRequest, user: User = Depends(get_current_user)
) -> dict:
    """Listing をレビュー待ちとして公開する."""
    try:
        cat = MarketplaceCategory(req.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無効なカテゴリ: {req.category}",
        )

    listing = MarketplaceListing(
        id="",
        name=req.name,
        description=req.description,
        author=req.author,
        version=req.version,
        category=cat,
        status=ListingStatus.DRAFT,
        skill_type=req.skill_type,
        manifest=req.manifest,
        tags=req.tags,
    )
    result = await marketplace_service.publish(listing)
    return _listing_to_dict(result)


@router.post("/{listing_id}/install")
async def install_listing(
    listing_id: str, req: InstallRequest, user: User = Depends(get_current_user)
) -> dict:
    """Listing を企業にインストールする."""
    try:
        listing = await marketplace_service.install(listing_id, req.company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "status": "installed",
        "listing": _listing_to_dict(listing),
        "company_id": req.company_id,
    }


@router.post("/{listing_id}/review", status_code=201)
async def add_review(
    listing_id: str, req: ReviewRequest, user: User = Depends(get_current_user)
) -> dict:
    """Listing にレビューを追加する."""
    try:
        review = await marketplace_service.add_review(
            listing_id=listing_id,
            user_id=req.user_id,
            rating=req.rating,
            comment=req.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": review.id,
        "listing_id": review.listing_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
    }


# ---------- ヘルパー ----------


def _listing_to_dict(listing: MarketplaceListing) -> dict:
    """MarketplaceListing を dict に変換する."""
    return {
        "id": listing.id,
        "name": listing.name,
        "description": listing.description,
        "author": listing.author,
        "version": listing.version,
        "category": listing.category.value,
        "status": listing.status.value,
        "skill_type": listing.skill_type,
        "downloads": listing.downloads,
        "rating": listing.rating,
        "reviews_count": listing.reviews_count,
        "created_at": listing.created_at,
        "updated_at": listing.updated_at,
        "tags": listing.tags,
    }
