"""Task Runner - Picks up ready tasks from the queue and executes them.

Responsibilities:
- Poll for tasks in 'ready' status
- Execute tasks via the appropriate executor
- Handle retries and self-healing on failure
- Record execution results and update state
"""

import asyncio
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Allow importing from the api app
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))

MAX_RETRIES = 3


class TaskRunner:
    """Continuously picks up and executes ready tasks."""

    def __init__(self, poll_interval: float = 5.0) -> None:
        self.poll_interval = poll_interval
        self._llm_executor = None
        self._sandbox_executor = None

    def _get_llm_executor(self):
        if self._llm_executor is None:
            from app.executors.llm_executor import LLMExecutor
            self._llm_executor = LLMExecutor()
        return self._llm_executor

    def _get_sandbox_executor(self):
        if self._sandbox_executor is None:
            from app.executors.sandbox_executor import SandboxExecutor
            self._sandbox_executor = SandboxExecutor()
        return self._sandbox_executor

    async def run(self, shutdown_event: asyncio.Event) -> None:
        logger.info("TaskRunner started")
        while not shutdown_event.is_set():
            try:
                await self._process_ready_tasks()
            except Exception as e:
                logger.error(f"TaskRunner error: {e}")
            await asyncio.sleep(self.poll_interval)
        logger.info("TaskRunner stopped")

    async def _process_ready_tasks(self) -> None:
        """Find and execute ready tasks."""
        try:
            from app.core.database import async_session_factory
            from app.models.task import Task, TaskRun
            from app.models.audit import AuditLog
            from sqlalchemy import select
        except ImportError:
            return

        async with async_session_factory() as db:
            # Query tasks with status='ready'
            result = await db.execute(
                select(Task).where(Task.status == "ready").limit(10)
            )
            ready_tasks = result.scalars().all()

            for task in ready_tasks:
                await self._execute_single_task(db, task)

    async def _execute_single_task(self, db, task) -> None:
        """Execute a single task through the full pipeline."""
        from app.models.task import TaskRun
        from app.models.audit import AuditLog
        from app.core.security import generate_uuid
        from sqlalchemy import select

        task_id_str = str(task.id)
        logger.info(f"Processing task {task_id_str}: {task.title}")

        # 1. Mark as running
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)

        # Count existing runs
        result = await db.execute(
            select(TaskRun).where(TaskRun.task_id == task.id)
        )
        existing_runs = len(result.scalars().all())

        run = TaskRun(
            id=generate_uuid(),
            company_id=task.company_id,
            task_id=task.id,
            run_no=existing_runs + 1,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)

        audit_start = AuditLog(
            id=generate_uuid(),
            company_id=task.company_id,
            actor_type="system",
            event_type="task.started",
            target_type="task",
            target_id=task.id,
            task_id=task.id,
            details_json={"run_no": run.run_no},
        )
        db.add(audit_start)
        await db.commit()

        # 2. Execute based on task_type
        exec_result = await self._dispatch_execution(task)

        # 3. Judge output quality
        judge_result = self._judge_output(exec_result, task)

        # 4. Update status based on results
        if exec_result.success and judge_result.get("verdict") != "fail":
            task.status = "succeeded"
            task.completed_at = datetime.now(timezone.utc)
            run.status = "succeeded"
            run.output_snapshot_json = {
                "output": exec_result.output[:10000],
                "judge": judge_result,
                "model_used": exec_result.model_used,
                "cost_usd": exec_result.cost_usd,
            }
        else:
            # 5. Attempt self-healing on failure
            if run.run_no < MAX_RETRIES:
                task.status = "ready"  # Will be picked up again
                run.status = "failed"
                run.error_code = exec_result.error_code or "judge_fail"
                run.error_message = exec_result.error_message or judge_result.get("reasons", "")
                logger.info(f"Task {task_id_str} failed, retrying (run {run.run_no}/{MAX_RETRIES})")
            else:
                task.status = "failed"
                run.status = "failed"
                run.error_code = exec_result.error_code or "max_retries"
                run.error_message = exec_result.error_message or "Max retries exceeded"
                logger.warning(f"Task {task_id_str} failed after {MAX_RETRIES} attempts")

        run.finished_at = datetime.now(timezone.utc)

        audit_end = AuditLog(
            id=generate_uuid(),
            company_id=task.company_id,
            actor_type="system",
            event_type=f"task.{task.status}",
            target_type="task",
            target_id=task.id,
            task_id=task.id,
            details_json={
                "run_no": run.run_no,
                "success": exec_result.success,
                "cost_usd": exec_result.cost_usd,
                "tokens_used": exec_result.tokens_used,
            },
        )
        db.add(audit_end)
        await db.commit()

    async def _dispatch_execution(self, task):
        """Dispatch task to appropriate executor based on task_type."""
        from app.executors.llm_executor import ExecutionResult

        task_type = task.task_type or "execution"

        if task_type in ("execution", "generation", "analysis", "translation"):
            executor = self._get_llm_executor()
            return await executor.execute(
                task_description=f"{task.title}\n\n{task.description or ''}",
                context={
                    "task_type": task_type,
                },
            )
        elif task_type == "code_execution":
            sandbox = self._get_sandbox_executor()
            result = await sandbox.execute_python(task.description or "")
            return ExecutionResult(
                success=result.success,
                output=result.stdout or result.stderr,
                error_code=None if result.success else "sandbox_error",
                error_message=result.error,
            )
        else:
            executor = self._get_llm_executor()
            return await executor.execute(
                task_description=f"[{task_type}] {task.title}\n\n{task.description or ''}",
            )

    def _judge_output(self, exec_result, task) -> dict:
        """Judge the quality of task output."""
        try:
            from app.orchestration.judge import judge_output, JudgeVerdict
            result = judge_output(
                output={"content": exec_result.output, "task_type": task.task_type},
                operations=[],
                context={"task_title": task.title},
            )
            return {
                "verdict": result.verdict.value,
                "score": result.score,
                "reasons": "; ".join(result.reasons),
                "requires_human_review": result.requires_human_review,
            }
        except ImportError:
            return {"verdict": "pass", "score": 1.0, "reasons": ""}
