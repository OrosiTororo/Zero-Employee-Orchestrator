"""RSS/ToS 自動更新パイプライン — AI サービスの変更を自動監視.

主要 AI プロバイダーの RSS フィード・利用規約・料金ページを定期的に監視し、
モデル更新・料金変更・利用規約改定・廃止予定などの変更を自動検出する。

検出された変更はモデルカタログの自動更新トリガーとして使用される。

対応プロバイダー:
- OpenAI, Anthropic, Google AI, Mistral, Cohere, Meta AI

安全性:
- 外部 HTTP 通信はデータ保護ポリシーに従う
- 取得コンテンツの LLM 入力時は wrap_external_data() を適用
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
    """検出される変更の種類."""

    MODEL_UPDATE = "model_update"
    PRICING_CHANGE = "pricing_change"
    TOS_UPDATE = "tos_update"
    NEW_FEATURE = "new_feature"
    DEPRECATION = "deprecation"
    API_CHANGE = "api_change"
    SECURITY_ADVISORY = "security_advisory"


class ImpactLevel(str, Enum):
    """変更の影響レベル."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MonitoredService:
    """監視対象のサービス."""

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
    """検出された変更."""

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


# 主要 AI プロバイダーの事前定義
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

# 変更分類用キーワード
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
    """RSS/ToS 自動更新モニター.

    AI プロバイダーの RSS フィード・利用規約・料金ページを定期的に監視し、
    変更を検出して通知・モデルカタログ更新をトリガーする。
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
        """監視対象サービスを登録する.

        Args:
            name: サービス名
            rss_url: RSS フィード URL
            tos_url: 利用規約 URL
            pricing_url: 料金ページ URL
            interval: チェック間隔（時間）

        Returns:
            登録されたサービス
        """
        service = MonitoredService(
            name=name,
            rss_url=rss_url,
            tos_url=tos_url,
            pricing_url=pricing_url,
            check_interval_hours=interval,
        )
        self._services[service.id] = service
        logger.info("監視サービス登録: %s (%s)", name, service.id)
        return service

    async def check_service(self, service_id: str) -> list[DetectedChange]:
        """指定サービスの変更をチェックする.

        RSS フィードと ToS ページを取得し、前回チェック時からの変更を検出する。

        Args:
            service_id: サービスID

        Returns:
            検出された変更のリスト
        """
        service = self._services.get(service_id)
        if not service:
            logger.warning("不明なサービスID: %s", service_id)
            return []

        changes: list[DetectedChange] = []

        # RSS フィードのチェック
        if service.rss_url:
            rss_changes = await self._check_rss(service)
            changes.extend(rss_changes)

        # ToS ページのチェック
        if service.tos_url:
            tos_changes = await self._check_tos(service)
            changes.extend(tos_changes)

        # 料金ページのチェック
        if service.pricing_url:
            pricing_changes = await self._check_pricing(service)
            changes.extend(pricing_changes)

        service.last_checked = datetime.now(UTC)
        if changes:
            service.last_change_detected = datetime.now(UTC)
            self._changes.extend(changes)

        logger.info(
            "サービスチェック完了: %s, 変更数=%d",
            service.name,
            len(changes),
        )
        return changes

    async def check_all(self) -> list[DetectedChange]:
        """全サービスの変更をチェックする.

        チェック間隔を超えたサービスのみ対象とする。

        Returns:
            検出された全変更のリスト
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

        logger.info("全サービスチェック完了: 合計変更数=%d", len(all_changes))
        return all_changes

    async def _check_rss(self, service: MonitoredService) -> list[DetectedChange]:
        """RSS フィードを取得してチェックする.

        取得した外部コンテンツはプロンプトインジェクション検査を適用する。
        """
        content = await self._fetch_url(service.rss_url)
        if not content:
            return []

        # 外部データのプロンプトインジェクション検査
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
        """利用規約ページの変更を検出する."""
        content = await self._fetch_url(service.tos_url)
        if not content:
            return []

        return self._detect_tos_changes(service, content)

    async def _check_pricing(self, service: MonitoredService) -> list[DetectedChange]:
        """料金ページの変更を検出する."""
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
                title=f"{service.name} 料金ページ更新検出",
                summary=f"{service.name} の料金ページに変更が検出されました。",
                source_url=service.pricing_url,
                impact_level=ImpactLevel.MEDIUM,
            )
        ]

    def _parse_rss_feed(self, content: str) -> list[dict[str, str]]:
        """RSS XML をパースしてエントリーを抽出する.

        簡易 XML パーサーで <item> / <entry> 要素を抽出する。

        Args:
            content: RSS フィードの XML 文字列

        Returns:
            エントリーの辞書リスト (title, summary, link, content)
        """
        entries: list[dict[str, str]] = []

        # <item> (RSS 2.0) または <entry> (Atom) を検出
        item_pattern = re.compile(
            r"<(?:item|entry)>(.*?)</(?:item|entry)>",
            re.DOTALL | re.IGNORECASE,
        )

        for match in item_pattern.finditer(content):
            item_xml = match.group(1)
            entry: dict[str, str] = {}

            # タイトル
            title_match = re.search(r"<title[^>]*>(.*?)</title>", item_xml, re.DOTALL)
            if title_match:
                entry["title"] = self._strip_xml_tags(title_match.group(1)).strip()

            # リンク
            link_match = re.search(
                r"<link[^>]*(?:href=[\"']([^\"']+)[\"']|>(.*?)</link>)",
                item_xml,
                re.DOTALL,
            )
            if link_match:
                entry["link"] = (link_match.group(1) or link_match.group(2) or "").strip()

            # 概要
            desc_match = re.search(
                r"<(?:description|summary)[^>]*>(.*?)</(?:description|summary)>",
                item_xml,
                re.DOTALL,
            )
            if desc_match:
                entry["summary"] = self._strip_xml_tags(desc_match.group(1)).strip()

            # 本文
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
        """利用規約の変更を検出する.

        キャッシュ済みのハッシュと比較して変更を検出する。

        Args:
            service: 監視対象サービス
            current_content: 現在の利用規約テキスト

        Returns:
            検出された変更のリスト
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
                title=f"{service.name} 利用規約更新検出",
                summary=f"{service.name} の利用規約に変更が検出されました。確認してください。",
                source_url=service.tos_url,
                impact_level=ImpactLevel.HIGH,
            )
        ]

    def _classify_change(self, title: str, content: str) -> ChangeType:
        """タイトルと内容からChangeTypeを判定する.

        キーワードマッチングに基づいて変更の種類を分類する。

        Args:
            title: 変更のタイトル
            content: 変更の内容

        Returns:
            判定された変更タイプ
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
        """変更の影響レベルを評価する.

        Args:
            change: 検出された変更

        Returns:
            影響レベル
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
        """テキストと変更タイプから影響レベルを評価する."""
        # 変更タイプに基づくベースライン
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

        # 緊急キーワードでエスカレーション
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
        """最近の変更を取得する.

        Args:
            limit: 取得件数上限
            change_type: フィルタする変更タイプ
            service_name: フィルタするサービス名

        Returns:
            フィルタ済みの変更リスト（新しい順）
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
        """変更を確認済みにする.

        Args:
            change_id: 変更ID

        Returns:
            確認済みに設定できたかどうか
        """
        for change in self._changes:
            if change.id == change_id:
                change.acknowledged = True
                logger.info("変更確認済み: %s", change_id)
                return True
        return False

    def get_monitoring_status(self) -> dict:
        """監視状況の概要を返す.

        Returns:
            サービス数・変更数・未確認数などの概要辞書
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
        """モデルカタログの更新をトリガーする.

        MODEL_UPDATE タイプの変更が検出された場合にモデルカタログの
        更新処理を起動する。ユーザーがファイルを一切触らずに
        AI モデル更新を自動で行う。

        Args:
            change: 検出されたモデル更新の変更

        Returns:
            更新がトリガーされたかどうか
        """
        if change.change_type != ChangeType.MODEL_UPDATE:
            logger.debug("モデル更新ではないためスキップ: %s", change.change_type.value)
            return False

        service = self._services.get(change.service_id)
        service_name = service.name if service else change.service_id

        logger.info(
            "モデルカタログ更新トリガー: service=%s, title=%s",
            service_name,
            change.title,
        )

        try:
            from app.providers.model_registry import get_model_registry

            registry = get_model_registry()
            updated = await registry.refresh_catalog()
            if updated:
                logger.info(
                    "モデルカタログ自動更新完了: service=%s, updated=%s",
                    service_name,
                    updated,
                )
            else:
                logger.info("モデルカタログ変更なし: %s", service_name)
            return True
        except Exception as exc:
            logger.error("モデルカタログ更新失敗: %s", exc)

        return False

    async def check_and_auto_update(self) -> dict:
        """全サービスをチェックし、モデル更新を自動適用する.

        RSS/ToS パイプラインからモデル更新を検出し、
        model_catalog.json を自動で更新する。
        ユーザーの手動操作は不要。

        Returns:
            更新結果の概要
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
        """URL からコンテンツを取得する.

        httpx を使用して非同期 HTTP GET を実行する。

        Args:
            url: 取得対象の URL

        Returns:
            レスポンスのテキスト。エラー時は空文字列。
        """
        if not url:
            return ""

        try:
            import httpx
        except ImportError:
            logger.warning("httpx が未インストールのため URL 取得をスキップ: %s", url)
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
            logger.warning("URL 取得失敗: %s — %s", url, exc)
            return ""

    @staticmethod
    def _hash_content(content: str) -> str:
        """コンテンツの SHA-256 ハッシュを生成する."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _strip_xml_tags(text: str) -> str:
        """XML / HTML タグを除去する."""
        # CDATA セクションの展開
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        # タグの除去
        text = re.sub(r"<[^>]+>", "", text)
        # HTML エンティティの基本的な変換
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text


# グローバルインスタンス
rss_tos_monitor = RSSToSMonitor()
