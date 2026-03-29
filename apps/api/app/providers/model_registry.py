"""Dynamic Model Registry -- Dynamic LLM model management and auto-update.

Manages models by combining an external config file (model_catalog.json)
with dynamic discovery from provider APIs, without relying on hardcoded model names.

Key features:
  - JSON file-based model catalog management
  - Model availability checks via provider APIs
  - Auto-detection and fallback for deprecated models
  - Dynamic cost information updates
  - Periodic model catalog refresh
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default catalog file location
_DEFAULT_CATALOG_PATH = Path(__file__).parent.parent.parent / "model_catalog.json"

# Cache TTL for provider health checks (seconds)
_HEALTH_CHECK_TTL = 300  # 5 minutes


@dataclass
class ModelEntry:
    """Individual model definition."""

    id: str  # e.g. "anthropic/claude-opus" (family name)
    provider: str  # e.g. "anthropic"
    display_name: str  # e.g. "Claude Opus"
    latest_model_id: str = ""  # Actual model ID used for API calls (e.g. "claude-opus-4-6")
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_tokens: int = 4096
    supports_tools: bool = False
    supports_vision: bool = False
    deprecated: bool = False  # End-of-service flag
    successor: str | None = None  # Successor model ID
    tags: list[str] = field(default_factory=list)  # e.g. ["quality", "speed"]

    def resolve_api_model_id(self) -> str:
        """Return the actual model ID used for API calls.

        Uses latest_model_id if set, otherwise returns the family ID as-is.
        """
        return self.latest_model_id or self.id


@dataclass
class ModeCatalog:
    """Model priority list per execution mode."""

    quality: list[str] = field(default_factory=list)
    speed: list[str] = field(default_factory=list)
    cost: list[str] = field(default_factory=list)
    free: list[str] = field(default_factory=list)
    subscription: list[str] = field(default_factory=list)


@dataclass
class QualitySLAModels:
    """Model configuration per quality mode."""

    draft: dict[str, list[str]] = field(default_factory=dict)
    standard: dict[str, list[str]] = field(default_factory=dict)
    high: dict[str, list[str]] = field(default_factory=dict)
    critical: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ProviderHealthStatus:
    """Provider health status."""

    provider: str
    available: bool
    checked_at: float
    available_models: list[str] = field(default_factory=list)
    error: str | None = None


class ModelRegistry:
    """Dynamic model registry.

    Loads model definitions from a JSON catalog file and combines
    them with provider API availability checks for optimal model selection.
    """

    def __init__(self, catalog_path: str | Path | None = None) -> None:
        self._catalog_path = Path(catalog_path) if catalog_path else _DEFAULT_CATALOG_PATH
        self._models: dict[str, ModelEntry] = {}
        self._latest_id_index: dict[str, ModelEntry] = {}
        self._mode_catalog = ModeCatalog()
        self._quality_sla = QualitySLAModels()
        self._provider_health: dict[str, ProviderHealthStatus] = {}
        self._last_loaded: float = 0
        self._catalog_version: str = ""
        self._load_catalog()

    # ------------------------------------------------------------------
    # Catalog I/O
    # ------------------------------------------------------------------

    def _load_catalog(self) -> None:
        """Load model definitions from the JSON catalog file."""
        if not self._catalog_path.exists():
            logger.warning(
                "Model catalog not found at %s, using empty registry",
                self._catalog_path,
            )
            return

        try:
            with open(self._catalog_path, encoding="utf-8") as f:
                data = json.load(f)

            self._catalog_version = data.get("version", "unknown")

            # Model definitions
            for m in data.get("models", []):
                entry = ModelEntry(
                    id=m["id"],
                    provider=m.get("provider", m["id"].split("/")[0]),
                    display_name=m.get("display_name", m["id"]),
                    latest_model_id=m.get("latest_model_id", ""),
                    cost_per_1k_input=m.get("cost_per_1k_input", 0.0),
                    cost_per_1k_output=m.get("cost_per_1k_output", 0.0),
                    max_tokens=m.get("max_tokens", 4096),
                    supports_tools=m.get("supports_tools", False),
                    supports_vision=m.get("supports_vision", False),
                    deprecated=m.get("deprecated", False),
                    successor=m.get("successor"),
                    tags=m.get("tags", []),
                )
                self._models[entry.id] = entry

            # Per-mode catalog
            modes = data.get("mode_catalog", {})
            self._mode_catalog = ModeCatalog(
                quality=modes.get("quality", []),
                speed=modes.get("speed", []),
                cost=modes.get("cost", []),
                free=modes.get("free", []),
                subscription=modes.get("subscription", []),
            )

            # Quality SLA configuration
            sla = data.get("quality_sla", {})
            self._quality_sla = QualitySLAModels(
                draft=sla.get("draft", {}),
                standard=sla.get("standard", {}),
                high=sla.get("high", {}),
                critical=sla.get("critical", {}),
            )

            # Build reverse-lookup index for O(1) resolution by latest_model_id
            self._latest_id_index: dict[str, ModelEntry] = {}
            for entry in self._models.values():
                if entry.latest_model_id:
                    self._latest_id_index[entry.latest_model_id] = entry
                    full_key = f"{entry.provider}/{entry.latest_model_id}"
                    self._latest_id_index[full_key] = entry

            self._last_loaded = time.time()
            logger.info(
                "Loaded model catalog v%s with %d models",
                self._catalog_version,
                len(self._models),
            )
        except Exception as exc:
            logger.error("Failed to load model catalog: %s", exc)

    def reload(self) -> None:
        """Reload the catalog."""
        self._models.clear()
        self._latest_id_index.clear()
        self._load_catalog()

    def save_catalog(self) -> None:
        """Save the current registry state to the JSON catalog file."""
        data: dict[str, Any] = {
            "version": self._catalog_version,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "description": (
                "Zero-Employee Orchestrator model catalog. "
                "Edit this file to add/remove models or update costs. "
                "Changes take effect on app restart or API-triggered reload."
            ),
            "models": [
                {
                    "id": m.id,
                    "provider": m.provider,
                    "display_name": m.display_name,
                    "latest_model_id": m.latest_model_id,
                    "cost_per_1k_input": m.cost_per_1k_input,
                    "cost_per_1k_output": m.cost_per_1k_output,
                    "max_tokens": m.max_tokens,
                    "supports_tools": m.supports_tools,
                    "supports_vision": m.supports_vision,
                    "deprecated": m.deprecated,
                    "successor": m.successor,
                    "tags": m.tags,
                }
                for m in self._models.values()
            ],
            "mode_catalog": {
                "quality": self._mode_catalog.quality,
                "speed": self._mode_catalog.speed,
                "cost": self._mode_catalog.cost,
                "free": self._mode_catalog.free,
                "subscription": self._mode_catalog.subscription,
            },
            "quality_sla": {
                "draft": self._quality_sla.draft,
                "standard": self._quality_sla.standard,
                "high": self._quality_sla.high,
                "critical": self._quality_sla.critical,
            },
        }
        self._catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Saved model catalog to %s", self._catalog_path)

    # ------------------------------------------------------------------
    # Model queries
    # ------------------------------------------------------------------

    def get_model(self, model_id: str) -> ModelEntry | None:
        """Get an entry by model ID."""
        return self._models.get(model_id)

    def get_active_model(
        self, model_id: str, *, allow_deprecated: bool = False
    ) -> ModelEntry | None:
        """Get a model entry, optionally allowing deprecated/legacy models.

        By default, deprecated models are auto-replaced with their successor.
        Set ``allow_deprecated=True`` to explicitly use a legacy model that is
        still operational (e.g. GPT-4o on Azure until its sunset date).
        """
        entry = self._models.get(model_id)
        if entry is None:
            return None
        if entry.deprecated and entry.successor and not allow_deprecated:
            successor = self._models.get(entry.successor)
            if successor and not successor.deprecated:
                logger.info(
                    "Model %s is deprecated, using successor %s",
                    model_id,
                    entry.successor,
                )
                return successor
        return entry

    def list_models(
        self,
        provider: str | None = None,
        include_deprecated: bool = False,
        tag: str | None = None,
    ) -> list[ModelEntry]:
        """Get a list of models.

        Use ``tag="legacy"`` with ``include_deprecated=True`` to list older
        models that are still operational and available for explicit selection.
        """
        result = []
        for m in self._models.values():
            if not include_deprecated and m.deprecated:
                continue
            if provider and m.provider != provider:
                continue
            if tag and tag not in m.tags:
                continue
            result.append(m)
        return result

    def resolve_api_id(self, family_id: str) -> str:
        """Resolve a family ID to the actual API model ID.

        Example: "anthropic/claude-opus" -> "claude-opus-4-6"
        Returns the family ID as-is for unknown models.
        """
        entry = self._models.get(family_id)
        if entry is None:
            return family_id
        return entry.resolve_api_model_id()

    def get_models_for_mode(self, mode: str) -> list[str]:
        """Get the list of model IDs for the given execution mode."""
        catalog_map = {
            "quality": self._mode_catalog.quality,
            "speed": self._mode_catalog.speed,
            "cost": self._mode_catalog.cost,
            "free": self._mode_catalog.free,
            "subscription": self._mode_catalog.subscription,
        }
        models = catalog_map.get(mode, self._mode_catalog.quality)
        # Auto-replace deprecated models with successors
        return self._resolve_deprecated(models)

    def get_sla_models(self, quality_mode: str) -> dict[str, list[str]]:
        """Get the model configuration for the given quality mode."""
        sla_map = {
            "draft": self._quality_sla.draft,
            "standard": self._quality_sla.standard,
            "high": self._quality_sla.high,
            "critical": self._quality_sla.critical,
        }
        sla = sla_map.get(quality_mode, self._quality_sla.standard)
        return {
            "preferred": self._resolve_deprecated(sla.get("preferred", [])),
            "fallback": self._resolve_deprecated(sla.get("fallback", [])),
        }

    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate model cost.

        Lookup is possible by either family ID or latest_model_id.
        """
        # g4f / ollama are always free
        if model_id.startswith(("g4f/", "ollama/")):
            return 0.0

        # First search by family ID
        entry = self._models.get(model_id)
        if entry is None:
            # O(1) reverse lookup by latest_model_id via pre-built index
            entry = self._latest_id_index.get(model_id)
        if entry:
            return (input_tokens / 1000 * entry.cost_per_1k_input) + (
                output_tokens / 1000 * entry.cost_per_1k_output
            )
        # Fallback: assume moderate cost for unknown models
        return (input_tokens / 1000 * 0.001) + (output_tokens / 1000 * 0.002)

    def get_cost_table(self) -> dict[str, dict[str, float]]:
        """Generate a CostGuard-compatible cost table.

        Lookup is possible by family ID, latest_model_id, and short name.
        """
        table: dict[str, dict[str, float]] = {}
        for m in self._models.values():
            if m.deprecated:
                continue
            cost_entry = {
                "input": m.cost_per_1k_input,
                "output": m.cost_per_1k_output,
            }
            # Family ID (e.g. "anthropic/claude-opus")
            table[m.id] = cost_entry
            # Family short name (e.g. "claude-opus")
            short_name = m.id.split("/", 1)[-1] if "/" in m.id else m.id
            table[short_name] = cost_entry
            # latest_model_id (e.g. "claude-opus-4-6")
            if m.latest_model_id:
                table[m.latest_model_id] = cost_entry
                # Provider-prefixed latest (e.g. "anthropic/claude-opus-4-6")
                table[f"{m.provider}/{m.latest_model_id}"] = cost_entry
        return table

    # ------------------------------------------------------------------
    # Deprecation handling
    # ------------------------------------------------------------------

    def _resolve_deprecated(self, model_ids: list[str]) -> list[str]:
        """Auto-replace deprecated models with their successors."""
        resolved: list[str] = []
        seen: set[str] = set()
        for mid in model_ids:
            entry = self._models.get(mid)
            if entry and entry.deprecated and entry.successor:
                replacement = entry.successor
                if replacement not in seen:
                    resolved.append(replacement)
                    seen.add(replacement)
                logger.debug("Replaced deprecated %s with %s", mid, replacement)
            elif mid not in seen:
                resolved.append(mid)
                seen.add(mid)
        return resolved

    def mark_deprecated(self, model_id: str, successor: str | None = None) -> bool:
        """Mark a model as deprecated."""
        entry = self._models.get(model_id)
        if entry is None:
            return False
        entry.deprecated = True
        entry.successor = successor
        logger.info("Marked model %s as deprecated (successor: %s)", model_id, successor)
        return True

    def get_deprecated_models(self) -> list[ModelEntry]:
        """List of deprecated models."""
        return [m for m in self._models.values() if m.deprecated]

    # ------------------------------------------------------------------
    # Provider health checks
    # ------------------------------------------------------------------

    async def check_provider_health(self, provider: str) -> ProviderHealthStatus:
        """Check provider availability."""
        cached = self._provider_health.get(provider)
        if cached and (time.time() - cached.checked_at) < _HEALTH_CHECK_TTL:
            return cached

        status = ProviderHealthStatus(
            provider=provider,
            available=False,
            checked_at=time.time(),
        )

        try:
            if provider == "ollama":
                status = await self._check_ollama()
            elif provider in ("openai", "anthropic", "gemini", "openrouter"):
                status = await self._check_api_provider(provider)
            elif provider == "g4f":
                status = self._check_g4f()
            else:
                status.error = f"Unknown provider: {provider}"
        except Exception as exc:
            status.error = str(exc)

        self._provider_health[provider] = status
        return status

    async def check_all_providers(self) -> dict[str, ProviderHealthStatus]:
        """Batch check availability of all providers."""
        providers = set()
        for m in self._models.values():
            if not m.deprecated:
                providers.add(m.provider)

        for p in providers:
            await self.check_provider_health(p)

        return dict(self._provider_health)

    async def _check_ollama(self) -> ProviderHealthStatus:
        """Ollama availability check."""
        try:
            from app.providers.ollama_provider import ollama_provider

            is_up = await ollama_provider.health_check()
            models = await ollama_provider.list_models() if is_up else []
            return ProviderHealthStatus(
                provider="ollama",
                available=is_up,
                checked_at=time.time(),
                available_models=[f"ollama/{m.name}" for m in models],
            )
        except Exception as exc:
            return ProviderHealthStatus(
                provider="ollama",
                available=False,
                checked_at=time.time(),
                error=str(exc),
            )

    async def _check_api_provider(self, provider: str) -> ProviderHealthStatus:
        """Cloud API provider availability check (API key existence verification)."""
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        env_key = env_keys.get(provider, "")
        has_key = bool(os.environ.get(env_key, ""))

        available_models = [
            m.id for m in self._models.values() if m.provider == provider and not m.deprecated
        ]

        return ProviderHealthStatus(
            provider=provider,
            available=has_key,
            checked_at=time.time(),
            available_models=available_models if has_key else [],
            error=None if has_key else f"API key not set: {env_key}",
        )

    def _check_g4f(self) -> ProviderHealthStatus:
        """g4f availability check."""
        try:
            import g4f  # noqa: F401

            available_models = [
                m.id for m in self._models.values() if m.provider == "g4f" and not m.deprecated
            ]
            return ProviderHealthStatus(
                provider="g4f",
                available=True,
                checked_at=time.time(),
                available_models=available_models,
            )
        except ImportError:
            return ProviderHealthStatus(
                provider="g4f",
                available=False,
                checked_at=time.time(),
                error="g4f not installed",
            )

    # ------------------------------------------------------------------
    # Dynamic model update
    # ------------------------------------------------------------------

    def add_model(self, entry: ModelEntry) -> None:
        """Add a model to the registry."""
        self._models[entry.id] = entry

    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the registry."""
        return self._models.pop(model_id, None) is not None

    def update_cost(self, model_id: str, cost_input: float, cost_output: float) -> bool:
        """Update a model's cost information."""
        entry = self._models.get(model_id)
        if entry is None:
            return False
        entry.cost_per_1k_input = cost_input
        entry.cost_per_1k_output = cost_output
        return True

    def update_latest_model_id(self, family_id: str, new_model_id: str) -> bool:
        """Update a family's latest_model_id and auto-save the catalog.

        Automatically reflects AI model updates without manual file editing.

        Args:
            family_id: Family ID (e.g. "anthropic/claude-opus")
            new_model_id: New API model ID (e.g. "claude-opus-4-7")

        Returns:
            Whether the update was successful.
        """
        entry = self._models.get(family_id)
        if entry is None:
            logger.warning("Unknown model family: %s", family_id)
            return False

        old_id = entry.latest_model_id
        entry.latest_model_id = new_model_id
        self.save_catalog()
        logger.info(
            "Auto-updated model %s: %s → %s",
            family_id,
            old_id,
            new_model_id,
        )
        return True

    async def refresh_catalog(self) -> dict[str, str]:
        """Re-check model availability from provider APIs and update the catalog.

        Reflects the latest model state in the catalog without user intervention.
        Also auto-detects and updates the Ollama model list.

        Returns:
            Dictionary of updated models {family_id: new_latest_model_id}.
        """
        updated: dict[str, str] = {}

        # Auto-detect and update Ollama models
        try:
            from app.providers.ollama_provider import ollama_provider

            is_up = await ollama_provider.health_check()
            if is_up:
                models = await ollama_provider.list_models()
                for m in models:
                    family_id = f"ollama/{m.name}"
                    if family_id not in self._models:
                        self.add_model(
                            ModelEntry(
                                id=family_id,
                                provider="ollama",
                                display_name=m.name,
                                latest_model_id=m.name,
                                cost_per_1k_input=0.0,
                                cost_per_1k_output=0.0,
                                tags=["free"],
                            )
                        )
                        updated[family_id] = m.name
                        logger.info("Auto-discovered Ollama model: %s", m.name)
        except Exception as exc:
            logger.debug("Ollama model refresh failed: %s", exc)

        # Auto-update g4f models
        try:
            from app.providers.g4f_provider import _G4F_MODEL_MAP

            for model_key, info in _G4F_MODEL_MAP.items():
                if model_key not in self._models:
                    self.add_model(
                        ModelEntry(
                            id=model_key,
                            provider="g4f",
                            display_name=info.get("description", model_key),
                            latest_model_id=info.get("model", ""),
                            cost_per_1k_input=0.0,
                            cost_per_1k_output=0.0,
                            tags=["free", "subscription"],
                        )
                    )
                    updated[model_key] = info.get("model", "")
        except Exception as exc:
            logger.debug("g4f model refresh failed: %s", exc)

        # Check availability of all providers
        await self.check_all_providers()

        if updated:
            self.save_catalog()
            logger.info("Catalog refreshed: %d models updated", len(updated))

        return updated

    @property
    def catalog_version(self) -> str:
        return self._catalog_version

    @property
    def catalog_path(self) -> Path:
        return self._catalog_path

    @property
    def last_loaded(self) -> float:
        return self._last_loaded

    @property
    def model_count(self) -> int:
        return len(self._models)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_registry: ModelRegistry | None = None
_registry_lock = threading.Lock()


def get_model_registry() -> ModelRegistry:
    """Get the global model registry (thread-safe singleton)."""
    global _registry
    if _registry is not None:
        return _registry
    with _registry_lock:
        # Double-checked locking
        if _registry is None:
            catalog_path = os.environ.get("MODEL_CATALOG_PATH", str(_DEFAULT_CATALOG_PATH))
            _registry = ModelRegistry(catalog_path=catalog_path)
    return _registry


def reload_model_registry() -> ModelRegistry:
    """Reload the model registry (thread-safe)."""
    global _registry
    with _registry_lock:
        catalog_path = os.environ.get("MODEL_CATALOG_PATH", str(_DEFAULT_CATALOG_PATH))
        _registry = ModelRegistry(catalog_path=catalog_path)
    return _registry
