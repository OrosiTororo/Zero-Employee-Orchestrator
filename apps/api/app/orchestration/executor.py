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

    async def critique_output(
        self,
        draft_content: str,
        node_title: str,
        execution_mode: ExecutionMode = ExecutionMode.QUALITY,
    ) -> dict:
        """Critique pattern (inspired by Copilot Cowork): use a second model call
        to review the draft output for errors, omissions, and improvements.

        Returns dict with keys: approved (bool), issues (list[str]), revised (str|None).
        """
        critique_prompt = (
            "You are a strict quality reviewer. Review this draft output and identify "
            "any errors, omissions, logical flaws, or improvements needed.\n\n"
            f"Task: {node_title}\n\n"
            f"Draft output:\n{draft_content}\n\n"
            "Respond in JSON: "
            '{"approved": true/false, "issues": ["issue1", ...], '
            '"revised": "improved version if not approved, null if approved"}'
        )
        try:
            response = await self._gateway.complete(
                CompletionRequest(
                    messages=[{"role": "user", "content": critique_prompt}],
                    mode=execution_mode,
                    temperature=0.2,
                    max_tokens=2048,
                )
            )
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(content)
        except Exception as exc:
            logger.debug("Critique parsing failed, approving draft: %s", exc)
            return {"approved": True, "issues": [], "revised": None}

    async def execute_node(
        self,
        node: TaskNode,
        context: str = "",
        execution_mode: ExecutionMode = ExecutionMode.QUALITY,
        enable_critique: bool = False,
    ) -> ExecutionResult:
        """Execute a single DAG node by calling the LLM Gateway.

        When enable_critique=True, applies the Critique pattern: a second model
        call reviews the draft and may revise it (inspired by Copilot Cowork).
        """
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

            final_content = response.content

            # Critique pattern: review draft with a second pass
            if enable_critique and final_content and not final_content.startswith("Error:"):
                critique = await self.critique_output(final_content, node.title, execution_mode)
                if not critique.get("approved", True) and critique.get("revised"):
                    logger.info(
                        "Critique revised node %s: %d issues found",
                        node.id,
                        len(critique.get("issues", [])),
                    )
                    final_content = critique["revised"]

            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)

            # Judge the output
            judge_result = self._rule_judge.evaluate(
                {"content": final_content},
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
                content=final_content,
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
        enable_critique: bool = False,
        checkpoint_store: dict | None = None,
    ) -> PlanExecutionResult:
        """Execute the entire DAG plan, node by node, respecting dependencies.

        Args:
            enable_critique: When True, each node output is reviewed by a second
                model call (Critique pattern, inspired by Copilot Cowork).
            checkpoint_store: Optional dict to persist execution state after each
                node completes (LangGraph-inspired checkpointing). Keys written:
                ``completed_nodes``, ``accumulated_context``, ``node_results``.
                Enables pause/resume by restoring from a previous checkpoint.
        """
        result = PlanExecutionResult(plan_id=dag.plan_id, status="running")

        # Restore from checkpoint if available (LangGraph-style resume)
        accumulated_context = ""
        if checkpoint_store and checkpoint_store.get("accumulated_context"):
            accumulated_context = checkpoint_store["accumulated_context"]
            for nr_data in checkpoint_store.get("node_results", []):
                result.node_results.append(ExecutionResult(**nr_data))
            logger.info("Resumed plan %s from checkpoint", dag.plan_id)

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
                critique: bool = enable_critique,
            ) -> tuple[TaskNode, ExecutionResult]:
                nr = await self.execute_node(
                    n, context=ctx, execution_mode=mode, enable_critique=critique
                )
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

                    # Checkpoint after each successful node (LangGraph-inspired)
                    if checkpoint_store is not None:
                        checkpoint_store["accumulated_context"] = accumulated_context
                        checkpoint_store["completed_nodes"] = [
                            n.id for n in dag.nodes if n.status == TaskNodeStatus.SUCCEEDED
                        ]
                        checkpoint_store["node_results"] = [
                            {
                                "node_id": r.node_id,
                                "success": r.success,
                                "content": r.content,
                                "model_used": r.model_used,
                                "tokens_input": r.tokens_input,
                                "tokens_output": r.tokens_output,
                                "cost_usd": r.cost_usd,
                                "judge_score": r.judge_score,
                                "judge_verdict": r.judge_verdict,
                                "duration_ms": r.duration_ms,
                            }
                            for r in result.node_results
                            if r.success
                        ]
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
