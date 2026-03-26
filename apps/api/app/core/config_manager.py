"""Runtime configuration manager for API keys and provider settings.

Allows changing settings such as API keys and execution modes from
the CLI, API, or application UI without directly editing .env files.

Settings are applied in the following priority order:
1. Environment variables (highest priority)
2. Runtime config file (~/.zero-employee/config.json)
3. .env file
4. Default values
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Runtime config file path
_CONFIG_DIR = Path.home() / ".zero-employee"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# Configurable keys and their descriptions
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
        "description": "UI language: ja | en | zh | ko | pt | tr",
        "description_ja": "UI 言語: ja | en | zh | ko | pt | tr",
        "category": "general",
        "sensitive": "false",
    },
    "SENTRY_DSN": {
        "description": "Sentry DSN for error monitoring",
        "description_ja": "Sentry DSN（エラー監視）",
        "category": "monitoring",
        "sensitive": "true",
    },
    # --- Security ---
    "SANDBOX_LEVEL": {
        "description": "File sandbox level: strict | moderate | permissive",
        "description_ja": "ファイルサンドボックスレベル: strict | moderate | permissive",
        "category": "security",
        "sensitive": "false",
    },
    "SANDBOX_ALLOWED_PATHS": {
        "description": "Comma-separated list of allowed folder paths",
        "description_ja": "許可フォルダパス（カンマ区切り）",
        "category": "security",
        "sensitive": "false",
    },
    "SECURITY_TRANSFER_POLICY": {
        "description": "Data transfer policy: lockdown | restricted | permissive",
        "description_ja": "データ転送ポリシー: lockdown | restricted | permissive",
        "category": "security",
        "sensitive": "false",
    },
    "SECURITY_UPLOAD_ENABLED": {
        "description": "Enable AI upload: true | false",
        "description_ja": "AI アップロードを有効化: true | false",
        "category": "security",
        "sensitive": "false",
    },
    "SECURITY_UPLOAD_REQUIRE_APPROVAL": {
        "description": "Require approval for uploads: true | false",
        "description_ja": "アップロード時に承認を要求: true | false",
        "category": "security",
        "sensitive": "false",
    },
    "PII_AUTO_DETECT": {
        "description": "Enable automatic PII detection: true | false",
        "description_ja": "PII 自動検出を有効化: true | false",
        "category": "security",
        "sensitive": "false",
    },
    # --- Workspace ---
    "WORKSPACE_LOCAL_ACCESS_ENABLED": {
        "description": "Enable local folder access: true | false",
        "description_ja": "ローカルフォルダアクセスを有効化: true | false",
        "category": "workspace",
        "sensitive": "false",
    },
    "WORKSPACE_CLOUD_ACCESS_ENABLED": {
        "description": "Enable cloud storage access: true | false",
        "description_ja": "クラウドストレージアクセスを有効化: true | false",
        "category": "workspace",
        "sensitive": "false",
    },
    "WORKSPACE_CLOUD_PROVIDERS": {
        "description": "Cloud storage providers JSON array (e.g. '[\"google_drive\"]')",
        "description_ja": "クラウドストレージプロバイダー JSON 配列",
        "category": "workspace",
        "sensitive": "false",
    },
    "WORKSPACE_STORAGE_LOCATION": {
        "description": "Artifact storage location: internal | local | cloud",
        "description_ja": "成果物の保存先: internal | local | cloud",
        "category": "workspace",
        "sensitive": "false",
    },
    # --- Additional provider keys ---
    "MISTRAL_API_KEY": {
        "description": "Mistral API key",
        "description_ja": "Mistral API キー",
        "category": "provider",
        "sensitive": "true",
    },
    "COHERE_API_KEY": {
        "description": "Cohere API key",
        "description_ja": "Cohere API キー",
        "category": "provider",
        "sensitive": "true",
    },
    "DEEPSEEK_API_KEY": {
        "description": "DeepSeek API key",
        "description_ja": "DeepSeek API キー",
        "category": "provider",
        "sensitive": "true",
    },
    # --- External tool integrations ---
    "GITHUB_TOKEN": {
        "description": "GitHub personal access token",
        "description_ja": "GitHub パーソナルアクセストークン",
        "category": "integration",
        "sensitive": "true",
    },
    "SLACK_BOT_TOKEN": {
        "description": "Slack Bot OAuth token",
        "description_ja": "Slack Bot OAuth トークン",
        "category": "integration",
        "sensitive": "true",
    },
    "SLACK_SIGNING_SECRET": {
        "description": "Slack signing secret",
        "description_ja": "Slack 署名シークレット",
        "category": "integration",
        "sensitive": "true",
    },
    "DISCORD_BOT_TOKEN": {
        "description": "Discord bot token",
        "description_ja": "Discord Bot トークン",
        "category": "integration",
        "sensitive": "true",
    },
    "NOTION_API_KEY": {
        "description": "Notion API key",
        "description_ja": "Notion API キー",
        "category": "integration",
        "sensitive": "true",
    },
    "JIRA_URL": {
        "description": "Jira instance URL",
        "description_ja": "Jira URL",
        "category": "integration",
        "sensitive": "false",
    },
    "JIRA_API_TOKEN": {
        "description": "Jira API token",
        "description_ja": "Jira API トークン",
        "category": "integration",
        "sensitive": "true",
    },
    "FIGMA_ACCESS_TOKEN": {
        "description": "Figma access token (MCP)",
        "description_ja": "Figma アクセストークン（MCP 経由）",
        "category": "integration",
        "sensitive": "true",
    },
    "LINE_CHANNEL_SECRET": {
        "description": "LINE channel secret",
        "description_ja": "LINE チャネルシークレット",
        "category": "integration",
        "sensitive": "true",
    },
    "LINE_CHANNEL_ACCESS_TOKEN": {
        "description": "LINE channel access token",
        "description_ja": "LINE チャネルアクセストークン",
        "category": "integration",
        "sensitive": "true",
    },
    # --- Media generation ---
    "STABILITY_API_KEY": {
        "description": "Stability AI API key (Stable Diffusion)",
        "description_ja": "Stability AI API キー（Stable Diffusion）",
        "category": "media",
        "sensitive": "true",
    },
    "REPLICATE_API_TOKEN": {
        "description": "Replicate API token (Flux, SVD, etc.)",
        "description_ja": "Replicate API トークン（Flux, SVD等）",
        "category": "media",
        "sensitive": "true",
    },
    "ELEVENLABS_API_KEY": {
        "description": "ElevenLabs API key (voice generation)",
        "description_ja": "ElevenLabs API キー（音声生成）",
        "category": "media",
        "sensitive": "true",
    },
    "SUNO_API_KEY": {
        "description": "Suno API key (music generation)",
        "description_ja": "Suno API キー（音楽生成）",
        "category": "media",
        "sensitive": "true",
    },
    "RUNWAY_API_KEY": {
        "description": "Runway ML API key (video generation)",
        "description_ja": "Runway ML API キー（動画生成）",
        "category": "media",
        "sensitive": "true",
    },
    # --- OAuth ---
    "GOOGLE_CLIENT_ID": {
        "description": "Google OAuth2 client ID",
        "description_ja": "Google OAuth2 クライアント ID",
        "category": "integration",
        "sensitive": "false",
    },
    "GOOGLE_CLIENT_SECRET": {
        "description": "Google OAuth2 client secret",
        "description_ja": "Google OAuth2 クライアントシークレット",
        "category": "integration",
        "sensitive": "true",
    },
    # --- Production ---
    "SECRET_KEY": {
        "description": "Secret key for JWT / encryption (required for production)",
        "description_ja": "JWT / 暗号化用シークレットキー（本番環境必須）",
        "category": "security",
        "sensitive": "true",
    },
    "CORS_ORIGINS": {
        "description": "Allowed CORS origins JSON array",
        "description_ja": "許可 CORS オリジン JSON 配列",
        "category": "security",
        "sensitive": "false",
    },
}


def _ensure_config_dir() -> None:
    """Create the config directory."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict[str, Any]:
    """Load the runtime config file."""
    if not _CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load config file: %s", exc)
        return {}


