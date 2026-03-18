"""Reasoning Trace — エージェント推論過程の記録と可視化.

エージェントがタスクを実行する際の思考過程を段階的に記録し、
「なぜその判断をしたか」を追跡可能にする。ブラックボックス化を解消する
ための中核モジュール。

記録される推論ステップ:
  1. コンテキスト収集 — どの情報を参照したか
  2. 選択肢列挙 — どのような選択肢があったか
  3. 評価・比較 — 各選択肢をどう評価したか
  4. 意思決定 — 最終的にどれを選び、なぜか
  5. 実行結果 — 結果と自己評価

使い方:
  trace = ReasoningTrace(task_id="...", agent_id="...")
  trace.add_step(ReasoningStepType.CONTEXT, "Spec の制約条件を確認", {...})
  trace.add_step(ReasoningStepType.DECISION, "Claude Opus を選択", {"reason": "品質CRITICAL"})
  trace.finalize(outcome="succeeded")
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ReasoningStepType(str, Enum):
    """推論ステップの種類."""

    # 情報収集フェーズ
    CONTEXT_GATHERING = "context_gathering"  # 情報源からのコンテキスト収集
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # Experience Memory / RAG からの知識検索
    CONSTRAINT_CHECK = "constraint_check"  # 制約条件・ポリシーの確認

    # 分析フェーズ
    OPTION_ENUMERATION = "option_enumeration"  # 選択肢の列挙
    OPTION_EVALUATION = "option_evaluation"  # 各選択肢の評価・スコアリング
    RISK_ASSESSMENT = "risk_assessment"  # リスク評価

    # 意思決定フェーズ
    DECISION = "decision"  # 最終的な意思決定
    DELEGATION = "delegation"  # 他エージェントへの委譲判断
    APPROVAL_REQUEST = "approval_request"  # 承認要求の判断

    # 実行フェーズ
    MODEL_SELECTION = "model_selection"  # LLM モデルの選択理由
    TOOL_SELECTION = "tool_selection"  # ツール・Skill の選択理由
    PROMPT_CONSTRUCTION = "prompt_construction"  # プロンプト構築の意図
    EXECUTION = "execution"  # 実行とその結果

    # 検証フェーズ
    QUALITY_CHECK = "quality_check"  # 出力品質の自己評価
    JUDGE_RESULT = "judge_result"  # Judge Layer の判定結果
    SELF_CORRECTION = "self_correction"  # 自己修正の判断

    # 例外フェーズ
    ERROR_ANALYSIS = "error_analysis"  # エラー原因の分析
    FALLBACK_DECISION = "fallback_decision"  # フォールバック戦略の選択
    REPLAN_TRIGGER = "replan_trigger"  # 再計画のトリガー


class ReasoningConfidence(str, Enum):
    """推論の確信度."""

    HIGH = "high"  # 明確な根拠あり
    MEDIUM = "medium"  # 合理的だが他の選択肢もあり得る
    LOW = "low"  # 不確実、より多くの情報が必要
    UNCERTAIN = "uncertain"  # 判断材料が不足


@dataclass
class ReasoningStep:
    """推論の1ステップ."""

    step_id: str
    step_type: ReasoningStepType
    summary: str  # 人間が読める要約
    details: dict[str, Any]  # 構造化された詳細情報
    confidence: ReasoningConfidence = ReasoningConfidence.MEDIUM
    timestamp: float = field(default_factory=time.time)
    duration_ms: int = 0  # このステップの所要時間
    parent_step_id: str | None = None  # 親ステップ（ネスト時）
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "summary": self.summary,
            "details": self.details,
            "confidence": self.confidence.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "parent_step_id": self.parent_step_id,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningTrace:
    """1つのタスク実行における推論トレース全体."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str | None = None
    task_run_id: str | None = None
    agent_id: str | None = None
    company_id: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    outcome: str | None = None  # succeeded, failed, cancelled
    steps: list[ReasoningStep] = field(default_factory=list)
    summary: str = ""  # 全体の推論サマリー
    total_decisions: int = 0
    total_fallbacks: int = 0

    def add_step(
        self,
        step_type: ReasoningStepType,
        summary: str,
        details: dict[str, Any] | None = None,
        *,
        confidence: ReasoningConfidence = ReasoningConfidence.MEDIUM,
        parent_step_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReasoningStep:
        """推論ステップを追加."""
        step = ReasoningStep(
            step_id=str(uuid.uuid4()),
            step_type=step_type,
            summary=summary,
            details=details or {},
            confidence=confidence,
            timestamp=time.time(),
            parent_step_id=parent_step_id,
            metadata=metadata or {},
        )
        self.steps.append(step)

        if step_type == ReasoningStepType.DECISION:
            self.total_decisions += 1
        elif step_type == ReasoningStepType.FALLBACK_DECISION:
            self.total_fallbacks += 1

        return step

    def add_context(
        self, summary: str, sources: list[str], data: dict | None = None
    ) -> ReasoningStep:
        """コンテキスト収集ステップを追加（ショートカット）."""
        return self.add_step(
            ReasoningStepType.CONTEXT_GATHERING,
            summary,
            {"sources": sources, **(data or {})},
        )

    def add_decision(
        self,
        summary: str,
        chosen: str,
        alternatives: list[str] | None = None,
        reason: str = "",
        confidence: ReasoningConfidence = ReasoningConfidence.MEDIUM,
    ) -> ReasoningStep:
        """意思決定ステップを追加（ショートカット）."""
        return self.add_step(
            ReasoningStepType.DECISION,
            summary,
            {
                "chosen": chosen,
                "alternatives": alternatives or [],
                "reason": reason,
            },
            confidence=confidence,
        )

    def add_model_selection(
        self,
        model: str,
        mode: str,
        reason: str,
        candidates: list[str] | None = None,
    ) -> ReasoningStep:
        """モデル選択ステップを追加（ショートカット）."""
        return self.add_step(
            ReasoningStepType.MODEL_SELECTION,
            f"モデル選択: {model} ({mode}モード)",
            {
                "selected_model": model,
                "execution_mode": mode,
                "reason": reason,
                "candidates": candidates or [],
            },
        )

    def add_judge_result(
        self,
        verdict: str,
        score: float,
        reasons: list[str],
        violations: list[str] | None = None,
    ) -> ReasoningStep:
        """Judge判定結果を追加（ショートカット）."""
        return self.add_step(
            ReasoningStepType.JUDGE_RESULT,
            f"品質判定: {verdict} (スコア: {score:.2f})",
            {
                "verdict": verdict,
                "score": score,
                "reasons": reasons,
                "policy_violations": violations or [],
            },
        )

    def add_error(self, error: str, analysis: str, recovery_plan: str = "") -> ReasoningStep:
        """エラー分析ステップを追加（ショートカット）."""
        return self.add_step(
            ReasoningStepType.ERROR_ANALYSIS,
            f"エラー分析: {error}",
            {
                "error": error,
                "analysis": analysis,
                "recovery_plan": recovery_plan,
            },
            confidence=ReasoningConfidence.LOW,
        )

    def finalize(self, outcome: str, summary: str = "") -> None:
        """トレースを完了する."""
        self.finished_at = time.time()
        self.outcome = outcome
        if summary:
            self.summary = summary
        else:
            self.summary = f"{len(self.steps)}ステップ, {self.total_decisions}判断, 結果: {outcome}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "task_run_id": self.task_run_id,
            "agent_id": self.agent_id,
            "company_id": self.company_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "outcome": self.outcome,
            "summary": self.summary,
            "total_decisions": self.total_decisions,
            "total_fallbacks": self.total_fallbacks,
            "steps": [s.to_dict() for s in self.steps],
            "duration_ms": int((self.finished_at - self.started_at) * 1000)
            if self.finished_at
            else None,
        }

    def get_decisions(self) -> list[ReasoningStep]:
        """意思決定ステップのみを抽出."""
        return [s for s in self.steps if s.step_type == ReasoningStepType.DECISION]

    def get_errors(self) -> list[ReasoningStep]:
        """エラー関連ステップのみを抽出."""
        return [
            s
            for s in self.steps
            if s.step_type
            in (
                ReasoningStepType.ERROR_ANALYSIS,
                ReasoningStepType.FALLBACK_DECISION,
            )
        ]


