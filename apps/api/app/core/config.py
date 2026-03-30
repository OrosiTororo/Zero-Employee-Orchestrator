"""Application configuration using pydantic-settings."""

import logging
import os
import secrets
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEYS = frozenset(
    {
        "change-me-in-production",
        "change-this-to-a-random-secret-key",
        "auto-generated-change-me",
    }
)


def _auto_secret_key() -> str:
    """Return SECRET_KEY from env / .env, or generate a random key for local dev.

    This allows fresh clones to start the server immediately without
    manually creating a .env file.  The generated key is ephemeral —
    it changes on every restart, so JWT sessions won't survive restarts.
    In production, always set SECRET_KEY explicitly.
    """
    env_key = os.environ.get("SECRET_KEY", "").strip()
    if env_key and env_key.lower() not in _INSECURE_DEFAULT_KEYS:
        return env_key
    # No explicit key — generate one for this process
    return secrets.token_urlsafe(32)


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
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security — auto-generated for local dev if not explicitly set
    SECRET_KEY: str = _auto_secret_key()

    # CORS — In production (DEBUG=false), defaults to Tauri origins only.
    # Override via CORS_ORIGINS env var with comma-separated URLs.
    # In development (DEBUG=true), localhost origins are also included.
    CORS_ORIGINS: list[str] = [
        "tauri://localhost",
        "https://tauri.localhost",
        "http://tauri.localhost",
    ]

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

    # Language: en (English) / ja (Japanese) / zh (Chinese) / ko (Korean) / pt (Portuguese) / tr (Turkish)
    LANGUAGE: str = "en"

    # g4f (subscription/no-API-key mode)
    # When true, g4f is loaded at startup enabling free AI access without API keys.
    USE_G4F: bool = True

    # Default execution mode: quality | speed | cost | free | subscription
    DEFAULT_EXECUTION_MODE: str = "quality"

    # Model catalog path (for dynamic model registry)
    # Default: apps/api/model_catalog.json
    MODEL_CATALOG_PATH: str = ""

    # Google OAuth (optional — users configure via `zero-employee config set`)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Sentry DSN for error monitoring (optional)
    SENTRY_DSN: str = ""

    # Sandbox mode: local | docker | workers
    SANDBOX_MODE: str = "local"

    # Cloudflare account ID (for Workers deployment)
    CLOUDFLARE_ACCOUNT_ID: str = ""

    # Credential store directory (AI agents cannot access this via IAM)
    # In Docker, overridden by ENV to /app/data/credentials
    CREDENTIAL_DIR: str = os.path.join(
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
        "zero-employee",
        "credentials",
    )


settings = Settings()

# ---------------------------------------------------------------------------
# Automatically add localhost origins in development mode
# ---------------------------------------------------------------------------
if settings.DEBUG:
    _dev_origins = ["http://localhost:3000", "http://localhost:5173"]
    for origin in _dev_origins:
        if origin not in settings.CORS_ORIGINS:
            settings.CORS_ORIGINS.append(origin)

# ---------------------------------------------------------------------------
# Startup safety check: warn on insecure defaults in development,
# reject them in production (DEBUG=false)
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
