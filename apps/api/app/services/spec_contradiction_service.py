"""Spec 間矛盾検出サービス — Spec Contradiction Detector.

複数チケットの Spec が互いに矛盾していないかを CrossModelJudge の応用で検証する。
既存の Judge 基盤（否定パターン検出・数値不整合・セマンティック比較）を流用して、
Spec レベルの矛盾を検出する。

検証対象:
- 同一プロジェクト内の複数 Spec の目的・制約条件・受け入れ基準
- リソース割り当ての競合
- スケジュール・期限の矛盾
- 技術的前提条件の不整合
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from app.orchestration.judge import (
    _NEGATION_PAIRS,
    _jaccard_similarity,
    _numeric_close,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------


class ContradictionType(str, Enum):
    """矛盾の種類."""

    OBJECTIVE_CONFLICT = "objective_conflict"
    CONSTRAINT_CONFLICT = "constraint_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    SCHEDULE_CONFLICT = "schedule_conflict"
    ACCEPTANCE_CRITERIA_CONFLICT = "acceptance_criteria_conflict"
    TECHNICAL_CONFLICT = "technical_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    NEGATION_CONFLICT = "negation_conflict"
    NUMERIC_DISCREPANCY = "numeric_discrepancy"


class ContradictionSeverity(str, Enum):
    """矛盾の深刻度."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SpecSummary:
    """検証対象の Spec の概要."""

    spec_id: str = ""
    ticket_id: str = ""
    ticket_title: str = ""
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    risk_notes: str = ""
    priority: str = "medium"
    estimated_budget: float | None = None
    deadline: str | None = None


@dataclass
class ContradictionDetail:
    """検出された矛盾の詳細."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ContradictionType = ContradictionType.OBJECTIVE_CONFLICT
    severity: ContradictionSeverity = ContradictionSeverity.WARNING
    spec_a_id: str = ""
    spec_a_ticket: str = ""
    spec_b_id: str = ""
    spec_b_ticket: str = ""
    field_a: str = ""
    value_a: str = ""
    field_b: str = ""
    value_b: str = ""
    description: str = ""
    suggestion: str = ""


@dataclass
class SpecContradictionReport:
    """Spec 間矛盾検出レポート."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    project_id: str | None = None
    analyzed_specs: int = 0
    contradictions: list[ContradictionDetail] = field(default_factory=list)
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    overall_consistency_score: float = 1.0
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# 矛盾検出エンジン
# ---------------------------------------------------------------------------


