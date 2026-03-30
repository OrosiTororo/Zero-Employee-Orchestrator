"""Execution Monitor — Real-time execution monitoring and WebSocket delivery.

Monitors multi-agent task execution in real-time and delivers reasoning traces,
communication logs, and state changes to the frontend via WebSocket.

Monitoring targets:
  - Agent state changes
  - Task execution progress
  - Individual reasoning trace steps
  - Inter-agent communication
  - Judge verdict results
  - Escalations and errors

Usage:
  monitor = get_execution_monitor()
  await monitor.on_task_started(task_id, agent_id, company_id)
  await monitor.on_reasoning_step(trace_id, step)
  await monitor.on_agent_message(message)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MonitorEventType(str, Enum):
    """Monitor event type."""

    # Task execution
    TASK_STARTED = "monitor.task.started"
    TASK_PROGRESS = "monitor.task.progress"
    TASK_COMPLETED = "monitor.task.completed"
    TASK_FAILED = "monitor.task.failed"
    TASK_RETRYING = "monitor.task.retrying"

    # Agent
    AGENT_STATE_CHANGED = "monitor.agent.state_changed"
    AGENT_ASSIGNED = "monitor.agent.assigned"
    AGENT_RELEASED = "monitor.agent.released"

    # Reasoning trace
    REASONING_STEP = "monitor.reasoning.step"
    REASONING_DECISION = "monitor.reasoning.decision"
    REASONING_COMPLETED = "monitor.reasoning.completed"

    # Agent communication
    AGENT_COMM = "monitor.agent_comm"
    AGENT_DELEGATION = "monitor.agent_delegation"
    AGENT_ESCALATION = "monitor.agent_escalation"

    # Quality / Governance
    JUDGE_RESULT = "monitor.judge.result"
    APPROVAL_REQUESTED = "monitor.approval.requested"
    APPROVAL_RESOLVED = "monitor.approval.resolved"
    COST_WARNING = "monitor.cost.warning"

    # System
    ERROR = "monitor.error"
    HEARTBEAT = "monitor.heartbeat"


@dataclass
class MonitorEvent:
    """Monitor event."""

    event_type: MonitorEventType
    company_id: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    task_id: str | None = None
    agent_id: str | None = None
    trace_id: str | None = None

    def to_ws_event(self) -> dict[str, Any]:
        """Convert to dict for WebSocket delivery."""
        return {
            "event_type": self.event_type.value,
            "target_type": "monitor",
            "target_id": self.task_id or self.agent_id,
            "data": {
                "company_id": self.company_id,
                "task_id": self.task_id,
                "agent_id": self.agent_id,
                "trace_id": self.trace_id,
                "timestamp": self.timestamp,
                **self.data,
            },
        }


@dataclass
class ActiveExecution:
    """Monitoring information for a currently executing task."""

    task_id: str
    agent_id: str
    company_id: str
    started_at: float = field(default_factory=time.time)
    status: str = "running"
    progress_pct: float = 0.0
    current_step: str = ""
    trace_id: str | None = None
    model_used: str | None = None
    provider_override: dict | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    reasoning_steps: int = 0
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "company_id": self.company_id,
            "started_at": self.started_at,
            "status": self.status,
            "progress_pct": self.progress_pct,
            "current_step": self.current_step,
            "trace_id": self.trace_id,
            "model_used": self.model_used,
            "provider_override": self.provider_override,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "reasoning_steps": self.reasoning_steps,
            "elapsed_ms": int((time.time() - self.started_at) * 1000),
            "last_updated": self.last_updated,
        }


class ExecutionMonitor:
    """Real-time execution monitoring.

    Works with WebSocket emit_event to deliver execution status
    to the frontend in real-time.

    Includes a kill switch mechanism to halt all active executions
    and prevent new ones from starting.
    """

    def __init__(self) -> None:
        self._active: dict[str, ActiveExecution] = {}  # task_id → ActiveExecution
        self._recent_events: list[MonitorEvent] = []
        self._max_events = 500
        self._killed: bool = False

    # ------------------------------------------------------------------
    # Kill switch
    # ------------------------------------------------------------------

    @property
    def is_killed(self) -> bool:
        """Whether the kill switch is currently active."""
        return self._killed

    async def kill_all(self) -> dict[str, Any]:
        """Activate the kill switch: stop all active executions and prevent new ones.

        Returns a summary of killed tasks.
        """
        self._killed = True
        killed_tasks: list[str] = []

        for task_id, execution in list(self._active.items()):
            execution.status = "killed"
            execution.last_updated = time.time()
            killed_tasks.append(task_id)

            await self._emit(
                MonitorEvent(
                    event_type=MonitorEventType.TASK_FAILED,
                    company_id=execution.company_id,
                    task_id=task_id,
                    agent_id=execution.agent_id,
                    trace_id=execution.trace_id,
                    data={
                        "error": "Kill switch activated — execution terminated",
                        "will_retry": False,
                        "killed_by": "kill_switch",
                    },
                )
            )

        # Clear all active executions
        self._active.clear()
        logger.warning("Kill switch activated — %d task(s) terminated", len(killed_tasks))

        return {
            "killed": True,
            "tasks_killed": len(killed_tasks),
            "task_ids": killed_tasks,
        }

    async def kill_task(self, task_id: str) -> dict[str, Any]:
        """Kill a specific task by its ID.

        Returns info about the killed task or an error if not found.
        """
        execution = self._active.pop(task_id, None)
        if execution is None:
            return {"killed": False, "error": f"Task {task_id} not found in active executions"}

        execution.status = "killed"
        execution.last_updated = time.time()

        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.TASK_FAILED,
                company_id=execution.company_id,
                task_id=task_id,
                agent_id=execution.agent_id,
                trace_id=execution.trace_id,
                data={
                    "error": "Task killed by operator",
                    "will_retry": False,
                    "killed_by": "kill_task",
                },
            )
        )

        logger.warning("Task %s killed by operator", task_id)
        return {"killed": True, "task_id": task_id, "agent_id": execution.agent_id}

    def resume(self) -> dict[str, Any]:
        """Deactivate the kill switch, allowing new executions to start again."""
        was_killed = self._killed
        self._killed = False
        logger.info("Kill switch deactivated (was_active=%s)", was_killed)
        return {"resumed": True, "was_killed": was_killed}

    # ------------------------------------------------------------------
    # Event delivery
    # ------------------------------------------------------------------

    async def _emit(self, event: MonitorEvent) -> None:
        """Deliver event via WebSocket."""
        self._recent_events.append(event)
        if len(self._recent_events) > self._max_events:
            self._recent_events = self._recent_events[-(self._max_events // 2) :]

        try:
            from app.api.ws.events import emit_event

            await emit_event(
                company_id=event.company_id,
                event_type=event.event_type.value,
                target_type="monitor",
                target_id=event.task_id or event.agent_id,
                data=event.to_ws_event()["data"],
            )
        except Exception as exc:
            logger.debug("Monitor emit failed (WS not available): %s", exc)

    # ------------------------------------------------------------------
    # Task execution events
    # ------------------------------------------------------------------

    async def on_task_started(
        self,
        task_id: str,
        agent_id: str,
        company_id: str,
        *,
        model: str | None = None,
        trace_id: str | None = None,
        provider_override: dict | None = None,
    ) -> None:
        """Task execution started.

        Raises RuntimeError if the kill switch is active.
        """
        if self._killed:
            logger.warning(
                "Kill switch active — rejecting new task %s from agent %s",
                task_id,
                agent_id,
            )
            raise RuntimeError(
                "Kill switch is active. No new executions are allowed. "
                "Call resume() to re-enable executions."
            )

        execution = ActiveExecution(
            task_id=task_id,
            agent_id=agent_id,
            company_id=company_id,
            trace_id=trace_id,
            model_used=model,
            provider_override=provider_override,
        )
        self._active[task_id] = execution

        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.TASK_STARTED,
                company_id=company_id,
                task_id=task_id,
                agent_id=agent_id,
                trace_id=trace_id,
                data={
                    "model": model,
                    "message": f"Agent {agent_id} started task execution",
                },
            )
        )

    async def on_task_progress(
        self,
        task_id: str,
        progress_pct: float,
        current_step: str,
        company_id: str,
    ) -> None:
        """Task progress update."""
        if task_id in self._active:
            ex = self._active[task_id]
            ex.progress_pct = progress_pct
            ex.current_step = current_step
            ex.last_updated = time.time()

        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.TASK_PROGRESS,
                company_id=company_id,
                task_id=task_id,
                data={
                    "progress_pct": progress_pct,
                    "current_step": current_step,
                },
            )
        )

    async def on_task_completed(
        self,
        task_id: str,
        company_id: str,
        *,
        outcome: str = "succeeded",
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Task completed."""
        execution = self._active.pop(task_id, None)

        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.TASK_COMPLETED,
                company_id=company_id,
                task_id=task_id,
                agent_id=execution.agent_id if execution else None,
                trace_id=execution.trace_id if execution else None,
                data={
                    "outcome": outcome,
                    "tokens_used": tokens_used,
                    "cost_usd": cost_usd,
                    "duration_ms": int((time.time() - execution.started_at) * 1000)
                    if execution
                    else 0,
                },
            )
        )

    async def on_task_failed(
        self,
        task_id: str,
        company_id: str,
        error: str,
        *,
        will_retry: bool = False,
    ) -> None:
        """Task failed."""
        execution = self._active.get(task_id)
        event_type = MonitorEventType.TASK_RETRYING if will_retry else MonitorEventType.TASK_FAILED

        if not will_retry:
            self._active.pop(task_id, None)

        await self._emit(
            MonitorEvent(
                event_type=event_type,
                company_id=company_id,
                task_id=task_id,
                agent_id=execution.agent_id if execution else None,
                data={
                    "error": error,
                    "will_retry": will_retry,
                },
            )
        )

    # ------------------------------------------------------------------
    # Reasoning trace events
    # ------------------------------------------------------------------

    async def on_reasoning_step(
        self,
        task_id: str,
        company_id: str,
        step_type: str,
        summary: str,
        *,
        trace_id: str | None = None,
        details: dict | None = None,
        confidence: str = "medium",
    ) -> None:
        """Reasoning step occurred."""
        if task_id in self._active:
            self._active[task_id].reasoning_steps += 1
            self._active[task_id].current_step = summary
            self._active[task_id].last_updated = time.time()

        is_decision = step_type == "decision"
        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.REASONING_DECISION
                if is_decision
                else MonitorEventType.REASONING_STEP,
                company_id=company_id,
                task_id=task_id,
                trace_id=trace_id,
                data={
                    "step_type": step_type,
                    "summary": summary,
                    "confidence": confidence,
                    "details": details or {},
                },
            )
        )

    async def on_reasoning_completed(
        self,
        task_id: str,
        company_id: str,
        trace_id: str,
        total_steps: int,
        total_decisions: int,
        outcome: str,
    ) -> None:
        """Reasoning trace completed."""
        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.REASONING_COMPLETED,
                company_id=company_id,
                task_id=task_id,
                trace_id=trace_id,
                data={
                    "total_steps": total_steps,
                    "total_decisions": total_decisions,
                    "outcome": outcome,
                },
            )
        )

    # ------------------------------------------------------------------
    # Agent communication events
    # ------------------------------------------------------------------

    async def on_agent_message(
        self,
        company_id: str,
        msg_type: str,
        sender_agent_id: str | None,
        receiver_agent_id: str | None,
        content: str,
        *,
        task_id: str | None = None,
    ) -> None:
        """Inter-agent message."""
        is_delegation = msg_type == "delegation"
        is_escalation = msg_type == "escalation"

        if is_escalation:
            event_type = MonitorEventType.AGENT_ESCALATION
        elif is_delegation:
            event_type = MonitorEventType.AGENT_DELEGATION
        else:
            event_type = MonitorEventType.AGENT_COMM

        await self._emit(
            MonitorEvent(
                event_type=event_type,
                company_id=company_id,
                task_id=task_id,
                agent_id=sender_agent_id,
                data={
                    "msg_type": msg_type,
                    "sender": sender_agent_id,
                    "receiver": receiver_agent_id,
                    "content": content,
                },
            )
        )

    # ------------------------------------------------------------------
    # Quality / Governance events
    # ------------------------------------------------------------------

    async def on_judge_result(
        self,
        task_id: str,
        company_id: str,
        verdict: str,
        score: float,
        reasons: list[str],
    ) -> None:
        """Judge verdict result."""
        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.JUDGE_RESULT,
                company_id=company_id,
                task_id=task_id,
                data={
                    "verdict": verdict,
                    "score": score,
                    "reasons": reasons,
                },
            )
        )

    async def on_error(
        self,
        company_id: str,
        error: str,
        *,
        task_id: str | None = None,
        agent_id: str | None = None,
        severity: str = "medium",
    ) -> None:
        """Error notification."""
        await self._emit(
            MonitorEvent(
                event_type=MonitorEventType.ERROR,
                company_id=company_id,
                task_id=task_id,
                agent_id=agent_id,
                data={
                    "error": error,
                    "severity": severity,
                },
            )
        )

    # ------------------------------------------------------------------
    # Monitoring dashboard queries
    # ------------------------------------------------------------------

    def get_active_executions(self, company_id: str | None = None) -> list[dict]:
        """List of currently executing tasks."""
        result = list(self._active.values())
        if company_id:
            result = [e for e in result if e.company_id == company_id]
        return [e.to_dict() for e in result]

    def get_recent_events(
        self,
        company_id: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List of recent events."""
        result = self._recent_events
        if company_id:
            result = [e for e in result if e.company_id == company_id]
        if event_type:
            result = [e for e in result if e.event_type.value == event_type]
        return [e.to_ws_event() for e in result[-limit:]]

    def get_agent_activity(self, agent_id: str) -> dict[str, Any]:
        """Agent activity summary."""
        active_tasks = [e for e in self._active.values() if e.agent_id == agent_id]
        recent = [e for e in self._recent_events if e.agent_id == agent_id]

        return {
            "agent_id": agent_id,
            "active_task_count": len(active_tasks),
            "active_tasks": [e.to_dict() for e in active_tasks],
            "recent_event_count": len(recent[-50:]),
            "recent_events": [e.to_ws_event() for e in recent[-20:]],
        }

    def get_system_summary(self, company_id: str | None = None) -> dict[str, Any]:
        """System-wide summary."""
        active = self.get_active_executions(company_id)
        events = self._recent_events
        if company_id:
            events = [e for e in events if e.company_id == company_id]

        errors = [e for e in events if e.event_type == MonitorEventType.ERROR]
        escalations = [e for e in events if e.event_type == MonitorEventType.AGENT_ESCALATION]

        return {
            "active_executions": len(active),
            "total_events": len(events),
            "recent_errors": len(errors[-10:]),
            "recent_escalations": len(escalations[-10:]),
            "active_agents": list(set(e["agent_id"] for e in active if e.get("agent_id"))),
        }

    @property
    def active_count(self) -> int:
        return len(self._active)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_monitor: ExecutionMonitor | None = None


def get_execution_monitor() -> ExecutionMonitor:
    global _monitor
    if _monitor is None:
        _monitor = ExecutionMonitor()
    return _monitor
