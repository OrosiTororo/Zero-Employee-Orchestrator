"""Tests for marketplace_service."""

from __future__ import annotations

import pytest

from app.services.marketplace_service import (
    ListingStatus,
    MarketplaceCategory,
    MarketplaceListing,
    MarketplaceService,
)


def _make_listing(name: str = "demo-skill") -> MarketplaceListing:
    return MarketplaceListing(
        id="",
        name=name,
        description="demo description",
        author="tester",
        version="0.1.0",
        category=MarketplaceCategory.DEVELOPMENT,
        status=ListingStatus.DRAFT,
        skill_type="skill",
    )


@pytest.mark.asyncio
async def test_publish_sets_pending_review_and_assigns_id():
    svc = MarketplaceService()
    listing = await svc.publish(_make_listing())
    assert listing.id
    assert listing.status == ListingStatus.PENDING_REVIEW


@pytest.mark.asyncio
async def test_approve_transitions_to_published():
    svc = MarketplaceService()
    listing = await svc.publish(_make_listing())
    approved = await svc.approve(listing.id)
    assert approved.status == ListingStatus.PUBLISHED


@pytest.mark.asyncio
async def test_reject_rejects_unknown_listing():
    svc = MarketplaceService()
    with pytest.raises(ValueError):
        await svc.reject("nonexistent-id", reason="bad")


@pytest.mark.asyncio
async def test_search_returns_only_published():
    svc = MarketplaceService()
    published = await svc.publish(_make_listing(name="published-one"))
    await svc.approve(published.id)
    # Draft listing (pending) should be filtered out by search.
    await svc.publish(_make_listing(name="pending-one"))

    results = await svc.search(category=MarketplaceCategory.DEVELOPMENT)
    ids = [r.id for r in results]
    assert published.id in ids


@pytest.mark.asyncio
async def test_install_requires_published_listing():
    svc = MarketplaceService()
    listing = await svc.publish(_make_listing())
    # Not yet approved — install must reject.
    with pytest.raises(ValueError):
        await svc.install(listing.id, company_id="co-1")

    await svc.approve(listing.id)
    installed = await svc.install(listing.id, company_id="co-1")
    assert installed.downloads >= 1
