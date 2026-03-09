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
    SUBSCRIPTION = "subscription"  # no API key — uses g4f free/subscription providers


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
#   gemini/       → direct Gemini API (GEMINI_API_KEY)
#   google/       → Gemini via OpenRouter (OPENROUTER_API_KEY)
#   openai/       → OpenAI direct or via OpenRouter
#   ollama/       → local Ollama instance (no key required)
#   g4f/<Name>    → free/subscription provider via gpt4free (no API key)
MODEL_CATALOG: dict[ExecutionMode, list[str]] = {
    ExecutionMode.QUALITY: [
        "anthropic/claude-opus-4-6",
        "openai/gpt-5.4",
        "gemini/gemini-2.5-pro",       # direct Gemini API (stable)
        "google/gemini-2.5-pro",       # Gemini via OpenRouter
    ],
    ExecutionMode.SPEED: [
        "anthropic/claude-haiku-4-5-20251001",
        "openai/gpt-5-mini",
        "gemini/gemini-2.5-flash",     # direct Gemini API
        "google/gemini-2.5-flash",     # Gemini via OpenRouter
    ],
    ExecutionMode.COST: [
        "anthropic/claude-haiku-4-5-20251001",
        "openai/gpt-5-mini",
        "gemini/gemini-2.5-flash-lite", # direct Gemini API
        "deepseek/deepseek-chat",
    ],
    ExecutionMode.FREE: [
        "gemini/gemini-2.5-flash",   # Google AI Studio free-tier quota
        "g4f/GeminiPro",             # Gemini 2.5 Flash via g4f (no API key)
        "g4f/Copilot",               # Microsoft Copilot via g4f (no API key)
        "ollama/llama3.2",
        "ollama/mistral",
        "ollama/phi3",
    ],
    # SUBSCRIPTION mode: works without any paid API key.
    # Free g4f providers need no account at all.
    # Authenticated g4f providers (g4f/Gemini) use a Google session cookie.
    ExecutionMode.SUBSCRIPTION: [
        "g4f/GeminiPro",             # Gemini 2.5 Flash — free, no account
        "g4f/Copilot",               # Microsoft Copilot — free, no account
        "g4f/OpenaiChat",            # ChatGPT web — free tier, no account
        "g4f/Claude",                # Claude via free relay, no account
        "g4f/Gemini",                # Google Gemini with Google account
        "g4f/DeepInfra",             # Llama 3.1 70B via DeepInfra, no account
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
                    "openai/gpt-5.4",
                    "openai/gpt-5-mini",
                    "anthropic/claude-opus-4-6",
                    "anthropic/claude-sonnet-4-6",
                    "anthropic/claude-haiku-4-5-20251001",
                    "google/gemini-2.5-pro",
                    "google/gemini-2.5-flash",
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
                models=["openai/gpt-5.4", "openai/gpt-5-mini"],
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
                    "anthropic/claude-sonnet-4-6",
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
                    "gemini/gemini-2.5-pro",
                    "gemini/gemini-2.5-flash",
                    "gemini/gemini-2.5-flash-lite",
                ],
            )
            logger.info("Configured provider: gemini")

        # Ollama — local models, no API key required
        # Uses enhanced OllamaProvider for direct HTTP, model discovery, etc.
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._ollama_url = ollama_url
        self.configure_provider(
            "ollama",
            api_key=None,
            base_url=ollama_url,
            models=["ollama/llama3.2", "ollama/mistral", "ollama/phi3"],
        )
        # Ollama is always registered; actual availability depends on runtime
        # Dynamic model discovery happens asynchronously via discover_ollama_models()

        # g4f — subscription / no-API-key mode
        # Enabled by default; set USE_G4F=false to disable
        use_g4f = os.environ.get("USE_G4F", "true").lower() not in ("false", "0", "no")
        if use_g4f:
            try:
                from app.providers.g4f_provider import g4f_provider, FREE_G4F_MODELS
                if g4f_provider.available:
                    self.configure_provider(
                        "g4f",
                        api_key=None,
                        base_url=None,
                        models=list(FREE_G4F_MODELS),
                    )
                    logger.info(
                        "Configured provider: g4f (subscription/no-API-key mode) "
                        "with %d free models",
                        len(FREE_G4F_MODELS),
                    )
            except Exception as exc:
                logger.debug("g4f provider not loaded: %s", exc)

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
        For SUBSCRIPTION mode g4f models are always considered available.
        """
        candidates = MODEL_CATALOG.get(mode, MODEL_CATALOG[ExecutionMode.QUALITY])
        available = set(self._configured_models())

        if available:
            for candidate in candidates:
                # g4f models are always "available" if g4f is installed
                if candidate.startswith("g4f/") or candidate in available:
                    return candidate

        # Fall back to first candidate regardless of configuration
        return candidates[0] if candidates else "openai/gpt-5-mini"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send completion request, routing to appropriate provider."""
        model = request.model or self.select_model(request.mode)

        # ── Route ollama/* models through the enhanced direct provider ──────
        if model.startswith("ollama/"):
            return await self._complete_via_ollama_direct(model, request)

        # ── Route g4f/* models through the subscription/no-API-key provider ─
        if model.startswith("g4f/"):
            return await self._complete_via_g4f(model, request)

        # ── Standard path via LiteLLM ──────────────────────────────────────
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

    async def _complete_via_g4f(
        self, model: str, request: CompletionRequest
    ) -> CompletionResponse:
        """Route a completion request through the g4f subscription provider."""
        try:
            from app.providers.g4f_provider import g4f_provider, complete_with_fallback

            if not g4f_provider.available:
                return CompletionResponse(
                    content=(
                        "[g4f not installed. Run: pip install g4f  "
                        "or choose a different provider / execution mode]"
                    ),
                    model_used=model,
                    provider="g4f_unavailable",
                    finish_reason="error",
                )

            # SUBSCRIPTION mode: always use the fallback chain across free models
            # for maximum resilience. For other modes the caller already selected
            # a specific g4f model, so we call it directly.
            if request.mode == ExecutionMode.SUBSCRIPTION:
                from app.providers.g4f_provider import FREE_G4F_MODELS
                g4f_resp = await complete_with_fallback(
                    provider=g4f_provider,
                    models=list(FREE_G4F_MODELS),
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
            else:
                g4f_resp = await g4f_provider.complete(
                    model=model,
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

            return CompletionResponse(
                content=g4f_resp.content,
                model_used=g4f_resp.model_used,
                provider=g4f_resp.provider,
                tokens_input=g4f_resp.tokens_input,
                tokens_output=g4f_resp.tokens_output,
                cost_usd=0.0,  # g4f providers have no direct API cost
                finish_reason=g4f_resp.finish_reason,
            )
        except Exception as exc:
            logger.error("g4f completion error: %s", exc)
            return CompletionResponse(
                content=f"[g4f error: {exc}]",
                model_used=model,
                provider="g4f_error",
                finish_reason="error",
            )

    # ------------------------------------------------------------------
    # Enhanced Ollama integration
    # ------------------------------------------------------------------

    async def discover_ollama_models(self) -> list[str]:
        """Dynamically discover models available on the local Ollama instance.

        Updates the internal model catalog with actually installed models.
        """
        try:
            from app.providers.ollama_provider import ollama_provider

            models = await ollama_provider.list_models()
            if models:
                model_names = [f"ollama/{m.name}" for m in models]
                # Update the provider config with discovered models
                self._providers["ollama"]["models"] = model_names
                logger.info(
                    "Discovered %d Ollama models: %s",
                    len(model_names),
                    ", ".join(m.name for m in models),
                )
                return model_names
        except Exception as exc:
            logger.debug("Ollama model discovery failed: %s", exc)
        return []

    async def ollama_health(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            from app.providers.ollama_provider import ollama_provider
            return await ollama_provider.health_check()
        except Exception:
            return False

    async def _complete_via_ollama_direct(
        self, model: str, request: CompletionRequest
    ) -> CompletionResponse:
        """Route request directly to Ollama via enhanced provider (bypasses LiteLLM)."""
        try:
            from app.providers.ollama_provider import ollama_provider

            resp = await ollama_provider.complete(
                messages=request.messages,
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=request.tools,
            )

            return CompletionResponse(
                content=resp.content,
                model_used=f"ollama/{resp.model_used}" if not resp.model_used.startswith("ollama/") else resp.model_used,
                provider=resp.provider,
                tokens_input=resp.tokens_input,
                tokens_output=resp.tokens_output,
                cost_usd=0.0,
                tool_calls=resp.tool_calls,
                finish_reason=resp.finish_reason,
            )
        except Exception as exc:
            logger.error("Ollama direct completion failed: %s", exc)
            return CompletionResponse(
                content=f"[Ollama error: {exc}]",
                model_used=model,
                provider="ollama_error",
                finish_reason="error",
            )

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost for a given model and token count."""
        # g4f models have no direct API billing — always $0
        if model.startswith("g4f/"):
            return 0.0

        # Rough estimates per 1K tokens (0.0 means free / no billing)
        costs = {
            "anthropic/claude-opus-4-6": (0.015, 0.075),
            "anthropic/claude-sonnet-4-6": (0.003, 0.015),
            "anthropic/claude-haiku-4-5-20251001": (0.001, 0.005),
            "openai/gpt-5.4": (0.005, 0.015),
            "openai/gpt-5-mini": (0.00015, 0.0006),
            "gemini/gemini-2.5-pro": (0.00125, 0.005),
            "gemini/gemini-2.5-flash": (0.0001, 0.0004),
            # gemini-2.5-flash-lite: lowest cost Gemini model
            "gemini/gemini-2.5-flash-lite": (0.0, 0.0),
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
