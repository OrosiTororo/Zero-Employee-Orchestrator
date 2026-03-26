"""Web browser-based AI session provider.

Integrates AI services such as GPT, Gemini, Claude, etc. into the system
via web browser UI without API fees.

How it works:
1. Access AI web UIs through browser automation (browser-use, etc.)
2. Input prompts and retrieve responses
3. Integrate into ZEO's LLM Gateway

Usage patterns:
- Pattern A: g4f (gpt4free) -- Automatically routes through web endpoints (existing)
- Pattern B: Browser session -- Operates AI web UIs via actual browser automation
- Pattern C: Cookie/session auth -- Reuses already-logged-in sessions

Notes:
- Review the terms of service for each AI service
- Official APIs with API keys are the most stable and reliable
- Web UI access carries risks of rate limiting and blocking
- Official APIs are recommended for production environments
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Web AI service definitions
# ---------------------------------------------------------------------------


class WebAIService(str, Enum):
    """AI services available via browser."""

    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    CLAUDE = "claude"
    COPILOT = "copilot"
    DEEPSEEK = "deepseek"
    PERPLEXITY = "perplexity"


@dataclass
class WebSessionConfig:
    """Web AI session configuration."""

    service: WebAIService
    session_cookies: dict | None = None  # Cookies exported from browser
    profile_dir: str | None = None  # Chrome profile directory
    headless: bool = True
    timeout_seconds: int = 120


@dataclass
class WebSessionResponse:
    """AI response via web session."""

    content: str
    service: str
    model_hint: str = ""  # Model selected in web UI (if retrievable)
    cost_usd: float = 0.0  # Always 0 via web UI
    finish_reason: str = "stop"
    tokens_input: int = 0
    tokens_output: int = 0


# ---------------------------------------------------------------------------
# Web AI session catalog
# ---------------------------------------------------------------------------

_WEB_AI_CATALOG: dict[WebAIService, dict] = {
    WebAIService.CHATGPT: {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "free_tier": True,
        "free_model": "GPT-4o mini",
        "subscription_model": "GPT-4o / o1",
        "subscription_name": "ChatGPT Plus",
        "input_selector": "#prompt-textarea",
        "submit_selector": "button[data-testid='send-button']",
        "response_selector": ".markdown",
        "env_cookie_key": "CHATGPT_SESSION_COOKIE",
    },
    WebAIService.GEMINI: {
        "name": "Google Gemini",
        "url": "https://gemini.google.com",
        "free_tier": True,
        "free_model": "Gemini 2.5 Flash",
        "subscription_model": "Gemini 2.5 Pro",
        "subscription_name": "Gemini Advanced",
        "input_selector": ".ql-editor",
        "submit_selector": "button[aria-label='Send message']",
        "response_selector": ".model-response-text",
        "env_cookie_key": "GEMINI_SESSION_COOKIE",
    },
    WebAIService.CLAUDE: {
        "name": "Claude",
        "url": "https://claude.ai",
        "free_tier": True,
        "free_model": "Claude Sonnet 4",
        "subscription_model": "Claude Opus 4",
        "subscription_name": "Claude Pro",
        "input_selector": ".ProseMirror",
        "submit_selector": "button[aria-label='Send Message']",
        "response_selector": ".font-claude-message",
        "env_cookie_key": "CLAUDE_SESSION_COOKIE",
    },
    WebAIService.COPILOT: {
        "name": "Microsoft Copilot",
        "url": "https://copilot.microsoft.com",
        "free_tier": True,
        "free_model": "GPT-4o",
        "subscription_model": "GPT-4o + DALL-E",
        "subscription_name": "Copilot Pro",
        "input_selector": "#userInput",
        "submit_selector": "button[aria-label='Submit']",
        "response_selector": ".ac-textBlock",
        "env_cookie_key": "COPILOT_SESSION_COOKIE",
    },
    WebAIService.DEEPSEEK: {
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "free_tier": True,
        "free_model": "DeepSeek V3",
        "subscription_model": "DeepSeek R1",
        "subscription_name": "DeepSeek (free)",
        "input_selector": "textarea",
        "submit_selector": "button[type='submit']",
        "response_selector": ".markdown-body",
        "env_cookie_key": "DEEPSEEK_SESSION_COOKIE",
    },
    WebAIService.PERPLEXITY: {
        "name": "Perplexity",
        "url": "https://www.perplexity.ai",
        "free_tier": True,
        "free_model": "Default",
        "subscription_model": "Pro Search",
        "subscription_name": "Perplexity Pro",
        "input_selector": "textarea",
        "submit_selector": "button[aria-label='Submit']",
        "response_selector": ".prose",
        "env_cookie_key": "PERPLEXITY_SESSION_COOKIE",
    },
}


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------


class WebSessionProvider:
    """Provider that uses AI services via web browser.

    Offers 3 methods:
    1. Via g4f (recommended) -- Simplest. g4f auto-routes through web endpoints
    2. Browser session -- Automates browsers via browser-use, etc.
    3. Cookie auth -- Reuses cookies from already-logged-in sessions

    Recommended usage order:
    1. Official APIs with free tiers (Gemini free tier, etc.)
    2. g4f (existing g4f_provider.py)
    3. Ollama (local)
    4. Browser session (this class)
    """

    def __init__(self) -> None:
        self._sessions: dict[str, WebSessionConfig] = {}

    def list_services(self) -> list[dict]:
        """Return a list of available Web AI services."""
        services = []
        for service, info in _WEB_AI_CATALOG.items():
            has_cookie = bool(os.environ.get(info["env_cookie_key"], ""))
            services.append(
                {
                    "service": service.value,
                    "name": info["name"],
                    "url": info["url"],
                    "free_tier": info["free_tier"],
                    "free_model": info["free_model"],
                    "subscription_model": info["subscription_model"],
                    "subscription_name": info["subscription_name"],
                    "cookie_configured": has_cookie,
                    "cost_usd": 0.0,
                }
            )
        return services

    def get_recommended_free_options(self) -> list[dict]:
        """Return options available without API fees in recommended order.

        Organized methods for using AI at no cost:
        1. Free API keys (Gemini free tier)
        2. g4f (web endpoint auto-routing)
        3. Ollama (local)
        4. Web AI sessions (this provider)
        """
        options = [
            {
                "method": "gemini_free_api",
                "name": "Google Gemini Free API",
                "description": (
                    "Get a free API key from Google AI Studio. Rate-limited but highly stable."
                ),
                "setup": "Set GEMINI_API_KEY",
                "stability": "high",
                "rate_limit": "15 RPM (free tier)",
                "cost": 0.0,
                "recommended": True,
            },
            {
                "method": "g4f",
                "name": "g4f (gpt4free)",
                "description": (
                    "Auto-routes through web endpoints. Falls back across multiple providers."
                ),
                "setup": "pip install g4f (USE_G4F=true is the default)",
                "stability": "medium",
                "rate_limit": "Varies by provider",
                "cost": 0.0,
                "recommended": True,
            },
            {
                "method": "ollama",
                "name": "Ollama (Local LLM)",
                "description": (
                    "Run LLMs locally. Completely offline and free. "
                    "High-quality models are available with a GPU."
                ),
                "setup": "Install Ollama and pull a model",
                "stability": "high",
                "rate_limit": "Hardware-dependent",
                "cost": 0.0,
                "recommended": True,
            },
            {
                "method": "web_session",
                "name": "Web AI Session",
                "description": (
                    "Use ChatGPT / Gemini / Claude, etc. web UIs via browser. "
                    "Only requires each service's subscription fee; no API fees."
                ),
                "setup": "Install browser-use Plugin or configure cookies",
                "stability": "low",
                "rate_limit": "Depends on web UI rate limits",
                "cost": 0.0,
                "recommended": False,
            },
        ]
        return options

    async def complete(
        self,
        service: WebAIService,
        messages: list[dict],
        config: WebSessionConfig | None = None,
    ) -> WebSessionResponse:
        """Send a completion request via web AI session.

        The current implementation falls back to g4f.
        Browser automation mode is also available when the browser-use adapter is installed.

        Args:
            service: AI service to use
            messages: Message list
            config: Session configuration (defaults if omitted)

        Returns:
            AI response
        """
        catalog_entry = _WEB_AI_CATALOG.get(service)
        if not catalog_entry:
            return WebSessionResponse(
                content=f"[Unsupported service: {service.value}]",
                service=service.value,
                finish_reason="error",
            )

        # Method 1: Via g4f (recommended, most stable)
        g4f_result = await self._try_g4f(service, messages)
        if g4f_result and g4f_result.finish_reason != "error":
            return g4f_result

        # Method 2: Via browser session
        browser_result = await self._try_browser_session(service, messages, catalog_entry, config)
        if browser_result:
            return browser_result

        # Fallback
        return WebSessionResponse(
            content=(
                f"[Failed to access {catalog_entry['name']}. "
                "Install g4f or add the browser-use Plugin.]"
            ),
            service=service.value,
            finish_reason="error",
        )

    async def _try_g4f(
        self,
        service: WebAIService,
        messages: list[dict],
    ) -> WebSessionResponse | None:
        """Attempt a request via g4f."""
        g4f_model_map: dict[WebAIService, str] = {
            WebAIService.CHATGPT: "g4f/OpenaiChat",
            WebAIService.GEMINI: "g4f/GeminiPro",
            WebAIService.CLAUDE: "g4f/Claude",
            WebAIService.COPILOT: "g4f/Copilot",
            WebAIService.DEEPSEEK: "g4f/DeepInfra",
        }

        model = g4f_model_map.get(service)
        if not model:
            return None

        try:
            from app.providers.g4f_provider import g4f_provider

            if not g4f_provider.available:
                return None

            resp = await g4f_provider.complete(model=model, messages=messages)
            if resp.finish_reason == "error":
                return None

            return WebSessionResponse(
                content=resp.content,
                service=service.value,
                model_hint=resp.model_used,
                cost_usd=0.0,
                finish_reason=resp.finish_reason,
            )
        except Exception as exc:
            logger.debug("g4f fallback failed for %s: %s", service.value, exc)
            return None

    async def _try_browser_session(
        self,
        service: WebAIService,
        messages: list[dict],
        catalog_entry: dict,
        config: WebSessionConfig | None,
    ) -> WebSessionResponse | None:
        """Attempt a request via browser session."""
        try:
            from app.tools.browser_adapter import BrowserTask, browser_adapter_registry

            adapter = browser_adapter_registry.get_adapter("browser-use")
            if adapter is None:
                return None

            # Combine messages to create a prompt
            prompt = "\n".join(m.get("content", "") for m in messages if m.get("role") != "system")

            task = BrowserTask(
                instruction=(
                    f"Access {catalog_entry['url']}, "
                    f"enter the following prompt, and retrieve the AI response:\n\n{prompt}"
                ),
                url=catalog_entry["url"],
                max_steps=20,
                timeout_seconds=config.timeout_seconds if config else 120,
                require_approval=False,  # Web AI sessions do not require approval
            )

            result = await adapter.execute_task(task)
            if result.status.value == "completed" and result.output:
                return WebSessionResponse(
                    content=result.output,
                    service=service.value,
                    model_hint=catalog_entry.get("free_model", ""),
                    cost_usd=0.0,
                    finish_reason="stop",
                )
        except Exception as exc:
            logger.debug("Browser session failed for %s: %s", service.value, exc)

        return None


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

web_session_provider = WebSessionProvider()
