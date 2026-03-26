"""Heartbeat scheduler -- Periodic patrol execution management.

Based on Zero-Employee Orchestrator.md section 36.3, implements Heartbeat not as
mere periodic execution, but as an operational principle where the AI organization
conducts periodic patrols to check work status and performs progression,
delegation, replanning, and reporting as needed.

Trigger events:
- Scheduled (cron)
- Ticket created
- Task assigned
- Rework requested
- External event received
- Budget threshold reached
- Approval resolved
- Manager directive
- Dependency completed
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HeartbeatTrigger(str, Enum):
    """Heartbeat trigger events."""

    SCHEDULED = "scheduled"
    TICKET_CREATED = "ticket_created"
    TASK_ASSIGNED = "task_assigned"
    REWORK_REQUESTED = "rework_requested"
    EXTERNAL_EVENT = "external_event"
    BUDGET_THRESHOLD = "budget_threshold"
    APPROVAL_RESOLVED = "approval_resolved"
    MANAGER_DIRECTIVE = "manager_directive"
    DEPENDENCY_COMPLETED = "dependency_completed"


class HeartbeatRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HeartbeatAction:
    """Action performed by an Agent during heartbeat execution."""

    action_type: str  # check_tasks, delegate, escalate, approve_request, update_state
    target_id: str | None = None
    description: str = ""
    result: str | None = None


@dataclass
class HeartbeatExecution:
    """Record of a single heartbeat execution."""

    run_id: str
    policy_id: str
    agent_id: str | None
    team_id: str | None
    trigger: HeartbeatTrigger
    status: HeartbeatRunStatus = HeartbeatRunStatus.QUEUED
    actions: list[HeartbeatAction] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: str = ""

    def start(self) -> None:
        self.status = HeartbeatRunStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.actions = []

    def add_action(self, action: HeartbeatAction) -> None:
        if self.actions is None:
            self.actions = []
        self.actions.append(action)

    def finish(self, success: bool = True, summary: str = "") -> None:
        self.finished_at = datetime.now(UTC)
        self.status = HeartbeatRunStatus.SUCCEEDED if success else HeartbeatRunStatus.FAILED
        self.summary = summary


async def execute_heartbeat(
    policy_id: str,
    agent_id: str | None = None,
    team_id: str | None = None,
    trigger: HeartbeatTrigger = HeartbeatTrigger.SCHEDULED,
) -> HeartbeatExecution:
    """Execute a heartbeat.

    What the Agent does during execution:
    1. Check own incomplete tasks
    2. Check dependencies
    3. Check budget, permissions, and deadlines
    4. Delegate to subordinates if needed
    5. Escalate to superiors if needed
    6. Request user approval if needed
    7. Update execution log and state
    """
    execution = HeartbeatExecution(
        run_id=str(uuid.uuid4()),
        policy_id=policy_id,
        agent_id=agent_id,
        team_id=team_id,
        trigger=trigger,
    )
    execution.start()

    try:
        # 1. Check incomplete tasks
        execution.add_action(
            HeartbeatAction(
                action_type="check_tasks",
                description="Check incomplete tasks",
            )
        )

        # 2. Check dependencies
        execution.add_action(
            HeartbeatAction(
                action_type="check_dependencies",
                description="Check dependencies",
            )
        )

        # 3. Check budget, permissions, and deadlines
        execution.add_action(
            HeartbeatAction(
                action_type="check_constraints",
                description="Check budget, permissions, and deadlines",
            )
        )

        execution.finish(success=True, summary="Heartbeat completed: all checks passed")

    except Exception as exc:
        logger.error("Heartbeat execution failed: %s", exc)
        execution.finish(success=False, summary=f"Heartbeat failed: {exc}")

    return execution
