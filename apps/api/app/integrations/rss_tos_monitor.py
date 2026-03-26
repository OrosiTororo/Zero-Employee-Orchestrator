"""RSS/ToS auto-update pipeline — automatically monitor changes in AI services.

Periodically monitors RSS feeds, terms of service, and pricing pages of major
AI providers, automatically detecting changes such as model updates, pricing
changes, terms of service revisions, and deprecation notices.

Detected changes are used as triggers for automatic model catalog updates.

Supported providers:
- OpenAI, Anthropic, Google AI, Mistral, Cohere, Meta AI

Safety:
- External HTTP communication follows data protection policies
- wrap_external_data() is applied when feeding fetched content to LLMs
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of detected changes."""

    MODEL_UPDATE = "model_update"
    PRICING_CHANGE = "pricing_change"
    TOS_UPDATE = "tos_update"
    NEW_FEATURE = "new_feature"
    DEPRECATION = "deprecation"
    API_CHANGE = "api_change"
    SECURITY_ADVISORY = "security_advisory"


class ImpactLevel(str, Enum):
    """Impact level of changes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MonitoredService:
    """Monitored service."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    rss_url: str = ""
    tos_url: str = ""
    pricing_url: str = ""
    check_interval_hours: int = 24
    last_checked: datetime | None = None
    last_change_detected: datetime | None = None


