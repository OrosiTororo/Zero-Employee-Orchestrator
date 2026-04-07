"""Task Executor — Core orchestration engine.

Connects all layers: Interview → DAG → LLM → Judge → Result.
This is the central execution engine that drives end-to-end task completion.

Flow:
  1. Generate execution plan (DAG) from ticket spec via LLM
  2. Execute each DAG node by calling the LLM Gateway
  3. Verify results via Judge layer
  4. Record experience for future improvement
  5. Handle failures via Re-Propose layer
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.orchestration.dag import (
    ExecutionDAG,
    TaskNode,
    TaskNodeStatus,
    rebuild_dag_after_failure,
)
from app.orchestration.judge import CrossModelJudge, JudgeVerdict, RuleBasedJudge
from app.orchestration.repropose import classify_failure, generate_reproposal
from app.providers.gateway import CompletionRequest, ExecutionMode, LLMGateway

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a single node execution."""

    node_id: str
    success: bool
    content: str = ""
    model_used: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    error: str | None = None
    judge_score: float = 1.0
    judge_verdict: str = "pass"
    duration_ms: int = 0


@dataclass
class PlanExecutionResult:
    """Result of executing the entire plan."""

    plan_id: str
    status: str = "pending"  # pending | running | succeeded | failed | partial
    node_results: list[ExecutionResult] = field(default_factory=list)
    final_output: str = ""
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    total_duration_ms: int = 0
    failure_reason: str | None = None


