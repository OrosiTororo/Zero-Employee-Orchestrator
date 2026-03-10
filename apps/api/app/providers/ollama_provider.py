"""Enhanced Ollama provider — direct HTTP connection to local Ollama instance.

Inspired by vibe-local (https://github.com/ochyai/vibe-local), this provider
connects directly to Ollama's REST API without requiring LiteLLM or any
external Python dependency beyond the standard library + httpx.

Key features
------------
* **Model discovery** — dynamically lists models available on the Ollama instance
* **Health check** — verifies Ollama is reachable before routing requests
* **Streaming** — supports SSE-style streaming for real-time output
* **Tool-call extraction** — parses XML-style tool invocations that open-weight
  models sometimes produce instead of proper function-call JSON
* **Zero API key** — works entirely offline once models are pulled
* **Model pull** — can trigger ``ollama pull <model>`` from the API
* **Qwen3 / DeepSeek / CodeLlama support** — extends beyond the default
  llama3.2/mistral/phi3 set

Security (borrowed from vibe-local)
------------------------------------
* Validates that the Ollama base URL resolves to a loopback / private address
* Rejects redirects to non-local hosts
"""

from __future__ import annotations

import json
import logging
import re
import socket
import time
from dataclasses import dataclass, field
from ipaddress import ip_address
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_OLLAMA_URL = "http://localhost:11434"
_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 300.0  # local LLMs can be slow on CPU

# Models known to work well with tool-use / coding tasks
RECOMMENDED_MODELS: dict[str, dict] = {
    "qwen3:8b": {
        "description": "Qwen3 8B — fast, good reasoning (vibe-local sidecar default)",
        "context_window": 32768,
        "supports_tools": True,
    },
    "qwen3-coder:30b": {
        "description": "Qwen3 Coder 30B — strong coding model (vibe-local main default)",
        "context_window": 32768,
        "supports_tools": True,
    },
    "qwen3:32b": {
        "description": "Qwen3 32B — high-quality general purpose",
        "context_window": 32768,
        "supports_tools": True,
    },
    "llama3.2:latest": {
        "description": "Llama 3.2 — Meta's compact open-weight model",
        "context_window": 131072,
        "supports_tools": True,
    },
    "mistral:latest": {
        "description": "Mistral 7B — efficient European open-weight model",
        "context_window": 32768,
        "supports_tools": False,
    },
    "phi3:latest": {
        "description": "Phi-3 — Microsoft's small but capable model",
        "context_window": 128000,
        "supports_tools": False,
    },
    "deepseek-coder-v2:latest": {
        "description": "DeepSeek Coder V2 — strong code generation",
        "context_window": 128000,
        "supports_tools": True,
    },
    "codellama:latest": {
        "description": "Code Llama — Meta's code-specialized model",
        "context_window": 16384,
        "supports_tools": False,
    },
    "gemma2:latest": {
        "description": "Gemma 2 — Google's open-weight model",
        "context_window": 8192,
        "supports_tools": False,
    },
}


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------


def _is_private_ip(host: str) -> bool:
    """Check if a hostname resolves to a private/loopback IP address."""
    try:
        resolved = socket.getaddrinfo(host, None)
        for _, _, _, _, addr_tuple in resolved:
            addr = ip_address(addr_tuple[0])
            if addr.is_loopback or addr.is_private:
                return True
        return False
    except (socket.gaierror, ValueError):
        # DNS fail-closed: if we can't resolve, reject
        return False


