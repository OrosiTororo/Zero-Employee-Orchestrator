"""Dynamic Model Registry — LLM モデルの動的管理と自動更新.

ハードコードされたモデル名に依存せず、外部設定ファイル (model_catalog.json) と
プロバイダー API からの動的検出を組み合わせてモデルを管理する。

主な機能:
  - JSON ファイルベースのモデルカタログ管理
  - プロバイダー API へのモデル可用性チェック
  - 廃止モデルの自動検出とフォールバック
  - コスト情報の動的更新
  - モデルカタログの定期リフレッシュ
"""

from __future__ import annotations

import json
import logging
import os
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
    """個別モデルの定義."""

    id: str                          # e.g. "anthropic/claude-opus-4-6"
    provider: str                    # e.g. "anthropic"
    display_name: str                # e.g. "Claude Opus 4.6"
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_tokens: int = 4096
    supports_tools: bool = False
    supports_vision: bool = False
    deprecated: bool = False         # サービス終了フラグ
    successor: str | None = None     # 後継モデル ID
    tags: list[str] = field(default_factory=list)  # e.g. ["quality", "speed"]


@dataclass
class ModeCatalog:
    """実行モード別のモデル優先リスト."""

    quality: list[str] = field(default_factory=list)
    speed: list[str] = field(default_factory=list)
    cost: list[str] = field(default_factory=list)
    free: list[str] = field(default_factory=list)
    subscription: list[str] = field(default_factory=list)


@dataclass
class QualitySLAModels:
    """品質モード別のモデル設定."""

    draft: dict[str, list[str]] = field(default_factory=dict)
    standard: dict[str, list[str]] = field(default_factory=dict)
    high: dict[str, list[str]] = field(default_factory=dict)
    critical: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ProviderHealthStatus:
    """プロバイダーの健全性ステータス."""

    provider: str
    available: bool
    checked_at: float
    available_models: list[str] = field(default_factory=list)
    error: str | None = None