def _save_config(config: dict[str, Any]) -> None:
    """Save to the runtime config file."""
    _ensure_config_dir()
    _CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    # Restrict file permissions to owner only (to protect API keys)
    try:
        os.chmod(_CONFIG_FILE, 0o600)
    except OSError:
        pass


def get_config_value(key: str) -> str:
    """Get a config value (priority: env var > runtime config > Settings default)."""
    # 1. Environment variables take highest priority
    env_val = os.environ.get(key)
    if env_val is not None:
        return env_val

    # 2. Runtime config file
    config = _load_config()
    if key in config:
        return str(config[key])

    # 3. Settings default
    return str(getattr(settings, key, ""))


def set_config_value(key: str, value: str) -> None:
    """Save a runtime config value and reflect it in the running settings."""
    if key not in CONFIGURABLE_KEYS:
        raise ValueError(f"Unknown config key: {key}")

    # Basic value validation
    if key == "DEFAULT_EXECUTION_MODE" and value not in (
        "quality",
        "speed",
        "cost",
        "free",
        "subscription",
    ):
        raise ValueError(
            f"Invalid execution mode: {value}. "
            "Must be one of: quality, speed, cost, free, subscription"
        )
    if key == "LANGUAGE" and value not in ("ja", "en", "zh", "ko", "pt", "tr"):
        raise ValueError(f"Invalid language: {value}. Must be one of: ja, en, zh, ko, pt, tr")
    if key == "SANDBOX_LEVEL" and value not in ("strict", "moderate", "permissive"):
        raise ValueError(
            f"Invalid sandbox level: {value}. Must be one of: strict, moderate, permissive"
        )
    if key == "SECURITY_TRANSFER_POLICY" and value not in (
        "lockdown",
        "restricted",
        "permissive",
    ):
        raise ValueError(
            f"Invalid transfer policy: {value}. Must be one of: lockdown, restricted, permissive"
        )
    if key == "WORKSPACE_STORAGE_LOCATION" and value not in ("internal", "local", "cloud"):
        raise ValueError(
            f"Invalid storage location: {value}. Must be one of: internal, local, cloud"
        )
    _boolean_keys = {
        "USE_G4F",
        "SECURITY_UPLOAD_ENABLED",
        "SECURITY_UPLOAD_REQUIRE_APPROVAL",
        "PII_AUTO_DETECT",
        "WORKSPACE_LOCAL_ACCESS_ENABLED",
        "WORKSPACE_CLOUD_ACCESS_ENABLED",
    }
    if key in _boolean_keys and value.lower() not in ("true", "false", "1", "0"):
        raise ValueError(f"Invalid boolean value: {value}. Must be true or false")

    config = _load_config()
    config[key] = value
    _save_config(config)

    # Also reflect in the running settings object (only CONFIGURABLE_KEYS allowed)
    if hasattr(settings, key) and key in CONFIGURABLE_KEYS:
        try:
            object.__setattr__(settings, key, value)
        except (TypeError, AttributeError):
            logger.debug("Could not update settings.%s at runtime", key)

    # When LANGUAGE changes, immediately reflect in the i18n module
    if key == "LANGUAGE":
        from app.core.i18n import set_language

        set_language(value)

    logger.info("Config updated: %s", key)


