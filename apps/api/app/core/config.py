"""Application configuration using pydantic-settings."""

import logging
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEYS = frozenset(
    {
        "change-me-in-production",
        "change-this-to-a-random-secret-key",
    }
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "Zero-Employee Orchestrator"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "CHANGE-ME-in-production"

    # ---------------------------------------------------------------------------
    # CORS — Cross-Origin Resource Sharing
    #
    # 本番環境では以下の変数を必ず設定すること:
    #   CORS_ORIGINS        — 許可するオリジンの JSON 配列 (ワイルドカード "*" は使用しない)
    #                         例: '["https://app.example.com"]'
    #   CORS_ALLOW_METHODS  — 許可する HTTP メソッドの JSON 配列
    #                         例: '["GET","POST","PUT","PATCH","DELETE"]'
    #   CORS_ALLOW_HEADERS  — 許可するリクエストヘッダーの JSON 配列
    #                         例: '["Authorization","Content-Type","X-Request-ID"]'
    #
    # デフォルト値はローカル開発専用。本番環境でのワイルドカード ("*") 使用は禁止。
    # ---------------------------------------------------------------------------
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    # 本番推奨: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_METHODS: list[str] = ["*"]
    # 本番推奨: ["Authorization", "Content-Type", "X-Request-ID", "Accept"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./zero_employee_orchestrator.db"

    # LLM Providers (all optional — configure at least one to enable AI execution)
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = ""  # auto-detect if empty
    OLLAMA_TIMEOUT: int = 300  # seconds (local LLMs can be slow on CPU)
    OLLAMA_DIRECT: bool = True  # use direct HTTP instead of LiteLLM for Ollama

    # Local RAG store directory (for file-based vector DB)
    RAG_STORE_DIR: str = ".zero_employee/rag_store"

    # Language: ja (Japanese) / en (English) / zh (Chinese)
    LANGUAGE: str = "ja"

    # g4f (subscription/no-API-key mode)
    # When true, g4f is loaded at startup enabling free AI access without API keys.
    USE_G4F: bool = True

    # Default execution mode: quality | speed | cost | free | subscription
    DEFAULT_EXECUTION_MODE: str = "quality"

    # Model catalog path (for dynamic model registry)
    # Default: apps/api/model_catalog.json
    MODEL_CATALOG_PATH: str = ""

    # Sentry DSN for error monitoring (optional)
    SENTRY_DSN: str = ""

    # Sandbox mode: local | docker | workers
    SANDBOX_MODE: str = "local"

    # Cloudflare account ID (for Workers deployment)
    CLOUDFLARE_ACCOUNT_ID: str = ""

    # Credential store directory (AI agents cannot access this)
    CREDENTIAL_DIR: str = "/etc/zero-employee/credentials"


settings = Settings()

# ---------------------------------------------------------------------------
# Startup safety check: reject insecure defaults in production (DEBUG=false)
# ---------------------------------------------------------------------------
if settings.SECRET_KEY.lower() in _INSECURE_DEFAULT_KEYS:
    if settings.DEBUG:
        warnings.warn(
            "SECRET_KEY is set to an insecure default. "
            "Set a strong random value before deploying to production.",
            UserWarning,
            stacklevel=1,
        )
    else:
        raise RuntimeError(
            "SECRET_KEY is still set to an insecure default value. "
            'Generate a secure key with: python -c "import secrets; print(secrets.token_urlsafe(32))" '
            "and set it in your .env file or environment variables. "
            "If this is intentional for local development, set DEBUG=true."
        )
