"""Longrun Scheduler — 24/365 long-running execution scheduler.

A scheduler for continuous AI organization operation, managing periodic tasks,
event-driven tasks, and continuous execution tasks.

ROADMAP v1.0: 24/365 long-running execution platform.

Schedule types:
  - INTERVAL: Repeated execution at fixed intervals
  - CRON: Schedule based on cron expressions
  - EVENT_DRIVEN: Execution triggered by external events
  - CONTINUOUS: Always running (until stop instruction)
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ScheduleType(str, Enum):
    """Schedule type."""

    INTERVAL = "interval"  # Fixed interval
    CRON = "cron"  # Cron expression
    EVENT_DRIVEN = "event_driven"  # Event-driven
    CONTINUOUS = "continuous"  # Always running


class JobStatus(str, Enum):
    """Job status."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    """Scheduled job."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    interval_seconds: int | None = None
    cron_expression: str | None = None
    event_trigger: str | None = None
    handler_name: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.SCHEDULED
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schedule_type": self.schedule_type.value,
            "interval_seconds": self.interval_seconds,
            "cron_expression": self.cron_expression,
            "event_trigger": self.event_trigger,
            "handler_name": self.handler_name,
            "params": self.params,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class JobResult:
    """Job execution result."""

    job_id: str = ""
    success: bool = False
    output: Any = None
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "job_id": self.job_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": (self.finished_at.isoformat() if self.finished_at else None),
            "duration_ms": self.duration_ms,
        }


# ---------------------------------------------------------------------------
# Longrun Scheduler
# ---------------------------------------------------------------------------

_LOOP_INTERVAL_SECONDS = 1.0
_MAX_RESULTS_PER_JOB = 200


