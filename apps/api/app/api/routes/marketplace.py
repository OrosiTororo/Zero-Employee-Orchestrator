"""Skill marketplace API endpoints.

Provides publishing, searching, reviewing, and installing
community Skills / Plugins / Extensions.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection
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
    """Listing publish request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    author: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="0.1.0")
    category: str = Field(default="other")
    skill_type: str = Field(default="skill", description="skill | plugin | extension")
    manifest: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    """Review submission request."""

    user_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


class InstallRequest(BaseModel):
    """Install request."""

    company_id: str = Field(..., min_length=1)


# ---------- Response Schemas ----------


class MarketplaceListingResponse(BaseModel):
    """Single marketplace listing response."""

    id: str
    name: str
    description: str
    author: str
    version: str
    category: str
    status: str
    skill_type: str
    downloads: int
    rating: float
    reviews_count: int
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[str] = Field(default_factory=list)


class InstallListingResponse(BaseModel):
    """Response for installing a listing."""

    status: str
    listing: MarketplaceListingResponse
    company_id: str


class ReviewItemResponse(BaseModel):
    """Single review item response."""

    id: str
    listing_id: str
    user_id: str
    rating: int
    comment: str
    created_at: str | None = None


# ---------- Endpoints ----------


# No auth required: marketplace browsing is public
@router.get("/search", response_model=list[MarketplaceListingResponse])
async def search_listings(
    query: str = "",
    category: str | None = None,
    sort_by: str = Query(default="downloads", pattern="^(downloads|rating|name|created_at)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """Search marketplace listings."""
    cat = None
    if category:
        try:
            cat = MarketplaceCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. "
                f"Valid values: {[c.value for c in MarketplaceCategory]}",
            )

    results = await marketplace_service.search(
        query=query, category=cat, sort_by=sort_by, limit=limit, offset=offset
    )
    return [_listing_to_dict(r) for r in results]


# No auth required: marketplace browsing is public
@router.get("/trending", response_model=list[MarketplaceListingResponse])
async def get_trending(
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    """Get trending listings."""
    results = await marketplace_service.get_trending(limit=limit)
    return [_listing_to_dict(r) for r in results]


# No auth required: marketplace browsing is public
@router.get("/{listing_id}", response_model=MarketplaceListingResponse)
async def get_listing(listing_id: str) -> dict:
    """Get a listing by ID."""
    listing = await marketplace_service.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _listing_to_dict(listing)


@router.post("/publish", status_code=201, response_model=MarketplaceListingResponse)
@limiter.limit("10/minute")
async def publish_listing(
    request: Request, req: PublishRequest, user: User = Depends(get_current_user)
) -> dict:
    """Publish a listing as pending review."""
    from app.policies.approval_gate import check_approval_required

    gate = check_approval_required("publish_content")
    if gate.requires_approval:
        logger.info("Marketplace publish gate: risk=%s, user=%s", gate.risk_level, user.id)

    try:
        cat = MarketplaceCategory(req.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {req.category}",
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


@router.post("/{listing_id}/install", response_model=InstallListingResponse)
async def install_listing(
    listing_id: str, req: InstallRequest, user: User = Depends(get_current_user)
) -> dict:
    """Install a listing to a company."""
    try:
        listing = await marketplace_service.install(listing_id, req.company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "status": "installed",
        "listing": _listing_to_dict(listing),
        "company_id": req.company_id,
    }


@router.post("/{listing_id}/review", status_code=201, response_model=ReviewItemResponse)
@limiter.limit("10/minute")
async def add_review(
    request: Request,
    listing_id: str,
    req: ReviewRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Add a review to a listing."""
    # Prompt injection + PII check on review comment
    guard_result = scan_prompt_injection(req.comment)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected.",
        )
    pii_result = detect_and_mask_pii(req.comment)
    if pii_result.detected_count > 0:
        logger.warning("PII detected in marketplace review: types=%s", pii_result.detected_types)

    try:
        review = await marketplace_service.add_review(
            listing_id=listing_id,
            user_id=req.user_id,
            rating=req.rating,
            comment=pii_result.masked_text,
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


@router.get("/{listing_id}/reviews", response_model=list[ReviewItemResponse])
async def get_reviews(listing_id: str) -> list[dict]:
    """Get reviews for a listing."""
    reviews = await marketplace_service.get_reviews(listing_id)
    return [
        {
            "id": r.id,
            "listing_id": r.listing_id,
            "user_id": r.user_id,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at,
        }
        for r in reviews
    ]


@router.post("/{listing_id}/approve", response_model=MarketplaceListingResponse)
async def approve_listing(listing_id: str, user: User = Depends(get_current_user)) -> dict:
    """Approve a pending listing for publication."""
    try:
        listing = await marketplace_service.approve(listing_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _listing_to_dict(listing)


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


@router.post("/{listing_id}/reject", response_model=MarketplaceListingResponse)
async def reject_listing(
    listing_id: str, req: RejectRequest, user: User = Depends(get_current_user)
) -> dict:
    """Reject a pending listing."""
    try:
        listing = await marketplace_service.reject(listing_id, req.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _listing_to_dict(listing)


# ---------- Helpers ----------


def _listing_to_dict(listing: MarketplaceListing) -> dict:
    """Convert MarketplaceListing to dict."""
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
