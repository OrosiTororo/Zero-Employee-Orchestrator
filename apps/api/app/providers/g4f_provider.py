"""Subscription-mode / No-API-key LLM provider using gpt4free (g4f).

This provider lets Zero-Employee Orchestrator operate **without any paid API
key** by routing requests through free and subscription-based AI services.

Free tier (no account needed)
------------------------------
* ``g4f/GeminiPro``    — Google Gemini 2.5 Flash via a free web endpoint
* ``g4f/Copilot``      — Microsoft Copilot (GPT-5.4 backbone)
* ``g4f/OpenaiChat``   — ChatGPT web interface (free tier, GPT-5-mini)
* ``g4f/Claude``       — Anthropic Claude via a free relay (Claude Haiku 4.5)
* ``g4f/DeepInfra``    — Various open-weight models (Llama, Mistral, …)
* ``g4f/ApiAirforce``  — Multi-model free relay

Subscription tier (requires browser session / account cookies)
--------------------------------------------------------------
* ``g4f/Gemini``       — Full Google Gemini with a Google account (or
                          Gemini Advanced subscription) — higher limits
* ``g4f/CopilotAccount`` — Copilot Pro subscription

Usage
-----
Set ``USE_G4F=true`` (default) in your ``.env`` and choose
``DEFAULT_EXECUTION_MODE=subscription``.  For subscription providers also set
the provider-specific cookie env vars (see ``.env.example``).

Note on Terms of Service
-------------------------
The free providers route through publicly accessible web endpoints.  Usage
policies are set by each individual service.  Review the terms of the service
you use before deploying in a production environment.  For fully compliant,
stable, and SLA-backed operation prefer official API keys.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model → g4f-provider mapping
# ---------------------------------------------------------------------------

# Key: model name used inside this system (e.g. "g4f/GeminiPro")
# Value: dict with g4f provider name (string) and model string for g4f
_G4F_MODEL_MAP: dict[str, dict] = {
    # ── Free providers (no account needed) ─────────────────────────────────
    "g4f/GeminiPro": {
        "provider": "GeminiPro",
        "model": "models/gemini-2.5-flash",
        "needs_auth": False,
        "description": "Google Gemini 2.5 Flash (free, no API key)",
    },
    "g4f/Copilot": {
        "provider": "Copilot",
        "model": "gpt-5.4",
        "needs_auth": False,
        "description": "Microsoft Copilot / GPT-5.4 (free, no API key)",
    },
    "g4f/OpenaiChat": {
        "provider": "OpenaiChat",
        "model": "gpt-5-mini",
        "needs_auth": False,
        "description": "ChatGPT web interface (free tier, GPT-5-mini, no API key)",
    },
    "g4f/Claude": {
        "provider": "Claude",
        "model": "claude-haiku-4-5-20251001",
        "needs_auth": False,
        "description": "Anthropic Claude Haiku 4.5 via free relay (no API key)",
    },
    "g4f/DeepInfra": {
        "provider": "DeepInfra",
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "needs_auth": False,
        "description": "Llama 3.1 70B via DeepInfra free relay (no API key)",
    },
    "g4f/ApiAirforce": {
        "provider": "ApiAirforce",
        "model": "gpt-5-mini",
        "needs_auth": False,
        "description": "Multi-model free relay (GPT-5-mini, no API key)",
    },
    # ── Subscription / authenticated providers ──────────────────────────────
    "g4f/Gemini": {
        "provider": "Gemini",
        "model": "gemini-2.5-flash",  # authenticated Gemini; g4f uses this identifier
        "needs_auth": True,
        "description": "Google Gemini with Google account (Gemini Advanced subscription)",
    },
    "g4f/CopilotAccount": {
        "provider": "CopilotAccount",
        "model": "gpt-5.4",
        "needs_auth": True,
        "description": "Microsoft Copilot Pro subscription (GPT-5.4)",
    },
}

# Free models (no authentication required)
FREE_G4F_MODELS: list[str] = [k for k, v in _G4F_MODEL_MAP.items() if not v["needs_auth"]]

# Subscription models (authentication required)
SUBSCRIPTION_G4F_MODELS: list[str] = [k for k, v in _G4F_MODEL_MAP.items() if v["needs_auth"]]


# ---------------------------------------------------------------------------
# Response dataclass (matches gateway.CompletionResponse structure)
# ---------------------------------------------------------------------------


@dataclass
class G4FResponse:
    content: str
    model_used: str
    provider: str
    finish_reason: str = "stop"
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------


class G4FProvider:
    """Async LLM provider backed by gpt4free.

    Supports both free (no-auth) providers and subscription-based providers
    that use a Google / Microsoft account session cookie for authentication.
    """

    def __init__(self) -> None:
        self._available = False
        self._g4f = None
        self._try_import()

    def _try_import(self) -> None:
        try:
            import g4f  # noqa: F401

            self._g4f = g4f
            self._available = True
            logger.info("g4f provider available (subscription / no-API-key mode enabled)")
        except ImportError:
            logger.warning(
                "g4f not installed — subscription/no-API-key mode unavailable. "
                "Install with: pip install g4f"
            )

    @property
    def available(self) -> bool:
        return self._available

    def list_free_models(self) -> list[str]:
        """Return model names usable without any API key."""
        if not self._available:
            return []
        return list(FREE_G4F_MODELS)

    def list_subscription_models(self) -> list[str]:
        """Return model names that require a logged-in session."""
        if not self._available:
            return []
        return list(SUBSCRIPTION_G4F_MODELS)

    def get_model_info(self, model: str) -> dict | None:
        return _G4F_MODEL_MAP.get(model)

    async def complete(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        cookies: dict | None = None,
    ) -> G4FResponse:
        """Send a chat completion request through g4f.

        Args:
            model:       One of the ``g4f/*`` model names defined in this module.
            messages:    OpenAI-style message list.
            max_tokens:  Maximum output tokens (best-effort, not all providers
                         honour this).
            temperature: Sampling temperature.
            cookies:     Provider-specific authentication cookies for
                         subscription providers.  Pass ``None`` for free
                         providers.

        Returns:
            A ``G4FResponse`` with the completion text.
        """
        if not self._available:
            return G4FResponse(
                content="[g4f not installed — run: pip install g4f]",
                model_used=model,
                provider="g4f_unavailable",
                finish_reason="error",
            )

        model_info = _G4F_MODEL_MAP.get(model)
        if model_info is None:
            return G4FResponse(
                content=f"[Unknown g4f model: {model}]",
                model_used=model,
                provider="g4f_error",
                finish_reason="error",
            )

        provider_name = model_info["provider"]
        g4f_model = model_info["model"]

        try:
            import g4f.Provider as Providers
            from g4f.client import AsyncClient

            provider_cls = getattr(Providers, provider_name, None)
            if provider_cls is None:
                return G4FResponse(
                    content=f"[g4f provider not found: {provider_name}]",
                    model_used=model,
                    provider="g4f_error",
                    finish_reason="error",
                )

            client = AsyncClient()

            # Build kwargs
            kwargs: dict = {
                "messages": messages,
                "model": g4f_model,
                "provider": provider_cls,
                "max_tokens": max_tokens,
                "ignore_stream": True,
            }
            if cookies:
                kwargs["cookies"] = cookies

            # g4f's AsyncClient returns an awaitable — use asyncio timeout
            response = await asyncio.wait_for(
                client.chat.completions.create(**kwargs),
                timeout=120.0,
            )

            content = ""
            if response and response.choices:
                content = response.choices[0].message.content or ""

            return G4FResponse(
                content=content,
                model_used=model,
                provider=f"g4f/{provider_name}",
                finish_reason="stop",
            )

        except TimeoutError:
            logger.warning("g4f request timed out for provider %s", provider_name)
            return G4FResponse(
                content="[g4f request timed out]",
                model_used=model,
                provider=f"g4f/{provider_name}",
                finish_reason="error",
            )
        except Exception as exc:
            logger.error("g4f completion failed for %s: %s", provider_name, exc)
            return G4FResponse(
                content=f"[g4f error: {exc}]",
                model_used=model,
                provider=f"g4f/{provider_name}",
                finish_reason="error",
            )


# ---------------------------------------------------------------------------
# Fallback chain helpers
# ---------------------------------------------------------------------------


async def complete_with_fallback(
    provider: G4FProvider,
    models: list[str],
    messages: list[dict],
    max_tokens: int = 2048,
    temperature: float = 0.7,
    cookies: dict | None = None,
) -> G4FResponse:
    """Try each model in order and return the first successful response.

    A response is considered successful when ``finish_reason`` is not ``"error"``
    and the content is non-empty.

    This makes the no-API-key path resilient to individual provider outages.
    """
    last_response: G4FResponse | None = None
    for model in models:
        resp = await provider.complete(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            cookies=cookies,
        )
        if resp.finish_reason != "error" and resp.content:
            return resp
        last_response = resp
        logger.debug("g4f model %s failed, trying next", model)

    # Return last response (even if error) if nothing worked
    return last_response or G4FResponse(
        content="[All g4f providers failed]",
        model_used=models[-1] if models else "g4f/unknown",
        provider="g4f_fallback",
        finish_reason="error",
    )


# Global singleton
g4f_provider = G4FProvider()
