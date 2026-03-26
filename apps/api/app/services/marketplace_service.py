"""Skill marketplace service -- Community Skill/Plugin publishing, search, review, and installation.

Publishes Skill / Plugin / Extension to the marketplace,
enabling search, review, and installation.

Publishing flow:
1. Developer creates a Listing as DRAFT
2. publish() transitions to review pending (PENDING_REVIEW)
3. Admin approves or rejects with approve() or reject()
4. PUBLISHED Listings become searchable and installable
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MarketplaceCategory(str, Enum):
    """Marketplace category."""

    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    DATA_ANALYSIS = "data_analysis"
    DEVELOPMENT = "development"
    MEDIA = "media"
    SECURITY = "security"
    INTEGRATION = "integration"
    AUTOMATION = "automation"
    AI_ENHANCEMENT = "ai_enhancement"
    OTHER = "other"


class ListingStatus(str, Enum):
    """Listing status."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class MarketplaceListing:
    """Marketplace listing."""

    id: str
    name: str
    description: str
    author: str
    version: str
    category: MarketplaceCategory
    status: ListingStatus
    skill_type: str  # "skill" | "plugin" | "extension"
    manifest: dict = field(default_factory=dict)
    downloads: int = 0
    rating: float = 0.0
    reviews_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Review:
    """Review."""

    id: str
    listing_id: str
    user_id: str
    rating: int  # 1-5
    comment: str
    created_at: str = ""


