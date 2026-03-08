"""Heartbeat Runner - Executes heartbeat policies on schedule.

Heartbeats are not just cron jobs - they are the operational principle
by which AI agents periodically check their responsibilities:
- Check incomplete tasks
- Verify dependencies
- Check budget/permission/deadline
- Delegate to subordinates if needed
- Escalate to superiors if needed
- Request user approval if needed
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Allow importing from the api app
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))


class HeartbeatRunner:
    """Runs heartbeat policies according to their cron schedules."""

    def __init__(self, check_interval: float = 30.0) -> None:
        self.check_interval = check_interval

    async def run(self, shutdown_event: asyncio.Event) -> None:
        logger.info("HeartbeatRunner started")
        while not shutdown_event.is_set():
            try:
                await self._check_heartbeats()
            except Exception as e:
                logger.error(f"HeartbeatRunner error: {e}")
            await asyncio.sleep(self.check_interval)
        logger.info("HeartbeatRunner stopped")

    async def _check_heartbeats(self) -> None:
        """Check which heartbeat policies are due and execute them."""
        try:
            from app.core.database import async_session_factory
            from app.models.heartbeat import HeartbeatPolicy, HeartbeatRun
            from app.models.task import Task
            from app.models.agent import Agent
            from app.models.audit import AuditLog
            from app.core.security import generate_uuid
            from sqlalchemy import select
        except ImportError:
            return

        async with async_session_factory() as db:
            # Query active heartbeat policies
            result = await db.execute(
                select(HeartbeatPolicy).where(HeartbeatPolicy.status == "active")
            )
            policies = result.scalars().all()

            now = datetime.now(timezone.utc)

            for policy in policies:
                if self._is_due(policy, now):
                    await self._execute_heartbeat(db, policy, now)

    def _is_due(self, policy, now: datetime) -> bool:
        """Check if a heartbeat policy is due for execution."""
        if not hasattr(policy, "last_run_at") or policy.last_run_at is None:
            return True

        interval_seconds = getattr(policy, "interval_seconds", 300) or 300
        elapsed = (now - policy.last_run_at).total_seconds()
        return elapsed >= interval_seconds

    async def _execute_heartbeat(self, db, policy, now: datetime) -> None:
        """Execute a single heartbeat cycle for a policy."""
        from app.models.heartbeat import HeartbeatRun
        from app.models.task import Task
        from app.models.agent import Agent
        from app.models.audit import AuditLog
        from app.core.security import generate_uuid
        from sqlalchemy import select

        logger.info(f"Executing heartbeat for policy {policy.id}")

        # Create HeartbeatRun record
        run = HeartbeatRun(
            id=generate_uuid(),
            company_id=policy.company_id,
            policy_id=policy.id,
            status="running",
            started_at=now,
        )
        db.add(run)

        summary_items = []

        try:
            # Find agents bound to this heartbeat policy
            agents_result = await db.execute(
                select(Agent).where(Agent.heartbeat_policy_id == policy.id)
            )
            agents = agents_result.scalars().all()

            for agent in agents:
                agent_summary = await self._check_agent_responsibilities(
                    db, agent, policy
                )
                summary_items.append(agent_summary)

            run.status = "completed"
            run.summary_json = {"agents_checked": len(agents), "items": summary_items}

        except Exception as e:
            logger.error(f"Heartbeat execution failed: {e}")
            run.status = "failed"
            run.summary_json = {"error": str(e)}

        run.finished_at = datetime.now(timezone.utc)

        # Update policy last run
        if hasattr(policy, "last_run_at"):
            policy.last_run_at = now

        audit = AuditLog(
            id=generate_uuid(),
            company_id=policy.company_id,
            actor_type="system",
            event_type="heartbeat.executed",
            target_type="heartbeat_policy",
            target_id=policy.id,
            details_json={
                "status": run.status,
                "agents_checked": len(summary_items),
            },
        )
        db.add(audit)
        await db.commit()

    async def _check_agent_responsibilities(self, db, agent, policy) -> dict:
        """Have an agent check its incomplete tasks and responsibilities."""
        from app.models.task import Task
        from app.models.budget import CostLedger, BudgetPolicy
        from sqlalchemy import select, func

        agent_id_str = str(agent.id)
        summary = {"agent_id": agent_id_str, "agent_name": agent.name, "actions": []}

        # Check incomplete tasks
        result = await db.execute(
            select(Task).where(
                Task.assignee_agent_id == agent.id,
                Task.status.in_(["pending", "ready", "running", "blocked"]),
            )
        )
        incomplete_tasks = result.scalars().all()
        summary["incomplete_tasks"] = len(incomplete_tasks)

        # Check for blocked tasks and try to unblock
        for task in incomplete_tasks:
            if task.status == "blocked":
                summary["actions"].append({
                    "type": "blocked_task_detected",
                    "task_id": str(task.id),
                    "task_title": task.title,
                })

        # Check budget consumption
        if agent.budget_policy_id:
            budget_result = await db.execute(
                select(BudgetPolicy).where(BudgetPolicy.id == agent.budget_policy_id)
            )
            budget_policy = budget_result.scalar_one_or_none()

            if budget_policy:
                cost_result = await db.execute(
                    select(func.coalesce(func.sum(CostLedger.cost_usd), 0)).where(
                        CostLedger.scope_id == agent.id
                    )
                )
                total_cost = float(cost_result.scalar() or 0)
                limit = float(budget_policy.limit_usd or 0)

                if limit > 0:
                    usage_pct = (total_cost / limit) * 100
                    warn_threshold = float(budget_policy.warn_threshold_pct or 80)

                    if usage_pct >= warn_threshold:
                        summary["actions"].append({
                            "type": "budget_warning",
                            "usage_pct": round(usage_pct, 1),
                            "total_cost": round(total_cost, 4),
                            "limit": round(limit, 2),
                        })

        # Check for overdue tasks
        now = datetime.now(timezone.utc)
        for task in incomplete_tasks:
            if hasattr(task, "due_at") and task.due_at and task.due_at < now:
                summary["actions"].append({
                    "type": "overdue_task",
                    "task_id": str(task.id),
                    "task_title": task.title,
                })

        return summary
