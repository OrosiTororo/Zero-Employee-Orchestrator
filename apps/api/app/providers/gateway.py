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


# ---------------------------------------------------------------------------
# Model catalog — loaded from model_catalog.json via ModelRegistry.
# Falls back to hardcoded defaults only when the catalog file is missing.
# To update models, edit model_catalog.json (no code change required).
# ---------------------------------------------------------------------------


def _load_model_catalog() -> dict[ExecutionMode, list[str]]:
    """Load model catalog from the dynamic ModelRegistry."""
    try:
        from app.providers.model_registry import get_model_registry

        registry = get_model_registry()
        if registry.model_count > 0:
            return {
                ExecutionMode.QUALITY: registry.get_models_for_mode("quality"),
                ExecutionMode.SPEED: registry.get_models_for_mode("speed"),
                ExecutionMode.COST: registry.get_models_for_mode("cost"),
                ExecutionMode.FREE: registry.get_models_for_mode("free"),
                ExecutionMode.SUBSCRIPTION: registry.get_models_for_mode("subscription"),
            }
    except Exception as exc:
        logger.warning("Failed to load model catalog from registry: %s", exc)

    # Hardcoded fallback (used only when model_catalog.json is missing)
    logger.info("Using hardcoded fallback model catalog")
    return {
        ExecutionMode.QUALITY: [
            "anthropic/claude-opus",
            "openai/gpt",
            "gemini/gemini-pro",
            "google/gemini-pro",
        ],
        ExecutionMode.SPEED: [
            "anthropic/claude-haiku",
            "openai/gpt-mini",
            "gemini/gemini-flash",
            "google/gemini-flash",
        ],
        ExecutionMode.COST: [
            "anthropic/claude-haiku",
            "openai/gpt-mini",
            "gemini/gemini-flash-lite",
            "deepseek/deepseek-chat",
        ],
        ExecutionMode.FREE: [
            "gemini/gemini-flash",
            "g4f/GeminiPro",
            "g4f/Copilot",
            "ollama/llama",
            "ollama/mistral",
            "ollama/phi",
        ],
        ExecutionMode.SUBSCRIPTION: [
            "g4f/GeminiPro",
            "g4f/Copilot",
            "g4f/OpenaiChat",
            "g4f/Claude",
            "g4f/Gemini",
            "g4f/DeepInfra",
        ],
    }