class LongrunScheduler:
    """24/365 long-running execution scheduler.

    Centrally manages job registration, scheduling, execution, and monitoring.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._results: list[JobResult] = []
        self._running: bool = False
        self._loop_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def register_handler(
        self,
        name: str,
        handler_fn: Callable[..., Any],
    ) -> None:
        """Register a job handler.

        Args:
            name: Handler name (name specified in schedule_job).
            handler_fn: Callable to execute (async supported).
        """
        self._handlers[name] = handler_fn
        logger.info("Longrun: handler '%s' registered", name)

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    def schedule_job(
        self,
        name: str,
        schedule_type: ScheduleType,
        handler_name: str,
        params: dict[str, Any] | None = None,
        *,
        interval: int | None = None,
        cron: str | None = None,
        event_trigger: str | None = None,
        description: str = "",
        max_retries: int = 3,
    ) -> ScheduledJob:
        """Schedule a job.

        Args:
            name: Job name.
            schedule_type: Schedule type.
            handler_name: Handler name to execute.
            params: Parameters to pass to the handler.
            interval: Interval in seconds (required for INTERVAL type).
            cron: Cron expression (required for CRON type).
            event_trigger: Event name (required for EVENT_DRIVEN type).
            description: Job description.
            max_retries: Maximum retry count.

        Returns:
            The scheduled job.
        """
        now = datetime.now(UTC)
        next_run: datetime | None = None

        if schedule_type == ScheduleType.INTERVAL and interval:
            from datetime import timedelta

            next_run = now + timedelta(seconds=interval)
        elif schedule_type == ScheduleType.CRON:
            next_run = self._calculate_next_cron(cron, now)
        elif schedule_type == ScheduleType.CONTINUOUS:
            next_run = now  # Start immediately

        job = ScheduledJob(
            name=name,
            description=description,
            schedule_type=schedule_type,
            interval_seconds=interval,
            cron_expression=cron,
            event_trigger=event_trigger,
            handler_name=handler_name,
            params=params or {},
            next_run=next_run,
            max_retries=max_retries,
        )
        self._jobs[job.id] = job

        logger.info(
            "Longrun: job '%s' scheduled (type=%s, handler=%s)",
            name,
            schedule_type.value,
            handler_name,
        )
        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = JobStatus.CANCELLED
        job.next_run = None
        logger.info("Longrun: job '%s' cancelled", job.name)
        return True

    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        job = self._jobs.get(job_id)
        if not job or job.status not in (JobStatus.SCHEDULED, JobStatus.RUNNING):
            return False
        job.status = JobStatus.PAUSED
        logger.info("Longrun: job '%s' paused", job.name)
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a job."""
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.PAUSED:
            return False
        job.status = JobStatus.SCHEDULED

        # Recalculate next run time
        now = datetime.now(UTC)
        if job.schedule_type == ScheduleType.INTERVAL and job.interval_seconds:
            from datetime import timedelta

            job.next_run = now + timedelta(seconds=job.interval_seconds)
        elif job.schedule_type == ScheduleType.CONTINUOUS:
            job.next_run = now

        logger.info("Longrun: job '%s' resumed", job.name)
        return True

    def get_job(self, job_id: str) -> ScheduledJob | None:
        """Get a job."""
        return self._jobs.get(job_id)

    def list_jobs(self, status_filter: JobStatus | None = None) -> list[ScheduledJob]:
        """Get list of jobs."""
        jobs = list(self._jobs.values())
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        return jobs

    def get_job_history(self, job_id: str, limit: int = 50) -> list[JobResult]:
        """Get job execution history."""
        results = [r for r in self._results if r.job_id == job_id]
        return results[-limit:]

    # ------------------------------------------------------------------
    # Scheduler start/stop
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            logger.warning("Longrun: scheduler is already running")
            return

        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        logger.info("Longrun: scheduler started")

    async def stop(self) -> None:
        """Safely stop the scheduler."""
        self._running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        self._loop_task = None
        logger.info("Longrun: scheduler stopped")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Main scheduler loop — periodically checks for jobs to execute."""
        logger.info("Longrun: scheduler loop started")
        while self._running:
            try:
                now = datetime.now(UTC)
                due_jobs = [
                    job
                    for job in self._jobs.values()
                    if (
                        job.status == JobStatus.SCHEDULED
                        and job.next_run is not None
                        and job.next_run <= now
                    )
                ]

                for job in due_jobs:
                    await self._execute_job(job)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Longrun: error in scheduler loop")

            await asyncio.sleep(_LOOP_INTERVAL_SECONDS)

        logger.info("Longrun: scheduler loop ended")

    async def _execute_job(self, job: ScheduledJob) -> JobResult:
        """Execute a single job."""
        handler = self._handlers.get(job.handler_name)
        if not handler:
            result = JobResult(
                job_id=job.id,
                success=False,
                error=f"Handler '{job.handler_name}' is not registered",
                finished_at=datetime.now(UTC),
            )
            job.status = JobStatus.FAILED
            self._results.append(result)
            return result

        job.status = JobStatus.RUNNING
        job.last_run = datetime.now(UTC)
        start_time = time.monotonic()

        result = JobResult(job_id=job.id, started_at=datetime.now(UTC))
        retries = 0

        while retries <= job.max_retries:
            try:
                if asyncio.iscoroutinefunction(handler):
                    output = await handler(**job.params)
                else:
                    output = handler(**job.params)

                result.success = True
                result.output = output
                result.error = None
                break

            except Exception as exc:
                retries += 1
                result.error = f"{exc.__class__.__name__}: {exc}"
                if retries > job.max_retries:
                    result.success = False
                    logger.error(
                        "Longrun: job '%s' failed after %d retries: %s",
                        job.name,
                        job.max_retries,
                        exc,
                    )
                else:
                    logger.warning(
                        "Longrun: job '%s' retry %d/%d: %s",
                        job.name,
                        retries,
                        job.max_retries,
                        exc,
                    )
                    await asyncio.sleep(min(2**retries, 30))

        elapsed_ms = (time.monotonic() - start_time) * 1000
        result.finished_at = datetime.now(UTC)
        result.duration_ms = round(elapsed_ms, 2)
        job.run_count += 1

        # Save results (with capacity limit)
        self._results.append(result)
        if len(self._results) > _MAX_RESULTS_PER_JOB * len(self._jobs or {"_": None}):
            self._results = self._results[-(_MAX_RESULTS_PER_JOB * max(1, len(self._jobs))) :]

        # Calculate next run time
        if result.success:
            job.status = JobStatus.SCHEDULED
            self._schedule_next_run(job)
        else:
            job.status = JobStatus.FAILED

        logger.info(
            "Longrun: job '%s' %s (%.1f ms, run #%d)",
            job.name,
            "succeeded" if result.success else "failed",
            elapsed_ms,
            job.run_count,
        )
        return result

    def _schedule_next_run(self, job: ScheduledJob) -> None:
        """Calculate and set the next run time."""
        now = datetime.now(UTC)

        if job.schedule_type == ScheduleType.INTERVAL and job.interval_seconds:
            from datetime import timedelta

            job.next_run = now + timedelta(seconds=job.interval_seconds)
        elif job.schedule_type == ScheduleType.CRON:
            job.next_run = self._calculate_next_cron(job.cron_expression, now)
        elif job.schedule_type == ScheduleType.CONTINUOUS:
            job.next_run = now  # Immediate re-execution
        elif job.schedule_type == ScheduleType.EVENT_DRIVEN:
            job.next_run = None  # Waiting for event
            job.status = JobStatus.SCHEDULED

    def _calculate_next_cron(
        self,
        cron_expression: str | None,
        now: datetime,
    ) -> datetime | None:
        """Calculate next run time from a cron expression.

        Simple implementation: supports only basic minute-level patterns.
        A full cron parser will be introduced via an external library in the future.
        """
        if not cron_expression:
            return None

        from datetime import timedelta

        parts = cron_expression.strip().split()
        if len(parts) < 5:
            logger.warning("Longrun: invalid cron expression '%s'", cron_expression)
            # Fallback: 1 hour later
            return now + timedelta(hours=1)

        minute_part = parts[0]
        hour_part = parts[1]

        try:
            # "*/N" format minute interval
            if minute_part.startswith("*/"):
                interval_min = int(minute_part[2:])
                return now + timedelta(minutes=interval_min)

            # Fixed time (HH:MM)
            if minute_part != "*" and hour_part != "*":
                target_min = int(minute_part)
                target_hour = int(hour_part)
                target = now.replace(
                    hour=target_hour,
                    minute=target_min,
                    second=0,
                    microsecond=0,
                )
                if target <= now:
                    target += timedelta(days=1)
                return target

        except (ValueError, IndexError):
            pass

        # Default: 1 hour later
        return now + timedelta(hours=1)

    # ------------------------------------------------------------------
    # Event-driven
    # ------------------------------------------------------------------

    async def trigger_event(self, event_name: str) -> list[JobResult]:
        """Fire an event and execute matching jobs.

        Args:
            event_name: Event name.

        Returns:
            List of executed job results.
        """
        triggered_jobs = [
            job
            for job in self._jobs.values()
            if (
                job.schedule_type == ScheduleType.EVENT_DRIVEN
                and job.event_trigger == event_name
                and job.status in (JobStatus.SCHEDULED, JobStatus.PAUSED)
            )
        ]

        results: list[JobResult] = []
        for job in triggered_jobs:
            if job.status == JobStatus.PAUSED:
                continue
            result = await self._execute_job(job)
            results.append(result)

        logger.info(
            "Longrun: event '%s' triggered %d jobs",
            event_name,
            len(results),
        )
        return results

    # ------------------------------------------------------------------
    # System health
    # ------------------------------------------------------------------

    def get_system_health(self) -> dict[str, Any]:
        """Return the scheduler status summary."""
        jobs_by_status: dict[str, int] = {}
        for job in self._jobs.values():
            status = job.status.value
            jobs_by_status[status] = jobs_by_status.get(status, 0) + 1

        total_results = len(self._results)
        recent_results = self._results[-100:] if self._results else []
        success_count = sum(1 for r in recent_results if r.success)
        recent_success_rate = success_count / len(recent_results) if recent_results else 0.0

        avg_duration = 0.0
        if recent_results:
            avg_duration = sum(r.duration_ms for r in recent_results) / len(recent_results)

        return {
            "running": self._running,
            "total_jobs": len(self._jobs),
            "jobs_by_status": jobs_by_status,
            "registered_handlers": list(self._handlers.keys()),
            "total_executions": total_results,
            "recent_success_rate": round(recent_success_rate, 4),
            "average_duration_ms": round(avg_duration, 2),
        }


# Global instance
longrun_scheduler = LongrunScheduler()
