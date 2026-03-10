"""Hypothesis Engine — 仮説の並行検証とレビュー.

マルチエージェントが仮説検証とレビューのループを回す機能。
複数の仮説を並行して検証し、クロスレビューで精度を高める。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    INVESTIGATING = "investigating"
    EVIDENCE_FOUND = "evidence_found"
    REFUTED = "refuted"
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"


class ReviewVerdict(str, Enum):
    AGREE = "agree"
    DISAGREE = "disagree"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    PARTIALLY_AGREE = "partially_agree"


@dataclass
class Evidence:
    """仮説を支持または反証するエビデンス."""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str = ""
    agent_id: str = ""
    supports: bool = True
    description: str = ""
    source: str = ""
    confidence: float = 0.5
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Review:
    """仮説に対するレビュー."""
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str = ""
    reviewer_agent_id: str = ""
    verdict: ReviewVerdict = ReviewVerdict.NEEDS_MORE_EVIDENCE
    reasoning: str = ""
    suggested_actions: list[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: float = field(default_factory=time.time)


@dataclass
class Hypothesis:
    """検証対象の仮説."""
    hypothesis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str | None = None
    company_id: str | None = None
    proposer_agent_id: str = ""
    title: str = ""
    description: str = ""
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    priority: int = 0
    evidence: list[Evidence] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    assigned_investigators: list[str] = field(default_factory=list)
    parent_hypothesis_id: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    resolved_at: float | None = None

    @property
    def support_score(self) -> float:
        """エビデンスに基づく支持スコア（-1.0〜1.0）."""
        if not self.evidence:
            return 0.0
        total_weight = sum(e.confidence for e in self.evidence)
        if total_weight == 0:
            return 0.0
        weighted = sum(
            e.confidence * (1.0 if e.supports else -1.0) for e in self.evidence
        )
        return weighted / total_weight

    @property
    def review_consensus(self) -> str:
        """レビューのコンセンサス."""
        if not self.reviews:
            return "no_reviews"
        agrees = sum(1 for r in self.reviews if r.verdict == ReviewVerdict.AGREE)
        total = len(self.reviews)
        ratio = agrees / total
        if ratio >= 0.8:
            return "strong_agreement"
        if ratio >= 0.5:
            return "majority_agreement"
        if ratio >= 0.3:
            return "mixed"
        return "disagreement"

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "task_id": self.task_id,
            "company_id": self.company_id,
            "proposer_agent_id": self.proposer_agent_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "support_score": self.support_score,
            "review_consensus": self.review_consensus,
            "evidence_count": len(self.evidence),
            "review_count": len(self.reviews),
            "assigned_investigators": self.assigned_investigators,
            "parent_hypothesis_id": self.parent_hypothesis_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
        }


class HypothesisEngine:
    """仮説の並行検証を管理するエンジン."""

    def __init__(self, max_hypotheses: int = 1000) -> None:
        self._hypotheses: dict[str, Hypothesis] = {}
        self._max = max_hypotheses

    def propose(
        self,
        title: str,
        description: str,
        proposer_agent_id: str,
        *,
        task_id: str | None = None,
        company_id: str | None = None,
        priority: int = 0,
        parent_hypothesis_id: str | None = None,
    ) -> Hypothesis:
        """新しい仮説を提案."""
        h = Hypothesis(
            task_id=task_id,
            company_id=company_id,
            proposer_agent_id=proposer_agent_id,
            title=title,
            description=description,
            priority=priority,
            parent_hypothesis_id=parent_hypothesis_id,
        )
        if len(self._hypotheses) >= self._max:
            resolved = [
                k for k, v in self._hypotheses.items()
                if v.status in (HypothesisStatus.CONFIRMED, HypothesisStatus.REFUTED)
            ]
            for k in resolved[:len(resolved) // 2]:
                del self._hypotheses[k]

        self._hypotheses[h.hypothesis_id] = h
        logger.info("Hypothesis proposed: %s by %s", title, proposer_agent_id)
        return h

    def assign_investigator(
        self, hypothesis_id: str, agent_id: str
    ) -> bool:
        """仮説の調査担当エージェントを割り当て."""
        h = self._hypotheses.get(hypothesis_id)
        if not h:
            return False
        if agent_id not in h.assigned_investigators:
            h.assigned_investigators.append(agent_id)
        h.status = HypothesisStatus.INVESTIGATING
        h.updated_at = time.time()
        return True

    def add_evidence(
        self,
        hypothesis_id: str,
        agent_id: str,
        supports: bool,
        description: str,
        *,
        source: str = "",
        confidence: float = 0.5,
        data: dict[str, Any] | None = None,
    ) -> Evidence | None:
        """エビデンスを追加."""
        h = self._hypotheses.get(hypothesis_id)
        if not h:
            return None

        ev = Evidence(
            hypothesis_id=hypothesis_id,
            agent_id=agent_id,
            supports=supports,
            description=description,
            source=source,
            confidence=confidence,
            data=data or {},
        )
        h.evidence.append(ev)
        h.status = HypothesisStatus.EVIDENCE_FOUND
        h.updated_at = time.time()
        return ev

    def submit_review(
        self,
        hypothesis_id: str,
        reviewer_agent_id: str,
        verdict: ReviewVerdict,
        reasoning: str,
        *,
        confidence: float = 0.5,
        suggested_actions: list[str] | None = None,
    ) -> Review | None:
        """レビューを提出."""
        h = self._hypotheses.get(hypothesis_id)
        if not h:
            return None

        review = Review(
            hypothesis_id=hypothesis_id,
            reviewer_agent_id=reviewer_agent_id,
            verdict=verdict,
            reasoning=reasoning,
            confidence=confidence,
            suggested_actions=suggested_actions or [],
        )
        h.reviews.append(review)
        h.status = HypothesisStatus.REVIEWED
        h.updated_at = time.time()
        return review

    def resolve(
        self, hypothesis_id: str, confirmed: bool
    ) -> bool:
        """仮説を解決（確認/反証）."""
        h = self._hypotheses.get(hypothesis_id)
        if not h:
            return False
        h.status = HypothesisStatus.CONFIRMED if confirmed else HypothesisStatus.REFUTED
        h.resolved_at = time.time()
        h.updated_at = time.time()
        return True

    def get(self, hypothesis_id: str) -> Hypothesis | None:
        return self._hypotheses.get(hypothesis_id)

    def get_by_task(self, task_id: str) -> list[Hypothesis]:
        return [h for h in self._hypotheses.values() if h.task_id == task_id]

    def get_active(self, company_id: str | None = None) -> list[Hypothesis]:
        result = [
            h for h in self._hypotheses.values()
            if h.status not in (HypothesisStatus.CONFIRMED, HypothesisStatus.REFUTED)
        ]
        if company_id:
            result = [h for h in result if h.company_id == company_id]
        return sorted(result, key=lambda x: x.priority, reverse=True)

    def get_needing_review(self, company_id: str | None = None) -> list[Hypothesis]:
        result = [
            h for h in self._hypotheses.values()
            if h.status in (HypothesisStatus.EVIDENCE_FOUND, HypothesisStatus.NEEDS_REVIEW)
        ]
        if company_id:
            result = [h for h in result if h.company_id == company_id]
        return result


# Global singleton
hypothesis_engine = HypothesisEngine()