class ModelRegistry:
    """動的モデルレジストリ.

    JSON カタログファイルからモデル定義を読み込み、
    プロバイダー API への可用性チェックと組み合わせて
    最適なモデル選択を行う。
    """

    def __init__(self, catalog_path: str | Path | None = None) -> None:
        self._catalog_path = Path(catalog_path) if catalog_path else _DEFAULT_CATALOG_PATH
        self._models: dict[str, ModelEntry] = {}
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
        """JSON カタログファイルからモデル定義を読み込む."""
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

            # モデル定義
            for m in data.get("models", []):
                entry = ModelEntry(
                    id=m["id"],
                    provider=m.get("provider", m["id"].split("/")[0]),
                    display_name=m.get("display_name", m["id"]),
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

            # モード別カタログ
            modes = data.get("mode_catalog", {})
            self._mode_catalog = ModeCatalog(
                quality=modes.get("quality", []),
                speed=modes.get("speed", []),
                cost=modes.get("cost", []),
                free=modes.get("free", []),
                subscription=modes.get("subscription", []),
            )

            # 品質SLA設定
            sla = data.get("quality_sla", {})
            self._quality_sla = QualitySLAModels(
                draft=sla.get("draft", {}),
                standard=sla.get("standard", {}),
                high=sla.get("high", {}),
                critical=sla.get("critical", {}),
            )

            self._last_loaded = time.time()
            logger.info(
                "Loaded model catalog v%s with %d models",
                self._catalog_version,
                len(self._models),
            )
        except Exception as exc:
            logger.error("Failed to load model catalog: %s", exc)

    def reload(self) -> None:
        """カタログを再読み込みする."""
        self._models.clear()
        self._load_catalog()

    def save_catalog(self) -> None:
        """現在のレジストリ状態を JSON カタログファイルに保存."""
        data: dict[str, Any] = {
            "version": self._catalog_version,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "description": (
                "Zero-Employee Orchestrator モデルカタログ. "
                "モデルの追加・削除・コスト更新はこのファイルを編集してください。"
                "アプリ再起動またはAPI経由のリロードで反映されます。"
            ),
            "models": [
                {
                    "id": m.id,
                    "provider": m.provider,
                    "display_name": m.display_name,
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
        """モデルIDからエントリを取得."""
        return self._models.get(model_id)

    def get_active_model(self, model_id: str) -> ModelEntry | None:
        """非廃止のモデルを取得。廃止されている場合は後継モデルを返す."""
        entry = self._models.get(model_id)
        if entry is None:
            return None
        if entry.deprecated and entry.successor:
            successor = self._models.get(entry.successor)
            if successor and not successor.deprecated:
                logger.info(
                    "Model %s is deprecated, using successor %s",
                    model_id, entry.successor,
                )
                return successor
        return entry

    def list_models(self, provider: str | None = None, include_deprecated: bool = False) -> list[ModelEntry]:
        """モデル一覧を取得."""
        result = []
        for m in self._models.values():
            if not include_deprecated and m.deprecated:
                continue
            if provider and m.provider != provider:
                continue
            result.append(m)
        return result

    def get_models_for_mode(self, mode: str) -> list[str]:
        """実行モードに対応するモデルIDリストを取得."""
        catalog_map = {
            "quality": self._mode_catalog.quality,
            "speed": self._mode_catalog.speed,
            "cost": self._mode_catalog.cost,
            "free": self._mode_catalog.free,
            "subscription": self._mode_catalog.subscription,
        }
        models = catalog_map.get(mode, self._mode_catalog.quality)
        # 廃止モデルを後継に自動置換
        return self._resolve_deprecated(models)

    def get_sla_models(self, quality_mode: str) -> dict[str, list[str]]:
        """品質モードに対応するモデル設定を取得."""
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
        """モデルのコストを見積もる."""
        # g4f / ollama は常に無料
        if model_id.startswith(("g4f/", "ollama/")):
            return 0.0

        entry = self._models.get(model_id)
        if entry:
            return (
                (input_tokens / 1000 * entry.cost_per_1k_input)
                + (output_tokens / 1000 * entry.cost_per_1k_output)
            )
        # フォールバック: 未知のモデルは中程度のコストを仮定
        return (input_tokens / 1000 * 0.001) + (output_tokens / 1000 * 0.002)

    def get_cost_table(self) -> dict[str, dict[str, float]]:
        """CostGuard 互換のコストテーブルを生成."""
        table: dict[str, dict[str, float]] = {}
        for m in self._models.values():
            if m.deprecated:
                continue
            # プロバイダープレフィックスなしのキーも生成（CostGuard互換）
            short_name = m.id.split("/", 1)[-1] if "/" in m.id else m.id
            table[short_name] = {
                "input": m.cost_per_1k_input,
                "output": m.cost_per_1k_output,
            }
            table[m.id] = {
                "input": m.cost_per_1k_input,
                "output": m.cost_per_1k_output,
            }
        return table

    # ------------------------------------------------------------------
    # Deprecation handling
    # ------------------------------------------------------------------

    def _resolve_deprecated(self, model_ids: list[str]) -> list[str]:
        """廃止モデルを後継モデルに自動置換."""
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
        """モデルを廃止としてマークする."""
        entry = self._models.get(model_id)
        if entry is None:
            return False
        entry.deprecated = True
        entry.successor = successor
        logger.info("Marked model %s as deprecated (successor: %s)", model_id, successor)
        return True

    def get_deprecated_models(self) -> list[ModelEntry]:
        """廃止済みモデルの一覧."""
        return [m for m in self._models.values() if m.deprecated]

    # ------------------------------------------------------------------
    # Provider health checks
    # ------------------------------------------------------------------

    async def check_provider_health(self, provider: str) -> ProviderHealthStatus:
        """プロバイダーの可用性をチェック."""
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
        """全プロバイダーの可用性を一括チェック."""
        providers = set()
        for m in self._models.values():
            if not m.deprecated:
                providers.add(m.provider)

        for p in providers:
            await self.check_provider_health(p)

        return dict(self._provider_health)

    async def _check_ollama(self) -> ProviderHealthStatus:
        """Ollama の可用性チェック."""
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
        """クラウド API プロバイダーの可用性チェック（APIキー存在確認）."""
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        env_key = env_keys.get(provider, "")
        has_key = bool(os.environ.get(env_key, ""))

        available_models = [
            m.id for m in self._models.values()
            if m.provider == provider and not m.deprecated
        ]

        return ProviderHealthStatus(
            provider=provider,
            available=has_key,
            checked_at=time.time(),
            available_models=available_models if has_key else [],
            error=None if has_key else f"API key not set: {env_key}",
        )

    def _check_g4f(self) -> ProviderHealthStatus:
        """g4f の可用性チェック."""
        try:
            import g4f  # noqa: F401
            available_models = [
                m.id for m in self._models.values()
                if m.provider == "g4f" and not m.deprecated
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
        """モデルをレジストリに追加."""
        self._models[entry.id] = entry

    def remove_model(self, model_id: str) -> bool:
        """モデルをレジストリから削除."""
        return self._models.pop(model_id, None) is not None

    def update_cost(self, model_id: str, cost_input: float, cost_output: float) -> bool:
        """モデルのコスト情報を更新."""
        entry = self._models.get(model_id)
        if entry is None:
            return False
        entry.cost_per_1k_input = cost_input
        entry.cost_per_1k_output = cost_output
        return True

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


def get_model_registry() -> ModelRegistry:
    """グローバルモデルレジストリを取得."""
    global _registry
    if _registry is None:
        catalog_path = os.environ.get("MODEL_CATALOG_PATH", str(_DEFAULT_CATALOG_PATH))
        _registry = ModelRegistry(catalog_path=catalog_path)
    return _registry


def reload_model_registry() -> ModelRegistry:
    """モデルレジストリを再読み込み."""
    global _registry
    catalog_path = os.environ.get("MODEL_CATALOG_PATH", str(_DEFAULT_CATALOG_PATH))
    _registry = ModelRegistry(catalog_path=catalog_path)
    return _registry
