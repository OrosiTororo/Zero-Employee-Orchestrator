"""LLM Gateway via LiteLLM - Multi-provider support.

Supports OpenRouter, OpenAI, Anthropic, Google (Gemini), Azure,
local models (Ollama / LM Studio), and any OpenAI-compatible API.

Note on subscriptions vs API keys
----------------------------------
Consumer subscription plans (ChatGPT Plus, Gemini Advanced, Claude Pro …) are
web/app services and do **not** grant programmatic API access.  API access is a
separate paid product billed per token.

To use this system without spending money you have two options:
  1. **Ollama** – run open-weight LLMs locally (Llama 3, Mistral, etc.).
     Set OLLAMA_BASE_URL and choose ``ExecutionMode.FREE``.
  2. **Google Gemini free tier** – Google AI Studio provides a free API key
     with generous rate limits.  Set GEMINI_API_KEY.
"""

import logging
import os
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


# Model catalog with recommendations per mode.
# Prefix convention:
#   gemini/  → direct Gemini API (GEMINI_API_KEY)
#   google/  → Gemini via OpenRouter (OPENROUTER_API_KEY)
#   openai/  → OpenAI direct or via OpenRouter
#   ollama/  → local Ollama instance (no key required)
MODEL_CATALOG: dict[ExecutionMode, list[str]] = {
    ExecutionMode.QUALITY: [
        "anthropic/claude-opus-4-6",
        "openai/gpt-4o",
        "gemini/gemini-2.0-flash",     # direct Gemini API
        "google/gemini-2.0-flash",     # Gemini via OpenRouter
    ],
    ExecutionMode.SPEED: [
        "anthropic/claude-haiku-4-5-20251001",
        "openai/gpt-4o-mini",
        "gemini/gemini-1.5-flash",     # direct Gemini API
        "google/gemini-2.0-flash",     # Gemini via OpenRouter
    ],
    ExecutionMode.COST: [
        "anthropic/claude-haiku-4-5-20251001",
        "openai/gpt-4o-mini",
        "gemini/gemini-1.5-flash",     # direct Gemini API
        "deepseek/deepseek-chat",
    ],
    ExecutionMode.FREE: [
        "gemini/gemini-1.5-flash",   # Google AI Studio free-tier quota
        "ollama/llama3.2",
        "ollama/mistral",
        "ollama/phi3",
    ],
}


class LLMGateway:
    """Unified LLM gateway using LiteLLM for multi-provider support."""

    def __init__(self) -> None:
        self._providers: dict[str, dict] = {}
        self._default_mode = ExecutionMode.QUALITY

    # ------------------------------------------------------------------
    # Provider configuration
    # ------------------------------------------------------------------

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

    def configure_from_env(self) -> None:
        """Auto-configure providers from environment variables.

        Reads the standard LLM API key variables and registers providers
        automatically.  Call this once at application startup.
        """
        # OpenRouter — recommended multi-provider gateway
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        if openrouter_key:
            self.configure_provider(
                "openrouter",
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                models=[
                    "openai/gpt-4o",
                    "openai/gpt-4o-mini",
                    "anthropic/claude-opus-4-6",
                    "anthropic/claude-haiku-4-5-20251001",
                    "google/gemini-2.0-flash",
                    "deepseek/deepseek-chat",
                ],
            )
            logger.info("Configured provider: openrouter")

        # OpenAI direct
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key:
            self.configure_provider(
                "openai",
                api_key=openai_key,
                models=["openai/gpt-4o", "openai/gpt-4o-mini"],
            )
            logger.info("Configured provider: openai")

        # Anthropic direct
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            self.configure_provider(
                "anthropic",
                api_key=anthropic_key,
                models=[
                    "anthropic/claude-opus-4-6",
                    "anthropic/claude-haiku-4-5-20251001",
                ],
            )
            logger.info("Configured provider: anthropic")

        # Google Gemini (free tier available via Google AI Studio)
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if gemini_key:
            self.configure_provider(
                "gemini",
                api_key=gemini_key,
                models=[
                    "gemini/gemini-2.0-flash",
                    "gemini/gemini-1.5-pro",
                    "gemini/gemini-1.5-flash",
                ],
            )
            logger.info("Configured provider: gemini")

        # Ollama — local models, no API key required
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.configure_provider(
            "ollama",
            api_key=None,
            base_url=ollama_url,
            models=["ollama/llama3.2", "ollama/mistral", "ollama/phi3"],
        )
        # Ollama is always registered; actual availability depends on runtime

    def _configured_models(self) -> list[str]:
        """Return all models registered across configured providers."""
        models: list[str] = []
        for cfg in self._providers.values():
            models.extend(cfg.get("models") or [])
        return models

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------

    def select_model(self, mode: ExecutionMode) -> str:
        """Select best model for the given execution mode.

        Prefers models that belong to a configured provider so the caller
        is less likely to encounter authentication errors.
        """
        candidates = MODEL_CATALOG.get(mode, MODEL_CATALOG[ExecutionMode.QUALITY])
        available = set(self._configured_models())

        if available:
            for candidate in candidates:
                if candidate in available:
                    return candidate

        # Fall back to first candidate regardless of configuration
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
        # Rough estimates per 1K tokens (0.0 means free / no billing)
        costs = {
            "anthropic/claude-opus-4-6": (0.015, 0.075),
            "anthropic/claude-sonnet-4-6": (0.003, 0.015),
            "anthropic/claude-haiku-4-5-20251001": (0.001, 0.005),
            "openai/gpt-4o": (0.005, 0.015),
            "openai/gpt-4o-mini": (0.00015, 0.0006),
            "gemini/gemini-2.0-flash": (0.0001, 0.0004),
            # gemini-1.5-flash: free up to the Google AI Studio quota limit,
            # billed at standard rates after quota exhaustion.
            "gemini/gemini-1.5-flash": (0.0, 0.0),
            "gemini/gemini-1.5-pro": (0.00125, 0.005),
            "deepseek/deepseek-chat": (0.00014, 0.00028),
            # Local models are always free
            "ollama/llama3.2": (0.0, 0.0),
            "ollama/mistral": (0.0, 0.0),
            "ollama/phi3": (0.0, 0.0),
        }
        input_rate, output_rate = costs.get(model, (0.001, 0.002))
        return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


# Global gateway instance — auto-configured from environment variables
llm_gateway = LLMGateway()
llm_gateway.configure_from_env()
