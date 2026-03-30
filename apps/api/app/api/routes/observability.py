"""Observability API routes — reasoning traces, communication logs, execution monitoring.

API to eliminate the black-box nature of multi-agent systems:
  - /traces/*       — Reasoning traces (why a decision was made)
  - /communications/* — Inter-agent communication logs
  - /monitor/*      — Real-time execution monitoring
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TraceStepResponse(BaseModel):
    step_id: str
    step_type: str
    summary: str
    details: dict = {}
    confidence: str = "medium"
    timestamp: float
    duration_ms: int = 0
    parent_step_id: str | None = None


class TraceResponse(BaseModel):
    trace_id: str
    task_id: str | None = None
    agent_id: str | None = None
    started_at: float
    finished_at: float | None = None
    outcome: str | None = None
    summary: str = ""
    total_decisions: int = 0
    total_fallbacks: int = 0
    duration_ms: int | None = None
    steps: list[TraceStepResponse] = []


class TraceListResponse(BaseModel):
    traces: list[TraceResponse]
    total: int


class AgentMessageResponse(BaseModel):
    message_id: str
    msg_type: str
    sender_agent_id: str | None = None
    receiver_agent_id: str | None = None
    task_id: str | None = None
    content: str = ""
    structured_data: dict = {}
    priority: str = "normal"
    in_reply_to: str | None = None
    thread_id: str | None = None
    timestamp: float
    acknowledged: bool = False


class CommListResponse(BaseModel):
    messages: list[AgentMessageResponse]
    total: int


class ThreadResponse(BaseModel):
    thread_id: str
    task_id: str | None = None
    participants: list[str] = []
    subject: str = ""
    message_count: int = 0
    messages: list[AgentMessageResponse] = []
    started_at: float
    closed_at: float | None = None


class ActiveExecutionResponse(BaseModel):
    task_id: str
    agent_id: str
    company_id: str
    started_at: float
    status: str = "running"
    progress_pct: float = 0.0
    current_step: str = ""
    trace_id: str | None = None
    model_used: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    reasoning_steps: int = 0
    elapsed_ms: int = 0


class MonitorSummaryResponse(BaseModel):
    active_executions: int
    total_events: int
    recent_errors: int
    recent_escalations: int
    active_agents: list[str] = []


class MonitorDashboardResponse(BaseModel):
    summary: MonitorSummaryResponse
    active: list[ActiveExecutionResponse]
    recent_events: list[dict] = []


class EscalationResponse(BaseModel):
    messages: list[AgentMessageResponse]
    total: int


# ---------------------------------------------------------------------------
# Reasoning Trace API
# ---------------------------------------------------------------------------


@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    company_id: str | None = None,
    task_id: str | None = None,
    agent_id: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    """List reasoning traces.

    View agent thought processes and decision rationale.
    """
    from app.orchestration.reasoning_trace import trace_store

    if task_id:
        traces = trace_store.get_by_task(task_id)
    elif agent_id:
        traces = trace_store.get_by_agent(agent_id, limit=limit)
    else:
        traces = trace_store.get_recent(company_id=company_id, limit=limit)

    return TraceListResponse(
        traces=[_trace_to_response(t) for t in traces],
        total=len(traces),
    )


@router.get("/traces/active", response_model=TraceListResponse)
async def list_active_traces(user: User = Depends(get_current_user)):
    """Get currently active reasoning traces."""
    from app.orchestration.reasoning_trace import trace_store

    traces = trace_store.get_active()
    return TraceListResponse(
        traces=[_trace_to_response(t) for t in traces],
        total=len(traces),
    )


@router.get("/traces/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: str, user: User = Depends(get_current_user)):
    """Get details of a specific reasoning trace.

    Includes reasoning process, decision rationale, and confidence for each step.
    """
    from app.orchestration.reasoning_trace import trace_store

    trace = trace_store.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    return _trace_to_response(trace, include_steps=True)


@router.get("/traces/{trace_id}/decisions")
async def get_trace_decisions(trace_id: str, user: User = Depends(get_current_user)):
    """Extract only the decision steps from a reasoning trace.

    Concisely view what the agent chose and why it made that decision.
    """
    from app.orchestration.reasoning_trace import trace_store

    trace = trace_store.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    decisions = trace.get_decisions()
    return {
        "trace_id": trace_id,
        "decisions": [
            {
                "step_id": s.step_id,
                "summary": s.summary,
                "chosen": s.details.get("chosen", ""),
                "alternatives": s.details.get("alternatives", []),
                "reason": s.details.get("reason", ""),
                "confidence": s.confidence.value,
                "timestamp": s.timestamp,
            }
            for s in decisions
        ],
        "total": len(decisions),
    }


# ---------------------------------------------------------------------------
# Inter-agent Communication API
# ---------------------------------------------------------------------------


@router.get("/communications", response_model=CommListResponse)
async def list_communications(
    company_id: str | None = None,
    agent_id: str | None = None,
    task_id: str | None = None,
    msg_type: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    """List inter-agent communication logs.

    View all messages during multi-agent coordination.
    """
    from app.orchestration.agent_communication import MessageType, comm_log

    mt = MessageType(msg_type) if msg_type else None
    messages = comm_log.get_messages(
        agent_id=agent_id,
        task_id=task_id,
        msg_type=mt,
        company_id=company_id,
        limit=limit,
    )

    return CommListResponse(
        messages=[_msg_to_response(m) for m in messages],
        total=len(messages),
    )


@router.get("/communications/escalations", response_model=EscalationResponse)
async def list_escalations(
    company_id: str | None = None,
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    """List escalations.

    Display items where agents could not make a decision and deferred to humans.
    """
    from app.orchestration.agent_communication import comm_log

    escalations = comm_log.get_escalations(company_id=company_id, limit=limit)
    return EscalationResponse(
        messages=[_msg_to_response(m) for m in escalations],
        total=len(escalations),
    )


@router.get("/communications/agent/{agent_id}/interactions")
async def get_agent_interactions(agent_id: str, user: User = Depends(get_current_user)):
    """Aggregated communication statistics for a specific agent.

    Understand which agents interact most frequently.
    """
    from app.orchestration.agent_communication import comm_log

    interactions = comm_log.get_agent_interactions(agent_id)
    return {
        "agent_id": agent_id,
        "interactions": interactions,
        "total_partners": len(interactions),
        "total_messages": sum(interactions.values()),
    }


@router.get("/communications/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str, user: User = Depends(get_current_user)):
    """Get conversation thread details."""
    from app.orchestration.agent_communication import comm_log

    thread = comm_log.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    return ThreadResponse(
        thread_id=thread.thread_id,
        task_id=thread.task_id,
        participants=thread.participants,
        subject=thread.subject,
        message_count=len(thread.messages),
        messages=[_msg_to_response(m) for m in thread.messages],
        started_at=thread.started_at,
        closed_at=thread.closed_at,
    )


# ---------------------------------------------------------------------------
# Execution Monitoring API
# ---------------------------------------------------------------------------


@router.get("/monitor/dashboard", response_model=MonitorDashboardResponse)
async def monitor_dashboard(company_id: str | None = None, user: User = Depends(get_current_user)):
    """Execution monitoring dashboard.

    Retrieve currently running tasks, recent events, and system summary in one call.
    """
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    summary_data = monitor.get_system_summary(company_id)
    active = monitor.get_active_executions(company_id)
    recent = monitor.get_recent_events(company_id=company_id, limit=30)

    return MonitorDashboardResponse(
        summary=MonitorSummaryResponse(**summary_data),
        active=[ActiveExecutionResponse(**e) for e in active],
        recent_events=recent,
    )


@router.get("/monitor/active")
async def list_active_executions(
    company_id: str | None = None, user: User = Depends(get_current_user)
):
    """List currently running tasks."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    active = monitor.get_active_executions(company_id)
    return {"executions": active, "total": len(active)}