# ---------------------------------------------------------------------------
# In-memory trace store (production では DB に永続化する)
# ---------------------------------------------------------------------------


class TraceStore:
    """推論トレースのインメモリストア.

    最大保持数を超えると古いトレースから自動削除される。
    将来的には DB バックエンドに置き換え可能。
    """

    def __init__(self, max_traces: int = 1000) -> None:
        self._traces: dict[str, ReasoningTrace] = {}
        self._max_traces = max_traces

    def store(self, trace: ReasoningTrace) -> None:
        """トレースを保存."""
        if len(self._traces) >= self._max_traces:
            # 最も古いトレースを削除
            oldest_id = min(self._traces, key=lambda k: self._traces[k].started_at)
            del self._traces[oldest_id]
        self._traces[trace.trace_id] = trace

    def get(self, trace_id: str) -> ReasoningTrace | None:
        return self._traces.get(trace_id)

    def get_by_task(self, task_id: str) -> list[ReasoningTrace]:
        return [t for t in self._traces.values() if t.task_id == task_id]

    def get_by_agent(self, agent_id: str, limit: int = 20) -> list[ReasoningTrace]:
        traces = [t for t in self._traces.values() if t.agent_id == agent_id]
        traces.sort(key=lambda t: t.started_at, reverse=True)
        return traces[:limit]

    def get_recent(self, company_id: str | None = None, limit: int = 50) -> list[ReasoningTrace]:
        traces = list(self._traces.values())
        if company_id:
            traces = [t for t in traces if t.company_id == company_id]
        traces.sort(key=lambda t: t.started_at, reverse=True)
        return traces[:limit]

    def get_active(self) -> list[ReasoningTrace]:
        """現在実行中（未完了）のトレースを取得."""
        return [t for t in self._traces.values() if t.finished_at is None]

    @property
    def count(self) -> int:
        return len(self._traces)


# Global store
trace_store = TraceStore()