class TaskExecutor:
    """Central execution engine that orchestrates the full task lifecycle."""

    MAX_RETRIES = 2
    JUDGE_PASS_THRESHOLD = 0.6

    def __init__(self, gateway: LLMGateway | None = None) -> None:
        self._gateway = gateway or LLMGateway()
        self._rule_judge = RuleBasedJudge()
        self._cross_judge = CrossModelJudge()
        # Add default quality rules
        self._rule_judge.add_rule(
            "non_empty",
            lambda output, ctx: bool(output.get("content", "").strip()),
            severity="error",
        )
        self._rule_judge.add_rule(
            "minimum_length",
            lambda output, ctx: len(output.get("content", "")) >= 20,
            severity="warning",
        )
        self._rule_judge.add_rule(
            "no_error_response",
            lambda output, ctx: not output.get("content", "").startswith("Error:"),
            severity="error",
        )

    async def generate_plan(
        self,
        ticket_title: str,
        spec_text: str,
        execution_mode: ExecutionMode = ExecutionMode.QUALITY,
    ) -> ExecutionDAG:
        """Generate an execution plan (DAG) from a ticket spec using LLM."""
        plan_id = str(uuid.uuid4())

        prompt = (
            "You are a task planner. Decompose this task into sequential steps.\n\n"
            f"Task: {ticket_title}\n\n"
            f"Specification:\n{spec_text}\n\n"
            "Return a JSON array of steps. Each step has:\n"
            '- "id": unique string (e.g. "step_1")\n'
            '- "title": short description of what to do\n'
            '- "depends_on": array of step IDs this depends on (empty for first steps)\n'
            '- "prompt": the detailed instruction for the AI to execute this step\n'
            '- "estimated_minutes": estimated time in minutes\n\n'
            "Return ONLY the JSON array, no other text."
        )

        response = await self._gateway.complete(
            CompletionRequest(
                messages=[{"role": "user", "content": prompt}],
                mode=execution_mode,
                temperature=0.3,
                max_tokens=2048,
            )
        )

        # Parse LLM response into DAG nodes
        dag = ExecutionDAG(plan_id=plan_id)
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            steps = json.loads(content)

            for step in steps:
                node = TaskNode(
                    id=step.get("id", f"step_{uuid.uuid4().hex[:8]}"),
                    title=step.get("title", "Untitled step"),
                    depends_on=step.get("depends_on", []),
                    estimated_minutes=step.get("estimated_minutes", 5),
                )
                # Store the execution prompt as provider_override metadata
                node.provider_override = {"prompt": step.get("prompt", step.get("title", ""))}
                dag.add_node(node)

        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse plan from LLM, creating single-step plan: %s", exc)
            # Fallback: single-step plan
            dag.add_node(
                TaskNode(
                    id="step_1",
                    title=ticket_title,
                    provider_override={"prompt": spec_text or ticket_title},
                    estimated_minutes=10,
                )
            )

        logger.info("Generated plan %s with %d nodes", plan_id, len(dag.nodes))
        return dag

    async def execute_node(
        self,
        node: TaskNode,
        context: str = "",
        execution_mode: ExecutionMode = ExecutionMode.QUALITY,
    ) -> ExecutionResult:
        """Execute a single DAG node by calling the LLM Gateway."""
        start = datetime.now(UTC)
        node.status = TaskNodeStatus.RUNNING

        prompt = (node.provider_override or {}).get("prompt", node.title)
        messages = []
        if context:
            messages.append({"role": "system", "content": f"Previous context:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._gateway.complete(
                CompletionRequest(
                    messages=messages,
                    mode=execution_mode,
                    temperature=0.7,
                    max_tokens=4096,
                )
            )

            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)

            # Judge the output
            judge_result = self._rule_judge.evaluate(
                {"content": response.content},
                {"node_title": node.title, "verification": node.verification_criteria},
            )

            node.status = (
                TaskNodeStatus.SUCCEEDED
                if judge_result.score >= self.JUDGE_PASS_THRESHOLD
                and judge_result.verdict != JudgeVerdict.FAIL
                else TaskNodeStatus.FAILED
            )

            return ExecutionResult(
                node_id=node.id,
                success=node.status == TaskNodeStatus.SUCCEEDED,
                content=response.content,
                model_used=response.model_used,
                tokens_input=response.tokens_input,
                tokens_output=response.tokens_output,
                cost_usd=response.cost_usd,
                judge_score=judge_result.score,
                judge_verdict=judge_result.verdict.value,
                duration_ms=elapsed,
            )

        except Exception as exc:
            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
            node.status = TaskNodeStatus.FAILED
            logger.error("Node %s execution failed: %s", node.id, exc)
            return ExecutionResult(
                node_id=node.id,
                success=False,
                error=str(exc),
                duration_ms=elapsed,
            )

    async def execute_plan(
        self,
        dag: ExecutionDAG,
        execution_mode: ExecutionMode = ExecutionMode.QUALITY,
        on_progress: asyncio.coroutine | None = None,
    ) -> PlanExecutionResult:
        """Execute the entire DAG plan, node by node, respecting dependencies."""
        result = PlanExecutionResult(plan_id=dag.plan_id, status="running")
        accumulated_context = ""

        max_iterations = len(dag.nodes) * (self.MAX_RETRIES + 1)
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            ready_nodes = dag.get_ready_nodes()

            if not ready_nodes:
                # Check if all nodes are done
                all_done = all(
                    n.status in (TaskNodeStatus.SUCCEEDED, TaskNodeStatus.SKIPPED)
                    for n in dag.nodes
                )
                if all_done:
                    result.status = "succeeded"
                    break

                has_failed = any(n.status == TaskNodeStatus.FAILED for n in dag.nodes)
                if has_failed:
                    result.status = "failed"
                    result.failure_reason = "One or more tasks failed"
                    break

                # Deadlock — no ready nodes and not all done
                result.status = "failed"
                result.failure_reason = "Execution deadlock: no nodes ready"
                break

            # Separate blocked nodes from executable ones
            executable = []
            for node in ready_nodes:
                if node.requires_approval:
                    logger.info("Node %s requires approval — skipping for now", node.id)
                    node.status = TaskNodeStatus.BLOCKED
                else:
                    executable.append(node)

            if not executable:
                continue

            # Execute independent nodes in parallel via asyncio.gather
            async def _run_node(
                n: TaskNode,
                ctx: str = accumulated_context,
                mode: ExecutionMode = execution_mode,
            ) -> tuple[TaskNode, ExecutionResult]:
                nr = await self.execute_node(n, context=ctx, execution_mode=mode)
                return n, nr

            node_pairs = await asyncio.gather(
                *[_run_node(n) for n in executable],
                return_exceptions=True,
            )

            for pair in node_pairs:
                if isinstance(pair, BaseException):
                    logger.error("Unexpected error during parallel execution: %s", pair)
                    continue
                node, node_result = pair
                result.node_results.append(node_result)
                result.total_cost_usd += node_result.cost_usd
                result.total_tokens += node_result.tokens_input + node_result.tokens_output
                result.total_duration_ms += node_result.duration_ms

                if node_result.success:
                    accumulated_context += f"\n\n--- {node.title} ---\n{node_result.content}"
                    dag.mark_completed(node.id, success=True)
                else:
                    retry_count = sum(
                        1 for r in result.node_results if r.node_id == node.id and not r.success
                    )
                    if retry_count <= self.MAX_RETRIES:
                        logger.info(
                            "Retrying node %s (attempt %d/%d)",
                            node.id,
                            retry_count,
                            self.MAX_RETRIES,
                        )
                        rebuild_dag_after_failure(dag, node.id, strategy="retry")
                    else:
                        logger.warning("Node %s failed after %d retries", node.id, self.MAX_RETRIES)
                        dag.mark_completed(node.id, success=False)

                        rework_reason = classify_failure(
                            None, node_result.error or "Quality check failed"
                        )
                        reproposal = generate_reproposal(dag.to_dict(), [rework_reason])
                        logger.info(
                            "Reproposal generated: %s (confidence=%.2f)",
                            reproposal.new_plan_summary,
                            reproposal.confidence_score,
                        )

                if on_progress:
                    try:
                        await on_progress(node.id, node.status.value, node_result)
                    except Exception:
                        pass

        # Build final output from all successful node results
        successful_results = [r for r in result.node_results if r.success]
        if successful_results:
            result.final_output = successful_results[-1].content

        if result.status == "running":
            result.status = "succeeded" if successful_results else "failed"

        # Record experience for future improvement
        failed_results = [r for r in result.node_results if not r.success]
        if failed_results:
            try:
                from app.core.database import get_session
                from app.orchestration.experience_memory import PersistentExperienceMemory

                async for db in get_session():
                    # Use a placeholder company_id for system-level memory
                    memory = PersistentExperienceMemory(db, "00000000-0000-0000-0000-000000000000")
                    for fr in failed_results:
                        reason = classify_failure(None, fr.error or "Quality check failed")
                        await memory.add_failure(
                            category=reason.category,
                            subcategory=reason.severity,
                            description=f"Node '{fr.node_id}' failed: {fr.error or 'judge rejected'}",
                            prevention_strategy=f"Consider model={fr.model_used}, "
                            f"judge_score={fr.judge_score}",
                        )
                    break
            except Exception as exc:
                logger.debug("Experience memory recording skipped: %s", exc)

        logger.info(
            "Plan %s completed: status=%s, nodes=%d, cost=$%.4f",
            dag.plan_id,
            result.status,
            len(result.node_results),
            result.total_cost_usd,
        )
        return result


# Module-level singleton
_executor: TaskExecutor | None = None


def get_executor() -> TaskExecutor:
    """Get or create the module-level TaskExecutor singleton."""
    global _executor
    if _executor is None:
        _executor = TaskExecutor()
    return _executor