@router.get("/monitor/agent/{agent_id}")
async def get_agent_activity(agent_id: str, user: User = Depends(get_current_user)):
    """Get activity for a specific agent."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    return monitor.get_agent_activity(agent_id)


@router.get("/monitor/events")
async def list_monitor_events(
    company_id: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    """List monitoring events."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    events = monitor.get_recent_events(company_id, event_type, limit)
    return {"events": events, "total": len(events)}


# ---------------------------------------------------------------------------
# Kill Switch API
# ---------------------------------------------------------------------------


class KillSwitchStatusResponse(BaseModel):
    active: bool
    active_executions: int


class KillSwitchActivateResponse(BaseModel):
    killed: bool
    tasks_killed: int
    task_ids: list[str] = []


class KillSwitchTaskResponse(BaseModel):
    killed: bool
    task_id: str | None = None
    agent_id: str | None = None
    error: str | None = None


class KillSwitchDeactivateResponse(BaseModel):
    resumed: bool
    was_killed: bool


@router.post("/kill-switch/activate", response_model=KillSwitchActivateResponse)
async def activate_kill_switch(user: User = Depends(get_current_user)):
    """Activate the kill switch — stop all active executions and block new ones."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    result = await monitor.kill_all()
    logger.warning("Kill switch activated by user %s", user.id)
    return KillSwitchActivateResponse(**result)


@router.post("/kill-switch/deactivate", response_model=KillSwitchDeactivateResponse)
async def deactivate_kill_switch(user: User = Depends(get_current_user)):
    """Deactivate the kill switch — allow new executions to start."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    result = monitor.resume()
    logger.info("Kill switch deactivated by user %s", user.id)
    return KillSwitchDeactivateResponse(**result)


@router.post("/kill-switch/task/{task_id}", response_model=KillSwitchTaskResponse)
async def kill_specific_task(task_id: str, user: User = Depends(get_current_user)):
    """Kill a specific task by its ID."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    result = await monitor.kill_task(task_id)
    if not result.get("killed"):
        raise HTTPException(status_code=404, detail=result.get("error", "Task not found"))
    logger.warning("Task %s killed by user %s", task_id, user.id)
    return KillSwitchTaskResponse(**result)


@router.get("/kill-switch/status", response_model=KillSwitchStatusResponse)
async def get_kill_switch_status(user: User = Depends(get_current_user)):
    """Check whether the kill switch is currently active."""
    from app.orchestration.execution_monitor import get_execution_monitor

    monitor = get_execution_monitor()
    return KillSwitchStatusResponse(
        active=monitor.is_killed,
        active_executions=monitor.active_count,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _trace_to_response(trace, include_steps: bool = False) -> TraceResponse:
    d = trace.to_dict()
    steps = []
    if include_steps:
        steps = [TraceStepResponse(**s) for s in d.get("steps", [])]
    return TraceResponse(
        trace_id=d["trace_id"],
        task_id=d.get("task_id"),
        agent_id=d.get("agent_id"),
        started_at=d["started_at"],
        finished_at=d.get("finished_at"),
        outcome=d.get("outcome"),
        summary=d.get("summary", ""),
        total_decisions=d.get("total_decisions", 0),
        total_fallbacks=d.get("total_fallbacks", 0),
        duration_ms=d.get("duration_ms"),
        steps=steps,
    )


def _msg_to_response(msg) -> AgentMessageResponse:
    d = msg.to_dict()
    return AgentMessageResponse(**d)
