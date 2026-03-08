"""LLM Executor - Executes tasks by calling LLM providers.

Uses the Provider Interface Layer to send prompts and receive responses.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    output: str = ""
    error_code: str | None = None
    error_message: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    artifacts: list[dict] | None = None


class LLMExecutor:
    """Execute tasks by calling LLM providers."""

    async def execute(
        self,
        task_description: str,
        context: dict | None = None,
        model: str | None = None,
    ) -> ExecutionResult:
        """Execute a task using LLM completion."""
        try:
            # In production, use the LLM Gateway
            # from app.providers.gateway import llm_gateway, CompletionRequest
            logger.info(f"Executing LLM task: {task_description[:100]}...")

            # Placeholder - would call llm_gateway.complete()
            return ExecutionResult(
                success=True,
                output="[Task execution pending LLM configuration]",
            )
        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            return ExecutionResult(
                success=False,
                error_code="llm_error",
                error_message=str(e),
            )
