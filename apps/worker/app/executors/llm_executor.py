"""LLM Executor - Executes tasks by calling LLM providers.

Uses the Provider Interface Layer to send prompts and receive responses.
"""

import logging
import sys
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Allow importing from the api app
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "api"))


@dataclass
class ExecutionResult:
    success: bool
    output: str = ""
    error_code: str | None = None
    error_message: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    artifacts: list[dict] = field(default_factory=list)
    model_used: str = ""
    provider: str = ""


class LLMExecutor:
    """Execute tasks by calling LLM providers via the gateway."""

    def __init__(self) -> None:
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            try:
                from app.providers.gateway import llm_gateway
                self._gateway = llm_gateway
            except ImportError:
                logger.warning("LLM Gateway not available")
        return self._gateway

    async def execute(
        self,
        task_description: str,
        context: dict | None = None,
        model: str | None = None,
        mode: str = "quality",
    ) -> ExecutionResult:
        """Execute a task using LLM completion."""
        gateway = self._get_gateway()

        if gateway is None:
            return ExecutionResult(
                success=False,
                error_code="gateway_unavailable",
                error_message="LLM Gateway is not configured",
            )

        try:
            from app.providers.gateway import CompletionRequest, ExecutionMode

            exec_mode = ExecutionMode(mode) if mode in [m.value for m in ExecutionMode] else ExecutionMode.QUALITY

            messages = self._build_messages(task_description, context)

            request = CompletionRequest(
                messages=messages,
                model=model,
                mode=exec_mode,
                temperature=0.7,
                max_tokens=4096,
            )

            response = await gateway.complete(request)

            cost = gateway.estimate_cost(
                response.model_used,
                response.tokens_input,
                response.tokens_output,
            )

            return ExecutionResult(
                success=response.finish_reason != "error",
                output=response.content,
                tokens_used=response.tokens_input + response.tokens_output,
                cost_usd=cost,
                model_used=response.model_used,
                provider=response.provider,
            )

        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            return ExecutionResult(
                success=False,
                error_code="llm_error",
                error_message=str(e),
            )

    def _build_messages(self, task_description: str, context: dict | None) -> list[dict]:
        """Build LLM messages from task description and context."""
        system_prompt = (
            "You are an AI agent within the Zero-Employee Orchestrator system. "
            "Execute the assigned task accurately and thoroughly. "
            "Follow all constraints and produce verifiable output."
        )

        if context:
            if context.get("spec_objective"):
                system_prompt += f"\n\nProject objective: {context['spec_objective']}"
            if context.get("constraints"):
                system_prompt += f"\n\nConstraints: {context['constraints']}"
            if context.get("acceptance_criteria"):
                system_prompt += f"\n\nAcceptance criteria: {context['acceptance_criteria']}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description},
        ]

        if context and context.get("previous_output"):
            messages.insert(1, {
                "role": "assistant",
                "content": f"Previous task output:\n{context['previous_output']}",
            })

        return messages
