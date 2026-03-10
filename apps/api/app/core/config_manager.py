"""Runtime configuration manager for API keys and provider settings.

.env ファイルを直接編集せずに、CLI・API・アプリケーション画面から
API キーや実行モードなどの設定を変更できるようにする。

設定は以下の優先順位で適用される:
1. 環境変数（最優先）
2. ランタイム設定ファイル (~/.zero-employee/config.json)
3. .env ファイル
4. デフォルト値
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ランタイム設定ファイルのパス
_CONFIG_DIR = Path.home() / ".zero-employee"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# 設定可能なキーとその説明
CONFIGURABLE_KEYS: dict[str, dict[str, str]] = {
    "OPENROUTER_API_KEY": {
        "description": "OpenRouter API key (multiple LLM providers via single key)",
        "description_ja": "OpenRouter API キー（複数LLMを一括利用）",
        "category": "provider",
        "sensitive": "true",
    },
    "OPENAI_API_KEY": {
        "description": "OpenAI API key (GPT-5.4 etc.)",
        "description_ja": "OpenAI API キー（GPT-5.4等）",
        "category": "provider",
        "sensitive": "true",
    },
    "ANTHROPIC_API_KEY": {
        "description": "Anthropic API key (Claude etc.)",
        "description_ja": "Anthropic API キー（Claude等）",
        "category": "provider",
        "sensitive": "true",
    },
    "GEMINI_API_KEY": {
        "description": "Google Gemini API key (free tier available)",
        "description_ja": "Google Gemini API キー（無料枠あり）",
        "category": "provider",
        "sensitive": "true",
    },
    "OLLAMA_BASE_URL": {
        "description": "Ollama server URL (default: http://localhost:11434)",
        "description_ja": "Ollama サーバーURL",
        "category": "provider",
        "sensitive": "false",
    },
    "OLLAMA_DEFAULT_MODEL": {
        "description": "Default Ollama model name",
        "description_ja": "デフォルト Ollama モデル名",
        "category": "provider",
        "sensitive": "false",
    },
    "DEFAULT_EXECUTION_MODE": {
        "description": "Execution mode: quality | speed | cost | free | subscription",
        "description_ja": "実行モード: quality | speed | cost | free | subscription",
        "category": "general",
        "sensitive": "false",
    },
    "USE_G4F": {
        "description": "Enable g4f (API-key-free mode): true | false",
        "description_ja": "g4f（APIキー不要モード）を有効化: true | false",
        "category": "general",
        "sensitive": "false",
    },
    "LANGUAGE": {
        "description": "UI language: ja | en | zh",
        "description_ja": "UI 言語: ja | en | zh",
        "category": "general",
        "sensitive": "false",
    },
    "SENTRY_DSN": {
        "description": "Sentry DSN for error monitoring",
        "description_ja": "Sentry DSN（エラー監視）",
        "category": "monitoring",
        "sensitive": "true",
    },
}


def _ensure_config_dir() -> None:
    """設定ディレクトリを作成する."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict[str, Any]:
    """ランタイム設定ファイルを読み込む."""
    if not _CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load config file: %s", exc)
        return {}


def _save_config(config: dict[str, Any]) -> None:
    """ランタイム設定ファイルに保存する."""
    _ensure_config_dir()
    _CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    # ファイル権限をユーザーのみに制限（API キーを保護）
    try:
        os.chmod(_CONFIG_FILE, 0o600)
    except OSError:
        pass


def get_config_value(key: str) -> str:
    """設定値を取得する（優先順位: 環境変数 > ランタイム設定 > Settings デフォルト）."""
    # 1. 環境変数を最優先
    env_val = os.environ.get(key)
    if env_val is not None:
        return env_val

    # 2. ランタイム設定ファイル
    config = _load_config()
    if key in config:
        return str(config[key])

    # 3. Settings デフォルト
    return str(getattr(settings, key, ""))


