"""Meta-Skills — AI エージェントの「学び方を学ぶ」能力.

AI エージェントが自己改善するための 5 つのメタスキルを定義する:
  - Feeling: ユーザーインタラクションから感情・文脈シグナルを分析
  - Seeing: 過去の経験からパターンを認識
  - Dreaming: 創造的な仮説的解決策を生成
  - Making: 計画から具体的なアウトプットを生成
  - Learning: 実行結果から教訓を抽出し全メタスキルを更新

ROADMAP v0.3: Meta-Skills 基盤。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetaSkillType(str, Enum):
    """メタスキルの種類."""

    FEELING = "feeling"  # 直感・文脈感知
    SEEING = "seeing"  # パターン認識
    DREAMING = "dreaming"  # 創造的仮説生成
    MAKING = "making"  # 実行・成果物生成
    LEARNING = "learning"  # 教訓抽出・自己更新


@dataclass
class Insight:
    """メタスキル横断で生成される洞察."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_skill: MetaSkillType = MetaSkillType.LEARNING
    content: str = ""
    relevance_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """辞書表現を返す."""
        return {
            "id": self.id,
            "source_skill": self.source_skill.value,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat(),
            "applied_count": self.applied_count,
        }


@dataclass
class MetaSkillState:
    """各メタスキルの現在状態."""

    skill_type: MetaSkillType
    confidence: float = 0.0
    experience_count: int = 0
    last_activated: datetime | None = None
    insights: list[Insight] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """辞書表現を返す."""
        return {
            "skill_type": self.skill_type.value,
            "confidence": self.confidence,
            "experience_count": self.experience_count,
            "last_activated": (self.last_activated.isoformat() if self.last_activated else None),
            "insight_count": len(self.insights),
        }


# ---------------------------------------------------------------------------
# Meta-Skill Engine
# ---------------------------------------------------------------------------


