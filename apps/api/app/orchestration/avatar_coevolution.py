"""Avatar AI Co-evolution — User-AI co-evolution engine.

Learns decision criteria from user interactions and implements a
co-evolution model where AI grows together with the user.

Key features:
  - Interaction recording and preference extraction
  - Decision criteria learning and accumulation
  - User preference prediction
  - Option ranking suggestions
  - User model export/import
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class UserPreference:
    """Learned user preference."""

    category: str = ""
    key: str = ""
    value: Any = None
    confidence: float = 0.0
    learned_from: list[str] = field(default_factory=list)  # interaction IDs
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "learned_from_count": len(self.learned_from),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DecisionCriterion:
    """Learned decision criterion."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = ""
    description: str = ""
    weight: float = 0.5
    learned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_count: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "id": self.id,
            "domain": self.domain,
            "description": self.description,
            "weight": self.weight,
            "learned_at": self.learned_at.isoformat(),
            "applied_count": self.applied_count,
            "success_rate": self.success_rate,
        }


@dataclass
class InteractionRecord:
    """User interaction record."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    user_decision: str = ""
    ai_suggestion: str = ""
    user_accepted: bool = False
    feedback: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "context": self.context,
            "user_decision": self.user_decision,
            "ai_suggestion": self.ai_suggestion,
            "user_accepted": self.user_accepted,
            "feedback": self.feedback,
            "timestamp": self.timestamp.isoformat(),
        }


# ---------------------------------------------------------------------------
# Avatar Co-evolution Engine
# ---------------------------------------------------------------------------

_MAX_INTERACTIONS = 5000


class AvatarCoevolution:
    """User-AI co-evolution engine.

    Continuously learns user decision-making patterns
    and improves AI suggestion accuracy.
    """

    def __init__(self) -> None:
        # user_id -> category -> UserPreference
        self._preferences: dict[str, dict[str, UserPreference]] = {}
        # user_id -> list[DecisionCriterion]
        self._criteria: dict[str, list[DecisionCriterion]] = {}
        self._interactions: list[InteractionRecord] = []

    # ------------------------------------------------------------------
    # Interaction recording
    # ------------------------------------------------------------------

    def record_interaction(
        self,
        user_id: str,
        context: dict[str, Any],
        user_decision: str,
        ai_suggestion: str,
        accepted: bool,
        feedback: str = "",
    ) -> InteractionRecord:
        """Record a user interaction.

        Args:
            user_id: User ID.
            context: Interaction context.
            user_decision: User's actual decision.
            ai_suggestion: AI's suggestion.
            accepted: Whether the user adopted the AI suggestion.
            feedback: Feedback from the user.

        Returns:
            The recorded interaction.
        """
        record = InteractionRecord(
            user_id=user_id,
            context=context,
            user_decision=user_decision,
            ai_suggestion=ai_suggestion,
            user_accepted=accepted,
            feedback=feedback,
        )

        # Capacity limit
        if len(self._interactions) >= _MAX_INTERACTIONS:
            self._interactions = self._interactions[-(_MAX_INTERACTIONS // 2) :]

        self._interactions.append(record)

        # Auto-learn preferences from interaction
        self.learn_preference(user_id, record)

        logger.debug(
            "Avatar: interaction recorded for user '%s' (accepted=%s)",
            user_id,
            accepted,
        )
        return record

    # ------------------------------------------------------------------
    # Preference learning
    # ------------------------------------------------------------------

    def learn_preference(
        self,
        user_id: str,
        interaction: InteractionRecord,
    ) -> UserPreference | None:
        """Extract and update user preferences from an interaction.

        Args:
            user_id: User ID.
            interaction: Source interaction for learning.

        Returns:
            Updated or newly created preference. None if not a learning target.
        """
        domain = interaction.context.get("domain", "general")
        decision = interaction.user_decision

        if not decision:
            return None

        if user_id not in self._preferences:
            self._preferences[user_id] = {}

        prefs = self._preferences[user_id]
        category = f"{domain}:decision"

        if category in prefs:
            pref = prefs[category]
            # Update confidence (increases as the same choice is repeated)
            if pref.value == decision:
                pref.confidence = min(1.0, pref.confidence + 0.05)
            else:
                # Different choice — lower confidence, update value if below threshold
                pref.confidence = max(0.0, pref.confidence - 0.1)
                if pref.confidence < 0.3:
                    pref.value = decision
                    pref.confidence = 0.3
            pref.learned_from.append(interaction.id)
            pref.updated_at = datetime.now(UTC)
        else:
            pref = UserPreference(
                category=category,
                key=domain,
                value=decision,
                confidence=0.3,
                learned_from=[interaction.id],
            )
            prefs[category] = pref

        # Update decision criteria
        self._update_criteria(user_id, interaction)

        return pref

    def _update_criteria(
        self,
        user_id: str,
        interaction: InteractionRecord,
    ) -> None:
        """Update decision criteria from an interaction."""
        if user_id not in self._criteria:
            self._criteria[user_id] = []

        domain = interaction.context.get("domain", "general")
        criteria_list = self._criteria[user_id]

        # Search for existing criteria in the same domain
        existing = next((c for c in criteria_list if c.domain == domain), None)

        if existing:
            existing.applied_count += 1
            if interaction.user_accepted:
                # AI suggestion was adopted = criteria accuracy is high
                total = existing.applied_count
                existing.success_rate = (existing.success_rate * (total - 1) + 1.0) / total
                existing.weight = min(1.0, existing.weight + 0.02)
            else:
                total = existing.applied_count
                existing.success_rate = existing.success_rate * (total - 1) / total
                existing.weight = max(0.1, existing.weight - 0.01)
        else:
            criterion = DecisionCriterion(
                domain=domain,
                description=(f"User decision-making pattern in domain '{domain}'"),
                weight=0.5,
                applied_count=1,
                success_rate=1.0 if interaction.user_accepted else 0.0,
            )
            criteria_list.append(criterion)

    # ------------------------------------------------------------------
    # Preference prediction
    # ------------------------------------------------------------------

    async def predict_preference(
        self,
        user_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Predict a user's preference.

        Args:
            user_id: User ID.
            context: Context for prediction.

        Returns:
            Prediction result (predicted_value, confidence, basis).
        """
        domain = context.get("domain", "general")
        category = f"{domain}:decision"

        prefs = self._preferences.get(user_id, {})
        pref = prefs.get(category)

        if pref and pref.confidence >= 0.3:
            return {
                "predicted_value": pref.value,
                "confidence": round(pref.confidence, 4),
                "basis": "direct_preference",
                "domain": domain,
                "learned_from_count": len(pref.learned_from),
            }

        # Estimation from similar domains
        similar_prefs = [p for p in prefs.values() if p.key and domain.split(":")[0] in p.key]
        if similar_prefs:
            best = max(similar_prefs, key=lambda p: p.confidence)
            return {
                "predicted_value": best.value,
                "confidence": round(best.confidence * 0.6, 4),
                "basis": "similar_domain",
                "domain": domain,
                "source_domain": best.key,
            }

        return {
            "predicted_value": None,
            "confidence": 0.0,
            "basis": "no_data",
            "domain": domain,
        }

    # ------------------------------------------------------------------
    # Decision support
    # ------------------------------------------------------------------

    async def suggest_decision(
        self,
        user_id: str,
        context: dict[str, Any],
        options: list[str],
    ) -> list[dict[str, Any]]:
        """Rank options based on user preferences.

        Args:
            user_id: User ID.
            context: Decision context.
            options: List of options.

        Returns:
            Scored and ranked list of options.
        """
        if not options:
            return []

        domain = context.get("domain", "general")
        prediction = await self.predict_preference(user_id, context)
        predicted_value = prediction.get("predicted_value")
        pred_confidence = prediction.get("confidence", 0.0)

        # Calculate scores for each option from past interactions
        user_interactions = [
            i
            for i in self._interactions
            if i.user_id == user_id and i.context.get("domain", "") == domain
        ]

        scored_options: list[dict[str, Any]] = []
        for option in options:
            score = 0.5  # Base score

            # Match with predicted value
            if predicted_value and option == predicted_value:
                score += 0.3 * pred_confidence

            # Past selection frequency
            choice_count = sum(1 for i in user_interactions if i.user_decision == option)
            total = len(user_interactions) if user_interactions else 1
            frequency_score = choice_count / total
            score += 0.2 * frequency_score

            # Adjustment based on decision criteria
            criteria = self._criteria.get(user_id, [])
            domain_criteria = [c for c in criteria if c.domain == domain]
            if domain_criteria:
                avg_weight = sum(c.weight for c in domain_criteria) / len(domain_criteria)
                score *= 0.5 + 0.5 * avg_weight

            scored_options.append(
                {
                    "option": option,
                    "score": round(min(1.0, score), 4),
                    "choice_frequency": round(frequency_score, 4),
                    "prediction_match": option == predicted_value,
                }
            )

        # Sort by score descending
        scored_options.sort(key=lambda x: x["score"], reverse=True)

        # Assign ranks
        for i, opt in enumerate(scored_options):
            opt["rank"] = i + 1

        return scored_options

    # ------------------------------------------------------------------
    # User profile
    # ------------------------------------------------------------------

    def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Return a user's unified profile.

        Aggregates preferences, decision criteria, and interaction statistics.
        """
        prefs = self._preferences.get(user_id, {})
        criteria = self._criteria.get(user_id, [])
        interactions = [i for i in self._interactions if i.user_id == user_id]

        total_interactions = len(interactions)
        accepted_count = sum(1 for i in interactions if i.user_accepted)
        acceptance_rate = accepted_count / total_interactions if total_interactions > 0 else 0.0

        # ドメイン別統計
        domain_stats: dict[str, dict[str, int]] = {}
        for interaction in interactions:
            domain = interaction.context.get("domain", "general")
            if domain not in domain_stats:
                domain_stats[domain] = {"total": 0, "accepted": 0}
            domain_stats[domain]["total"] += 1
            if interaction.user_accepted:
                domain_stats[domain]["accepted"] += 1

        return {
            "user_id": user_id,
            "preferences": {k: v.to_dict() for k, v in prefs.items()},
            "criteria": [c.to_dict() for c in criteria],
            "total_interactions": total_interactions,
            "acceptance_rate": round(acceptance_rate, 4),
            "domain_stats": domain_stats,
            "preference_count": len(prefs),
            "criteria_count": len(criteria),
        }

    def get_alignment_score(self, user_id: str) -> float:
        """AI がユーザーをどれだけ理解しているかのスコア（0.0〜1.0）を返す.

        嗜好の信頼度・意思決定基準の成功率・インタラクション数を総合評価する。
        """
        prefs = self._preferences.get(user_id, {})
        criteria = self._criteria.get(user_id, [])
        interactions = [i for i in self._interactions if i.user_id == user_id]

        if not interactions:
            return 0.0

        # 嗜好の平均信頼度
        avg_pref_confidence = (
            sum(p.confidence for p in prefs.values()) / len(prefs) if prefs else 0.0
        )

        # 意思決定基準の平均成功率
        avg_criteria_success = (
            sum(c.success_rate for c in criteria) / len(criteria) if criteria else 0.0
        )

        # インタラクション数に基づく経験値（100 件で飽和）
        experience_factor = min(1.0, len(interactions) / 100.0)

        # 直近の受容率（最新 20 件）
        recent = interactions[-20:]
        recent_acceptance = (
            sum(1 for i in recent if i.user_accepted) / len(recent) if recent else 0.0
        )

        alignment = (
            avg_pref_confidence * 0.25
            + avg_criteria_success * 0.25
            + experience_factor * 0.2
            + recent_acceptance * 0.3
        )

        return round(min(1.0, alignment), 4)

    def get_evolution_history(self, user_id: str) -> list[dict[str, Any]]:
        """ユーザーとの共進化の時系列履歴を返す."""
        interactions = [i for i in self._interactions if i.user_id == user_id]

        history: list[dict[str, Any]] = []
        running_acceptance = 0

        for idx, interaction in enumerate(interactions, 1):
            if interaction.user_accepted:
                running_acceptance += 1

            history.append(
                {
                    "interaction_id": interaction.id,
                    "timestamp": interaction.timestamp.isoformat(),
                    "domain": interaction.context.get("domain", "general"),
                    "accepted": interaction.user_accepted,
                    "running_acceptance_rate": round(running_acceptance / idx, 4),
                    "feedback": interaction.feedback or None,
                }
            )

        return history

    # ------------------------------------------------------------------
    # エクスポート / インポート
    # ------------------------------------------------------------------

    def export_profile(self, user_id: str) -> dict[str, Any]:
        """ユーザープロファイルをエクスポート可能な形式で返す."""
        prefs = self._preferences.get(user_id, {})
        criteria = self._criteria.get(user_id, [])
        interactions = [i for i in self._interactions if i.user_id == user_id]

        return {
            "version": "1.0",
            "user_id": user_id,
            "exported_at": datetime.now(UTC).isoformat(),
            "preferences": {k: v.to_dict() for k, v in prefs.items()},
            "criteria": [c.to_dict() for c in criteria],
            "interactions": [i.to_dict() for i in interactions],
        }

    def import_profile(self, user_id: str, data: dict[str, Any]) -> bool:
        """エクスポートされたプロファイルをインポートする.

        Args:
            user_id: インポート先ユーザー ID。
            data: export_profile() で生成されたデータ。

        Returns:
            インポート成功なら True。
        """
        version = data.get("version", "")
        if version != "1.0":
            logger.warning("Avatar: unsupported profile version '%s'", version)
            return False

        # 嗜好のインポート
        prefs_data = data.get("preferences", {})
        imported_prefs: dict[str, UserPreference] = {}
        for category, pref_dict in prefs_data.items():
            imported_prefs[category] = UserPreference(
                category=pref_dict.get("category", category),
                key=pref_dict.get("key", ""),
                value=pref_dict.get("value"),
                confidence=pref_dict.get("confidence", 0.0),
                learned_from=[],  # リセット
            )
        self._preferences[user_id] = imported_prefs

        # 意思決定基準のインポート
        criteria_data = data.get("criteria", [])
        imported_criteria: list[DecisionCriterion] = []
        for c_dict in criteria_data:
            imported_criteria.append(
                DecisionCriterion(
                    id=c_dict.get("id", str(uuid.uuid4())),
                    domain=c_dict.get("domain", ""),
                    description=c_dict.get("description", ""),
                    weight=c_dict.get("weight", 0.5),
                    applied_count=c_dict.get("applied_count", 0),
                    success_rate=c_dict.get("success_rate", 0.0),
                )
            )
        self._criteria[user_id] = imported_criteria

        # インタラクション履歴のインポート
        interactions_data = data.get("interactions", [])
        for i_dict in interactions_data:
            record = InteractionRecord(
                id=i_dict.get("id", str(uuid.uuid4())),
                user_id=user_id,
                context=i_dict.get("context", {}),
                user_decision=i_dict.get("user_decision", ""),
                ai_suggestion=i_dict.get("ai_suggestion", ""),
                user_accepted=i_dict.get("user_accepted", False),
                feedback=i_dict.get("feedback", ""),
            )
            self._interactions.append(record)

        logger.info(
            "Avatar: profile imported for user '%s' (%d prefs, %d criteria, %d interactions)",
            user_id,
            len(imported_prefs),
            len(imported_criteria),
            len(interactions_data),
        )
        return True


# グローバルインスタンス
avatar_coevolution = AvatarCoevolution()