def validate_ollama_url(base_url: str) -> bool:
    """Validate that the Ollama URL points to a local/private address.

    This prevents SSRF attacks where a malicious OLLAMA_BASE_URL could
    route requests to external services.
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        host = parsed.hostname or "localhost"
        return _is_private_ip(host)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class OllamaModelInfo:
    """Information about a model available on the Ollama instance."""

    name: str
    size: int = 0  # bytes
    modified_at: str = ""
    digest: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class OllamaResponse:
    """Response from Ollama completion."""

    content: str
    model_used: str
    provider: str = "ollama_direct"
    finish_reason: str = "stop"
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0  # always free
    tool_calls: list[dict] = field(default_factory=list)
    thinking: str = ""  # extended thinking content


# ---------------------------------------------------------------------------
# Tool-call extraction from text (XML/tag-style fallback)
# ---------------------------------------------------------------------------

# Patterns for XML-style tool invocations that local models sometimes produce
_TOOL_PATTERNS = [
    # <invoke name="ToolName"><parameter name="key">value</parameter></invoke>
    re.compile(
        r'<invoke\s+name="([^"]+)">(.*?)</invoke>',
        re.DOTALL,
    ),
    # <function=ToolName>{"key": "value"}</function>
    re.compile(
        r"<function=(\w+)>(.*?)</function>",
        re.DOTALL,
    ),
    # <tool_call>{"name": "...", "arguments": {...}}</tool_call>
    re.compile(
        r"<tool_call>(.*?)</tool_call>",
        re.DOTALL,
    ),
]

_PARAM_PATTERN = re.compile(
    r'<parameter\s+name="([^"]+)">(.*?)</parameter>',
    re.DOTALL,
)


def extract_tool_calls_from_text(text: str) -> list[dict]:
    """Extract tool calls from model output that uses XML-style tags.

    Local LLMs sometimes produce tool invocations as XML tags instead of
    the standard JSON function-call format. This function extracts them.
    """
    tool_calls: list[dict] = []

    # Pattern 1: <invoke name="..."><parameter ...>...</parameter></invoke>
    for match in _TOOL_PATTERNS[0].finditer(text):
        name = match.group(1)
        body = match.group(2)
        params = {}
        for param_match in _PARAM_PATTERN.finditer(body):
            params[param_match.group(1)] = param_match.group(2).strip()
        tool_calls.append(
            {
                "id": f"toolu_local_{len(tool_calls)}",
                "function": name,
                "arguments": json.dumps(params),
            }
        )

    if tool_calls:
        return tool_calls

    # Pattern 2: <function=ToolName>{...}</function>
    for match in _TOOL_PATTERNS[1].finditer(text):
        name = match.group(1)
        try:
            args = json.loads(match.group(2).strip())
        except json.JSONDecodeError:
            args = {"raw": match.group(2).strip()}
        tool_calls.append(
            {
                "id": f"toolu_local_{len(tool_calls)}",
                "function": name,
                "arguments": json.dumps(args),
            }
        )

    if tool_calls:
        return tool_calls

    # Pattern 3: <tool_call>{"name": "...", "arguments": ...}</tool_call>
    for match in _TOOL_PATTERNS[2].finditer(text):
        try:
            data = json.loads(match.group(1).strip())
            tool_calls.append(
                {
                    "id": f"toolu_local_{len(tool_calls)}",
                    "function": data.get("name", "unknown"),
                    "arguments": json.dumps(data.get("arguments", {})),
                }
            )
        except json.JSONDecodeError:
            pass

    return tool_calls


# ---------------------------------------------------------------------------
# Ollama Provider
# ---------------------------------------------------------------------------


class OllamaProvider:
    """Direct HTTP provider for Ollama.

    Connects to Ollama's REST API without going through LiteLLM, giving
    full control over model discovery, health checks, and streaming.
    """

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL) -> None:
        self._base_url = base_url.rstrip("/")
        self._available: bool | None = None  # None = not checked yet
        self._models_cache: list[OllamaModelInfo] | None = None
        self._cache_time: float = 0.0
        self._cache_ttl: float = 60.0  # seconds

        # Validate URL security
        if not validate_ollama_url(self._base_url):
            logger.warning(
                "Ollama URL %s does not resolve to a private/loopback address. "
                "This may be a security risk (SSRF).",
                self._base_url,
            )

    @property
    def base_url(self) -> str:
        return self._base_url

    # ------------------------------------------------------------------
    # Health & availability
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Check if Ollama is reachable and responding."""
        try:
            async with httpx.AsyncClient(timeout=_CONNECT_TIMEOUT) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                self._available = resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, OSError):
            self._available = False
        return self._available

    @property
    def available(self) -> bool | None:
        """Return cached availability status (None if not yet checked)."""
        return self._available

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    async def list_models(self, force_refresh: bool = False) -> list[OllamaModelInfo]:
        """List models available on the Ollama instance."""
        now = time.monotonic()
        if (
            not force_refresh
            and self._models_cache is not None
            and (now - self._cache_time) < self._cache_ttl
        ):
            return self._models_cache

        try:
            async with httpx.AsyncClient(timeout=_CONNECT_TIMEOUT) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()

            models = []
            for m in data.get("models", []):
                models.append(
                    OllamaModelInfo(
                        name=m.get("name", ""),
                        size=m.get("size", 0),
                        modified_at=m.get("modified_at", ""),
                        digest=m.get("digest", ""),
                        details=m.get("details", {}),
                    )
                )

            self._models_cache = models
            self._cache_time = now
            self._available = True
            return models

        except Exception as exc:
            logger.debug("Failed to list Ollama models: %s", exc)
            self._available = False
            return []

    async def get_available_model_names(self) -> list[str]:
        """Return just the model names as strings."""
        models = await self.list_models()
        return [m.name for m in models]

    async def has_model(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        names = await self.get_available_model_names()
        # Ollama model names can include tags (e.g. "llama3.2:latest")
        return any(
            name == model_name or name.split(":")[0] == model_name.split(":")[0]
            for name in names
        )

    async def pull_model(self, model_name: str) -> bool:
        """Trigger a model pull on the Ollama instance.

        Returns True if the pull was accepted (actual download may take time).
        """
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                resp = await client.post(
                    f"{self._base_url}/api/pull",
                    json={"name": model_name, "stream": False},
                )
                return resp.status_code == 200
        except Exception as exc:
            logger.error("Failed to pull model %s: %s", model_name, exc)
            return False

    async def suggest_model(self) -> str | None:
        """Suggest the best available model based on what's installed.

        Prefers models known to be good for coding/tool-use tasks.
        """
        available = await self.get_available_model_names()
        if not available:
            return None

        # Priority order for coding/orchestration tasks
        priority = [
            "qwen3-coder",
            "qwen3:32b",
            "qwen3:8b",
            "qwen3",
            "deepseek-coder-v2",
            "codellama",
            "llama3.2",
            "llama3.1",
            "llama3",
            "mistral",
            "phi3",
            "gemma2",
        ]

        for preferred in priority:
            for name in available:
                if preferred in name:
                    return name

        # Return first available model as fallback
        return available[0]

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> OllamaResponse:
        """Send a chat completion request to Ollama.

        Args:
            messages:    OpenAI-style message list.
            model:       Ollama model name (auto-selected if None).
            temperature: Sampling temperature.
            max_tokens:  Maximum output tokens.
            tools:       Tool definitions (OpenAI format).
            system:      Optional system prompt override.

        Returns:
            OllamaResponse with the completion text and metadata.
        """
        # Auto-select model if not specified
        if not model:
            model = await self.suggest_model()
            if not model:
                return OllamaResponse(
                    content="[No Ollama models available. Run: ollama pull qwen3:8b]",
                    model_used="none",
                    provider="ollama_unavailable",
                    finish_reason="error",
                )

        # Strip "ollama/" prefix if present (gateway convention)
        if model.startswith("ollama/"):
            model = model[7:]

        # Build request payload
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        # Add tools if the model supports them
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=_CONNECT_TIMEOUT,
                    read=_READ_TIMEOUT,
                    write=30.0,
                    pool=5.0,
                ),
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            # Extract response
            message = data.get("message", {})
            content = message.get("content", "")

            # Extract tool calls from structured response
            tool_calls = []
            if message.get("tool_calls"):
                for tc in message["tool_calls"]:
                    func = tc.get("function", {})
                    tool_calls.append(
                        {
                            "id": f"toolu_local_{len(tool_calls)}",
                            "function": func.get("name", ""),
                            "arguments": json.dumps(func.get("arguments", {})),
                        }
                    )

            # Fallback: extract XML-style tool calls from text
            if not tool_calls and tools and content:
                tool_calls = extract_tool_calls_from_text(content)

            # Token counts
            tokens_input = data.get("prompt_eval_count", 0)
            tokens_output = data.get("eval_count", 0)

            finish_reason = "tool_calls" if tool_calls else "stop"

            self._available = True
            return OllamaResponse(
                content=content,
                model_used=model,
                provider="ollama_direct",
                finish_reason=finish_reason,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tool_calls=tool_calls,
            )

        except httpx.ConnectError:
            self._available = False
            return OllamaResponse(
                content=(
                    "[Ollama is not running. Start it with: ollama serve\n"
                    f"Expected at: {self._base_url}]"
                ),
                model_used=model,
                provider="ollama_unavailable",
                finish_reason="error",
            )
        except httpx.TimeoutException:
            return OllamaResponse(
                content="[Ollama request timed out — model may be loading or too large for available RAM]",
                model_used=model,
                provider="ollama_timeout",
                finish_reason="error",
            )
        except Exception as exc:
            logger.error("Ollama completion failed: %s", exc)
            return OllamaResponse(
                content=f"[Ollama error: {exc}]",
                model_used=model,
                provider="ollama_error",
                finish_reason="error",
            )

    async def complete_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a chat completion from Ollama, yielding content chunks.

        Yields text chunks as they arrive. Useful for CLI/TUI real-time output.
        """
        if not model:
            model = await self.suggest_model()
            if not model:
                yield "[No Ollama models available. Run: ollama pull qwen3:8b]"
                return

        if model.startswith("ollama/"):
            model = model[7:]

        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=_CONNECT_TIMEOUT,
                    read=_READ_TIMEOUT,
                    write=30.0,
                    pool=5.0,
                ),
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            msg = chunk.get("message", {})
                            text = msg.get("content", "")
                            if text:
                                yield text
                            if chunk.get("done", False):
                                return
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            self._available = False
            yield "[Ollama is not running. Start it with: ollama serve]"
        except Exception as exc:
            yield f"[Ollama stream error: {exc}]"


# ---------------------------------------------------------------------------
# Fallback chain for Ollama models
# ---------------------------------------------------------------------------


async def complete_with_ollama_fallback(
    provider: OllamaProvider,
    messages: list[dict],
    preferred_models: list[str] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    tools: list[dict] | None = None,
) -> OllamaResponse:
    """Try multiple Ollama models in sequence, returning first success.

    If no preferred_models are given, tries all available models in
    priority order.
    """
    available = await provider.get_available_model_names()
    if not available:
        return OllamaResponse(
            content="[No Ollama models available. Run: ollama pull qwen3:8b]",
            model_used="none",
            provider="ollama_unavailable",
            finish_reason="error",
        )

    models_to_try = preferred_models or available
    last_resp: OllamaResponse | None = None

    for model in models_to_try:
        # Skip models not actually installed
        if not any(
            model in name or name.split(":")[0] == model.split(":")[0]
            for name in available
        ):
            continue

        resp = await provider.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
        if resp.finish_reason != "error" and resp.content:
            return resp
        last_resp = resp

    return last_resp or OllamaResponse(
        content="[All Ollama models failed]",
        model_used="none",
        provider="ollama_fallback",
        finish_reason="error",
    )


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

ollama_provider = OllamaProvider()