class SpecContradictionDetector:
    """Spec 間の矛盾を検出するサービス.

    CrossModelJudge の否定パターン・数値不整合・セマンティック比較を
    Spec の各フィールドに適用して矛盾を検出する。
    """

    def __init__(
        self,
        semantic_threshold: float = 0.6,
        numeric_tolerance: float = 0.05,
    ) -> None:
        self.semantic_threshold = semantic_threshold
        self.numeric_tolerance = numeric_tolerance

    def detect_contradictions(
        self,
        specs: list[SpecSummary],
        company_id: str = "",
        project_id: str | None = None,
    ) -> SpecContradictionReport:
        """複数の Spec 間の矛盾を検出する."""
        contradictions: list[ContradictionDetail] = []

        for i in range(len(specs)):
            for j in range(i + 1, len(specs)):
                pair_contradictions = self._compare_pair(specs[i], specs[j])
                contradictions.extend(pair_contradictions)

        critical = sum(1 for c in contradictions if c.severity == ContradictionSeverity.CRITICAL)
        error = sum(1 for c in contradictions if c.severity == ContradictionSeverity.ERROR)
        warning = sum(1 for c in contradictions if c.severity == ContradictionSeverity.WARNING)
        info = sum(1 for c in contradictions if c.severity == ContradictionSeverity.INFO)

        # 一貫性スコア: 矛盾が多いほど低い
        max_pairs = max(len(specs) * (len(specs) - 1) // 2, 1)
        penalty = (critical * 0.3 + error * 0.15 + warning * 0.05 + info * 0.01)
        score = max(0.0, 1.0 - penalty / max_pairs)

        return SpecContradictionReport(
            company_id=company_id,
            project_id=project_id,
            analyzed_specs=len(specs),
            contradictions=contradictions,
            critical_count=critical,
            error_count=error,
            warning_count=warning,
            info_count=info,
            overall_consistency_score=round(score, 3),
        )

    def _compare_pair(
        self, spec_a: SpecSummary, spec_b: SpecSummary
    ) -> list[ContradictionDetail]:
        """2つの Spec を比較して矛盾を検出する."""
        results: list[ContradictionDetail] = []

        # 1. 目的の矛盾チェック（否定パターン検出）
        if spec_a.objective and spec_b.objective:
            negations = self._check_negation_conflict(
                spec_a.objective, spec_b.objective
            )
            if negations:
                results.append(
                    ContradictionDetail(
                        type=ContradictionType.NEGATION_CONFLICT,
                        severity=ContradictionSeverity.ERROR,
                        spec_a_id=spec_a.spec_id,
                        spec_a_ticket=spec_a.ticket_title,
                        spec_b_id=spec_b.spec_id,
                        spec_b_ticket=spec_b.ticket_title,
                        field_a="objective",
                        value_a=spec_a.objective[:200],
                        field_b="objective",
                        value_b=spec_b.objective[:200],
                        description=f"目的に否定的矛盾を検出: {', '.join(negations)}",
                        suggestion="2つのSpecの目的が矛盾していないか確認してください",
                    )
                )

        # 2. 制約条件の矛盾チェック
        for ca in spec_a.constraints:
            for cb in spec_b.constraints:
                neg = self._check_negation_conflict(ca, cb)
                if neg:
                    results.append(
                        ContradictionDetail(
                            type=ContradictionType.CONSTRAINT_CONFLICT,
                            severity=ContradictionSeverity.ERROR,
                            spec_a_id=spec_a.spec_id,
                            spec_a_ticket=spec_a.ticket_title,
                            spec_b_id=spec_b.spec_id,
                            spec_b_ticket=spec_b.ticket_title,
                            field_a="constraint",
                            value_a=ca[:200],
                            field_b="constraint",
                            value_b=cb[:200],
                            description=f"制約条件に矛盾を検出: {', '.join(neg)}",
                            suggestion="制約条件を統一するか、優先順位を明確にしてください",
                        )
                    )

                # 数値不整合チェック
                num_conflict = self._check_numeric_conflict(ca, cb)
                if num_conflict:
                    results.append(num_conflict._replace_ids(
                        spec_a.spec_id, spec_a.ticket_title,
                        spec_b.spec_id, spec_b.ticket_title,
                    ) if False else ContradictionDetail(
                        type=ContradictionType.NUMERIC_DISCREPANCY,
                        severity=ContradictionSeverity.WARNING,
                        spec_a_id=spec_a.spec_id,
                        spec_a_ticket=spec_a.ticket_title,
                        spec_b_id=spec_b.spec_id,
                        spec_b_ticket=spec_b.ticket_title,
                        field_a="constraint",
                        value_a=ca[:200],
                        field_b="constraint",
                        value_b=cb[:200],
                        description="制約条件の数値に不整合があります",
                        suggestion="数値を確認・統一してください",
                    ))

        # 3. 受け入れ基準の矛盾チェック
        for aa in spec_a.acceptance_criteria:
            for ab in spec_b.acceptance_criteria:
                neg = self._check_negation_conflict(aa, ab)
                if neg:
                    results.append(
                        ContradictionDetail(
                            type=ContradictionType.ACCEPTANCE_CRITERIA_CONFLICT,
                            severity=ContradictionSeverity.ERROR,
                            spec_a_id=spec_a.spec_id,
                            spec_a_ticket=spec_a.ticket_title,
                            spec_b_id=spec_b.spec_id,
                            spec_b_ticket=spec_b.ticket_title,
                            field_a="acceptance_criteria",
                            value_a=aa[:200],
                            field_b="acceptance_criteria",
                            value_b=ab[:200],
                            description=f"受け入れ基準に矛盾を検出: {', '.join(neg)}",
                            suggestion="受け入れ基準を確認してください",
                        )
                    )

        # 4. 予算の競合チェック
        if spec_a.estimated_budget and spec_b.estimated_budget:
            result = _numeric_close(
                str(spec_a.estimated_budget),
                str(spec_b.estimated_budget),
                tolerance=self.numeric_tolerance,
            )
            # 同一リソースを参照している可能性がある場合のみ
            sim = _jaccard_similarity(spec_a.objective, spec_b.objective)
            if sim > self.semantic_threshold and result is False:
                results.append(
                    ContradictionDetail(
                        type=ContradictionType.RESOURCE_CONFLICT,
                        severity=ContradictionSeverity.WARNING,
                        spec_a_id=spec_a.spec_id,
                        spec_a_ticket=spec_a.ticket_title,
                        spec_b_id=spec_b.spec_id,
                        spec_b_ticket=spec_b.ticket_title,
                        field_a="estimated_budget",
                        value_a=str(spec_a.estimated_budget),
                        field_b="estimated_budget",
                        value_b=str(spec_b.estimated_budget),
                        description="類似の目的を持つSpecで予算見積もりに大きな差異があります",
                        suggestion="リソース配分を見直してください",
                    )
                )

        # 5. 優先度矛盾（類似目的で異なる優先度）
        if spec_a.priority != spec_b.priority:
            sim = _jaccard_similarity(spec_a.objective, spec_b.objective)
            if sim > self.semantic_threshold:
                results.append(
                    ContradictionDetail(
                        type=ContradictionType.PRIORITY_CONFLICT,
                        severity=ContradictionSeverity.INFO,
                        spec_a_id=spec_a.spec_id,
                        spec_a_ticket=spec_a.ticket_title,
                        spec_b_id=spec_b.spec_id,
                        spec_b_ticket=spec_b.ticket_title,
                        field_a="priority",
                        value_a=spec_a.priority,
                        field_b="priority",
                        value_b=spec_b.priority,
                        description="類似の目的を持つSpecで優先度が異なります",
                        suggestion="優先度の整合性を確認してください",
                    )
                )

        return results

    def _check_negation_conflict(self, text_a: str, text_b: str) -> list[str]:
        """否定パターンによる矛盾を検出する."""
        conflicts: list[str] = []
        for pos_pat, neg_pat in _NEGATION_PAIRS:
            a_pos = bool(pos_pat.search(text_a))
            a_neg = bool(neg_pat.search(text_a))
            b_pos = bool(pos_pat.search(text_b))
            b_neg = bool(neg_pat.search(text_b))
            # A が肯定で B が否定、または A が否定で B が肯定
            if (a_pos and not a_neg and b_neg and not b_pos) or (
                a_neg and not a_pos and b_pos and not b_neg
            ):
                conflicts.append(f"{pos_pat.pattern} vs {neg_pat.pattern}")
        return conflicts

    def _check_numeric_conflict(self, text_a: str, text_b: str) -> bool:
        """数値不整合を検出する."""
        import re
        nums_a = re.findall(r"\d+(?:\.\d+)?%?", text_a)
        nums_b = re.findall(r"\d+(?:\.\d+)?%?", text_b)
        for na in nums_a:
            for nb in nums_b:
                result = _numeric_close(na, nb, tolerance=self.numeric_tolerance)
                if result is False:
                    return True
        return False


# ---------------------------------------------------------------------------
# シングルトンインスタンス
# ---------------------------------------------------------------------------

spec_contradiction_detector = SpecContradictionDetector()