class MarketplaceService:
    """Skill マーケットプレイスサービス.

    コミュニティ Skill / Plugin / Extension の公開・検索・レビュー・
    インストールを管理する。
    """

    def __init__(self) -> None:
        self._listings: dict[str, MarketplaceListing] = {}
        self._reviews: dict[str, list[Review]] = {}
        self._installed: dict[str, list[str]] = {}  # company_id -> listing_ids

    # ------------------------------------------------------------------
    # Publishing & approval
    # ------------------------------------------------------------------

    async def publish(self, listing: MarketplaceListing) -> MarketplaceListing:
        """Listing をレビュー待ちとして提出する."""
        now = datetime.now(UTC).isoformat()
        if not listing.id:
            listing.id = str(uuid.uuid4())
        listing.status = ListingStatus.PENDING_REVIEW
        listing.created_at = listing.created_at or now
        listing.updated_at = now
        self._listings[listing.id] = listing
        self._reviews.setdefault(listing.id, [])
        logger.info(
            "マーケットプレイス: Listing 提出 id=%s name=%s",
            listing.id,
            listing.name,
        )
        return listing

    async def approve(self, listing_id: str) -> MarketplaceListing:
        """Listing を承認して公開する."""
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ValueError(f"Listing が見つかりません: {listing_id}")
        if listing.status != ListingStatus.PENDING_REVIEW:
            raise ValueError(
                f"承認できるのは PENDING_REVIEW 状態のみです (現在: {listing.status.value})"
            )
        listing.status = ListingStatus.PUBLISHED
        listing.updated_at = datetime.now(UTC).isoformat()
        logger.info("マーケットプレイス: Listing 承認 id=%s", listing_id)
        return listing

    async def reject(self, listing_id: str, reason: str) -> MarketplaceListing:
        """Listing を却下する."""
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ValueError(f"Listing が見つかりません: {listing_id}")
        if listing.status != ListingStatus.PENDING_REVIEW:
            raise ValueError(
                f"却下できるのは PENDING_REVIEW 状態のみです (現在: {listing.status.value})"
            )
        listing.status = ListingStatus.DRAFT
        listing.updated_at = datetime.now(UTC).isoformat()
        logger.info(
            "マーケットプレイス: Listing 却下 id=%s reason=%s",
            listing_id,
            reason,
        )
        return listing

    # ------------------------------------------------------------------
    # Search & retrieval
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str = "",
        category: MarketplaceCategory | None = None,
        sort_by: str = "downloads",
        limit: int = 20,
        offset: int = 0,
    ) -> list[MarketplaceListing]:
        """公開済み Listing を検索する."""
        results: list[MarketplaceListing] = []
        for listing in self._listings.values():
            if listing.status != ListingStatus.PUBLISHED:
                continue
            if category and listing.category != category:
                continue
            if query:
                q = query.lower()
                searchable = (
                    f"{listing.name} {listing.description} {' '.join(listing.tags)}"
                ).lower()
                if q not in searchable:
                    continue
            results.append(listing)

        # ソート
        if sort_by == "rating":
            results.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "name":
            results.sort(key=lambda x: x.name)
        elif sort_by == "created_at":
            results.sort(key=lambda x: x.created_at, reverse=True)
        else:  # downloads (デフォルト)
            results.sort(key=lambda x: x.downloads, reverse=True)

        return results[offset : offset + limit]

    async def get_listing(self, listing_id: str) -> MarketplaceListing | None:
        """Listing を ID で取得する."""
        return self._listings.get(listing_id)

    # ------------------------------------------------------------------
    # Install & uninstall
    # ------------------------------------------------------------------

    async def install(self, listing_id: str, company_id: str) -> MarketplaceListing:
        """Listing を企業にインストールする."""
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ValueError(f"Listing が見つかりません: {listing_id}")
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("公開済みの Listing のみインストール可能です")

        installed = self._installed.setdefault(company_id, [])
        if listing_id in installed:
            raise ValueError("既にインストール済みです")

        installed.append(listing_id)
        listing.downloads += 1
        logger.info(
            "マーケットプレイス: インストール listing=%s company=%s",
            listing_id,
            company_id,
        )
        return listing

    async def uninstall(self, listing_id: str, company_id: str) -> bool:
        """Listing を企業からアンインストールする."""
        installed = self._installed.get(company_id, [])
        if listing_id not in installed:
            raise ValueError("インストールされていません")
        installed.remove(listing_id)
        logger.info(
            "マーケットプレイス: アンインストール listing=%s company=%s",
            listing_id,
            company_id,
        )
        return True

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    async def add_review(
        self,
        listing_id: str,
        user_id: str,
        rating: int,
        comment: str,
    ) -> Review:
        """Listing にレビューを追加する."""
        if listing_id not in self._listings:
            raise ValueError(f"Listing が見つかりません: {listing_id}")
        if not 1 <= rating <= 5:
            raise ValueError("評価は 1〜5 の範囲で指定してください")

        review = Review(
            id=str(uuid.uuid4()),
            listing_id=listing_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            created_at=datetime.now(UTC).isoformat(),
        )
        reviews = self._reviews.setdefault(listing_id, [])
        reviews.append(review)

        # 平均評価を再計算
        listing = self._listings[listing_id]
        listing.reviews_count = len(reviews)
        listing.rating = sum(r.rating for r in reviews) / len(reviews)

        logger.info(
            "マーケットプレイス: レビュー追加 listing=%s user=%s rating=%d",
            listing_id,
            user_id,
            rating,
        )
        return review

    async def get_reviews(self, listing_id: str, limit: int = 20) -> list[Review]:
        """Listing のレビュー一覧を取得する."""
        reviews = self._reviews.get(listing_id, [])
        return sorted(reviews, key=lambda r: r.created_at, reverse=True)[:limit]

    # ------------------------------------------------------------------
    # Trending & installed
    # ------------------------------------------------------------------

    async def get_trending(self, limit: int = 10) -> list[MarketplaceListing]:
        """トレンドの Listing を取得する（ダウンロード数 + 評価でスコアリング）."""
        published = [
            item for item in self._listings.values() if item.status == ListingStatus.PUBLISHED
        ]
        # スコア: ダウンロード数 * 0.7 + 評価 * 0.3 * レビュー数
        published.sort(
            key=lambda x: x.downloads * 0.7 + x.rating * 0.3 * x.reviews_count,
            reverse=True,
        )
        return published[:limit]

    async def get_installed(self, company_id: str) -> list[MarketplaceListing]:
        """企業にインストール済みの Listing 一覧を取得する."""
        installed_ids = self._installed.get(company_id, [])
        return [self._listings[lid] for lid in installed_ids if lid in self._listings]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_listing(self, listing_id: str, updates: dict) -> MarketplaceListing:
        """Listing を更新する."""
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ValueError(f"Listing が見つかりません: {listing_id}")
        if listing.status == ListingStatus.SUSPENDED:
            raise ValueError("停止中の Listing は更新できません")

        allowed_fields = {
            "name",
            "description",
            "version",
            "category",
            "manifest",
            "tags",
            "skill_type",
        }
        for key, value in updates.items():
            if key in allowed_fields:
                if key == "category" and isinstance(value, str):
                    value = MarketplaceCategory(value)
                setattr(listing, key, value)

        listing.updated_at = datetime.now(UTC).isoformat()
        logger.info("マーケットプレイス: Listing 更新 id=%s", listing_id)
        return listing


# Global instance
marketplace_service = MarketplaceService()
