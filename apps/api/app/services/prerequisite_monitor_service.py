"""前提変化の汎用監視サービス — Prerequisite Monitor.

RSS/ToS パイプラインを拡張し、業務に関わる外部情報源（競合サイト、法規制ページ、
依存 API changelogs 等）をユーザーが登録して定期チェックする仕組み。
Heartbeat + Web fetch の組み合わせで実現。

既存の RSSToSMonitor を汎用化し、AI プロバイダー以外の任意の情報源を監視対象にできる。
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------


class PrerequisiteCategory(str, Enum):
    """監視対象のカテゴリ."""

    COMPETITOR = "competitor"
    REGULATION = "regulation"
    DEPENDENCY_API = "dependency_api"
    PRICING = "pricing"
    TOS = "tos"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    CUSTOM = "custom"


class ChangeImpact(str, Enum):
    """変更の影響レベル."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitorStatus(str, Enum):
    """監視ステータス."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PrerequisiteSource:
    """ユーザーが登録する監視対象の外部情報源."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    name: str = ""
    description: str = ""
    url: str = ""
    category: PrerequisiteCategory = PrerequisiteCategory.CUSTOM
    check_interval_hours: int = 24
    keywords: list[str] = field(default_factory=list)
    status: MonitorStatus = MonitorStatus.ACTIVE
    last_checked: datetime | None = None
    last_content_hash: str = ""
    last_change_detected: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""
    notify_on_change: bool = True
    linked_ticket_ids: list[str] = field(default_factory=list)


