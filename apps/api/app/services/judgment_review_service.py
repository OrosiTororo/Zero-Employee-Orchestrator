"""ユーザー判断の振り返りレポートサービス — Judgment Review.

承認・却下の履歴から「あなたはこの期間にこういう判断傾向があった」と
可視化する。ユーザー自身の意思決定の自己認識を支える方向。

分析対象:
- 承認/却下の比率・傾向
- 判断に要した時間の傾向
- リスクレベル別の判断パターン
- カテゴリ別の判断分布
- 時間帯・曜日別の判断パターン
- 差し戻し後の再提案承認率
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------


class JudgmentAction(str, Enum):
    """判断のアクション."""

    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    MODIFIED_AND_APPROVED = "modified_and_approved"


class JudgmentCategory(str, Enum):
    """判断のカテゴリ."""

    PLAN_APPROVAL = "plan_approval"
    TASK_REVIEW = "task_review"
    EXTERNAL_SEND = "external_send"
    PUBLISH = "publish"
    DELETE = "delete"
    BUDGET = "budget"
    PERMISSION = "permission"
    CREDENTIAL = "credential"
    SPEC_APPROVAL = "spec_approval"
    SKILL_IMPROVEMENT = "skill_improvement"
    OTHER = "other"


@dataclass
class JudgmentRecord:
    """個別の判断記録."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    company_id: str = ""
    action: JudgmentAction = JudgmentAction.APPROVED
    category: JudgmentCategory = JudgmentCategory.OTHER
    target_type: str = ""
    target_id: str = ""
    risk_level: str = "low"
    reason: str = ""
    response_time_seconds: float | None = None
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CategoryInsight:
    """カテゴリ別の洞察."""

    category: str = ""
    total: int = 0
    approved: int = 0
    rejected: int = 0
    deferred: int = 0
    approval_rate: float = 0.0
    avg_response_time_seconds: float | None = None


@dataclass
class TrendPoint:
    """トレンドのデータポイント."""

    period: str = ""
    total: int = 0
    approved: int = 0
    rejected: int = 0
    approval_rate: float = 0.0


@dataclass
class JudgmentPattern:
    """検出されたパターン."""

    pattern_type: str = ""
    description: str = ""
    confidence: float = 0.0
    suggestion: str = ""