class MetaSkillEngine:
    """メタスキルエンジン — 5 つのメタスキルを統合管理する.

    AI エージェントが自己の学習プロセス自体を改善できるよう、
    Feeling / Seeing / Dreaming / Making / Learning の 5 要素を
    相互に連携させる。
    """

    def __init__(self) -> None:
        self._states: dict[MetaSkillType, MetaSkillState] = {
            skill_type: MetaSkillState(skill_type=skill_type) for skill_type in MetaSkillType
        }
        self._global_insights: list[Insight] = []

    # ------------------------------------------------------------------
    # Feeling — 直感・文脈シグナル分析
    # ------------------------------------------------------------------

    async def feel(self, context: dict[str, Any]) -> dict[str, Any]:
        """ユーザーインタラクションから感情・文脈シグナルを分析し直感スコアを返す.

        Args:
            context: ユーザーの発話、トーン、緊急度などを含む辞書。

        Returns:
            直感スコアとシグナル分析結果。
        """
        state = self._states[MetaSkillType.FEELING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        # シグナル抽出
        urgency = context.get("urgency", 0.5)
        sentiment = context.get("sentiment", "neutral")
        complexity = context.get("complexity", 0.5)
        user_text = context.get("text", "")

        # 直感スコア計算: 緊急度・複雑度・テキスト長を総合
        text_density = min(len(user_text) / 500.0, 1.0)
        intuition_score = urgency * 0.4 + complexity * 0.3 + text_density * 0.3

        # 感情マッピング
        sentiment_map = {
            "positive": 0.2,
            "neutral": 0.0,
            "negative": -0.1,
            "frustrated": -0.3,
        }
        sentiment_modifier = sentiment_map.get(sentiment, 0.0)
        intuition_score = max(0.0, min(1.0, intuition_score + sentiment_modifier))

        # 信頼度を経験に基づいて更新
        state.confidence = min(1.0, state.confidence + 0.01 * (1.0 - state.confidence))

        result = {
            "intuition_score": round(intuition_score, 4),
            "signals": {
                "urgency": urgency,
                "sentiment": sentiment,
                "complexity": complexity,
                "text_density": round(text_density, 4),
            },
            "confidence": round(state.confidence, 4),
        }

        logger.debug("MetaSkill FEEL: intuition=%.3f", intuition_score)
        return result

    # ------------------------------------------------------------------
    # Seeing — パターン認識
    # ------------------------------------------------------------------

    async def see(self, data: dict[str, Any]) -> dict[str, Any]:
        """過去の経験データからパターンを認識する.

        Args:
            data: 分析対象のデータ。experiences (過去の経験リスト) や
                  current_context (現在のコンテキスト) を含む。

        Returns:
            発見されたパターンのリスト。
        """
        state = self._states[MetaSkillType.SEEING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        experiences: list[dict[str, Any]] = data.get("experiences", [])
        current_context = data.get("current_context", {})
        patterns_found: list[dict[str, Any]] = []

        # 類似コンテキストの経験を集約
        context_domain = current_context.get("domain", "")
        matching_experiences = [
            exp for exp in experiences if exp.get("domain", "") == context_domain
        ]

        if matching_experiences:
            # 成功率パターン
            successes = sum(1 for exp in matching_experiences if exp.get("success", False))
            total = len(matching_experiences)
            success_rate = successes / total if total > 0 else 0.0

            patterns_found.append(
                {
                    "pattern_type": "success_rate",
                    "domain": context_domain,
                    "value": round(success_rate, 4),
                    "sample_size": total,
                    "description": (
                        f"ドメイン '{context_domain}' での成功率: "
                        f"{success_rate:.1%} ({successes}/{total})"
                    ),
                }
            )

        # 頻出アプローチの抽出
        approach_counts: dict[str, int] = {}
        for exp in matching_experiences:
            approach = exp.get("approach", "unknown")
            approach_counts[approach] = approach_counts.get(approach, 0) + 1

        if approach_counts:
            best_approach = max(approach_counts, key=approach_counts.get)  # type: ignore[arg-type]
            patterns_found.append(
                {
                    "pattern_type": "preferred_approach",
                    "domain": context_domain,
                    "value": best_approach,
                    "frequency": approach_counts[best_approach],
                    "description": (
                        f"最頻出アプローチ: '{best_approach}' ({approach_counts[best_approach]} 回)"
                    ),
                }
            )

        # 信頼度更新
        state.confidence = min(
            1.0,
            state.confidence + 0.005 * len(patterns_found),
        )

        logger.debug("MetaSkill SEE: %d patterns found", len(patterns_found))
        return {
            "patterns": patterns_found,
            "total_experiences_analyzed": len(experiences),
            "matching_experiences": len(matching_experiences),
            "confidence": round(state.confidence, 4),
        }

    # ------------------------------------------------------------------
    # Dreaming — 創造的仮説生成
    # ------------------------------------------------------------------

    async def dream(self, problem_space: dict[str, Any]) -> dict[str, Any]:
        """問題空間から創造的な仮説的解決策を生成する.

        Args:
            problem_space: 問題の定義、制約条件、既知のアプローチなどを含む辞書。

        Returns:
            生成された仮説的解決策のリスト。
        """
        state = self._states[MetaSkillType.DREAMING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        problem = problem_space.get("problem", "")
        constraints: list[str] = problem_space.get("constraints", [])
        known_approaches: list[str] = problem_space.get("known_approaches", [])
        goals: list[str] = problem_space.get("goals", [])

        hypotheses: list[dict[str, Any]] = []

        # 既知アプローチの組み合わせによる新解法の生成
        if len(known_approaches) >= 2:
            for i, a1 in enumerate(known_approaches):
                for a2 in known_approaches[i + 1 :]:
                    hypotheses.append(
                        {
                            "hypothesis_id": str(uuid.uuid4()),
                            "type": "combination",
                            "description": f"'{a1}' と '{a2}' を組み合わせたハイブリッドアプローチ",
                            "source_approaches": [a1, a2],
                            "novelty_score": 0.6,
                            "feasibility_score": 0.7,
                        }
                    )

        # 制約緩和による解法の探索
        for constraint in constraints:
            hypotheses.append(
                {
                    "hypothesis_id": str(uuid.uuid4()),
                    "type": "constraint_relaxation",
                    "description": f"制約 '{constraint}' を緩和した場合の解法探索",
                    "relaxed_constraint": constraint,
                    "novelty_score": 0.8,
                    "feasibility_score": 0.4,
                }
            )

        # ゴール分解による段階的解法
        if goals:
            hypotheses.append(
                {
                    "hypothesis_id": str(uuid.uuid4()),
                    "type": "goal_decomposition",
                    "description": f"目標を {len(goals)} 段階に分解した段階的アプローチ",
                    "sub_goals": goals,
                    "novelty_score": 0.5,
                    "feasibility_score": 0.8,
                }
            )

        # 信頼度更新
        state.confidence = min(
            1.0,
            state.confidence + 0.008 * (1.0 - state.confidence),
        )

        logger.debug("MetaSkill DREAM: %d hypotheses generated", len(hypotheses))
        return {
            "hypotheses": hypotheses,
            "problem_summary": problem[:200],
            "constraints_count": len(constraints),
            "confidence": round(state.confidence, 4),
        }

    # ------------------------------------------------------------------
    # Making — 計画実行・成果物生成
    # ------------------------------------------------------------------

    async def make(self, plan: dict[str, Any]) -> dict[str, Any]:
        """計画から具体的なアウトプットを生成する.

        Args:
            plan: 実行する計画。steps, resources, expected_output を含む。

        Returns:
            実行結果とステータス。
        """
        state = self._states[MetaSkillType.MAKING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        steps: list[dict[str, Any]] = plan.get("steps", [])
        resources: list[str] = plan.get("resources", [])
        expected_output = plan.get("expected_output", "")

        execution_results: list[dict[str, Any]] = []
        completed = 0
        failed = 0

        for i, step in enumerate(steps):
            step_name = step.get("name", f"step_{i + 1}")
            step_action = step.get("action", "")
            prerequisites = step.get("prerequisites", [])

            # 前提条件チェック
            prereqs_met = all(
                any(r["step"] == p and r["success"] for r in execution_results)
                for p in prerequisites
            )

            if not prereqs_met and prerequisites:
                execution_results.append(
                    {
                        "step": step_name,
                        "action": step_action,
                        "success": False,
                        "reason": "前提条件が未達成",
                        "order": i + 1,
                    }
                )
                failed += 1
                continue

            # ステップ実行（シミュレーション）
            execution_results.append(
                {
                    "step": step_name,
                    "action": step_action,
                    "success": True,
                    "reason": "実行完了",
                    "order": i + 1,
                }
            )
            completed += 1

        total = len(steps)
        completion_rate = completed / total if total > 0 else 0.0

        # 信頼度更新
        state.confidence = min(
            1.0,
            state.confidence + 0.01 * completion_rate,
        )

        logger.debug("MetaSkill MAKE: %d/%d steps completed", completed, total)
        return {
            "execution_results": execution_results,
            "completed": completed,
            "failed": failed,
            "total_steps": total,
            "completion_rate": round(completion_rate, 4),
            "expected_output": expected_output,
            "resources_used": resources,
            "confidence": round(state.confidence, 4),
        }

    # ------------------------------------------------------------------
    # Learning — 教訓抽出・自己更新
    # ------------------------------------------------------------------

    async def learn(self, outcome: dict[str, Any]) -> dict[str, Any]:
        """実行結果から教訓を抽出し、全メタスキルの状態を更新する.

        Args:
            outcome: 実行結果。success, domain, approach, details, feedback を含む。

        Returns:
            抽出された教訓と更新されたメタスキル状態。
        """
        state = self._states[MetaSkillType.LEARNING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        success = outcome.get("success", False)
        domain = outcome.get("domain", "general")
        approach = outcome.get("approach", "")
        details = outcome.get("details", "")
        feedback = outcome.get("feedback", "")

        lessons: list[dict[str, Any]] = []

        # 成功/失敗からの教訓抽出
        if success:
            lesson = {
                "type": "success_pattern",
                "domain": domain,
                "approach": approach,
                "description": f"ドメイン '{domain}' で '{approach}' が成功",
                "actionable": f"同様の状況では '{approach}' を優先的に検討",
            }
            lessons.append(lesson)
        else:
            lesson = {
                "type": "failure_pattern",
                "domain": domain,
                "approach": approach,
                "description": f"ドメイン '{domain}' で '{approach}' が失敗: {details[:100]}",
                "actionable": f"'{approach}' の適用条件を再検討",
            }
            lessons.append(lesson)

        # フィードバックからの教訓
        if feedback:
            lessons.append(
                {
                    "type": "feedback_insight",
                    "domain": domain,
                    "description": f"ユーザーフィードバック: {feedback[:200]}",
                    "actionable": "フィードバックに基づきアプローチを調整",
                }
            )

        # Insight の生成と保存
        for lesson in lessons:
            insight = Insight(
                source_skill=MetaSkillType.LEARNING,
                content=lesson["description"],
                relevance_score=0.8 if success else 0.6,
            )
            state.insights.append(insight)
            self._global_insights.append(insight)

        # 全メタスキルの信頼度を微調整
        confidence_delta = 0.005 if success else -0.002
        for skill_state in self._states.values():
            skill_state.confidence = max(
                0.0,
                min(1.0, skill_state.confidence + confidence_delta),
            )

        logger.info(
            "MetaSkill LEARN: %d lessons extracted (success=%s)",
            len(lessons),
            success,
        )
        return {
            "lessons": lessons,
            "insights_generated": len(lessons),
            "success": success,
            "all_states": {k.value: v.to_dict() for k, v in self._states.items()},
        }

    # ------------------------------------------------------------------
    # 状態取得
    # ------------------------------------------------------------------

    def get_state(self, skill_type: MetaSkillType) -> MetaSkillState:
        """指定メタスキルの現在状態を返す."""
        return self._states[skill_type]

    def get_all_states(self) -> dict[MetaSkillType, MetaSkillState]:
        """全メタスキルの状態を返す."""
        return dict(self._states)

    # ------------------------------------------------------------------
    # 横断的インサイト
    # ------------------------------------------------------------------

    async def generate_meta_insight(self) -> Insight | None:
        """全メタスキルを横断した統合的インサイトを生成する.

        各スキルの経験・信頼度・直近のインサイトを総合し、
        メタレベルの洞察を導出する。
        """
        active_skills = [s for s in self._states.values() if s.experience_count > 0]
        if not active_skills:
            return None

        # 最も経験豊富なスキルと最も弱いスキルを特定
        most_experienced = max(active_skills, key=lambda s: s.experience_count)
        least_confident = min(active_skills, key=lambda s: s.confidence)

        # 最近のインサイトからテーマを抽出
        recent_insights = sorted(
            self._global_insights,
            key=lambda i: i.created_at,
            reverse=True,
        )[:10]

        insight_summary = (
            "; ".join(i.content[:50] for i in recent_insights)
            if recent_insights
            else "インサイトなし"
        )

        content = (
            f"メタ分析: 最も活用されているスキルは "
            f"'{most_experienced.skill_type.value}' "
            f"(経験数: {most_experienced.experience_count})。"
            f"信頼度が最も低いスキルは "
            f"'{least_confident.skill_type.value}' "
            f"(信頼度: {least_confident.confidence:.2f})。"
            f"直近のインサイト: {insight_summary}"
        )

        meta_insight = Insight(
            source_skill=MetaSkillType.LEARNING,
            content=content,
            relevance_score=0.9,
        )
        self._global_insights.append(meta_insight)

        logger.info("Meta-insight generated: %s", content[:80])
        return meta_insight

    async def suggest_learning_path(self, weakness_area: str) -> dict[str, Any]:
        """弱点領域に対する学習パスを提案する.

        Args:
            weakness_area: 改善したい領域（例: "pattern_recognition",
                "creative_thinking"）。

        Returns:
            推奨される学習ステップとメタスキルの活用順序。
        """
        # 弱点領域とメタスキルのマッピング
        area_skill_map: dict[str, list[MetaSkillType]] = {
            "pattern_recognition": [
                MetaSkillType.SEEING,
                MetaSkillType.LEARNING,
            ],
            "creative_thinking": [
                MetaSkillType.DREAMING,
                MetaSkillType.FEELING,
            ],
            "execution": [
                MetaSkillType.MAKING,
                MetaSkillType.SEEING,
            ],
            "user_understanding": [
                MetaSkillType.FEELING,
                MetaSkillType.LEARNING,
            ],
            "self_improvement": [
                MetaSkillType.LEARNING,
                MetaSkillType.DREAMING,
            ],
        }

        relevant_skills = area_skill_map.get(
            weakness_area,
            list(MetaSkillType),
        )

        steps: list[dict[str, Any]] = []
        for i, skill_type in enumerate(relevant_skills):
            skill_state = self._states[skill_type]
            steps.append(
                {
                    "order": i + 1,
                    "skill": skill_type.value,
                    "current_confidence": round(skill_state.confidence, 4),
                    "experience_count": skill_state.experience_count,
                    "recommendation": (
                        f"'{skill_type.value}' スキルを強化: "
                        f"現在の信頼度 {skill_state.confidence:.2f}、"
                        f"経験数 {skill_state.experience_count}"
                    ),
                    "exercises": self._suggest_exercises(skill_type),
                }
            )

        return {
            "weakness_area": weakness_area,
            "learning_path": steps,
            "estimated_sessions": max(3, 10 - len(relevant_skills)),
            "priority_skill": relevant_skills[0].value if relevant_skills else None,
        }

    def _suggest_exercises(self, skill_type: MetaSkillType) -> list[str]:
        """メタスキルごとの練習課題を提案する."""
        exercises_map: dict[MetaSkillType, list[str]] = {
            MetaSkillType.FEELING: [
                "ユーザー発話のトーン分析を 10 件実施",
                "コンテキスト切替時の直感精度を計測",
            ],
            MetaSkillType.SEEING: [
                "過去 50 件の実行ログからパターンを抽出",
                "類似タスクの成功要因を比較分析",
            ],
            MetaSkillType.DREAMING: [
                "既知アプローチの組合せから新解法を 5 件生成",
                "制約緩和シナリオを 3 パターン検討",
            ],
            MetaSkillType.MAKING: [
                "小規模計画を 3 件実行し完了率を計測",
                "前提条件チェーンの精度を検証",
            ],
            MetaSkillType.LEARNING: [
                "直近 10 件の成功/失敗から教訓を抽出",
                "フィードバックループの改善点を特定",
            ],
        }
        return exercises_map.get(skill_type, [])


# グローバルインスタンス
meta_skill_engine = MetaSkillEngine()
