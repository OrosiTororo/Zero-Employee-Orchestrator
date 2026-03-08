"""LLM Gateway via LiteLLM - Multi-provider support.

Supports OpenRouter, OpenAI, Anthropic, Google, Azure, local models (Ollama),
and any OpenAI-compatible API.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    QUALITY = "quality"
    SPEED = "speed"
    COST = "cost"
    FREE = "free"


@dataclass
class ModelInfo:
    id: str
    provider: str
    name: str
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_tokens: int = 4096
    supports_tools: bool = False
    supports_vision: bool = False


@dataclass
class CompletionRequest:
    messages: list[dict]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: list[dict] | None = None
    mode: ExecutionMode = ExecutionMode.QUALITY


@dataclass
class CompletionResponse:
    content: str
    model_used: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    tool_calls: list[dict] = field(default_factory=list)
    finish_reason: str = "stop"


# Model catalog with recommendations per mode
MODEL_CATALOG: dict[ExecutionMode, list[str]] = {
    ExecutionMode.QUALITY: [
        "anthropic/claude-opus-4-6",
        "openai/gpt-4o",
        "google/gemini-2.0-flash",
    ],
    ExecutionMode.SPEED: [
        "anthropic/claude-haiku-4-5-20251001",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash",
    ],
    ExecutionMode.COST: [
        "anthropic/claude-haiku-4-5-20251001",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-chat",
    ],
    ExecutionMode.FREE: [
        "ollama/llama3.2",
        "ollama/mistral",
    ],
}


class LLMGateway:
    """Unified LLM gateway using LiteLLM for multi-provider support."""

    def __init__(self) -> None:
        self._providers: dict[str, dict] = {}
        self._default_mode = ExecutionMode.QUALITY

    def configure_provider(
        self,
        name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        models: list[str] | None = None,
    ) -> None:
        self._providers[name] = {
            "api_key": api_key,
            "base_url": base_url,
            "models": models or [],
        }

    def select_model(self, mode: ExecutionMode) -> str:
        """Select best model for the given execution mode."""
        candidates = MODEL_CATALOG.get(mode, MODEL_CATALOG[ExecutionMode.QUALITY])
        # In production, check which models are available via configured providers
        return candidates[0] if candidates else "openai/gpt-4o-mini"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send completion request via LiteLLM."""
        model = request.model or self.select_model(request.mode)

        try:
            import litellm

            response = await litellm.acompletion(
                model=model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=request.tools,
            )

            content = response.choices[0].message.content or ""
            usage = response.usage
            tool_calls = []

            if response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "function": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                    for tc in response.choices[0].message.tool_calls
                ]

            return CompletionResponse(
                content=content,
                model_used=model,
                provider=model.split("/")[0] if "/" in model else "unknown",
                tokens_input=usage.prompt_tokens if usage else 0,
                tokens_output=usage.completion_tokens if usage else 0,
                cost_usd=0.0,  # LiteLLM can compute this
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason or "stop",
            )

        except ImportError:
            logger.warning("litellm not available, returning mock response")
            return CompletionResponse(
                content="[Mock response - LiteLLM not configured]",
                model_used=model,
                provider="mock",
            )
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            return CompletionResponse(
                content=f"Error: {e}",
                model_used=model,
                provider="error",
                finish_reason="error",
            )

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost for a given model and token count."""
        # Rough estimates per 1K tokens
        costs = {
            "anthropic/claude-opus-4-6": (0.015, 0.075),
            "anthropic/claude-sonnet-4-6": (0.003, 0.015),
            "anthropic/claude-haiku-4-5-20251001": (0.001, 0.005),
            "openai/gpt-4o": (0.005, 0.015),
            "openai/gpt-4o-mini": (0.00015, 0.0006),
        }
        input_rate, output_rate = costs.get(model, (0.001, 0.002))
        return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


# Global gateway instance
llm_gateway = LLMGateway()