@dataclass
class DetectedChange:
    """Detected change."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str = ""
    change_type: ChangeType = ChangeType.MODEL_UPDATE
    title: str = ""
    summary: str = ""
    details: str = ""
    source_url: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged: bool = False
    impact_level: ImpactLevel = ImpactLevel.LOW


# Predefined major AI providers
_DEFAULT_SERVICES: list[MonitoredService] = [
    MonitoredService(
        id="openai",
        name="OpenAI",
        rss_url="https://openai.com/blog/rss.xml",
        tos_url="https://openai.com/policies/terms-of-use",
        pricing_url="https://openai.com/pricing",
        check_interval_hours=12,
    ),
    MonitoredService(
        id="anthropic",
        name="Anthropic",
        rss_url="https://www.anthropic.com/rss.xml",
        tos_url="https://www.anthropic.com/policies/terms",
        pricing_url="https://www.anthropic.com/pricing",
        check_interval_hours=12,
    ),
    MonitoredService(
        id="google_ai",
        name="Google AI",
        rss_url="https://blog.google/technology/ai/rss/",
        tos_url="https://ai.google.dev/terms",
        pricing_url="https://ai.google.dev/pricing",
        check_interval_hours=12,
    ),
    MonitoredService(
        id="mistral",
        name="Mistral AI",
        rss_url="https://mistral.ai/feed/",
        tos_url="https://mistral.ai/terms/",
        pricing_url="https://mistral.ai/technology/#pricing",
        check_interval_hours=24,
    ),
    MonitoredService(
        id="cohere",
        name="Cohere",
        rss_url="https://cohere.com/blog/rss.xml",
        tos_url="https://cohere.com/terms-of-use",
        pricing_url="https://cohere.com/pricing",
        check_interval_hours=24,
    ),
    MonitoredService(
        id="meta_ai",
        name="Meta AI",
        rss_url="https://ai.meta.com/blog/rss/",
        tos_url="https://ai.meta.com/llama/license/",
        pricing_url="",
        check_interval_hours=24,
    ),
]

# Keywords for change classification
_CHANGE_KEYWORDS: dict[ChangeType, list[str]] = {
    ChangeType.MODEL_UPDATE: [
        "model",
        "release",
        "launch",
        "new version",
        "update",
        "モデル",
        "リリース",
        "新バージョン",
        "gpt",
        "claude",
        "gemini",
        "llama",
        "mistral",
    ],
    ChangeType.PRICING_CHANGE: [
        "pricing",
        "price",
        "cost",
        "rate",
        "tier",
        "plan",
        "料金",
        "価格",
        "プラン",
    ],
    ChangeType.TOS_UPDATE: [
        "terms",
        "policy",
        "privacy",
        "compliance",
        "legal",
        "規約",
        "ポリシー",
        "プライバシー",
    ],
    ChangeType.NEW_FEATURE: [
        "feature",
        "capability",
        "api",
        "endpoint",
        "function",
        "機能",
        "API",
    ],
    ChangeType.DEPRECATION: [
        "deprecat",
        "sunset",
        "end of life",
        "eol",
        "discontinu",
        "remov",
        "廃止",
        "終了",
    ],
    ChangeType.API_CHANGE: [
        "api change",
        "breaking change",
        "migration",
        "upgrade",
        "API 変更",
        "マイグレーション",
    ],
    ChangeType.SECURITY_ADVISORY: [
        "security",
        "vulnerability",
        "patch",
        "cve",
        "advisory",
        "セキュリティ",
        "脆弱性",
    ],
}


class RSSToSMonitor:
    """RSS/ToS auto-update monitor.

    Periodically monitors AI provider RSS feeds, terms of service, and pricing
    pages, detecting changes and triggering notifications and model catalog updates.
    """

    def __init__(self) -> None:
        self._services: dict[str, MonitoredService] = {s.id: s for s in _DEFAULT_SERVICES}
        self._changes: list[DetectedChange] = []
        self._feed_cache: dict[str, str] = {}

    def register_service(
        self,
        name: str,
        rss_url: str = "",
        tos_url: str = "",
        pricing_url: str = "",
        interval: int = 24,
    ) -> MonitoredService:
        """Register a service to monitor.

        Args:
            name: Service name
            rss_url: RSS feed URL
            tos_url: Terms of service URL
            pricing_url: Pricing page URL
            interval: Check interval (hours)

        Returns:
            Registered service
        """
        service = MonitoredService(
            name=name,
            rss_url=rss_url,
            tos_url=tos_url,
            pricing_url=pricing_url,
            check_interval_hours=interval,
        )
        self._services[service.id] = service
        logger.info("Monitoring service registered: %s (%s)", name, service.id)
        return service

    async def check_service(self, service_id: str) -> list[DetectedChange]:
        """Check for changes in a specified service.

        Fetches RSS feeds and ToS pages, detecting changes since the last check.

        Args:
            service_id: Service ID

        Returns:
            List of detected changes
        """
        service = self._services.get(service_id)
        if not service:
            logger.warning("Unknown service ID: %s", service_id)
            return []

        changes: list[DetectedChange] = []

        # Check RSS feed
        if service.rss_url:
            rss_changes = await self._check_rss(service)
            changes.extend(rss_changes)

        # Check ToS page
        if service.tos_url:
            tos_changes = await self._check_tos(service)
            changes.extend(tos_changes)

        # Check pricing page
        if service.pricing_url:
            pricing_changes = await self._check_pricing(service)
            changes.extend(pricing_changes)

        service.last_checked = datetime.now(UTC)
        if changes:
            service.last_change_detected = datetime.now(UTC)
            self._changes.extend(changes)

        logger.info(
            "Service check complete: %s, changes=%d",
            service.name,
            len(changes),
        )
        return changes

    async def check_all(self) -> list[DetectedChange]:
        """Check all services for changes.

        Only targets services that have exceeded their check interval.

        Returns:
            List of all detected changes
        """
        now = datetime.now(UTC)
        all_changes: list[DetectedChange] = []

        for service_id, service in self._services.items():
            if service.last_checked:
                interval = timedelta(hours=service.check_interval_hours)
                if now - service.last_checked < interval:
                    continue

            changes = await self.check_service(service_id)
            all_changes.extend(changes)

        logger.info("All services check complete: total_changes=%d", len(all_changes))
        return all_changes

    async def _check_rss(self, service: MonitoredService) -> list[DetectedChange]:
        """Fetch and check RSS feed.

        Prompt injection inspection is applied to fetched external content.
        """
        content = await self._fetch_url(service.rss_url)
        if not content:
            return []

        # Prompt injection inspection of external data
        try:
            from app.security.prompt_guard import scan_prompt_injection

            guard = scan_prompt_injection(content[:3000])
            if not guard.is_safe:
                logger.warning(
                    "Prompt injection detected in RSS feed %s: %s",
                    service.name,
                    guard.detections,
                )
        except ImportError:
            pass

        content_hash = self._hash_content(content)
        cache_key = f"rss:{service.id}"
        if self._feed_cache.get(cache_key) == content_hash:
            return []

        self._feed_cache[cache_key] = content_hash
        entries = self._parse_rss_feed(content)

        changes: list[DetectedChange] = []
        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", service.rss_url)

            change_type = self._classify_change(title, summary)
            impact = self._assess_impact_from_text(title, summary, change_type)

            change = DetectedChange(
                service_id=service.id,
                change_type=change_type,
                title=title,
                summary=summary,
                details=entry.get("content", ""),
                source_url=link,
                impact_level=impact,
            )
            changes.append(change)

        return changes

    async def _check_tos(self, service: MonitoredService) -> list[DetectedChange]:
        """Detect changes in terms of service page."""
        content = await self._fetch_url(service.tos_url)
        if not content:
            return []

        return self._detect_tos_changes(service, content)

    async def _check_pricing(self, service: MonitoredService) -> list[DetectedChange]:
        """Detect changes in pricing page."""
        content = await self._fetch_url(service.pricing_url)
        if not content:
            return []

        content_hash = self._hash_content(content)
        cache_key = f"pricing:{service.id}"
        if self._feed_cache.get(cache_key) == content_hash:
            return []

        self._feed_cache[cache_key] = content_hash
        return [
            DetectedChange(
                service_id=service.id,
                change_type=ChangeType.PRICING_CHANGE,
                title=f"{service.name} pricing page update detected",
                summary=f"Changes detected in {service.name} pricing page.",
                source_url=service.pricing_url,
                impact_level=ImpactLevel.MEDIUM,
            )
        ]

    def _parse_rss_feed(self, content: str) -> list[dict[str, str]]:
        """Parse RSS XML and extract entries.

        Uses a simple XML parser to extract <item> / <entry> elements.

        Args:
            content: RSS feed XML string

        Returns:
            List of entry dictionaries (title, summary, link, content)
        """
        entries: list[dict[str, str]] = []

        # Detect <item> (RSS 2.0) or <entry> (Atom)
        item_pattern = re.compile(
            r"<(?:item|entry)>(.*?)</(?:item|entry)>",
            re.DOTALL | re.IGNORECASE,
        )

        for match in item_pattern.finditer(content):
            item_xml = match.group(1)
            entry: dict[str, str] = {}

            # Title
            title_match = re.search(r"<title[^>]*>(.*?)</title>", item_xml, re.DOTALL)
            if title_match:
                entry["title"] = self._strip_xml_tags(title_match.group(1)).strip()

            # Link
            link_match = re.search(
                r"<link[^>]*(?:href=[\"']([^\"']+)[\"']|>(.*?)</link>)",
                item_xml,
                re.DOTALL,
            )
            if link_match:
                entry["link"] = (link_match.group(1) or link_match.group(2) or "").strip()

            # Summary
            desc_match = re.search(
                r"<(?:description|summary)[^>]*>(.*?)</(?:description|summary)>",
                item_xml,
                re.DOTALL,
            )
            if desc_match:
                entry["summary"] = self._strip_xml_tags(desc_match.group(1)).strip()

            # Body
            content_match = re.search(
                r"<content[^>]*>(.*?)</content>",
                item_xml,
                re.DOTALL,
            )
            if content_match:
                entry["content"] = self._strip_xml_tags(content_match.group(1)).strip()

            if entry.get("title"):
                entries.append(entry)

        return entries

    def _detect_tos_changes(
        self,
        service: MonitoredService,
        current_content: str,
    ) -> list[DetectedChange]:
        """Detect changes in terms of service.

        Compares with cached hash to detect changes.

        Args:
            service: Monitored service
            current_content: Current terms of service text

        Returns:
            List of detected changes
        """
        content_hash = self._hash_content(current_content)
        cache_key = f"tos:{service.id}"

        if self._feed_cache.get(cache_key) == content_hash:
            return []

        self._feed_cache[cache_key] = content_hash

        return [
            DetectedChange(
                service_id=service.id,
                change_type=ChangeType.TOS_UPDATE,
                title=f"{service.name} terms of service update detected",
                summary=f"Changes detected in {service.name} terms of service. Please review.",
                source_url=service.tos_url,
                impact_level=ImpactLevel.HIGH,
            )
        ]

    def _classify_change(self, title: str, content: str) -> ChangeType:
        """Determine ChangeType from title and content.

        Classifies the type of change based on keyword matching.

        Args:
            title: Title of the change
            content: Content of the change

        Returns:
            Determined change type
        """
        combined = f"{title} {content}".lower()
        scores: dict[ChangeType, int] = {ct: 0 for ct in ChangeType}

        for change_type, keywords in _CHANGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in combined:
                    scores[change_type] += 1

        best = max(scores, key=lambda ct: scores[ct])
        if scores[best] == 0:
            return ChangeType.NEW_FEATURE

        return best

    def _assess_impact(self, change: DetectedChange) -> ImpactLevel:
        """Assess the impact level of a change.

        Args:
            change: Detected change

        Returns:
            Impact level
        """
        return self._assess_impact_from_text(
            change.title,
            change.summary,
            change.change_type,
        )

    def _assess_impact_from_text(
        self,
        title: str,
        summary: str,
        change_type: ChangeType,
    ) -> ImpactLevel:
        """Assess impact level from text and change type."""
        # Baseline based on change type
        type_impact: dict[ChangeType, ImpactLevel] = {
            ChangeType.SECURITY_ADVISORY: ImpactLevel.CRITICAL,
            ChangeType.DEPRECATION: ImpactLevel.HIGH,
            ChangeType.TOS_UPDATE: ImpactLevel.HIGH,
            ChangeType.API_CHANGE: ImpactLevel.HIGH,
            ChangeType.PRICING_CHANGE: ImpactLevel.MEDIUM,
            ChangeType.MODEL_UPDATE: ImpactLevel.MEDIUM,
            ChangeType.NEW_FEATURE: ImpactLevel.LOW,
        }

        base_level = type_impact.get(change_type, ImpactLevel.LOW)

        # Escalate on urgency keywords
        combined = f"{title} {summary}".lower()
        critical_words = [
            "breaking",
            "urgent",
            "critical",
            "security",
            "vulnerability",
            "immediately",
            "緊急",
            "重大",
            "脆弱性",
        ]
        if any(w in combined for w in critical_words):
            return ImpactLevel.CRITICAL

        return base_level

    def get_recent_changes(
        self,
        limit: int = 50,
        change_type: ChangeType | None = None,
        service_name: str | None = None,
    ) -> list[DetectedChange]:
        """Get recent changes.

        Args:
            limit: Maximum number of entries to retrieve
            change_type: Change type to filter by
            service_name: Service name to filter by

        Returns:
            Filtered list of changes (newest first)
        """
        filtered = self._changes

        if change_type is not None:
            filtered = [c for c in filtered if c.change_type == change_type]

        if service_name is not None:
            service_ids = {
                sid for sid, s in self._services.items() if s.name.lower() == service_name.lower()
            }
            filtered = [c for c in filtered if c.service_id in service_ids]

        sorted_changes = sorted(
            filtered,
            key=lambda c: c.detected_at,
            reverse=True,
        )
        return sorted_changes[:limit]

    def acknowledge_change(self, change_id: str) -> bool:
        """Mark a change as acknowledged.

        Args:
            change_id: Change ID

        Returns:
            Whether it was successfully marked as acknowledged
        """
        for change in self._changes:
            if change.id == change_id:
                change.acknowledged = True
                logger.info("Change acknowledged: %s", change_id)
                return True
        return False

    def get_monitoring_status(self) -> dict:
        """Return a monitoring status summary.

        Returns:
            Summary dictionary with service count, change count, unacknowledged count, etc.
        """
        now = datetime.now(UTC)
        unacknowledged = [c for c in self._changes if not c.acknowledged]
        overdue: list[str] = []

        for service in self._services.values():
            if service.last_checked:
                interval = timedelta(hours=service.check_interval_hours)
                if now - service.last_checked > interval:
                    overdue.append(service.name)
            else:
                overdue.append(service.name)

        return {
            "total_services": len(self._services),
            "total_changes_detected": len(self._changes),
            "unacknowledged_changes": len(unacknowledged),
            "critical_changes": len(
                [c for c in unacknowledged if c.impact_level == ImpactLevel.CRITICAL]
            ),
            "overdue_checks": overdue,
            "services": {
                s.id: {
                    "name": s.name,
                    "last_checked": s.last_checked.isoformat() if s.last_checked else None,
                    "last_change": (
                        s.last_change_detected.isoformat() if s.last_change_detected else None
                    ),
                    "interval_hours": s.check_interval_hours,
                }
                for s in self._services.values()
            },
        }

    async def update_model_catalog(self, change: DetectedChange) -> bool:
        """Trigger a model catalog update.

        When a MODEL_UPDATE type change is detected, initiates the model
        catalog update process. Automatically updates AI models without
        any user file manipulation.

        Args:
            change: Detected model update change

        Returns:
            Whether the update was triggered
        """
        if change.change_type != ChangeType.MODEL_UPDATE:
            logger.debug("Not a model update, skipping: %s", change.change_type.value)
            return False

        service = self._services.get(change.service_id)
        service_name = service.name if service else change.service_id

        logger.info(
            "Model catalog update trigger: service=%s, title=%s",
            service_name,
            change.title,
        )

        try:
            from app.providers.model_registry import get_model_registry

            registry = get_model_registry()
            updated = await registry.refresh_catalog()
            if updated:
                logger.info(
                    "Model catalog auto-update complete: service=%s, updated=%s",
                    service_name,
                    updated,
                )
            else:
                logger.info("No model catalog changes: %s", service_name)
            return True
        except Exception as exc:
            logger.error("Model catalog update failed: %s", exc)

        return False

    async def check_and_auto_update(self) -> dict:
        """Check all services and auto-apply model updates.

        Detects model updates from the RSS/ToS pipeline and
        automatically updates model_catalog.json.
        No manual user action required.

        Returns:
            Update result summary
        """
        changes = await self.check_all()
        model_updates = [c for c in changes if c.change_type == ChangeType.MODEL_UPDATE]
        auto_updated = 0

        for change in model_updates:
            if await self.update_model_catalog(change):
                auto_updated += 1

        return {
            "total_changes": len(changes),
            "model_updates_detected": len(model_updates),
            "auto_updated": auto_updated,
        }

    async def _fetch_url(self, url: str) -> str:
        """Fetch content from a URL.

        Executes an async HTTP GET using httpx.

        Args:
            url: Target URL to fetch

        Returns:
            Response text. Empty string on error.
        """
        if not url:
            return ""

        try:
            import httpx
        except ImportError:
            logger.warning("httpx not installed, skipping URL fetch: %s", url)
            return ""

        try:
            async with httpx.AsyncClient(
                timeout=30,
                follow_redirects=True,
                headers={"User-Agent": "ZEO-RSS-Monitor/1.0"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as exc:
            logger.warning("URL fetch failed: %s — %s", url, exc)
            return ""

    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate a SHA-256 hash of the content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _strip_xml_tags(text: str) -> str:
        """Strip XML / HTML tags."""
        # Expand CDATA sections
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        # Remove tags
        text = re.sub(r"<[^>]+>", "", text)
        # Basic HTML entity conversion
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text


# Global instance
rss_tos_monitor = RSSToSMonitor()