def set_config_value(key: str, value: str) -> None:
    """ランタイム設定値を保存し、実行中の settings にも反映する."""
    if key not in CONFIGURABLE_KEYS:
        raise ValueError(f"Unknown config key: {key}")

    config = _load_config()
    config[key] = value
    _save_config(config)

    # 実行中の settings オブジェクトにも反映（次回起動時は config.json から読む）
    if hasattr(settings, key):
        # Pydantic Settings は通常 frozen だが、object.__setattr__ で直接設定
        object.__setattr__(settings, key, value)

    logger.info("Config updated: %s", key)


def delete_config_value(key: str) -> bool:
    """ランタイム設定値を削除する."""
    config = _load_config()
    if key in config:
        del config[key]
        _save_config(config)
        return True
    return False


def get_all_config() -> dict[str, dict[str, Any]]:
    """全設定値を取得する（機密値はマスク）."""
    result: dict[str, dict[str, Any]] = {}
    config = _load_config()

    for key, meta in CONFIGURABLE_KEYS.items():
        value = get_config_value(key)
        is_sensitive = meta.get("sensitive") == "true"

        # 機密値はマスクして返す
        if is_sensitive and value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 12 else "****"
        else:
            masked = value

        result[key] = {
            "value": masked,
            "is_set": bool(value),
            "source": _get_source(key, config),
            "category": meta.get("category", "general"),
            "description": meta.get("description", ""),
            "description_ja": meta.get("description_ja", ""),
            "sensitive": is_sensitive,
        }

    return result


def get_provider_status() -> dict[str, dict[str, Any]]:
    """各プロバイダーの接続状態を取得する."""
    providers = {
        "openrouter": {
            "name": "OpenRouter",
            "key": "OPENROUTER_API_KEY",
            "description": "Multiple LLM providers via single API key",
        },
        "openai": {
            "name": "OpenAI",
            "key": "OPENAI_API_KEY",
            "description": "GPT-5.4, GPT-5 Mini, etc.",
        },
        "anthropic": {
            "name": "Anthropic",
            "key": "ANTHROPIC_API_KEY",
            "description": "Claude Opus 4.6, Sonnet 4.6, Haiku 4.5, etc.",
        },
        "gemini": {
            "name": "Google Gemini",
            "key": "GEMINI_API_KEY",
            "description": "Gemini 2.5 Pro/Flash (free tier available)",
        },
        "ollama": {
            "name": "Ollama (Local)",
            "key": "OLLAMA_BASE_URL",
            "description": "Local LLM (offline, unlimited, free)",
        },
        "g4f": {
            "name": "g4f (Subscription)",
            "key": "USE_G4F",
            "description": "API-key-free mode via web services",
        },
    }

    result = {}
    for provider_id, info in providers.items():
        value = get_config_value(info["key"])
        if provider_id == "g4f":
            is_configured = value.lower() in ("true", "1", "yes")
        elif provider_id == "ollama":
            is_configured = bool(value) and value != "http://localhost:11434"
            # Ollama はデフォルトURLでも使えるので、設定されていなくても有効
            is_configured = True  # Ollama は常に試行可能
        else:
            is_configured = bool(value)

        result[provider_id] = {
            "name": info["name"],
            "description": info["description"],
            "configured": is_configured,
        }

    return result


def _get_source(key: str, runtime_config: dict[str, Any]) -> str:
    """設定値のソースを判定する."""
    if os.environ.get(key):
        return "environment"
    if key in runtime_config:
        return "config_file"
    if hasattr(settings, key) and getattr(settings, key):
        return "default"
    return "unset"


def apply_runtime_config() -> None:
    """起動時にランタイム設定ファイルの値を settings に適用する.

    環境変数が設定されていない項目のみ、config.json の値で上書きする。
    """
    config = _load_config()
    applied = 0
    for key, value in config.items():
        if key in CONFIGURABLE_KEYS and not os.environ.get(key):
            if hasattr(settings, key):
                object.__setattr__(settings, key, str(value))
                applied += 1

    if applied:
        logger.info("Applied %d runtime config values from %s", applied, _CONFIG_FILE)