def delete_config_value(key: str) -> bool:
    """Delete a runtime config value."""
    config = _load_config()
    if key in config:
        del config[key]
        _save_config(config)
        return True
    return False


def get_all_config() -> dict[str, dict[str, Any]]:
    """Get all config values (sensitive values are masked)."""
    result: dict[str, dict[str, Any]] = {}
    config = _load_config()

    for key, meta in CONFIGURABLE_KEYS.items():
        value = get_config_value(key)
        is_sensitive = meta.get("sensitive") == "true"

        # Mask sensitive values before returning
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
    """Get the connection status of each provider."""
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
            # Ollama works even with the default URL, so it's always available
            is_configured = True  # Ollama can always be attempted
        else:
            is_configured = bool(value)

        result[provider_id] = {
            "name": info["name"],
            "description": info["description"],
            "configured": is_configured,
        }

    return result


def _get_source(key: str, runtime_config: dict[str, Any]) -> str:
    """Determine the source of a config value."""
    if os.environ.get(key):
        return "environment"
    if key in runtime_config:
        return "config_file"
    if hasattr(settings, key) and getattr(settings, key):
        return "default"
    return "unset"


def apply_runtime_config() -> None:
    """Apply runtime config file values to settings at startup.

    Only overrides with config.json values for items where no environment variable is set.
    """
    config = _load_config()
    applied = 0
    for key, value in config.items():
        if key in CONFIGURABLE_KEYS and not os.environ.get(key):
            if hasattr(settings, key):
                try:
                    object.__setattr__(settings, key, str(value))
                    applied += 1
                except (TypeError, AttributeError):
                    logger.debug("Could not apply runtime config: %s", key)

    # If LANGUAGE is in the runtime config, also reflect in the i18n module
    if "LANGUAGE" in config and not os.environ.get("LANGUAGE"):
        from app.core.i18n import set_language

        set_language(str(config["LANGUAGE"]))

    if applied:
        logger.info("Applied %d runtime config values from %s", applied, _CONFIG_FILE)