MODEL_CATALOG: dict[ExecutionMode, list[str]] = _load_model_catalog()


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
                    "openai/gpt",
                    "openai/gpt-mini",
                    "anthropic/claude-opus",
                    "anthropic/claude-sonnet",
                    "anthropic/claude-haiku",
                    "google/gemini-pro",
                    "google/gemini-flash",
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
                models=["openai/gpt", "openai/gpt-mini"],
            )
            logger.info("Configured provider: openai")

        # Anthropic direct
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            self.configure_provider(
                "anthropic",
                api_key=anthropic_key,
                models=[
                    "anthropic/claude-opus",
                    "anthropic/claude-sonnet",
                    "anthropic/claude-haiku",
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
                    "gemini/gemini-pro",
                    "gemini/gemini-flash",
                    "gemini/gemini-flash-lite",
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
            models=["ollama/llama", "ollama/mistral", "ollama/phi"],
        )
        # Ollama is always registered; actual availability depends on runtime
        # Dynamic model discovery happens asynchronously via discover_ollama_models()

        # g4f — subscription / no-API-key mode
        # Enabled by default; set USE_G4F=false to disable
        use_g4f = os.environ.get("USE_G4F", "true").lower() not in ("false", "0", "no")
        if use_g4f:
            try:
                from app.providers.g4f_provider import FREE_G4F_MODELS, g4f_provider

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

    def _resolve_to_api_model(self, family_id: str) -> str:
        """Resolve a family-level model ID to the actual API model ID.

        Uses the ModelRegistry to look up latest_model_id.
        Falls back to the family ID itself if registry is unavailable.
        """
        try:
            from app.providers.model_registry import get_model_registry

            return get_model_registry().resolve_api_id(family_id)
        except Exception:
            return family_id

    def select_model(self, mode: ExecutionMode) -> str:
        """Select best model for the given execution mode.

        Prefers models that belong to a configured provider so the caller
        is less likely to encounter authentication errors.
        For SUBSCRIPTION mode g4f models are always considered available.
        Returns the resolved API model ID (not family ID).
        """
        candidates = MODEL_CATALOG.get(mode, MODEL_CATALOG[ExecutionMode.QUALITY])
        available = set(self._configured_models())

        if available:
            for candidate in candidates:
                # g4f models are always "available" if g4f is installed
                if candidate.startswith("g4f/") or candidate in available:
                    return self._resolve_to_api_model(candidate)

        # Fall back to first candidate regardless of configuration
        selected = candidates[0] if candidates else "openai/gpt-mini"
        return self._resolve_to_api_model(selected)

    @staticmethod
    def _sanitize_messages(messages: list[dict]) -> list[dict]:
        """Scan messages for prompt injection and wrap external data markers.

        This ensures all content sent to LLMs passes through the security
        pipeline — CLAUDE.md rule: "When passing external data to LLMs:
        always wrap with wrap_external_data() boundary markers".
        """
        try:
            from app.security.prompt_guard import scan_prompt_injection, wrap_external_data

            sanitized: list[dict] = []
            for msg in messages:
                content = msg.get("content", "")
                if not isinstance(content, str) or not content:
                    sanitized.append(msg)
                    continue

                # System messages are trusted; user/assistant messages may carry
                # external data that was injected (e.g. web scrape, file content).
                if msg.get("role") in ("user", "tool"):
                    guard_result = scan_prompt_injection(content)
                    if not guard_result.is_safe:
                        logger.warning(
                            "Prompt injection detected in LLM message [%s]: %s",
                            guard_result.threat_level.value,
                            guard_result.detections,
                        )
                        # Wrap with boundary markers so the LLM can distinguish
                        content = wrap_external_data(content, source="user_input")
                        sanitized.append({**msg, "content": content})
                        continue

                sanitized.append(msg)
            return sanitized
        except Exception as exc:
            logger.error(
                "Message sanitization FAILED — refusing to send unsanitized messages: %s", exc
            )
            # Return messages with a security warning prepended instead of silently skipping
            warning_msg = {
                "role": "system",
                "content": (
                    "[SECURITY WARNING] Message sanitization failed. "
                    "External data in these messages has NOT been scanned for prompt injection."
                ),
            }
            return [warning_msg] + messages

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send completion request, routing to appropriate provider."""
        model = request.model or self.select_model(request.mode)

        # Security: scan messages for prompt injection and apply boundary markers
        request.messages = self._sanitize_messages(request.messages)

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
                timeout=120,  # Prevent indefinite hangs on LLM calls
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
            logger.error("LLM completion failed: %s", e)
            return CompletionResponse(
                content=f"Error: {e}",
                model_used=model,
                provider="error",
                finish_reason="error",
            )

    async def _complete_via_g4f(self, model: str, request: CompletionRequest) -> CompletionResponse:
        """Route a completion request through the g4f subscription provider."""
        try:
            from app.providers.g4f_provider import complete_with_fallback, g4f_provider

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
                model_used=f"ollama/{resp.model_used}"
                if not resp.model_used.startswith("ollama/")
                else resp.model_used,
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
        """Estimate API cost for a given model and token count.

        Cost data is loaded from model_catalog.json via the ModelRegistry.
        Falls back to a conservative default for unknown models.
        """
        try:
            from app.providers.model_registry import get_model_registry

            return get_model_registry().estimate_cost(model, input_tokens, output_tokens)
        except Exception as exc:
            logger.debug("Cost estimation via registry failed for %s: %s", model, exc)

        # Inline fallback if registry is unavailable
        if model.startswith(("g4f/", "ollama/")):
            return 0.0
        return (input_tokens / 1000 * 0.001) + (output_tokens / 1000 * 0.002)


# Global gateway instance — auto-configured from environment variables
llm_gateway = LLMGateway()
llm_gateway.configure_from_env()