@dataclass
class PrerequisiteChange:
    """検出された外部変更."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    source_name: str = ""
    category: PrerequisiteCategory = PrerequisiteCategory.CUSTOM
    title: str = ""
    summary: str = ""
    diff_snippet: str = ""
    impact: ChangeImpact = ChangeImpact.LOW
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    affected_ticket_ids: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# キーワードベースの影響レベル自動判定
# ---------------------------------------------------------------------------

_CRITICAL_KEYWORDS = [
    "breaking change", "deprecated", "removed", "shutdown",
    "security vulnerability", "critical", "urgent", "breach",
    "data loss", "service termination", "end of life", "eol",
]

_HIGH_KEYWORDS = [
    "major update", "migration required", "incompatible",
    "regulation change", "compliance", "mandatory", "deadline",
    "rate limit", "quota change", "price increase",
]

_MEDIUM_KEYWORDS = [
    "update", "change", "new version", "release", "amendment",
    "revised", "modified", "pricing", "terms",
]


def _assess_impact(content: str, keywords: list[str]) -> ChangeImpact:
    """コンテンツとキーワードに基づいて影響レベルを自動判定."""
    content_lower = content.lower()

    for kw in _CRITICAL_KEYWORDS:
        if kw in content_lower:
            return ChangeImpact.CRITICAL

    for kw in _HIGH_KEYWORDS:
        if kw in content_lower:
            return ChangeImpact.HIGH

    # ユーザー指定キーワードにマッチした場合は MEDIUM 以上
    matched = [kw for kw in keywords if kw.lower() in content_lower]
    if matched:
        return ChangeImpact.MEDIUM

    for kw in _MEDIUM_KEYWORDS:
        if kw in content_lower:
            return ChangeImpact.MEDIUM

    return ChangeImpact.LOW


def _find_matched_keywords(content: str, keywords: list[str]) -> list[str]:
    """コンテンツ内でマッチしたキーワードを返す."""
    content_lower = content.lower()
    return [kw for kw in keywords if kw.lower() in content_lower]


# ---------------------------------------------------------------------------
# メインサービス
# ---------------------------------------------------------------------------


class PrerequisiteMonitorService:
    """前提変化の汎用監視サービス.

    ユーザーが登録した外部情報源を定期的にチェックし、変更を検出する。
    Heartbeat スケジューラと連携して定期実行が可能。
    """

    def __init__(self) -> None:
        self._sources: dict[str, PrerequisiteSource] = {}
        self._changes: list[PrerequisiteChange] = []
        self._content_cache: dict[str, str] = {}

    # -- ソース管理 --

    def register_source(
        self,
        company_id: str,
        name: str,
        url: str,
        category: PrerequisiteCategory = PrerequisiteCategory.CUSTOM,
        description: str = "",
        check_interval_hours: int = 24,
        keywords: list[str] | None = None,
        created_by: str = "",
        linked_ticket_ids: list[str] | None = None,
    ) -> PrerequisiteSource:
        """監視対象を登録する."""
        source = PrerequisiteSource(
            company_id=company_id,
            name=name,
            url=url,
            category=category,
            description=description,
            check_interval_hours=check_interval_hours,
            keywords=keywords or [],
            created_by=created_by,
            linked_ticket_ids=linked_ticket_ids or [],
        )
        self._sources[source.id] = source
        logger.info("Registered prerequisite source: %s (%s)", name, url)
        return source

    def update_source(
        self,
        source_id: str,
        **kwargs,
    ) -> PrerequisiteSource:
        """監視対象を更新する."""
        source = self._sources.get(source_id)
        if not source:
            raise ValueError(f"Source not found: {source_id}")
        for key, value in kwargs.items():
            if hasattr(source, key):
                setattr(source, key, value)
        return source

    def remove_source(self, source_id: str) -> bool:
        """監視対象を削除する."""
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False

    def get_source(self, source_id: str) -> PrerequisiteSource | None:
        """監視対象を取得する."""
        return self._sources.get(source_id)

    def list_sources(
        self,
        company_id: str | None = None,
        category: PrerequisiteCategory | None = None,
        status: MonitorStatus | None = None,
    ) -> list[PrerequisiteSource]:
        """監視対象を一覧取得する."""
        sources = list(self._sources.values())
        if company_id:
            sources = [s for s in sources if s.company_id == company_id]
        if category:
            sources = [s for s in sources if s.category == category]
        if status:
            sources = [s for s in sources if s.status == status]
        return sources

    # -- チェック実行 --

    def check_source(self, source_id: str, fetched_content: str) -> PrerequisiteChange | None:
        """ソースの内容を確認し、変更があれば検出する.

        fetched_content は外部から Web fetch した結果を渡す。
        HTTP 取得は呼び出し側で行い、このメソッドは変更検出のみを担当。
        """
        source = self._sources.get(source_id)
        if not source:
            raise ValueError(f"Source not found: {source_id}")

        content_hash = hashlib.sha256(fetched_content.encode()).hexdigest()
        now = datetime.now(UTC)
        source.last_checked = now

        # 初回チェック: ハッシュを保存して終了
        if not source.last_content_hash:
            source.last_content_hash = content_hash
            self._content_cache[source_id] = fetched_content
            return None

        # 変更なし
        if content_hash == source.last_content_hash:
            return None

        # 変更検出
        old_content = self._content_cache.get(source_id, "")
        diff_snippet = _generate_diff_snippet(old_content, fetched_content)
        matched_keywords = _find_matched_keywords(fetched_content, source.keywords)
        impact = _assess_impact(fetched_content, source.keywords)

        change = PrerequisiteChange(
            source_id=source.id,
            source_name=source.name,
            category=source.category,
            title=f"変更検出: {source.name}",
            summary=f"{source.name} ({source.url}) の内容が変更されました",
            diff_snippet=diff_snippet,
            impact=impact,
            affected_ticket_ids=source.linked_ticket_ids.copy(),
            matched_keywords=matched_keywords,
        )

        source.last_content_hash = content_hash
        source.last_change_detected = now
        self._content_cache[source_id] = fetched_content
        self._changes.append(change)

        logger.info(
            "Change detected for %s (impact: %s, keywords: %s)",
            source.name,
            impact.value,
            matched_keywords,
        )
        return change

    def check_all_due(self) -> list[PrerequisiteChange]:
        """チェック期限が到来したすべてのソースを返す（実際のfetchは呼び出し側）."""
        now = datetime.now(UTC)
        due_sources = []
        for source in self._sources.values():
            if source.status != MonitorStatus.ACTIVE:
                continue
            if source.last_checked is None:
                due_sources.append(source)
                continue
            interval = source.check_interval_hours * 3600
            elapsed = (now - source.last_checked).total_seconds()
            if elapsed >= interval:
                due_sources.append(source)
        return due_sources

    # -- 変更履歴 --

    def list_changes(
        self,
        company_id: str | None = None,
        source_id: str | None = None,
        impact: ChangeImpact | None = None,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> list[PrerequisiteChange]:
        """変更履歴を取得する."""
        changes = list(self._changes)
        if source_id:
            changes = [c for c in changes if c.source_id == source_id]
        if company_id:
            source_ids = {
                s.id for s in self._sources.values() if s.company_id == company_id
            }
            changes = [c for c in changes if c.source_id in source_ids]
        if impact:
            changes = [c for c in changes if c.impact == impact]
        if unacknowledged_only:
            changes = [c for c in changes if not c.acknowledged]
        changes.sort(key=lambda c: c.detected_at, reverse=True)
        return changes[:limit]

    def acknowledge_change(
        self, change_id: str, user_id: str
    ) -> PrerequisiteChange | None:
        """変更を確認済みにする."""
        for change in self._changes:
            if change.id == change_id:
                change.acknowledged = True
                change.acknowledged_by = user_id
                change.acknowledged_at = datetime.now(UTC)
                return change
        return None

    def get_summary(self, company_id: str) -> dict:
        """会社単位のサマリーを取得する."""
        sources = self.list_sources(company_id=company_id)
        changes = self.list_changes(company_id=company_id)
        unacked = [c for c in changes if not c.acknowledged]
        critical = [c for c in unacked if c.impact == ChangeImpact.CRITICAL]
        high = [c for c in unacked if c.impact == ChangeImpact.HIGH]

        return {
            "total_sources": len(sources),
            "active_sources": len([s for s in sources if s.status == MonitorStatus.ACTIVE]),
            "total_changes_detected": len(changes),
            "unacknowledged_changes": len(unacked),
            "critical_changes": len(critical),
            "high_changes": len(high),
            "sources_by_category": _count_by(sources, lambda s: s.category.value),
        }


def _count_by(items: list, key_fn) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        k = key_fn(item)
        result[k] = result.get(k, 0) + 1
    return result


def _generate_diff_snippet(old: str, new: str, max_lines: int = 10) -> str:
    """簡易差分スニペットを生成する."""
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    old_set = set(old_lines)
    new_set = set(new_lines)
    added = [f"+ {line}" for line in new_lines if line not in old_set][:max_lines]
    removed = [f"- {line}" for line in old_lines if line not in new_set][:max_lines]
    return "\n".join(removed + added) if (added or removed) else "(content changed)"


# ---------------------------------------------------------------------------
# シングルトンインスタンス
# ---------------------------------------------------------------------------

prerequisite_monitor = PrerequisiteMonitorService()
