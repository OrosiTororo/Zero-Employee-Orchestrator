"""Reasoning Trace — Agent reasoning process recording and visualization.

Records the thought process step-by-step as agents execute tasks,
making it possible to trace "why that decision was made." A core module
for eliminating black-box behavior.

Recorded reasoning steps:
  1. Context gathering — what information was referenced
  2. Option enumeration — what options were available
  3. Evaluation / comparison — how each option was evaluated
  4. Decision — what was ultimately chosen and why
  5. Execution result — outcome and self-evaluation

Usage:
  trace = ReasoningTrace(task_id="...", agent_id="...")
  trace.add_step(ReasoningStepType.CONTEXT, "Check spec constraints", {...})
  trace.add_step(ReasoningStepType.DECISION, "Selected Claude Opus", {"reason": "CRITICAL quality"})
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
    """Reasoning step type."""

    # Information gathering phase
    CONTEXT_GATHERING = "context_gathering"  # Context collection from sources
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # Knowledge retrieval from Experience Memory / RAG
    CONSTRAINT_CHECK = "constraint_check"  # Constraint / policy verification

    # Analysis phase
    OPTION_ENUMERATION = "option_enumeration"  # Option enumeration
    OPTION_EVALUATION = "option_evaluation"  # Option evaluation / scoring
    RISK_ASSESSMENT = "risk_assessment"  # Risk assessment

    # Decision phase
    DECISION = "decision"  # Final decision
    DELEGATION = "delegation"  # Delegation decision to another agent
    APPROVAL_REQUEST = "approval_request"  # Approval request decision

    # Execution phase
    MODEL_SELECTION = "model_selection"  # LLM model selection rationale
    TOOL_SELECTION = "tool_selection"  # Tool / Skill selection rationale
    PROMPT_CONSTRUCTION = "prompt_construction"  # Prompt construction intent
    EXECUTION = "execution"  # Execution and its result

    # Verification phase
    QUALITY_CHECK = "quality_check"  # Self-evaluation of output quality
    JUDGE_RESULT = "judge_result"  # Judge Layer verdict
    SELF_CORRECTION = "self_correction"  # Self-correction decision

    # Exception phase
    ERROR_ANALYSIS = "error_analysis"  # Error cause analysis
    FALLBACK_DECISION = "fallback_decision"  # Fallback strategy selection
    REPLAN_TRIGGER = "replan_trigger"  # Replan trigger


class ReasoningConfidence(str, Enum):
    """Reasoning confidence level."""

    HIGH = "high"  # Clear basis exists
    MEDIUM = "medium"  # Reasonable but alternatives exist
    LOW = "low"  # Uncertain, more information needed
    UNCERTAIN = "uncertain"  # Insufficient information for judgment


@dataclass
class ReasoningStep:
    """A single reasoning step."""

    step_id: str
    step_type: ReasoningStepType
    summary: str  # Human-readable summary
    details: dict[str, Any]  # Structured detail information
    confidence: ReasoningConfidence = ReasoningConfidence.MEDIUM
    timestamp: float = field(default_factory=time.time)
    duration_ms: int = 0  # Duration of this step
    parent_step_id: str | None = None  # Parent step (when nested)
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
    """Complete reasoning trace for a single task execution."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str | None = None
    task_run_id: str | None = None
    agent_id: str | None = None
    company_id: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    outcome: str | None = None  # succeeded, failed, cancelled
    steps: list[ReasoningStep] = field(default_factory=list)
    summary: str = ""  # Overall reasoning summary
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
        """Add a reasoning step."""
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
        """Add a context gathering step (shortcut)."""
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
        """Add a decision step (shortcut)."""
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
        """Add a model selection step (shortcut)."""
        return self.add_step(
            ReasoningStepType.MODEL_SELECTION,
            f"Model selection: {model} ({mode} mode)",
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
        """Add Judge verdict result (shortcut)."""
        return self.add_step(
            ReasoningStepType.JUDGE_RESULT,
            f"Quality verdict: {verdict} (score: {score:.2f})",
            {
                "verdict": verdict,
                "score": score,
                "reasons": reasons,
                "policy_violations": violations or [],
            },
        )

    def add_error(self, error: str, analysis: str, recovery_plan: str = "") -> ReasoningStep:
        """Add an error analysis step (shortcut)."""
        return self.add_step(
            ReasoningStepType.ERROR_ANALYSIS,
            f"Error analysis: {error}",
            {
                "error": error,
                "analysis": analysis,
                "recovery_plan": recovery_plan,
            },
            confidence=ReasoningConfidence.LOW,
        )

    def finalize(self, outcome: str, summary: str = "") -> None:
        """Finalize the trace."""
        self.finished_at = time.time()
        self.outcome = outcome
        if summary:
            self.summary = summary
        else:
            self.summary = f"{len(self.steps)} steps, {self.total_decisions} decisions, outcome: {outcome}"

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
        """Extract only decision steps."""
        return [s for s in self.steps if s.step_type == ReasoningStepType.DECISION]

    def get_errors(self) -> list[ReasoningStep]:
        """Extract only error-related steps."""
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
# In-memory trace store (in production, persist to DB)
# ---------------------------------------------------------------------------


class TraceStore:
    """In-memory store for reasoning traces.

    Automatically deletes oldest traces when max capacity is exceeded.
    Can be replaced with a DB backend in the future.
    """

    def __init__(self, max_traces: int = 1000) -> None:
        self._traces: dict[str, ReasoningTrace] = {}
        self._max_traces = max_traces

    def store(self, trace: ReasoningTrace) -> None:
        """Store a trace."""
        if len(self._traces) >= self._max_traces:
            # Delete the oldest trace
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
        """Get currently running (unfinished) traces."""
        return [t for t in self._traces.values() if t.finished_at is None]

    @property
    def count(self) -> int:
        return len(self._traces)


# Global store
trace_store = TraceStore()