@dataclass
class JudgmentReviewReport:
    """ユーザー判断の振り返りレポート."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    company_id: str = ""
    period_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    period_end: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_decisions: int = 0
    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    avg_response_time_seconds: float | None = None
    category_insights: list[CategoryInsight] = field(default_factory=list)
    risk_distribution: dict[str, int] = field(default_factory=dict)
    weekly_trend: list[TrendPoint] = field(default_factory=list)
    detected_patterns: list[JudgmentPattern] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# メインサービス
# ---------------------------------------------------------------------------


class JudgmentReviewService:
    """ユーザー判断の振り返りレポート生成サービス.

    承認・却下の履歴を分析し、判断傾向を可視化する。
    """

    def __init__(self) -> None:
        self._records: list[JudgmentRecord] = []

    def record_judgment(
        self,
        user_id: str,
        company_id: str,
        action: JudgmentAction,
        category: JudgmentCategory = JudgmentCategory.OTHER,
        target_type: str = "",
        target_id: str = "",
        risk_level: str = "low",
        reason: str = "",
        response_time_seconds: float | None = None,
    ) -> JudgmentRecord:
        """判断を記録する."""
        record = JudgmentRecord(
            user_id=user_id,
            company_id=company_id,
            action=action,
            category=category,
            target_type=target_type,
            target_id=target_id,
            risk_level=risk_level,
            reason=reason,
            response_time_seconds=response_time_seconds,
        )
        self._records.append(record)
        return record

    def generate_report(
        self,
        user_id: str,
        company_id: str,
        period_days: int = 30,
    ) -> JudgmentReviewReport:
        """振り返りレポートを生成する."""
        now = datetime.now(UTC)
        period_start = now - timedelta(days=period_days)

        # 期間内のレコードを取得
        records = [
            r
            for r in self._records
            if r.user_id == user_id
            and r.company_id == company_id
            and r.decided_at >= period_start
        ]

        if not records:
            return JudgmentReviewReport(
                user_id=user_id,
                company_id=company_id,
                period_start=period_start,
                period_end=now,
            )

        # 基本統計
        total = len(records)
        approved = sum(1 for r in records if r.action == JudgmentAction.APPROVED)
        rejected = sum(1 for r in records if r.action == JudgmentAction.REJECTED)
        approval_rate = approved / total if total > 0 else 0.0
        rejection_rate = rejected / total if total > 0 else 0.0

        # 平均応答時間
        response_times = [
            r.response_time_seconds
            for r in records
            if r.response_time_seconds is not None
        ]
        avg_response = (
            sum(response_times) / len(response_times) if response_times else None
        )

        # カテゴリ別洞察
        category_insights = self._analyze_categories(records)

        # リスク分布
        risk_dist: dict[str, int] = defaultdict(int)
        for r in records:
            risk_dist[r.risk_level] += 1

        # 週次トレンド
        weekly_trend = self._analyze_weekly_trend(records, period_start, now)

        # パターン検出
        patterns = self._detect_patterns(records, category_insights)

        return JudgmentReviewReport(
            user_id=user_id,
            company_id=company_id,
            period_start=period_start,
            period_end=now,
            total_decisions=total,
            approval_rate=round(approval_rate, 3),
            rejection_rate=round(rejection_rate, 3),
            avg_response_time_seconds=round(avg_response, 1) if avg_response else None,
            category_insights=category_insights,
            risk_distribution=dict(risk_dist),
            weekly_trend=weekly_trend,
            detected_patterns=patterns,
        )

    def _analyze_categories(
        self, records: list[JudgmentRecord]
    ) -> list[CategoryInsight]:
        """カテゴリ別に分析する."""
        by_cat: dict[str, list[JudgmentRecord]] = defaultdict(list)
        for r in records:
            by_cat[r.category.value].append(r)

        insights = []
        for cat, cat_records in by_cat.items():
            total = len(cat_records)
            approved = sum(1 for r in cat_records if r.action == JudgmentAction.APPROVED)
            rejected = sum(1 for r in cat_records if r.action == JudgmentAction.REJECTED)
            deferred = sum(1 for r in cat_records if r.action == JudgmentAction.DEFERRED)
            times = [
                r.response_time_seconds
                for r in cat_records
                if r.response_time_seconds is not None
            ]
            avg_time = sum(times) / len(times) if times else None

            insights.append(
                CategoryInsight(
                    category=cat,
                    total=total,
                    approved=approved,
                    rejected=rejected,
                    deferred=deferred,
                    approval_rate=round(approved / total, 3) if total > 0 else 0.0,
                    avg_response_time_seconds=round(avg_time, 1) if avg_time else None,
                )
            )

        insights.sort(key=lambda x: x.total, reverse=True)
        return insights

    def _analyze_weekly_trend(
        self,
        records: list[JudgmentRecord],
        start: datetime,
        end: datetime,
    ) -> list[TrendPoint]:
        """週次トレンドを分析する."""
        trend_points: list[TrendPoint] = []
        current = start
        while current < end:
            week_end = current + timedelta(days=7)
            week_records = [
                r for r in records if current <= r.decided_at < week_end
            ]
            total = len(week_records)
            approved = sum(
                1 for r in week_records if r.action == JudgmentAction.APPROVED
            )
            rejected = sum(
                1 for r in week_records if r.action == JudgmentAction.REJECTED
            )
            trend_points.append(
                TrendPoint(
                    period=current.strftime("%Y-%m-%d"),
                    total=total,
                    approved=approved,
                    rejected=rejected,
                    approval_rate=round(approved / total, 3) if total > 0 else 0.0,
                )
            )
            current = week_end
        return trend_points

    def _detect_patterns(
        self,
        records: list[JudgmentRecord],
        category_insights: list[CategoryInsight],
    ) -> list[JudgmentPattern]:
        """判断パターンを検出する."""
        patterns: list[JudgmentPattern] = []

        total = len(records)
        if total < 5:
            return patterns

        # パターン1: 高い却下率
        rejected = sum(1 for r in records if r.action == JudgmentAction.REJECTED)
        if rejected / total > 0.5:
            patterns.append(
                JudgmentPattern(
                    pattern_type="high_rejection_rate",
                    description=f"却下率が {rejected / total * 100:.0f}% と高めです",
                    confidence=0.8,
                    suggestion="AIの提案品質を確認するか、要件をより詳細に定義してください",
                )
            )

        # パターン2: 特定カテゴリへの偏り
        for ci in category_insights:
            if ci.total / total > 0.4 and total >= 10:
                patterns.append(
                    JudgmentPattern(
                        pattern_type="category_concentration",
                        description=f"判断の {ci.total / total * 100:.0f}% が「{ci.category}」カテゴリに集中しています",
                        confidence=0.7,
                        suggestion="特定カテゴリの自律実行範囲を拡大することで判断負荷を軽減できます",
                    )
                )

        # パターン3: リスクレベルと判断の相関
        high_risk = [r for r in records if r.risk_level in ("high", "critical")]
        if high_risk:
            high_approved = sum(
                1 for r in high_risk if r.action == JudgmentAction.APPROVED
            )
            if high_approved / len(high_risk) > 0.8:
                patterns.append(
                    JudgmentPattern(
                        pattern_type="high_risk_auto_approve",
                        description="高リスク操作の承認率が高い傾向があります",
                        confidence=0.6,
                        suggestion="承認基準が適切か見直してください。信頼できる操作は自律実行に移行も検討できます",
                    )
                )

        # パターン4: 応答時間の傾向
        times = [
            r.response_time_seconds
            for r in records
            if r.response_time_seconds is not None
        ]
        if times:
            avg_time = sum(times) / len(times)
            if avg_time > 3600:  # 1時間以上
                patterns.append(
                    JudgmentPattern(
                        pattern_type="slow_response",
                        description=f"平均応答時間が {avg_time / 3600:.1f} 時間です",
                        confidence=0.7,
                        suggestion="承認待ちによるボトルネックがあります。通知設定の確認をお勧めします",
                    )
                )

        return patterns

    def get_records(
        self,
        user_id: str,
        company_id: str,
        limit: int = 100,
    ) -> list[JudgmentRecord]:
        """判断記録を取得する."""
        records = [
            r
            for r in self._records
            if r.user_id == user_id and r.company_id == company_id
        ]
        records.sort(key=lambda r: r.decided_at, reverse=True)
        return records[:limit]


# ---------------------------------------------------------------------------
# シングルトンインスタンス
# ---------------------------------------------------------------------------

judgment_review_service = JudgmentReviewService()
